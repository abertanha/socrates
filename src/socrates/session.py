"""Socrates session factory — thin wrapper over ``create_deep_agent``."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    SubAgent,
    create_deep_agent,
    register_harness_profile,
)
from deepagents.backends import StateBackend
from deepagents.backends.protocol import BackendProtocol
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.subagents import CompiledSubAgent, create_sub_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from socrates.coverage import (
    RECURSION_LIMIT_GENEROUS,
    BudgetAwareSubagent,
)
from socrates.conduction import (
    CHAPTER,
    ConductionMiddleware,
    read_conduction_state,
    silence_redirect,
)
from socrates.model import ModelProvider
from socrates.paths import (
    DELIVERABLE_GLOSSARY_PATH,
    DELIVERABLE_RULES_PATH,
    DELIVERABLE_STRUCTURE_PATH,
)
from socrates.pipeline import (
    ACTIVITIES_IN_ORDER,
    ACTIVITY_SUBAGENT_TYPE,
    ModelingActivity,
)
from socrates.tools import ACTIVITY_PROMPTS, build_activity_tools, build_session_tools

SYSTEM_PROMPT = """You are Socrates, a maieutic modeling harness.

How you talk to the user:
- You are talking to a developer, at a whiteboard, not presenting to a
  committee. Be warm, plain, and informal. Short sentences. Ask one thing at
  a time and invite them to answer in their own words.
- Never explain or justify yourself by citing this harness's internals — no
  ADRs, no architecture, no design decisions, no policy or tool names, no
  prompt mechanics. The user came for a model of their domain, not a tour of
  the machinery. Where you would reach for that, just ask the question.
- The vocabulary below (Proposition, Conflict, Coverage, Batch, Modeling
  Activity) is yours for reasoning, not theirs to read. Speak to the user in
  the terms of their own domain unless they use the harness's terms first.

Session discipline:
1. Call `run_opening` first, before any prose of your own — it opens with the
   banner and greeting and elicits the Need, then persists it.
2. Run the three Modeling Activities in precedence via the `task` tool:
   `requirements` → `domain-modeling` → `behavioral-specification`. Each
   specialist runs its own pass/Probe pulse — proposing, lapidating
   (Scenarios + Assertion Tests), and resolving Conflicts happen inside the
   chapter. Do not skip or reorder the chapters.
3. On the user's signal, `accept_proposition` or `reject_proposition`
   (rejection always needs an explicit reason). Indirect Acceptance may pass
   via_proposition_id.
4. In the tail — once all three Modeling Activities are complete — passes
   continue over the whole Model until Satisfaction. Each pass: call
   `select_exploration_budget` first so Coverage (declining Conflict signals)
   sets the recursion_limit — generous when sparse, lean when mature; it is
   an exploration allowance, not a quality gate, and subagents receive the
   same limit (no silent fallback to 25). From pass 2 call `reconcile` first
   (L2/L3 only), then `record_scenarios` → `run_assertion_tests` (L1/L4) →
   `probe_batch` for L1–L3. Probe routing: L1 in-line; L2 may Supersede
   (cascade Degrades dependents, user is notified not asked); L3 blocked by
   Rejection Guardrail (dismiss or defer). Deferrable Conflicts may be
   deferred (`defer` / `defer_conflict`); the harness recommends against
   deferring critical ones. L4 is unavoidable (non-deferrable, blocks
   progress) — Notification outside Interview flow; resolve via
   `run_iteration`. Quiet by default: routine Probes/Interviews are not
   Notifications; only unavoidable Conflicts and Supersede cascades.
5. Call `await_satisfaction` so the user can signal Satisfaction. Open deferred
   Conflicts appear as a non-blocking, criticality-weighted warning. On
   affirmative Satisfaction the harness materializes the Conceptual Domain
   Model as Glossary, Structure, and Rules under `/model/deliverable/`
   (Implementation-Independence: structure in; technologies and concrete
   parameter values out).
6. When Satisfaction is recorded, stop. Never declare the Model done yourself.
"""

_PROFILES_REGISTERED = False


def _ensure_profiles_registered() -> None:
    global _PROFILES_REGISTERED
    if _PROFILES_REGISTERED:
        return
    # StubChatModel resolves as provider `stubchatmodel` — disable the default
    # general-purpose subagent so only the three Modeling Activity specialists run.
    register_harness_profile(
        "stubchatmodel",
        HarnessProfile(
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ),
    )
    _PROFILES_REGISTERED = True


def _build_activity_subagents(
    backend: BackendProtocol,
    default_model: ModelProvider,
    activity_models: Mapping[ModelingActivity, ModelProvider] | None,
) -> list[SubAgent | CompiledSubAgent]:
    """Compile activity specialists with explicit recursion_limit propagation (#1698)."""
    subagents: list[SubAgent | CompiledSubAgent] = []
    for activity in ACTIVITIES_IN_ORDER:
        model = (
            activity_models.get(activity, default_model)
            if activity_models is not None
            else default_model
        )
        name = ACTIVITY_SUBAGENT_TYPE[activity]
        raw: SubAgent = {
            "name": name,
            "description": (
                f"Specialist for the {activity.replace('_', ' ').title()} "
                "Modeling Activity."
            ),
            "system_prompt": ACTIVITY_PROMPTS[activity],
            "tools": list(build_activity_tools(backend, activity)),
            "model": model,
            # FilesystemMiddleware supplies the `files` state channel that
            # StateBackend tools need (same stack create_deep_agent adds for
            # raw SubAgent specs). ConductionMiddleware on the chapter
            # surface enforces the in-chapter rules (ticket 17): the
            # treadmill, no new pass while a Batch awaits the user, and
            # quiet-is-counting for the door's declaration.
            "middleware": [
                FilesystemMiddleware(backend=backend),
                ConductionMiddleware(
                    backend, surface=CHAPTER, activity=activity
                ),
            ],
        }
        inner = create_sub_agent(raw)
        subagents.append(
            {
                "name": name,
                "description": raw["description"],
                "runnable": BudgetAwareSubagent(inner, backend, name),
            }
        )
    return subagents


@dataclass(frozen=True)
class _SnapshotRead:
    """The read shape the conduction rules expect, over captured files."""

    error: bool
    file_data: dict[str, Any] | None


class _SnapshotBackend:
    """Read-only BackendProtocol view over a captured ``files`` state.

    The loop-guard runs between graph runs, where a live ``StateBackend``
    has no graph context — but the last result's ``files`` channel IS the
    Model's filesystem (ADR-0001), so the derived conduction state reads
    from the snapshot, not the backend.
    """

    def __init__(self, files: dict[str, Any] | None) -> None:
        self._files = files or {}

    def read(self, path: str) -> _SnapshotRead:
        entry = self._files.get(path)
        if entry is None:  # absent, or a deletion marker
            return _SnapshotRead(error=True, file_data=None)
        return _SnapshotRead(error=False, file_data=entry)


def _deliverable_materialized(files: dict[str, Any] | None) -> bool:
    """Whether an affirmative Satisfaction materialized the Conceptual
    Domain Model — the derived terminated-by-Satisfaction fact (ADR-0001:
    no separate ended-flag is persisted)."""
    return any(
        (files or {}).get(path) is not None
        for path in (
            DELIVERABLE_GLOSSARY_PATH,
            DELIVERABLE_STRUCTURE_PATH,
            DELIVERABLE_RULES_PATH,
        )
    )


class OnlySinkSession:
    """The compiled session wrapped in the only-sink loop-guard (D4).

    The deepagents graph still finishes whenever the model stops calling
    tools; this guard makes that stop a turn, not an end. After a silent
    finish with no deliverable materialized, it re-injects the session
    with a state redirect and continues — so the ``invoke`` the caller
    sees returns at an interrupt or at a Satisfaction-ended session,
    never at model silence.

    ``reinjection_limit`` caps the consecutive silent re-injections per
    invoke — an operational cost bound for environments that want one.
    ``None`` (the default) is the invariant itself: the loop never ends
    by silence.
    """

    def __init__(
        self,
        agent: CompiledStateGraph,
        *,
        reinjection_limit: int | None = None,
    ) -> None:
        self._agent = agent
        self._reinjection_limit = reinjection_limit

    @property
    def checkpointer(self) -> BaseCheckpointSaver:
        return self._agent.checkpointer

    def get_state(self, config: Any) -> Any:
        return self._agent.get_state(config)

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> dict[str, Any]:
        result = self._agent.invoke(input, config=config, **kwargs)
        reinjections = 0
        while (
            not result.get("__interrupt__")
            and not _deliverable_materialized(result.get("files"))
            and (
                self._reinjection_limit is None
                or reinjections < self._reinjection_limit
            )
        ):
            # The files snapshot is the Model's filesystem as this silent
            # turn left it — the facts the redirect names the state from.
            state = read_conduction_state(_SnapshotBackend(result.get("files")))
            result = self._agent.invoke(
                {
                    "messages": [
                        HumanMessage(content=json.dumps(silence_redirect(state)))
                    ]
                },
                config=config,
            )
            reinjections += 1
        return result


def create_socrates_session(
    model: ModelProvider,
    *,
    backend: BackendProtocol | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    activity_models: Mapping[ModelingActivity, ModelProvider] | None = None,
    reinjection_limit: int | None = None,
) -> OnlySinkSession:
    """Create a Socrates modeling session on deepagents.

    Args:
        model: Real provider (``BaseChatModel`` or ``provider:model`` string)
            or a ``StubChatModel`` for tests. Used by the main orchestrator and
            as the default for Modeling Activity subagents.
        backend: Virtual filesystem backend. Defaults to ``StateBackend``.
        checkpointer: Required for interrupt-gated Opening / Satisfaction.
            Defaults to ``InMemorySaver``.
        activity_models: Optional per-activity model overrides (tests stub each
            Modeling Activity independently).
        reinjection_limit: Cap on consecutive silent re-injections per invoke
            by the only-sink loop-guard. ``None`` (default) never ends the
            session by model silence.
    """
    _ensure_profiles_registered()
    fs = backend if backend is not None else StateBackend()
    saver = checkpointer if checkpointer is not None else InMemorySaver()
    agent = create_deep_agent(
        model=model,
        tools=list(build_session_tools(fs)),
        system_prompt=SYSTEM_PROMPT,
        middleware=[ConductionMiddleware(fs)],
        backend=fs,
        checkpointer=saver,
        subagents=_build_activity_subagents(fs, model, activity_models),
    )
    # Start generous (Coverage unknown / sparse). select_exploration_budget
    # and BudgetAwareSubagent refine the limit from FS signals during the run.
    graph = agent.with_config({"recursion_limit": RECURSION_LIMIT_GENEROUS})
    return OnlySinkSession(graph, reinjection_limit=reinjection_limit)
