"""Socrates session factory — thin wrapper over ``create_deep_agent``."""

from __future__ import annotations

from collections.abc import Mapping

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    SubAgent,
    create_deep_agent,
    register_harness_profile,
)
from deepagents.backends import StateBackend
from deepagents.backends.protocol import BackendProtocol
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from socrates.model import ModelProvider
from socrates.pipeline import (
    ACTIVITIES_IN_ORDER,
    ACTIVITY_SUBAGENT_TYPE,
    ModelingActivity,
)
from socrates.tools import ACTIVITY_PROMPTS, build_activity_tools, build_session_tools

SYSTEM_PROMPT = """You are Socrates, a maieutic modeling harness.

Session discipline:
1. Call `run_opening` to elicit the user's Need and persist it.
2. Run the three Modeling Activities in precedence via the `task` tool:
   `requirements` → `domain-modeling` → `behavioral-specification`.
   Each is a specialist subagent with its own posture and tool subset;
   do not skip or reorder them. Prefer proposing inside the active activity.
3. On the user's signal, `accept_proposition` or `reject_proposition`
   (rejection always needs an explicit reason). Indirect Acceptance may pass
   via_proposition_id.
4. Inference pass: from pass 2 call `reconcile` first (L2/L3 only), then
   `record_scenarios` → `run_assertion_tests` (L1/L4) → `probe_batch` for L1–L3.
   Probe routing: L1 in-line; L2 may Supersede (cascade Degrades dependents,
   user is notified not asked); L3 blocked by Rejection Guardrail (dismiss only).
   L4 (Accepted×Accepted) → `run_iteration` (propose most-upstream activity;
   user confirms; activity reopens against the current Model).
5. Call `await_satisfaction` so the user can signal Satisfaction.
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
) -> list[SubAgent]:
    subagents: list[SubAgent] = []
    for activity in ACTIVITIES_IN_ORDER:
        model = (
            activity_models.get(activity, default_model)
            if activity_models is not None
            else default_model
        )
        subagents.append(
            {
                "name": ACTIVITY_SUBAGENT_TYPE[activity],
                "description": (
                    f"Specialist for the {activity.replace('_', ' ').title()} "
                    "Modeling Activity."
                ),
                "system_prompt": ACTIVITY_PROMPTS[activity],
                "tools": list(build_activity_tools(backend, activity)),
                "model": model,
            }
        )
    return subagents


def create_socrates_session(
    model: ModelProvider,
    *,
    backend: BackendProtocol | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    activity_models: Mapping[ModelingActivity, ModelProvider] | None = None,
) -> CompiledStateGraph:
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
    """
    _ensure_profiles_registered()
    fs = backend if backend is not None else StateBackend()
    saver = checkpointer if checkpointer is not None else InMemorySaver()
    return create_deep_agent(
        model=model,
        tools=list(build_session_tools(fs)),
        system_prompt=SYSTEM_PROMPT,
        backend=fs,
        checkpointer=saver,
        subagents=_build_activity_subagents(fs, model, activity_models),
    )
