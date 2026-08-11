"""Interview and Proposition-lifecycle tools for a Socrates session."""

from __future__ import annotations

import json
from collections.abc import Sequence

from deepagents.backends.protocol import BackendProtocol
from langchain_core.tools import BaseTool
from langchain.tools import tool
from langgraph.types import interrupt

from socrates.paths import NEED_PATH
from socrates.proposition import PropositionStore

OPENING_QUESTION = "What Need should this Model serve?"
SATISFACTION_QUESTION = (
    "Do you signal Satisfaction with the Model as it stands?"
)


def build_session_tools(backend: BackendProtocol) -> Sequence[BaseTool]:
    """Build Opening, Satisfaction, and Proposition-lifecycle tools."""
    store = PropositionStore(backend)

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
    def propose_proposition(statement: str) -> str:
        """Propose a Proposition. Triages to Candidate, or Flagged if it resembles the Rejection Guardrail."""
        try:
            prop = store.propose(statement)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(
            {
                "ok": True,
                "id": prop.id,
                "statement": prop.statement,
                "status": prop.status,
                "flagged_against_id": prop.flagged_against_id,
            }
        )

    @tool
    def accept_proposition(proposition_id: str) -> str:
        """Accept a Candidate into the Model after the user's direct Acceptance signal."""
        interrupt(
            {
                "kind": "accept",
                "proposition_id": proposition_id,
                "question": (
                    f"Do you Accept Proposition {proposition_id} into the Model?"
                ),
            }
        )
        try:
            prop = store.accept(proposition_id)
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(
            {
                "ok": True,
                "id": prop.id,
                "statement": prop.statement,
                "status": prop.status,
            }
        )

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
        return json.dumps(
            {
                "ok": True,
                "id": prop.id,
                "statement": prop.statement,
                "status": prop.status,
                "reason": prop.reason,
            }
        )

    return [
        run_opening,
        await_satisfaction,
        propose_proposition,
        accept_proposition,
        reject_proposition,
    ]
