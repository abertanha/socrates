"""Inference Engine — Reconciliation, Scenarios, Assertion Tests, Batch, Probe.

Deterministic harness logic for Inference passes. From pass 2, Reconciliation
runs before Scenario generation / Assertion Tests and yields only L2/L3.
Conflict Levels are classified from the parties' lifecycle states. L4 arises
only from Assertion Tests on intersection Scenarios exercising two Accepted
Propositions.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from typing import Any, Literal

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import (
    BATCHES_PATH,
    CONFLICTS_PATH,
    INFERENCE_STATE_PATH,
    NEED_PATH,
    SCENARIOS_PATH,
)
from socrates.proposition import Proposition, PropositionStore, normalize_statement

ScenarioEdge = Literal["zero", "one", "many", "none", "intersection"]
ConflictKind = Literal["contradiction", "omission", "contrariety", "ambiguity"]
ConflictLevel = Literal["L1", "L2", "L3", "L4"]
ConflictSource = Literal["reconciliation", "assertion_test"]
ProbeAction = Literal[
    "revise_proposition", "add_proposition", "dismiss", "supersede"
]

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
    kind: ConflictKind
    summary: str
    level: ConflictLevel
    source: ConflictSource
    scenario_id: str | None = None
    other_proposition_id: str | None = None
    status: Literal["open", "resolved"] = "open"
    batch_id: str | None = None
    resolution: dict[str, Any] | None = None


@dataclass
class Batch:
    id: str
    conflict_ids: list[str]
    status: Literal["open", "probed"] = "open"


def classify_conflict_level(
    left: Proposition,
    *,
    other: Proposition | None = None,
    against_guardrail: bool = False,
) -> ConflictLevel:
    """Classify L1–L4 from the lifecycle state of the parties."""
    if against_guardrail:
        return "L3"
    if other is None:
        return "L1"
    if left.status == "accepted" and other.status == "accepted":
        return "L4"
    if other.status == "accepted" or left.status == "accepted":
        return "L2"
    return "L1"


class InferenceEngine:
    """Reconciliation, Assertion Tests, Batches, and Probes."""

    def __init__(self, backend: BackendProtocol) -> None:
        self._backend = backend
        self._propositions = PropositionStore(backend)

    def current_pass(self) -> int:
        """Pass 1 is the Opening-seeded pass; increments after each probed Batch."""
        probed = sum(1 for b in self._load_batches() if b.status == "probed")
        return probed + 1

    def reconcile(self, findings: list[dict[str, Any]]) -> list[Conflict]:
        """Surface latent L2/L3 conflicts from the latest ingest (pass 2+ only)."""
        pass_no = self.current_pass()
        if pass_no < 2:
            raise ValueError("Reconciliation applies from pass 2 onward")
        if not findings:
            raise ValueError("Reconciliation requires at least one finding")

        state = self._load_inference_state()
        if state.get("reconciliation_pass") == pass_no:
            raise ValueError(f"Reconciliation already completed for pass {pass_no}")

        surfaced: list[Conflict] = []
        conflicts = self._load_conflicts()
        blocked: set[str] = set(state.get("blocked_proposition_ids", []))

        for raw in findings:
            new_id = raw.get("new_proposition_id")
            kind = raw.get("kind")
            summary = str(raw.get("summary", "")).strip()
            against_kind = raw.get("against_kind")
            if not new_id:
                raise ValueError("Finding requires new_proposition_id")
            if kind not in VALID_KINDS:
                raise ValueError(
                    f"Conflict kind must be one of {sorted(VALID_KINDS)}; got {kind!r}"
                )
            if not summary:
                raise ValueError("Conflict summary must not be empty")

            new_prop = self._propositions.get(new_id)
            if against_kind == "guardrail":
                guardrail_id = raw.get("against_id")
                entry = self._find_guardrail(guardrail_id, new_prop.statement)
                level = classify_conflict_level(new_prop, against_guardrail=True)
                if level != "L3":
                    raise ValueError("Reconciliation guardrail findings must be L3")
                other_id = entry.proposition_id
            elif against_kind == "accepted":
                against_id = raw.get("against_id")
                if not against_id:
                    raise ValueError("L2 finding requires against_id of an Accepted Proposition")
                other = self._propositions.get(against_id)
                if other.status != "accepted":
                    raise ValueError(
                        f"Reconciliation L2 requires an Accepted party; "
                        f"{against_id} is {other.status}"
                    )
                level = classify_conflict_level(new_prop, other=other)
                if level != "L2":
                    raise ValueError(
                        "Reconciliation against Accepted must classify as L2 "
                        f"(got {level})"
                    )
                other_id = other.id
            else:
                raise ValueError(
                    "against_kind must be 'accepted' or 'guardrail' "
                    "(Reconciliation yields only L2/L3)"
                )

            conflict = Conflict(
                id=f"c{len(conflicts) + len(surfaced) + 1}",
                proposition_id=new_id,
                other_proposition_id=other_id,
                scenario_id=None,
                kind=kind,  # type: ignore[arg-type]
                summary=summary,
                level=level,
                source="reconciliation",
                status="open",
            )
            surfaced.append(conflict)
            blocked.add(new_id)

        conflicts.extend(surfaced)
        self._save_conflicts(conflicts)
        state["reconciliation_pass"] = pass_no
        state["blocked_proposition_ids"] = sorted(blocked)
        self._save_inference_state(state)
        return surfaced

    def record_scenarios(
        self,
        proposition_id: str,
        scenarios: list[dict[str, Any]],
    ) -> list[Scenario]:
        self._require_proposition(proposition_id)
        self._require_need()
        self._require_reconciliation_before_scenarios()
        if proposition_id in self._blocked_proposition_ids():
            raise ValueError(
                "Scenario generation skipped: Proposition "
                f"{proposition_id} was contradicted by Reconciliation"
            )
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
        self._require_reconciliation_before_scenarios()
        if proposition_id in self._blocked_proposition_ids():
            raise ValueError(
                "Assertion Tests skipped: Proposition "
                f"{proposition_id} was contradicted by Reconciliation"
            )

        prop = self._propositions.get(proposition_id)
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
            scenario = scenarios[scenario_id]
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
                raise ValueError(
                    "Conflict summary must not be empty when Elasticity breaks"
                )

            other_id = raw.get("other_proposition_id")
            other = self._propositions.get(other_id) if other_id else None
            level = classify_conflict_level(prop, other=other)
            if level in ("L2", "L3"):
                raise ValueError(
                    f"{level} conflicts must be surfaced by Reconciliation, "
                    "not Assertion Tests"
                )
            if level == "L4":
                if scenario.edge != "intersection":
                    raise ValueError(
                        "L4 requires an intersection Scenario exercising two "
                        "Accepted Propositions"
                    )
                if other is None:
                    raise ValueError("L4 requires other_proposition_id")

            conflict = Conflict(
                id=f"c{len(conflicts) + len(surfaced) + 1}",
                proposition_id=proposition_id,
                other_proposition_id=other_id,
                scenario_id=scenario_id,
                kind=kind,  # type: ignore[arg-type]
                summary=summary,
                level=level,
                source="assertion_test",
                status="open",
            )
            surfaced.append(conflict)

        conflicts.extend(surfaced)
        self._save_conflicts(conflicts)
        return surfaced

    def probe_batch(self) -> dict[str, Any]:
        """Gather open Conflicts into a Batch, Probe the user, apply resolutions."""
        conflicts = self._load_conflicts()
        open_conflicts = [
            c for c in conflicts if c.status == "open" and c.batch_id is None
        ]
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
                        "other_proposition_id": c.other_proposition_id,
                        "scenario_id": c.scenario_id,
                        "kind": c.kind,
                        "summary": c.summary,
                        "level": c.level,
                        "source": c.source,
                        "routing": _probe_routing(c.level),
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
            "notifications": self._propositions.list_notifications(),
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
        unblocked: set[str] = set()

        for raw in items:
            conflict_id = raw.get("conflict_id")
            action = raw.get("action")
            if conflict_id not in batch_conflict_ids:
                raise ValueError(
                    f"Conflict {conflict_id!r} is not in open Batch {batch_id}"
                )
            conflict = by_id[conflict_id]
            if conflict.level == "L3" and action != "dismiss":
                raise ValueError(
                    "L3 conflicts are blocked by the Rejection Guardrail; "
                    "only dismiss is allowed"
                )
            if action == "revise_proposition":
                if conflict.level == "L2":
                    # L2 may revise the new side in-line, but Supersede is the
                    # dedicated displacement path for the Accepted party.
                    pass
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
            elif action == "supersede":
                if conflict.level != "L2":
                    raise ValueError(
                        f"Supersede is only valid for L2 conflicts; "
                        f"{conflict_id} is {conflict.level}"
                    )
                reason = str(raw.get("reason", "")).strip()
                if not reason:
                    raise ValueError("supersede requires reason")
                accepted_id = conflict.other_proposition_id
                if not accepted_id:
                    raise ValueError("L2 conflict missing other_proposition_id (Accepted)")
                result = self._propositions.supersede(
                    accepted_id,
                    conflict.proposition_id,
                    reason,
                )
                applied.append(
                    {
                        "conflict_id": conflict_id,
                        "action": action,
                        **result,
                    }
                )
            elif action == "dismiss":
                applied.append(
                    {
                        "conflict_id": conflict_id,
                        "action": action,
                        "blocked": conflict.level == "L3",
                    }
                )
            else:
                raise ValueError(
                    f"Unknown Probe action {action!r}; expected one of "
                    f"revise_proposition, add_proposition, supersede, dismiss"
                )
            conflict.status = "resolved"
            conflict.resolution = dict(raw)
            resolved_ids.add(conflict_id)
            if conflict.source == "reconciliation":
                unblocked.add(conflict.proposition_id)

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

        if unblocked:
            state = self._load_inference_state()
            blocked = set(state.get("blocked_proposition_ids", [])) - unblocked
            state["blocked_proposition_ids"] = sorted(blocked)
            self._save_inference_state(state)

        return applied

    def _require_reconciliation_before_scenarios(self) -> None:
        pass_no = self.current_pass()
        if pass_no < 2:
            return
        state = self._load_inference_state()
        if state.get("reconciliation_pass") != pass_no:
            raise ValueError(
                "Reconciliation must run before Scenario generation / "
                f"Assertion Tests from pass 2 (current pass {pass_no})"
            )

    def _blocked_proposition_ids(self) -> set[str]:
        return set(self._load_inference_state().get("blocked_proposition_ids", []))

    def _find_guardrail(self, against_id: str | None, statement: str):
        entries = self._propositions.list_guardrail()
        if against_id:
            for entry in entries:
                if entry.proposition_id == against_id:
                    return entry
            raise ValueError(f"Unknown Rejection Guardrail entry {against_id!r}")
        key = normalize_statement(statement)
        for entry in entries:
            if normalize_statement(entry.statement) == key:
                return entry
        raise ValueError(
            "No Rejection Guardrail entry matches this Proposition for L3"
        )

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
        allowed = {f.name for f in fields(Conflict)}
        loaded: list[Conflict] = []
        for item in raw.get("conflicts", []):
            data = {k: v for k, v in item.items() if k in allowed}
            data.setdefault("level", "L1")
            data.setdefault("source", "assertion_test")
            loaded.append(Conflict(**data))
        return loaded

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

    def _load_inference_state(self) -> dict[str, Any]:
        raw = self._read_json(INFERENCE_STATE_PATH)
        if raw is None:
            return {"reconciliation_pass": None, "blocked_proposition_ids": []}
        return raw

    def _save_inference_state(self, state: dict[str, Any]) -> None:
        self._backend.write(INFERENCE_STATE_PATH, json.dumps(state, indent=2))

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


def _probe_routing(level: ConflictLevel) -> str:
    if level == "L1":
        return "inline"
    if level == "L2":
        return "supersede"
    if level == "L3":
        return "blocked"
    return "iteration"
