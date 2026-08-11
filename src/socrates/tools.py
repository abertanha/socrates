"""Interview, Proposition-lifecycle, and Modeling Activity tools."""

from __future__ import annotations

import json
from collections.abc import Sequence

from deepagents.backends.protocol import BackendProtocol
from langchain_core.tools import BaseTool, StructuredTool
from langchain.tools import tool
from langgraph.types import interrupt

from socrates.paths import NEED_PATH
from socrates.pipeline import ModelingActivity, PipelineStore
from socrates.proposition import PropositionStore
from socrates.inference import InferenceEngine

OPENING_QUESTION = "What Need should this Model serve?"
SATISFACTION_QUESTION = (
    "Do you signal Satisfaction with the Model as it stands?"
)

ACTIVITY_PROMPTS: dict[ModelingActivity, str] = {
    "requirements": (
        "You are the Requirements specialist. Elicit and bound the Need: what "
        "every later Model must include and exclude. Propose Need-scoped "
        "Propositions only. When finished, call complete_modeling_activity."
    ),
    "domain_modeling": (
        "You are the Domain Modeling specialist. Bound the Subject Domain and "
        "establish ubiquitous language and entities — what the domain is — "
        "within the Need. Propose structural Propositions only. When finished, "
        "call complete_modeling_activity."
    ),
    "behavioral_specification": (
        "You are the Behavioral Specification specialist. Infer conceptual "
        "behavior and relationships between entities as domain rules — what "
        "the domain does. Never propose functional requirements "
        "('the system shall...'). When finished, call complete_modeling_activity."
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


def build_session_tools(backend: BackendProtocol) -> Sequence[BaseTool]:
    """Tools for the main Socrates orchestrator."""
    store = PropositionStore(backend)
    inference = InferenceEngine(backend)

    @tool
    def run_opening() -> str:
        """Opening: elicit the Need from the user and persist it as the Model's first content."""
        need = str(
            interrupt(
                {
                    "kind": "opening",
                    "question": OPENING_QUESTION,
                }
            )
        )
        backend.write(NEED_PATH, need)
        return f"Need persisted to {NEED_PATH}."

    @tool
    def await_satisfaction() -> str:
        """Ask whether the user signals Satisfaction; blocks until they answer."""
        answer = str(
            interrupt(
                {
                    "kind": "satisfaction",
                    "question": SATISFACTION_QUESTION,
                }
            )
        )
        return f"Satisfaction signal received: {answer}"

    @tool
    def propose_proposition(statement: str, activity: ModelingActivity) -> str:
        """Propose a Proposition tagged with the Modeling Activity that produced it."""
        try:
            prop = store.propose(statement, activity=activity)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(_proposition_payload(prop))

    @tool
    def accept_proposition(
        proposition_id: str,
        via_proposition_id: str = "",
    ) -> str:
        """Accept a Candidate into the Model after the user's direct Acceptance signal.

        Optional via_proposition_id marks indirect Acceptance (foundation for cascades).
        """
        interrupt(
            {
                "kind": "accept",
                "proposition_id": proposition_id,
                "via_proposition_id": via_proposition_id or None,
                "question": (
                    f"Do you Accept Proposition {proposition_id} into the Model?"
                ),
            }
        )
        try:
            prop = store.accept(
                proposition_id,
                via_proposition_id=via_proposition_id or None,
            )
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(_proposition_payload(prop))

    @tool
    def reject_proposition(proposition_id: str, reason: str) -> str:
        """Reject a Proposition with an explicit reason; records it in the Rejection Guardrail."""
        interrupt(
            {
                "kind": "reject",
                "proposition_id": proposition_id,
                "reason": reason,
                "question": (
                    f"Do you Reject Proposition {proposition_id}? Reason: {reason}"
                ),
            }
        )
        try:
            prop = store.reject(proposition_id, reason)
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(_proposition_payload(prop))

    @tool
    def reconcile(findings_json: str) -> str:
        """From pass 2, surface latent L2/L3 Conflicts before Scenarios / Assertion Tests."""
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
        """Gather open Conflicts into one Batch and Probe the user to resolve them together."""
        try:
            result = inference.probe_batch()
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps({"ok": True, **result})

    return [
        run_opening,
        await_satisfaction,
        propose_proposition,
        accept_proposition,
        reject_proposition,
        reconcile,
        record_scenarios,
        run_assertion_tests,
        probe_batch,
    ]


def build_activity_tools(
    backend: BackendProtocol,
    activity: ModelingActivity,
) -> Sequence[BaseTool]:
    """Proposition tools bound to one Modeling Activity (subagent tool subset)."""
    store = PropositionStore(backend)
    pipeline = PipelineStore(backend)

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
        interrupt(
            {
                "kind": "accept",
                "proposition_id": proposition_id,
                "via_proposition_id": via_proposition_id or None,
                "question": (
                    f"Do you Accept Proposition {proposition_id} into the Model?"
                ),
            }
        )
        try:
            prop = store.accept(
                proposition_id,
                via_proposition_id=via_proposition_id or None,
            )
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(_proposition_payload(prop))

    def reject_proposition(proposition_id: str, reason: str) -> str:
        interrupt(
            {
                "kind": "reject",
                "proposition_id": proposition_id,
                "reason": reason,
                "question": (
                    f"Do you Reject Proposition {proposition_id}? Reason: {reason}"
                ),
            }
        )
        try:
            prop = store.reject(proposition_id, reason)
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(_proposition_payload(prop))

    def complete_modeling_activity() -> str:
        try:
            pipeline.complete(activity)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps({"ok": True, "completed": activity})

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
                f"Mark the {activity} Modeling Activity complete so the "
                "pipeline may advance."
            ),
        ),
    ]
