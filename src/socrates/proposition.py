"""Proposition lifecycle state machine persisted in the virtual filesystem.

States: Candidate → Accepted; plus Rejected (Rejection Guardrail), Flagged,
and Superseded (displaced Accepted, recorded with reason). Indirect Acceptance
is tracked via ``accepted_via`` for Supersede cascades.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, fields
from typing import Any, Literal

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import (
    PROPOSITIONS_PATH,
    REJECTION_GUARDRAIL_PATH,
)
from socrates.pipeline import ModelingActivity
from socrates.notifications import NotificationService

PropositionStatus = Literal[
    "candidate", "accepted", "rejected", "flagged", "superseded"
]

_FUNCTIONAL_REQUIREMENT = re.compile(r"\bthe system shall\b", re.IGNORECASE)


@dataclass
class Proposition:
    id: str
    statement: str
    status: PropositionStatus
    activity: ModelingActivity
    reason: str | None = None
    flagged_against_id: str | None = None
    accepted_via: str | None = None


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
        self._notifications = NotificationService(backend)

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

    def accept(
        self,
        proposition_id: str,
        *,
        via_proposition_id: str | None = None,
    ) -> Proposition:
        propositions = self._load_propositions()
        prop = self._get(propositions, proposition_id)
        if prop.status != "candidate":
            raise ValueError(
                f"Only a Candidate can be Accepted; {proposition_id} is {prop.status}"
            )
        if via_proposition_id is not None:
            via = self._get(propositions, via_proposition_id)
            if via.status != "accepted":
                raise ValueError(
                    f"Indirect Acceptance requires an Accepted foundation; "
                    f"{via_proposition_id} is {via.status}"
                )
            prop.accepted_via = via_proposition_id
        else:
            prop.accepted_via = None
        prop.status = "accepted"
        self._save_propositions(propositions)
        return prop

    def revise(self, proposition_id: str, statement: str) -> Proposition:
        """Reshape a Proposition; Accepted ones Degrade back to Candidate (ADR-0003)."""
        statement = statement.strip()
        if not statement:
            raise ValueError("Revised statement must not be empty")
        propositions = self._load_propositions()
        prop = self._get(propositions, proposition_id)
        if prop.status in ("rejected", "superseded"):
            raise ValueError(f"Cannot revise {prop.status} Proposition {proposition_id}")
        prop.statement = statement
        if prop.status == "accepted":
            prop.status = "candidate"
            prop.accepted_via = None
        self._save_propositions(propositions)
        return prop

    def degrade(self, proposition_id: str) -> Proposition:
        """Accepted → Candidate (foundation lost or Scenario break)."""
        propositions = self._load_propositions()
        prop = self._get(propositions, proposition_id)
        if prop.status != "accepted":
            raise ValueError(
                f"Only an Accepted Proposition can Degrade; "
                f"{proposition_id} is {prop.status}"
            )
        prop.status = "candidate"
        prop.accepted_via = None
        self._save_propositions(propositions)
        return prop

    def supersede(
        self,
        accepted_id: str,
        new_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """Displace an Accepted Proposition; cascade-Degrade indirect dependents."""
        reason = reason.strip()
        if not reason:
            raise ValueError("Supersede requires an explicit reason")

        propositions = self._load_propositions()
        accepted = self._get(propositions, accepted_id)
        new_prop = self._get(propositions, new_id)
        if accepted.status != "accepted":
            raise ValueError(
                f"Only an Accepted Proposition can be Superseded; "
                f"{accepted_id} is {accepted.status}"
            )
        if new_prop.status not in ("candidate", "flagged"):
            raise ValueError(
                f"Supersede new information must be Candidate or Flagged; "
                f"{new_id} is {new_prop.status}"
            )

        accepted.status = "superseded"
        accepted.reason = reason
        accepted.accepted_via = None

        new_prop.status = "candidate"
        new_prop.flagged_against_id = None

        degraded_ids = sorted(self._indirect_dependents(accepted_id, propositions))
        for dep_id in degraded_ids:
            dep = self._get(propositions, dep_id)
            dep.status = "candidate"
            dep.accepted_via = None

        self._save_propositions(propositions)

        notification = self._notifications.emit(
            "supersede_cascade",
            superseded_id=accepted_id,
            new_proposition_id=new_id,
            reason=reason,
            degraded_ids=degraded_ids,
        )

        return {
            "superseded_id": accepted_id,
            "new_proposition_id": new_id,
            "new_status": new_prop.status,
            "degraded_ids": degraded_ids,
            "notification": notification,
        }

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
        prop.accepted_via = None
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

    def get(self, proposition_id: str) -> Proposition:
        return self._get(self._load_propositions(), proposition_id)

    def list_guardrail(self) -> list[GuardrailEntry]:
        return self._load_guardrail()

    def list_notifications(self) -> list[dict[str, Any]]:
        return self._notifications.list_notifications()

    def _indirect_dependents(
        self,
        root_id: str,
        propositions: list[Proposition],
    ) -> set[str]:
        """Propositions Accepted (transitively) via ``root_id``."""
        dependents: set[str] = set()
        changed = True
        while changed:
            changed = False
            for prop in propositions:
                if prop.status != "accepted" or not prop.accepted_via:
                    continue
                if prop.accepted_via == root_id or prop.accepted_via in dependents:
                    if prop.id not in dependents:
                        dependents.add(prop.id)
                        changed = True
        return dependents

    def _get(self, propositions: list[Proposition], proposition_id: str) -> Proposition:
        for prop in propositions:
            if prop.id == proposition_id:
                return prop
        raise ValueError(f"Unknown Proposition id: {proposition_id}")

    def _next_id(self, propositions: list[Proposition]) -> str:
        return f"p{len(propositions) + 1}"

    def _load_propositions(self) -> list[Proposition]:
        raw = self._read_json(PROPOSITIONS_PATH)
        if raw is None:
            return []
        allowed = {f.name for f in fields(Proposition)}
        loaded: list[Proposition] = []
        for item in raw.get("propositions", []):
            data = {k: v for k, v in item.items() if k in allowed}
            data.setdefault("accepted_via", None)
            loaded.append(Proposition(**data))
        return loaded

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
