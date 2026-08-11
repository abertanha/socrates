"""Inference Engine — Scenarios, Assertion Tests, Batch, and Probe.

Deterministic harness logic for one Inference pass. Scenario *phrasing* is
supplied by the model provider; the harness enforces Relevance Filter,
several-scenarios-per-Proposition, Batch collection, and interrupt-gated Probe
resolution that updates the Model.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import (
    BATCHES_PATH,
    CONFLICTS_PATH,
    NEED_PATH,
    SCENARIOS_PATH,
)
from socrates.proposition import PropositionStore

ScenarioEdge = Literal["zero", "one", "many", "none", "intersection"]
ConflictKind = Literal["contradiction", "omission", "contrariety", "ambiguity"]
ProbeAction = Literal["revise_proposition", "add_proposition", "dismiss"]

MIN_SCENARIOS_PER_PROPOSITION = 2
VALID_EDGES: frozenset[str] = frozenset(
    {"zero", "one", "many", "none", "intersection"}
)
VALID_KINDS: frozenset[str] = frozenset(
    {"contradiction", "omission", "contrariety", "ambiguity"}
)


@dataclass
class Scenario:
    id: str
    proposition_id: str
    description: str
    edge: ScenarioEdge
    need_relevant: bool


@dataclass
class Conflict:
    id: str
    proposition_id: str
    scenario_id: str
    kind: ConflictKind
    summary: str
    status: Literal["open", "resolved"] = "open"
    batch_id: str | None = None
    resolution: dict[str, Any] | None = None


@dataclass
class Batch:
    id: str
    conflict_ids: list[str]
    status: Literal["open", "probed"] = "open"


class InferenceEngine:
    """Runs Assertion Tests over Scenarios and Probes Batches of Conflicts."""

    def __init__(self, backend: BackendProtocol) -> None:
        self._backend = backend
        self._propositions = PropositionStore(backend)

    def record_scenarios(
        self,
        proposition_id: str,
        scenarios: list[dict[str, Any]],
    ) -> list[Scenario]:
        self._require_proposition(proposition_id)
        self._require_need()
        if len(scenarios) < MIN_SCENARIOS_PER_PROPOSITION:
            raise ValueError(
                f"Several Scenarios are required per Proposition "
                f"(at least {MIN_SCENARIOS_PER_PROPOSITION}); got {len(scenarios)}"
            )

        recorded: list[Scenario] = []
        existing = self._load_scenarios()
        for raw in scenarios:
            description = str(raw.get("description", "")).strip()
            edge = raw.get("edge")
            need_relevant = raw.get("need_relevant")
            if not description:
                raise ValueError("Scenario description must not be empty")
            if edge not in VALID_EDGES:
                raise ValueError(
                    f"Scenario edge must be one of {sorted(VALID_EDGES)}; got {edge!r}"
                )
            if need_relevant is not True:
                raise ValueError(
                    "Relevance Filter: Scenarios must be Need-relevant "
                    "(need_relevant=true)"
                )
            scenario = Scenario(
                id=f"s{len(existing) + len(recorded) + 1}",
                proposition_id=proposition_id,
                description=description,
                edge=edge,  # type: ignore[arg-type]
                need_relevant=True,
            )
            recorded.append(scenario)

        existing.extend(recorded)
        self._save_scenarios(existing)
        return recorded

    def run_assertion_tests(
        self,
        proposition_id: str,
        outcomes: list[dict[str, Any]],
    ) -> list[Conflict]:
        self._require_proposition(proposition_id)
        scenarios = {
            s.id: s
            for s in self._load_scenarios()
            if s.proposition_id == proposition_id
        }
        if len(scenarios) < MIN_SCENARIOS_PER_PROPOSITION:
            raise ValueError(
                f"Assertion Tests require recorded Scenarios for {proposition_id}"
            )
        if not outcomes:
            raise ValueError("Assertion Tests require at least one outcome")

        surfaced: list[Conflict] = []
        conflicts = self._load_conflicts()
        for raw in outcomes:
            scenario_id = raw.get("scenario_id")
            if scenario_id not in scenarios:
                raise ValueError(
                    f"Unknown Scenario {scenario_id!r} for Proposition {proposition_id}"
                )
            survives = raw.get("survives")
            if survives is True:
                continue
            if survives is not False:
                raise ValueError("Outcome.survives must be a boolean")
            kind = raw.get("kind")
            summary = str(raw.get("summary", "")).strip()
            if kind not in VALID_KINDS:
                raise ValueError(
                    f"Conflict kind must be one of {sorted(VALID_KINDS)}; got {kind!r}"
                )
            if not summary:
                raise ValueError("Conflict summary must not be empty when Elasticity breaks")
            conflict = Conflict(
                id=f"c{len(conflicts) + len(surfaced) + 1}",
                proposition_id=proposition_id,
                scenario_id=scenario_id,
                kind=kind,  # type: ignore[arg-type]
                summary=summary,
                status="open",
            )
            surfaced.append(conflict)

        conflicts.extend(surfaced)
        self._save_conflicts(conflicts)
        return surfaced

    def probe_batch(self) -> dict[str, Any]:
        """Gather open Conflicts into a Batch, Probe the user, apply resolutions."""
        conflicts = self._load_conflicts()
        open_conflicts = [c for c in conflicts if c.status == "open" and c.batch_id is None]
        if not open_conflicts:
            raise ValueError("No open Conflicts to Probe")

        batches = self._load_batches()
        batch = Batch(
            id=f"b{len(batches) + 1}",
            conflict_ids=[c.id for c in open_conflicts],
            status="open",
        )
        for conflict in open_conflicts:
            conflict.batch_id = batch.id
        batches.append(batch)
        self._save_batches(batches)
        self._save_conflicts(conflicts)

        resolutions = interrupt_probe(
            {
                "kind": "probe",
                "batch_id": batch.id,
                "conflicts": [
                    {
                        "id": c.id,
                        "proposition_id": c.proposition_id,
                        "scenario_id": c.scenario_id,
                        "kind": c.kind,
                        "summary": c.summary,
                    }
                    for c in open_conflicts
                ],
            }
        )
        applied = self._apply_resolutions(batch.id, resolutions)
        return {
            "batch_id": batch.id,
            "conflict_ids": batch.conflict_ids,
            "applied": applied,
        }

    def _apply_resolutions(
        self,
        batch_id: str,
        resolutions: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(resolutions, dict):
            raise ValueError("Probe resume must be an object with 'resolutions'")
        items = resolutions.get("resolutions")
        if not isinstance(items, list) or not items:
            raise ValueError("Probe resume must include a non-empty resolutions list")

        conflicts = self._load_conflicts()
        by_id = {c.id: c for c in conflicts}
        batch_conflict_ids = {
            c.id for c in conflicts if c.batch_id == batch_id and c.status == "open"
        }
        resolved_ids: set[str] = set()
        applied: list[dict[str, Any]] = []

        for raw in items:
            conflict_id = raw.get("conflict_id")
            action = raw.get("action")
            if conflict_id not in batch_conflict_ids:
                raise ValueError(f"Conflict {conflict_id!r} is not in open Batch {batch_id}")
            conflict = by_id[conflict_id]
            if action == "revise_proposition":
                statement = str(raw.get("statement", "")).strip()
                if not statement:
                    raise ValueError("revise_proposition requires statement")
                prop = self._propositions.revise(conflict.proposition_id, statement)
                applied.append(
                    {
                        "conflict_id": conflict_id,
                        "action": action,
                        "proposition_id": prop.id,
                        "status": prop.status,
                        "statement": prop.statement,
                    }
                )
            elif action == "add_proposition":
                statement = str(raw.get("statement", "")).strip()
                activity = raw.get("activity")
                if not statement:
                    raise ValueError("add_proposition requires statement")
                if activity is None:
                    raise ValueError("add_proposition requires activity")
                prop = self._propositions.propose(statement, activity=activity)
                applied.append(
                    {
                        "conflict_id": conflict_id,
                        "action": action,
                        "proposition_id": prop.id,
                        "status": prop.status,
                        "statement": prop.statement,
                        "activity": prop.activity,
                    }
                )
            elif action == "dismiss":
                applied.append({"conflict_id": conflict_id, "action": action})
            else:
                raise ValueError(
                    f"Unknown Probe action {action!r}; expected one of "
                    f"revise_proposition, add_proposition, dismiss"
                )
            conflict.status = "resolved"
            conflict.resolution = dict(raw)
            resolved_ids.add(conflict_id)

        missing = batch_conflict_ids - resolved_ids
        if missing:
            raise ValueError(
                f"Probe must resolve every Conflict in the Batch; missing {sorted(missing)}"
            )

        batches = self._load_batches()
        for batch in batches:
            if batch.id == batch_id:
                batch.status = "probed"
        self._save_batches(batches)
        self._save_conflicts(conflicts)
        return applied

    def _require_proposition(self, proposition_id: str) -> None:
        self._propositions.get(proposition_id)

    def _require_need(self) -> str:
        result = self._backend.read(NEED_PATH)
        if result.error or result.file_data is None:
            raise ValueError("Need must be persisted before generating Scenarios")
        need = result.file_data["content"].strip()
        if not need:
            raise ValueError("Need must be persisted before generating Scenarios")
        return need

    def _load_scenarios(self) -> list[Scenario]:
        raw = self._read_json(SCENARIOS_PATH)
        if raw is None:
            return []
        return [Scenario(**item) for item in raw.get("scenarios", [])]

    def _save_scenarios(self, scenarios: list[Scenario]) -> None:
        self._backend.write(
            SCENARIOS_PATH,
            json.dumps({"scenarios": [asdict(s) for s in scenarios]}, indent=2),
        )

    def _load_conflicts(self) -> list[Conflict]:
        raw = self._read_json(CONFLICTS_PATH)
        if raw is None:
            return []
        return [Conflict(**item) for item in raw.get("conflicts", [])]

    def _save_conflicts(self, conflicts: list[Conflict]) -> None:
        self._backend.write(
            CONFLICTS_PATH,
            json.dumps({"conflicts": [asdict(c) for c in conflicts]}, indent=2),
        )

    def _load_batches(self) -> list[Batch]:
        raw = self._read_json(BATCHES_PATH)
        if raw is None:
            return []
        return [Batch(**item) for item in raw.get("batches", [])]

    def _save_batches(self, batches: list[Batch]) -> None:
        self._backend.write(
            BATCHES_PATH,
            json.dumps({"batches": [asdict(b) for b in batches]}, indent=2),
        )

    def _read_json(self, path: str) -> dict[str, Any] | None:
        result = self._backend.read(path)
        if result.error or result.file_data is None:
            return None
        content = result.file_data["content"]
        if not content.strip():
            return None
        return json.loads(content)


def interrupt_probe(payload: dict[str, Any]) -> Any:
    """Indirection so tests can import InferenceEngine without binding interrupt early."""
    from langgraph.types import interrupt

    return interrupt(payload)
