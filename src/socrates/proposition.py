"""Proposition lifecycle state machine persisted in the virtual filesystem.

States: Candidate → Accepted; plus Rejected (feeds the Rejection Guardrail)
and Flagged (triage hit against the Guardrail — not a Candidate).
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Literal

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import PROPOSITIONS_PATH, REJECTION_GUARDRAIL_PATH
from socrates.pipeline import ModelingActivity, PipelineStore

PropositionStatus = Literal["candidate", "accepted", "rejected", "flagged"]

_FUNCTIONAL_REQUIREMENT = re.compile(r"\bthe system shall\b", re.IGNORECASE)


@dataclass
class Proposition:
    id: str
    statement: str
    status: PropositionStatus
    activity: ModelingActivity
    reason: str | None = None
    flagged_against_id: str | None = None


@dataclass
class GuardrailEntry:
    proposition_id: str
    statement: str
    reason: str


def normalize_statement(statement: str) -> str:
    """Normalize for immediate-conflict and Guardrail resemblance checks."""
    return " ".join(statement.casefold().split())


class PropositionStore:
    """Deterministic Proposition lifecycle over a deepagents backend."""

    def __init__(self, backend: BackendProtocol) -> None:
        self._backend = backend
        self._pipeline = PipelineStore(backend)

    def propose(self, statement: str, activity: ModelingActivity) -> Proposition:
        statement = statement.strip()
        if not statement:
            raise ValueError("Proposition statement must not be empty")

        if activity == "behavioral_specification" and _FUNCTIONAL_REQUIREMENT.search(
            statement
        ):
            raise ValueError(
                "Behavioral Specification admits conceptual domain rules only; "
                "functional requirements ('the system shall...') are out of scope"
            )

        self._pipeline.begin(activity)

        propositions = self._load_propositions()
        guardrail = self._load_guardrail()
        key = normalize_statement(statement)

        for entry in guardrail:
            if normalize_statement(entry.statement) == key:
                prop = Proposition(
                    id=self._next_id(propositions),
                    statement=statement,
                    status="flagged",
                    activity=activity,
                    flagged_against_id=entry.proposition_id,
                )
                propositions.append(prop)
                self._save_propositions(propositions)
                return prop

        for existing in propositions:
            if (
                existing.status == "accepted"
                and normalize_statement(existing.statement) == key
            ):
                raise ValueError(
                    f"Immediate conflict with Accepted Proposition {existing.id}"
                )

        prop = Proposition(
            id=self._next_id(propositions),
            statement=statement,
            status="candidate",
            activity=activity,
        )
        propositions.append(prop)
        self._save_propositions(propositions)
        return prop

    def accept(self, proposition_id: str) -> Proposition:
        propositions = self._load_propositions()
        prop = self._get(propositions, proposition_id)
        if prop.status != "candidate":
            raise ValueError(
                f"Only a Candidate can be Accepted; {proposition_id} is {prop.status}"
            )
        prop.status = "accepted"
        self._save_propositions(propositions)
        return prop

    def reject(self, proposition_id: str, reason: str) -> Proposition:
        reason = reason.strip()
        if not reason:
            raise ValueError("Rejection requires an explicit reason")

        propositions = self._load_propositions()
        prop = self._get(propositions, proposition_id)
        if prop.status not in ("candidate", "flagged"):
            raise ValueError(
                f"Only a Candidate or Flagged Proposition can be Rejected; "
                f"{proposition_id} is {prop.status}"
            )
        prop.status = "rejected"
        prop.reason = reason
        self._save_propositions(propositions)

        guardrail = self._load_guardrail()
        guardrail.append(
            GuardrailEntry(
                proposition_id=prop.id,
                statement=prop.statement,
                reason=reason,
            )
        )
        self._save_guardrail(guardrail)
        return prop

    def list_propositions(self) -> list[Proposition]:
        return self._load_propositions()

    def list_guardrail(self) -> list[GuardrailEntry]:
        return self._load_guardrail()

    def _get(self, propositions: list[Proposition], proposition_id: str) -> Proposition:
        for prop in propositions:
            if prop.id == proposition_id:
                return prop
        raise KeyError(f"Unknown Proposition id: {proposition_id}")

    def _next_id(self, propositions: list[Proposition]) -> str:
        return f"p{len(propositions) + 1}"

    def _load_propositions(self) -> list[Proposition]:
        raw = self._read_json(PROPOSITIONS_PATH)
        if raw is None:
            return []
        return [Proposition(**item) for item in raw.get("propositions", [])]

    def _save_propositions(self, propositions: list[Proposition]) -> None:
        payload = {"propositions": [asdict(p) for p in propositions]}
        self._backend.write(PROPOSITIONS_PATH, json.dumps(payload, indent=2))

    def _load_guardrail(self) -> list[GuardrailEntry]:
        raw = self._read_json(REJECTION_GUARDRAIL_PATH)
        if raw is None:
            return []
        return [GuardrailEntry(**item) for item in raw.get("entries", [])]

    def _save_guardrail(self, entries: list[GuardrailEntry]) -> None:
        payload = {"entries": [asdict(e) for e in entries]}
        self._backend.write(REJECTION_GUARDRAIL_PATH, json.dumps(payload, indent=2))

    def _read_json(self, path: str) -> dict[str, Any] | None:
        result = self._backend.read(path)
        if result.error or result.file_data is None:
            return None
        content = result.file_data["content"]
        if not content.strip():
            return None
        return json.loads(content)
