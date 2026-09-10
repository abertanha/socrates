"""Session conduction — derived state, pure availability, redirect payloads.

Tickets 13–14 / spec `session-conduction`: the harness conducts, the model
asks. The session's order stops living in the prompt: a governor derives the
conduction state from persisted facts at tool-dispatch time and out-of-state
calls receive an explaining redirect (current state + admissible next steps),
never a bare "no".

Enforced seams: the Need gate (before the Opening only the Opening exists),
`run_opening` exactly once, Modeling Activity precedence for `task` (made
proactive, where the pipeline store already enforced it reactively), and the
pass/Probe pulse's placement — it runs inside the chapter specialists, and
on the orchestrator surface it exists only in the tail.

Ticket 17 adds the in-chapter rules (D2/D3): the treadmill — at most one
unlapidated Proposition while a chapter is open, with the maieutic valve
(ground born from Probe resolution is never tool-gated; it enters as
unlapidated ground the treadmill then counts); no new pass while a Batch
awaits the user; quiet-is-counting for the chapter door's declaration; and
the orchestrator propose tag-gate (D6 "propose tag k"). All three are
counting over persisted facts — never judgment (ADR-0002) — and all are
derived at read time (ADR-0001: no new persisted fields).

Ticket 20 adds the only-sink rules (D4/D6): `await_satisfaction` lives in
the tail and in the door's third answer, nowhere else; and the silence
redirect the outer loop-guard injects when the model stops without an
affirmative Satisfaction — the session's end is a steering wheel, never
model silence.

Ticket 22 / spec `need-refinement` adds the Need amendment gate:
`amend_need` is admitted only while the Requirements chapter is open —
its first pass (begun, or next in precedence with nothing completed), or
a reopening through Iteration, which re-enters the same facts shape.
Anywhere else the redirect names the Iteration path: a Need-level shift
outside Requirements is an L4-grade event that travels through Iteration,
which reopens Requirements and re-admits the amendment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from deepagents.backends.protocol import BackendProtocol
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import ToolMessage

from socrates.paths import (
    BATCHES_PATH,
    NEED_PATH,
    PROPOSITIONS_PATH,
    SCENARIOS_PATH,
)
from socrates.pipeline import (
    ACTIVITIES_IN_ORDER,
    ACTIVITY_SUBAGENT_TYPE,
    ModelingActivity,
    PipelineStore,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from langgraph.prebuilt.tool_node import ToolCallRequest

PRE_OPENING = "pre-opening"
BETWEEN_CHAPTERS = "between-chapters"
TAIL = "tail"

# The two governed surfaces: the main orchestrator and a chapter specialist
# (which conducts its own regime — one roof per chapter, D1/D5).
ORCHESTRATOR = "orchestrator"
CHAPTER = "chapter"

OPENING_TOOL = "run_opening"
TASK_TOOL = "task"
PROPOSE_TOOL = "propose_proposition"
COMPLETE_TOOL = "complete_modeling_activity"
SATISFACTION_TOOL = "await_satisfaction"
AMEND_TOOL = "amend_need"

# The pass/Probe pulse. Inside the chapters it is the specialist's own
# regime; on the orchestrator surface it is admissible only in the tail
# (`run_iteration` is excluded — a door move, admissible in any state).
PULSE_TOOLS = frozenset(
    {
        "select_exploration_budget",
        "reconcile",
        "record_scenarios",
        "run_assertion_tests",
        "probe_batch",
        "defer_conflict",
    }
)

# Pass attempts proper — the tools a new pass would run. `defer_conflict`
# is deliberately absent: deferring is a resolution move (it can park a
# batched Conflict from the tool surface), not a pass, so a pending Batch
# never redirects it (ticket 17 ruling).
PASS_TOOLS = frozenset(
    {
        "select_exploration_budget",
        "reconcile",
        "record_scenarios",
        "run_assertion_tests",
        "probe_batch",
    }
)

# A Proposition still owed a pass. Rejected and Superseded ground is dead —
# it can never be lapidated, and counting it would deadlock the treadmill
# (ticket 17 ruling).
_LIVE_STATUSES = frozenset({"candidate", "flagged", "accepted"})

# The lapidation path the redirects point to (Scenarios first, Assertion
# Tests after them).
_LAPIDATION_NEXT = ["record_scenarios", "run_assertion_tests"]
_RESOLVE_BATCH_NEXT = ["resolve the pending Probe Batch"]


@dataclass(frozen=True)
class ConductionState:
    """The session's conduction state, derived — never persisted (ADR-0001)."""

    need_registered: bool
    active: ModelingActivity | None
    completed: tuple[ModelingActivity, ...]
    # Ticket 17 — in-chapter facts, likewise derived at read time:
    # live Propositions that have never been through a pass, as
    # (id, activity) pairs, and whether a Probe Batch awaits the user.
    unlapidated: tuple[tuple[str, ModelingActivity], ...] = ()
    pending_batch: bool = False

    @property
    def label(self) -> str:
        if not self.need_registered:
            return PRE_OPENING
        if len(self.completed) >= len(ACTIVITIES_IN_ORDER):
            return TAIL
        if self.active is not None:
            return f"chapter:{self.active}"
        return BETWEEN_CHAPTERS

    @property
    def expected_activity(self) -> ModelingActivity | None:
        """The next chapter in precedence, or None outside the chapter walk."""
        if not self.need_registered:
            return None
        index = len(self.completed)
        if index >= len(ACTIVITIES_IN_ORDER):
            return None
        return ACTIVITIES_IN_ORDER[index]


def read_conduction_state(backend: BackendProtocol) -> ConductionState:
    """Derive the conduction state from the Model's filesystem facts."""
    need = backend.read(NEED_PATH)
    pipeline = PipelineStore(backend).snapshot()
    return ConductionState(
        need_registered=not need.error and need.file_data is not None,
        active=pipeline.get("active"),
        completed=tuple(pipeline.get("completed", ())),
        unlapidated=_read_unlapidated(backend),
        pending_batch=_read_pending_batch(backend),
    )


def _read_json(backend: BackendProtocol, path: str) -> dict[str, Any] | None:
    result = backend.read(path)
    if result.error or result.file_data is None:
        return None
    content = result.file_data["content"]
    if not content.strip():
        return None
    return json.loads(content)


def _read_unlapidated(
    backend: BackendProtocol,
) -> tuple[tuple[str, ModelingActivity], ...]:
    """Live Propositions with no recorded Scenario — never through a pass.

    Lapidation ruling (ticket 17): a Proposition counts as lapidated once at
    least one Scenario is recorded for it. `record_scenarios` is the pass's
    first lapidation step, so it is the earliest — and sufficient — signal:
    Assertion Tests always follow Scenarios, acceptance is a user judgment
    (never bookkeeping), and "alive when an earlier pass completed" is not
    derivable without new persisted state.
    """
    propositions = _read_json(backend, PROPOSITIONS_PATH) or {}
    scenarios = _read_json(backend, SCENARIOS_PATH) or {}
    lapidated = {
        s.get("proposition_id") for s in scenarios.get("scenarios", [])
    }
    return tuple(
        (item["id"], item["activity"])
        for item in propositions.get("propositions", [])
        if item.get("status") in _LIVE_STATUSES
        and item.get("id") not in lapidated
    )


def _read_pending_batch(backend: BackendProtocol) -> bool:
    """Whether a Probe Batch awaits the user (any ground — passes examine
    the whole Model)."""
    batches = _read_json(backend, BATCHES_PATH) or {}
    return any(
        batch.get("status") == "open" for batch in batches.get("batches", [])
    )


def conduction_check(
    state: ConductionState,
    tool_name: str,
    tool_args: dict[str, Any] | None = None,
    *,
    surface: str = ORCHESTRATOR,
    activity: ModelingActivity | None = None,
) -> dict[str, Any] | None:
    """Pure availability rule: None when admissible, else the redirect payload.

    Deterministic over the derived facts — same facts in, same decision out.
    ``surface`` selects which regime's rules apply (the orchestrator's
    placement rules vs the chapter specialist's in-chapter rules);
    ``activity`` is the chapter surface's own Modeling Activity, scoping the
    door's quiet count.
    """
    args = tool_args or {}
    if state.label == PRE_OPENING:
        if tool_name == OPENING_TOOL:
            return None
        return _redirect(
            state,
            tool_name,
            args,
            admissible_next=[OPENING_TOOL],
            reason=(
                "the Need is not registered yet — the Opening elicits and "
                "persists it before any modeling exists"
            ),
        )
    if tool_name == OPENING_TOOL:
        return _redirect(
            state,
            tool_name,
            args,
            admissible_next=_chapter_walk_next(state),
            reason=(
                "the Opening runs exactly once and the Need is already "
                "registered"
            ),
        )
    if tool_name == SATISFACTION_TOOL and state.label != TAIL:
        # D6: Satisfaction lives in the tail and in the door's third
        # answer, nowhere else (D4 rejected Satisfaction-from-anywhere —
        # it strands pending work behind an early exit).
        return _redirect(
            state,
            tool_name,
            args,
            admissible_next=_chapter_walk_next(state),
            reason=(
                "Satisfaction lives in the tail and in the door's third "
                "answer, nowhere else — the session is in "
                f"{state.label}; continue the chapter walk, and each "
                "door carries the question when its chapter is quiet"
            ),
        )
    if tool_name == AMEND_TOOL:
        if _requirements_open(state):
            return None
        return _redirect(
            state,
            tool_name,
            args,
            admissible_next=list(_ITERATION_NEXT),
            reason=(
                "the Need is amendable only while the Requirements "
                "chapter is open — its first pass, or a reopening through "
                f"Iteration (the session is in {state.label}); a "
                "Need-level shift outside Requirements is an L4-grade "
                "event: surface it and carry it through Iteration, which "
                "reopens Requirements and re-admits the amendment"
            ),
        )
    if tool_name == PROPOSE_TOOL:
        return _check_propose(state, args, surface)
    if tool_name == COMPLETE_TOOL and surface == CHAPTER:
        return _check_quiet(state, activity)
    if tool_name in PASS_TOOLS and state.pending_batch:
        # The Batch glossary rule, made mechanical: "the user clarifies
        # every Conflict in it before the next pass runs".
        return _redirect(
            state,
            tool_name,
            args,
            admissible_next=list(_RESOLVE_BATCH_NEXT),
            reason=(
                f"a Probe Batch still awaits the user — {tool_name} is a "
                "pass attempt and no new pass runs until every Conflict in "
                "the pending Batch is resolved or deferred"
            ),
        )
    if surface == ORCHESTRATOR:
        if tool_name == TASK_TOOL:
            expected = state.expected_activity
            if expected is None:
                return _redirect(
                    state,
                    tool_name,
                    args,
                    admissible_next=[_TAIL_NEXT],
                    reason=(
                        "all Modeling Activities are completed — the session "
                        "continues in the tail until Satisfaction"
                    ),
                )
            expected_task = f"task: {ACTIVITY_SUBAGENT_TYPE[expected]}"
            if args.get("subagent_type") != ACTIVITY_SUBAGENT_TYPE[expected]:
                return _redirect(
                    state,
                    tool_name,
                    args,
                    admissible_next=[expected_task],
                    reason=(
                        f"Modeling Activity precedence: expected '{expected}', "
                        f"attempted '{args.get('subagent_type')}'"
                    ),
                )
        if tool_name in PULSE_TOOLS and state.label != TAIL:
            # The pulse's home is the chapters; on this surface, only the tail.
            home = state.active if state.active is not None else state.expected_activity
            if home is None:  # pragma: no cover — non-tail post-Opening has one
                return None
            home_task = f"task: {ACTIVITY_SUBAGENT_TYPE[home]}"
            if state.active is not None:
                reason = (
                    f"the pass/Probe pulse runs inside the open {state.active} "
                    f"chapter — continue it via `{home_task}`; on this surface "
                    "the pulse exists only in the tail"
                )
            else:
                reason = (
                    f"the pass/Probe pulse runs inside the chapters — open the "
                    f"next one via `{home_task}`; on this surface the pulse "
                    "exists only in the tail"
                )
            return _redirect(
                state,
                tool_name,
                args,
                admissible_next=[home_task],
                reason=reason,
            )
    return None


def _check_propose(
    state: ConductionState,
    args: dict[str, Any],
    surface: str,
) -> dict[str, Any] | None:
    """The propose rules: the tag-gate on the orchestrator surface, the
    treadmill inside an open chapter."""
    if surface == ORCHESTRATOR and "activity" in args:
        # D6 "propose tag k": while a chapter is open — or next in
        # precedence, none begun — the orchestrator's propose is admitted
        # only tagged with that chapter's Activity. In the tail any tag
        # enters: the valve stays on (ground's tag, chapter stays closed).
        if state.active is not None:
            gate = state.active
        elif state.label == TAIL:
            gate = None
        else:
            gate = state.expected_activity
        if gate is not None and args.get("activity") != gate:
            gate_task = f"task: {ACTIVITY_SUBAGENT_TYPE[gate]}"
            return _redirect(
                state,
                PROPOSE_TOOL,
                args,
                admissible_next=[
                    gate_task,
                    f"propose_proposition (tag {gate})",
                ],
                reason=(
                    f"propose tag gate: '{gate}' is the chapter in "
                    f"precedence ({state.label}), so only ground tagged "
                    f"'{gate}' enters here — attempted tag "
                    f"'{args.get('activity')}' (in the tail any tag enters)"
                ),
            )
    # The treadmill (D2): while a chapter is open, at most one unlapidated
    # Proposition at any moment, on either surface. The valve exception is
    # structural — ground born from Probe resolution never passes through
    # tool dispatch, so it is never gated; it simply enters as unlapidated
    # ground this count then demands lapidation of.
    if state.active is not None and state.unlapidated:
        owed = ", ".join(pid for pid, _ in state.unlapidated)
        return _redirect(
            state,
            PROPOSE_TOOL,
            args,
            admissible_next=list(_LAPIDATION_NEXT),
            reason=(
                f"treadmill: Proposition(s) {owed} have never been through "
                "a pass — lapidate them (Scenarios, then Assertion Tests) "
                "before proposing the next one; only ground born from Probe "
                "resolution enters without waiting"
            ),
        )
    return None


def _check_quiet(
    state: ConductionState,
    activity: ModelingActivity | None,
) -> dict[str, Any] | None:
    """Quiet is counting (D3): the door's declaration is admissible when
    every Proposition born in this chapter has been through ≥1 pass and no
    Batch awaits the user on any ground. Deferred Conflicts are not a fact
    the door reads at all — parking never blocks. Bookkeeping only, never
    a quality judgment (ADR-0002)."""
    if activity is not None:
        owed = [
            pid for pid, born in state.unlapidated if born == activity
        ]
        if owed:
            return _redirect(
                state,
                COMPLETE_TOOL,
                {},
                admissible_next=list(_LAPIDATION_NEXT),
                reason=(
                    f"the chapter is not quiet: Proposition(s) "
                    f"{', '.join(owed)} born in '{activity}' have never "
                    "been through a pass — quiet is counting, so lapidate "
                    "them before declaring completion"
                ),
            )
    if state.pending_batch:
        return _redirect(
            state,
            COMPLETE_TOOL,
            {},
            admissible_next=list(_RESOLVE_BATCH_NEXT),
            reason=(
                "the chapter is not quiet: a Probe Batch still awaits the "
                "user — resolve or defer every Conflict in it before "
                "declaring completion"
            ),
        )
    return None


def _requirements_open(state: ConductionState) -> bool:
    """Ticket 22 ruling: "Requirements open" covers both first-pass shapes
    — the chapter begun, and post-Opening next-in-precedence before
    anything begins (where the Opening's raw first answer most needs
    sharpening) — plus the Iteration reopening, which re-enters the same
    facts shape (active Requirements, nothing downstream completed)."""
    return state.active == "requirements" or (
        state.active is None
        and state.expected_activity == "requirements"
    )


_TAIL_NEXT = "await_satisfaction"

# The amendment's way back when attempted out of state (ticket 22): a
# Need-level shift outside Requirements travels through Iteration (L4),
# which reopens Requirements and re-admits the amendment.
_ITERATION_NEXT = ["run_iteration (carry the L4 that invalidates the Need assumption)"]

# The tail's other admissible move, named for the silence redirect: the
# passes keep running wherever the Model still has ground to examine.
_TAIL_PULSE_NEXT = "pass/Probe pulse (propose, lapidate, resolve)"


def silence_redirect(state: ConductionState) -> dict[str, Any]:
    """The loop-guard's re-injection payload (D4): when the model stops
    without an affirmative Satisfaction, the session continues — this is
    the redirect injected as the next turn, naming the state and the
    admissible next steps (the same shape as every other redirect, so the
    model's map back is one it already knows how to read). The admissible
    step is always one the state actually admits: pre-Opening, the only
    admissible tool is the Opening itself (D6 row 1)."""
    if not state.need_registered:
        admissible_next = [OPENING_TOOL]
        reason = (
            "the session ends only through the user's Satisfaction — "
            "silence is not an end; the session has not opened yet — "
            "greet the user and elicit the Need via `run_opening`"
        )
    elif state.label == TAIL:
        admissible_next = [_TAIL_NEXT, _TAIL_PULSE_NEXT]
        reason = (
            "the session ends only through the user's Satisfaction — "
            "silence is not an end; ask via `await_satisfaction` or run "
            "another pass over the Model"
        )
    else:
        admissible_next = _chapter_walk_next(state)
        reason = (
            "the session ends only through the user's Satisfaction — "
            "silence is not an end; continue with the admissible next "
            "step (while chapters remain, the doors carry the "
            "Satisfaction answer)"
        )
    return {
        "ok": False,
        "conduction": {
            "state": state.label,
            "attempted": "(silence — no tool call)",
            "admissible_next": admissible_next,
        },
        "redirect": reason,
    }


def _chapter_walk_next(state: ConductionState) -> list[str]:
    expected = state.expected_activity
    if expected is None:
        return [_TAIL_NEXT]
    return [f"task: {ACTIVITY_SUBAGENT_TYPE[expected]}"]


def _attempted(tool_name: str, args: dict[str, Any]) -> str:
    if tool_name == TASK_TOOL and "subagent_type" in args:
        return f"task({args['subagent_type']})"
    return tool_name


def _redirect(
    state: ConductionState,
    tool_name: str,
    args: dict[str, Any],
    *,
    admissible_next: list[str],
    reason: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "conduction": {
            "state": state.label,
            "attempted": _attempted(tool_name, args),
            "admissible_next": list(admissible_next),
        },
        "redirect": reason,
    }


class ConductionMiddleware(AgentMiddleware):
    """Gates tool dispatch on the derived conduction state.

    Reads the Model's filesystem at dispatch time and short-circuits
    out-of-state calls with the redirect payload instead of executing them.
    In-state calls reach their handler untouched. Side-effect-free: it only
    reads and answers (ticket 13/14 shape).

    One instance per surface: the orchestrator's middleware applies the
    placement rules (`task` precedence, tail-only pulse, propose tag-gate);
    a chapter specialist's middleware applies the in-chapter rules
    (treadmill, pending-Batch, quiet) scoped to its own Modeling Activity.
    """

    def __init__(
        self,
        backend: BackendProtocol,
        *,
        surface: str = ORCHESTRATOR,
        activity: ModelingActivity | None = None,
    ) -> None:
        self._backend = backend
        self._surface = surface
        self._activity = activity

    def wrap_tool_call(
        self,
        request: "ToolCallRequest",
        handler: "Callable[[ToolCallRequest], ToolMessage | Any]",
    ) -> ToolMessage | Any:
        return self._gate(request) or handler(request)

    async def awrap_tool_call(
        self,
        request: "ToolCallRequest",
        handler: "Callable[[ToolCallRequest], Awaitable[ToolMessage | Any]]",
    ) -> ToolMessage | Any:
        return self._gate(request) or await handler(request)

    def _gate(self, request: "ToolCallRequest") -> ToolMessage | None:
        call = request.tool_call
        redirect = conduction_check(
            read_conduction_state(self._backend),
            call["name"],
            call.get("args") or {},
            surface=self._surface,
            activity=self._activity,
        )
        if redirect is None:
            return None
        return ToolMessage(
            content=json.dumps(redirect),
            tool_call_id=call.get("id") or "",
            name=call["name"],
        )
