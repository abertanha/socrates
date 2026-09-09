"""Interview, Proposition-lifecycle, and Modeling Activity tools."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from deepagents.backends.protocol import BackendProtocol
from langchain_core.tools import BaseTool, StructuredTool
from langchain.tools import tool
from langgraph.types import interrupt

from socrates.deliverable import DeliverableComposer, is_affirmative_satisfaction
from socrates.opening import (
    OPENING_GREETING,
    OPENING_QUESTION,
    render_opening,
)
from socrates.paths import NEED_PATH
from socrates.pipeline import ModelingActivity, PipelineStore
from socrates.proposition import PropositionStore
from socrates.inference import InferenceEngine
from socrates.coverage import CoverageStore

SATISFACTION_QUESTION = (
    "Does this feel right to you as it stands, or is there more to work through?"
)

# The door's three answers (ticket 17 / D3-D4): close the chapter, keep it
# open, or route to the Satisfaction flow without closing it.
DOOR_ANSWERS = ("close", "not yet", "satisfaction")

# The pass/Probe pulse, stated once for every chapter specialist: one
# regime per chapter — propose, lapidate, resolve under one roof (D1).
_ACTIVITY_PULSE = (
    " Run the pass/Probe pulse inside this chapter: call "
    "`select_exploration_budget` at the start of each pass so Coverage sets "
    "the exploration allowance — an allowance, never a quality gate; from "
    "pass 2, `reconcile` first (L2/L3 only — an empty findings array is "
    "valid, never fabricate findings); then `record_scenarios` → "
    "`run_assertion_tests` (L1/L4) → `probe_batch` for L1–L3. Deferrable "
    "Conflicts may be deferred. L4 Conflicts are unavoidable — never defer "
    "or Probe them; surface them and let the orchestrator carry them to "
    "Iteration. The treadmill keeps one unlapidated Proposition at a time: "
    "lapidate each Proposition (Scenarios, Assertion Tests) before proposing "
    "the next — ground born from Probe resolution is exempt and enters "
    "immediately. Call `complete_modeling_activity` when the chapter is "
    "quiet; the user then answers at the door: close, not yet, or "
    "Satisfaction."
)

ACTIVITY_PROMPTS: dict[ModelingActivity, str] = {
    "requirements": (
        "You are the Requirements specialist. Elicit and bound the Need: what "
        "every later Model must include and exclude. Propose Need-scoped "
        "Propositions only." + _ACTIVITY_PULSE
    ),
    "domain_modeling": (
        "You are the Domain Modeling specialist. Bound the Subject Domain and "
        "establish ubiquitous language and entities — what the domain is — "
        "within the Need. Propose structural Propositions only." + _ACTIVITY_PULSE
    ),
    "behavioral_specification": (
        "You are the Behavioral Specification specialist. Infer conceptual "
        "behavior and relationships between entities as domain rules — what "
        "the domain does. Never propose functional requirements "
        "('the system shall...')." + _ACTIVITY_PULSE
    ),
}


def _proposition_payload(prop) -> dict:
    return {
        "ok": True,
        "id": prop.id,
        "statement": prop.statement,
        "status": prop.status,
        "activity": prop.activity,
        "reason": prop.reason,
        "flagged_against_id": prop.flagged_against_id,
        "accepted_via": prop.accepted_via,
    }


_GENERIC_CONFIRMS = frozenset(
    {"yes", "y", "confirm", "confirmed", "ok", "true"}
)

# Polarity-specific affirmations confirm only their own action; the
# opposite word declines it, leaving the Proposition's status preserved.
_ACTION_CONFIRMS: dict[str, frozenset[str]] = {
    "accept": _GENERIC_CONFIRMS | {"accept", "accepted"},
    "reject": _GENERIC_CONFIRMS | {"reject", "rejected"},
}


def _is_confirmed(answer: Any, action: str) -> bool:
    """Whether the interrupt resume confirms ``action``.

    Affirmations are contextual to the action's polarity: "reject" never
    confirms an Acceptance (and "accept" never confirms a Rejection) — the
    cross-polarity word declines the action instead. English-only for now
    (bilingual support is deferred until after the first real-model
    testing pass).
    """
    if answer is True:
        return True
    if not isinstance(answer, str):
        return False
    normalized = " ".join(answer.strip().casefold().split())
    if normalized.startswith("yes"):
        return True
    return normalized in _ACTION_CONFIRMS.get(action, _GENERIC_CONFIRMS)


# The door's answer vocabulary (ticket 17) — contextual polarity like
# accept/reject: "yes" closes, "no" keeps the chapter open, a Satisfaction
# word routes to the Satisfaction flow. An unrecognized answer keeps the
# chapter open — the door never closes or ends the session on a mumble.
# English-only, consistent with the deferred bilingual confirm/decline work.
_DOOR_SATISFACTION_WORDS = frozenset(
    {
        "satisfaction",
        "satisfied",
        "im satisfied",
        "i am satisfied",
        "enough",
        "stop here",
        "terminate",
    }
)
_DOOR_CLOSE_WORDS = _GENERIC_CONFIRMS | {
    "close",
    "closed",
    "done",
    "proceed",
    "move on",
}
_DOOR_NOT_YET_WORDS = frozenset(
    {
        "not yet",
        "no",
        "n",
        "later",
        "wait",
        "not now",
        "keep open",
        "keep it open",
        "continue",
        "keep going",
    }
)


def _parse_door_answer(answer: Any) -> str:
    """Map a door resume to one of ``DOOR_ANSWERS`` ("close" / "not_yet" /
    "satisfaction")."""
    if isinstance(answer, bool):
        return "close" if answer else "not_yet"
    if not isinstance(answer, str):
        return "not_yet"
    normalized = " ".join(answer.strip().casefold().split())
    if not normalized:
        return "not_yet"
    if normalized in _DOOR_SATISFACTION_WORDS or "satisf" in normalized:
        return "satisfaction"
    if normalized in _DOOR_CLOSE_WORDS:
        return "close"
    if normalized in _DOOR_NOT_YET_WORDS:
        return "not_yet"
    if normalized.startswith("yes"):
        return "close"
    return "not_yet"


def _ask_satisfaction(
    inference: InferenceEngine, deliverable: DeliverableComposer
) -> str:
    """The Satisfaction interrupt and its follow-through — shared by the
    tail's `await_satisfaction` and the door's third answer (ticket 17)."""
    # Warning only — Satisfaction is never hard-blocked (ADR-0002).
    warning = inference.satisfaction_warning()
    answer = str(
        interrupt(
            {
                "kind": "satisfaction",
                "question": SATISFACTION_QUESTION,
                "deferred_warning": warning,
            }
        )
    )
    if is_affirmative_satisfaction(answer):
        paths = deliverable.materialize()
        joined = ", ".join(paths)
        return (
            f"Satisfaction signal received: {answer}. "
            f"Conceptual Domain Model materialized at {joined}."
        )
    return f"Satisfaction signal received: {answer}"


def _declined(action: str, proposition_id: str, status: str) -> str:
    return json.dumps(
        {
            "ok": False,
            "declined": True,
            "proposition_id": proposition_id,
            "status": status,
            "error": f"User declined {action}; Proposition {proposition_id} "
            f"remains {status}",
        }
    )


def build_session_tools(backend: BackendProtocol) -> Sequence[BaseTool]:
    """Tools for the main Socrates orchestrator.

    The pass/Probe pulse is composed in too (the tail's passes); the
    conduction governor admits it on this surface only in the tail and
    redirects out-of-state attempts into the chapters.
    """
    store = PropositionStore(backend)
    inference = InferenceEngine(backend)
    deliverable = DeliverableComposer(backend)

    @tool
    def run_opening() -> str:
        """Open the session: show the banner and greeting, then ask what the user is building.

        Call this before writing any prose of your own — it is the first thing
        the user sees, and it already does the greeting for you.
        """
        need = str(
            interrupt(
                {
                    "kind": "opening",
                    "greeting": OPENING_GREETING,
                    "question": OPENING_QUESTION,
                    "display": render_opening(),
                }
            )
        )
        backend.write(NEED_PATH, need)
        return f"Need persisted to {NEED_PATH}."

    @tool
    def await_satisfaction() -> str:
        """Ask the user, in plain words, whether the Model is right as it stands.

        Surfaces a non-blocking warning when deferred Conflicts remain open. On
        an affirmative answer, materializes the Conceptual Domain Model as
        Glossary + Structure + Rules under /model/deliverable/.
        """
        return _ask_satisfaction(inference, deliverable)

    @tool
    def propose_proposition(statement: str, activity: ModelingActivity) -> str:
        """Propose a Proposition tagged with the Modeling Activity that produced it."""
        try:
            prop = store.propose(statement, activity=activity)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        raised = inference.touch_propositions(prop.id)
        payload = _proposition_payload(prop)
        if raised:
            payload["re_raised_conflict_ids"] = [c.id for c in raised]
        return json.dumps(payload)

    @tool
    def accept_proposition(
        proposition_id: str,
        via_proposition_id: str = "",
    ) -> str:
        """Accept a Candidate into the Model after the user's direct Acceptance signal.

        Optional via_proposition_id marks indirect Acceptance (foundation for cascades).
        """
        answer = interrupt(
            {
                "kind": "accept",
                "proposition_id": proposition_id,
                "via_proposition_id": via_proposition_id or None,
                "question": (
                    f"Do you Accept Proposition {proposition_id} into the Model?"
                ),
            }
        )
        if not _is_confirmed(answer, "accept"):
            try:
                status = store.get(proposition_id).status
            except ValueError:
                status = "unknown"
            return _declined("Acceptance", proposition_id, status)
        try:
            prop = store.accept(
                proposition_id,
                via_proposition_id=via_proposition_id or None,
            )
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        raised = inference.touch_propositions(proposition_id)
        payload = _proposition_payload(prop)
        if raised:
            payload["re_raised_conflict_ids"] = [c.id for c in raised]
        return json.dumps(payload)

    @tool
    def reject_proposition(proposition_id: str, reason: str) -> str:
        """Reject a Proposition with an explicit reason; records it in the Rejection Guardrail."""
        answer = interrupt(
            {
                "kind": "reject",
                "proposition_id": proposition_id,
                "reason": reason,
                "question": (
                    f"Do you Reject Proposition {proposition_id}? Reason: {reason}"
                ),
            }
        )
        if not _is_confirmed(answer, "reject"):
            try:
                status = store.get(proposition_id).status
            except ValueError:
                status = "unknown"
            return _declined("Rejection", proposition_id, status)
        try:
            prop = store.reject(proposition_id, reason)
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        raised = inference.touch_propositions(proposition_id)
        payload = _proposition_payload(prop)
        if raised:
            payload["re_raised_conflict_ids"] = [c.id for c in raised]
        return json.dumps(payload)

    @tool
    def run_iteration(conflict_id: str) -> str:
        """Hand an L4 Conflict to Iteration: propose phase, confirm, reopen activity."""
        try:
            result = inference.run_iteration(conflict_id)
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps({"ok": True, **result})

    return [
        run_opening,
        await_satisfaction,
        propose_proposition,
        accept_proposition,
        reject_proposition,
        run_iteration,
        *build_pulse_tools(backend),
    ]


def build_pulse_tools(backend: BackendProtocol) -> Sequence[BaseTool]:
    """The pass/Probe pulse — one regime per chapter, and the tail's passes.

    Shared by the chapter specialists (unconditional) and the main
    orchestrator, where the conduction governor admits it only in the tail.
    """
    inference = InferenceEngine(backend)
    coverage = CoverageStore(backend)

    @tool
    def reconcile(findings_json: str) -> str:
        """From pass 2, surface latent L2/L3 Conflicts before Scenarios / Assertion Tests.

        An empty findings array is valid — it records that Reconciliation ran
        and surfaced nothing. Never fabricate findings to satisfy the gate.
        """
        try:
            findings = json.loads(findings_json)
            if not isinstance(findings, list):
                raise ValueError("findings_json must be a JSON array")
            surfaced = inference.reconcile(findings)
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(
            {
                "ok": True,
                "pass": inference.current_pass(),
                "conflicts": [c.__dict__ for c in surfaced],
            }
        )

    @tool
    def record_scenarios(proposition_id: str, scenarios_json: str) -> str:
        """Record several Need-relevant Scenarios for a Proposition (Relevance Filter enforced)."""
        try:
            scenarios = json.loads(scenarios_json)
            if not isinstance(scenarios, list):
                raise ValueError("scenarios_json must be a JSON array")
            recorded = inference.record_scenarios(proposition_id, scenarios)
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(
            {
                "ok": True,
                "proposition_id": proposition_id,
                "scenarios": [s.__dict__ for s in recorded],
            }
        )

    @tool
    def run_assertion_tests(proposition_id: str, outcomes_json: str) -> str:
        """Run Assertion Tests for a Proposition; non-surviving Scenarios surface Conflicts."""
        try:
            outcomes = json.loads(outcomes_json)
            if not isinstance(outcomes, list):
                raise ValueError("outcomes_json must be a JSON array")
            surfaced = inference.run_assertion_tests(proposition_id, outcomes)
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(
            {
                "ok": True,
                "proposition_id": proposition_id,
                "conflicts": [c.__dict__ for c in surfaced],
            }
        )

    @tool
    def probe_batch() -> str:
        """Gather open L1–L3 Conflicts into one Batch and Probe the user.

        L4 Conflicts are not Probe-resolved — use run_iteration.
        """
        try:
            result = inference.probe_batch()
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps({"ok": True, **result})

    @tool
    def defer_conflict(conflict_id: str) -> str:
        """Defer an open Conflict (any level) to resolve later; may re-raise on touch."""
        try:
            result = inference.defer_conflict(conflict_id)
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps({"ok": True, **result})

    @tool
    def select_exploration_budget() -> str:
        """Set this pass's recursion_limit from Coverage (∝ 1/Coverage).

        Coverage rises as Conflicts-per-pass decline. The budget is an
        exploration allowance only — never a quality gate. Subagents receive
        the same limit.
        """
        # Allowance, not a grader (ADR-0002/0004); propagation guards #1698.
        try:
            budget = coverage.select_budget()
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps({"ok": True, **budget})

    return [
        reconcile,
        record_scenarios,
        run_assertion_tests,
        probe_batch,
        defer_conflict,
        select_exploration_budget,
    ]


def build_activity_tools(
    backend: BackendProtocol,
    activity: ModelingActivity,
) -> Sequence[BaseTool]:
    """Chapter specialist tools: Proposition lifecycle + the pass/Probe pulse.

    One regime per Modeling Activity (D1) — propose, lapidate, resolve under
    one roof. The pulse composes in unconditionally here; conduction governs
    it only on the orchestrator surface. The chapter door (ticket 17) lives
    in `complete_modeling_activity`: when the chapter is quiet, its
    declaration interrupts the user with three answers — close / not yet /
    Satisfaction.
    """
    store = PropositionStore(backend)
    pipeline = PipelineStore(backend)
    inference = InferenceEngine(backend)
    deliverable = DeliverableComposer(backend)

    def propose_proposition(statement: str) -> str:
        try:
            pipeline.begin(activity)
            prop = store.propose(statement, activity=activity)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(_proposition_payload(prop))

    def accept_proposition(
        proposition_id: str,
        via_proposition_id: str = "",
    ) -> str:
        answer = interrupt(
            {
                "kind": "accept",
                "proposition_id": proposition_id,
                "via_proposition_id": via_proposition_id or None,
                "question": (
                    f"Do you Accept Proposition {proposition_id} into the Model?"
                ),
            }
        )
        if not _is_confirmed(answer, "accept"):
            try:
                status = store.get(proposition_id).status
            except ValueError:
                status = "unknown"
            return _declined("Acceptance", proposition_id, status)
        try:
            prop = store.accept(
                proposition_id,
                via_proposition_id=via_proposition_id or None,
            )
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(_proposition_payload(prop))

    def reject_proposition(proposition_id: str, reason: str) -> str:
        answer = interrupt(
            {
                "kind": "reject",
                "proposition_id": proposition_id,
                "reason": reason,
                "question": (
                    f"Do you Reject Proposition {proposition_id}? Reason: {reason}"
                ),
            }
        )
        if not _is_confirmed(answer, "reject"):
            try:
                status = store.get(proposition_id).status
            except ValueError:
                status = "unknown"
            return _declined("Rejection", proposition_id, status)
        try:
            prop = store.reject(proposition_id, reason)
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(_proposition_payload(prop))

    def complete_modeling_activity() -> str:
        """Declare the chapter complete — the user confirms at the door.

        The conduction governor has already established the chapter is quiet
        (every Proposition born in it through ≥1 pass, no Batch pending);
        quiet is bookkeeping, "good enough to close" is the user's judgment
        (ADR-0002). The declaration interrupts with three answers (D3/D4):
        "close" completes the chapter, "not yet" keeps it open (the
        maieutic valve stays live), "satisfaction" routes to the
        Satisfaction flow WITHOUT closing the chapter.
        """
        answer = interrupt(
            {
                "kind": "door",
                "activity": activity,
                "question": (
                    f"Confirm closing Modeling Activity '{activity}'?"
                ),
                "answers": list(DOOR_ANSWERS),
            }
        )
        door = _parse_door_answer(answer)
        if door == "not_yet":
            return json.dumps(
                {
                    "ok": True,
                    "door": "not_yet",
                    "activity": activity,
                    "chapter_open": True,
                }
            )
        if door == "satisfaction":
            outcome = _ask_satisfaction(inference, deliverable)
            return json.dumps(
                {
                    "ok": True,
                    "door": "satisfaction",
                    "activity": activity,
                    "chapter_open": True,
                    "satisfaction": outcome,
                }
            )
        try:
            # A chapter with no Propositions is vacuously quiet (D3): its
            # declaration opens and closes the door in one step.
            pipeline.begin(activity)
            pipeline.complete(activity)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(
            {"ok": True, "completed": activity, "door": "close"}
        )

    return [
        StructuredTool.from_function(
            func=propose_proposition,
            name="propose_proposition",
            description=(
                f"Propose a Proposition in the {activity} Modeling Activity. "
                "Triages to Candidate, or Flagged if it resembles the Rejection Guardrail."
            ),
        ),
        StructuredTool.from_function(
            func=accept_proposition,
            name="accept_proposition",
            description=(
                "Accept a Candidate into the Model after the user's direct "
                "Acceptance signal."
            ),
        ),
        StructuredTool.from_function(
            func=reject_proposition,
            name="reject_proposition",
            description=(
                "Reject a Proposition with an explicit reason; records it in "
                "the Rejection Guardrail."
            ),
        ),
        StructuredTool.from_function(
            func=complete_modeling_activity,
            name="complete_modeling_activity",
            description=(
                f"Declare the {activity} Modeling Activity complete when the "
                "chapter is quiet — every Proposition born in it has been "
                "through a pass (Scenarios / Assertion Tests) and no Batch "
                "awaits the user. The declaration opens the door: the user "
                "answers close, not yet, or Satisfaction."
            ),
        ),
        *build_pulse_tools(backend),
    ]
