"""Inference Engine — Reconciliation, Scenarios, Assertion Tests, Batch, Probe.

Deterministic harness logic for Inference passes. From pass 2, Reconciliation
runs before Scenario generation / Assertion Tests and yields only L2/L3.
Conflict Levels are classified from the parties' lifecycle states. L4 arises
only from Assertion Tests on intersection Scenarios exercising two Accepted
Propositions and is handed to Iteration (not Probe-resolved).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from typing import Any, Literal

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import (
    ASSERTIONS_PATH,
    BATCHES_PATH,
    CONFLICTS_PATH,
    INFERENCE_STATE_PATH,
    NOTIFICATIONS_PATH,
    PROPOSITIONS_PATH,
    SCENARIOS_PATH,
)
from socrates.asking import (
    AnswerLogRead,
    begin_pending,
    clear_pending,
    guard_pending,
    parse_envelope,
    read_log,
    require_pending,
    token_refusal,
)
from socrates.refusal import Refusal
from socrates.coverage import CoverageStore
from socrates.need import read_amendments, read_need
from socrates.notifications import NotificationService, is_unavoidable
from socrates.pipeline import ACTIVITIES_IN_ORDER, ModelingActivity, PipelineStore
from socrates.proposition import Proposition, PropositionStore, normalize_statement

ScenarioEdge = Literal["zero", "one", "many", "none", "intersection"]
ConflictKind = Literal["contradiction", "omission", "contrariety", "ambiguity"]
ConflictLevel = Literal["L1", "L2", "L3", "L4"]
ConflictSource = Literal["reconciliation", "assertion_test"]
ProbeAction = Literal[
    "revise_proposition",
    "add_proposition",
    "dismiss",
    "supersede",
    "defer",
]

MIN_SCENARIOS_PER_PROPOSITION = 2

# The self-answer window (socrates-seam ticket 01): an answer applied
# this soon after its ask could not have crossed a rendered turn and a
# human reader — it is the compound-command signature. Deliberately
# generous to the honest relay (render turn + reading + typing + a fresh
# process lands well past it; a compound lands inside the interpreter
# startups). A floor on suspicion, never a gate: nothing is refused on
# it — the warning surfaces the count and the user weighs it.
FAST_ANSWER_WINDOW_SECONDS = 5.0

# The Probe question's accepted answers (AskHuman, ticket 28) — the
# admissible resolution actions, with what each carries and its limits.
PROBE_ACCEPTED_ANSWERS: list[dict[str, str]] = [
    {
        "token": "revise_proposition",
        "meaning": "rewrite the quarreling Proposition's statement "
        "— carries 'statement'",
    },
    {
        "token": "add_proposition",
        "meaning": "ground the Conflict with a new Proposition "
        "— carries 'statement' and 'activity'",
    },
    {
        "token": "supersede",
        "meaning": "displace the Accepted party — L2 only, carries 'reason'",
    },
    {
        "token": "dismiss",
        "meaning": "the Conflict does not hold — drop it "
        "(with L3, one of only two options)",
    },
    {
        "token": "defer",
        "meaning": "park the Conflict for later — refused when unavoidable",
    },
]
PROBE_RESUME_CONTRACT = (
    "Resume with {canonical, raw}; canonical is "
    '{"resolutions": [{"conflict_id", "action", ...}]} '
    "resolving every Conflict of the Batch."
)

# The Iteration question's accepted answers are the menu the validator
# actually admits (review fix): `confirm` takes the proposal, an activity
# NAME reopens that one instead — no third grammar.
_ITERATION_RESUME_CONTRACT = (
    "Resume with {canonical, raw}; canonical is `confirm` (take the "
    "proposal) or the name of a Modeling Activity to reopen instead."
)


def _parse_iso(value: Any) -> datetime | None:
    """A timezone-aware UTC moment, or None for anything that is not one.

    Naive timestamps are read as UTC; anything unparseable is None — a
    binding that cannot be judged is skipped, never guessed.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment


def _iteration_answers(proposed: ModelingActivity) -> list[dict[str, str]]:
    return [
        {
            "token": "confirm",
            "meaning": f"reopen '{proposed}' — the proposed Modeling Activity",
        },
        *[
            {"token": activity, "meaning": f"reopen '{activity}' instead"}
            for activity in ACTIVITIES_IN_ORDER
        ],
    ]
VALID_EDGES: frozenset[str] = frozenset(
    {"zero", "one", "many", "none", "intersection"}
)
VALID_KINDS: frozenset[str] = frozenset(
    {"contradiction", "omission", "contrariety", "ambiguity"}
)
# Dimensions that mark a party as belonging to the Requirements activity
# (ticket 16) — used for the warning's scope tie-break.
_REQUIREMENTS_DIMENSIONS = frozenset({"requirements", "derivation+requirements"})


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
    status: Literal["open", "resolved", "deferred"] = "open"
    batch_id: str | None = None
    resolution: dict[str, Any] | None = None
    re_raised: bool = False


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


def propose_iteration_activity(
    left: Proposition,
    right: Proposition,
) -> ModelingActivity:
    """Most-upstream Modeling Activity whose output the L4 parties invalidate."""
    idx = min(
        ACTIVITIES_IN_ORDER.index(left.activity),
        ACTIVITIES_IN_ORDER.index(right.activity),
    )
    return ACTIVITIES_IN_ORDER[idx]


def assess_centrality(
    proposition: Proposition,
    dependents: int,
) -> dict[str, Any]:
    """Central Proposition signal (ticket 16) — derived, never stored.

    Central ⇔ transitive dependents in the ``accepted_via`` derivation graph
    ∨ Requirements activity. The v1 proxy is deliberately coarse — its
    Requirements half errs toward over-caution, the safe failure direction
    for a blocking-ness heuristic. Weight = dependents + (1 if Requirements):
    an input to payload and ordering only, never to blocking.
    """
    requirements = proposition.activity == "requirements"
    dependents = int(dependents)
    if dependents > 0 and requirements:
        dimension = "derivation+requirements"
    elif dependents > 0:
        dimension = "derivation"
    elif requirements:
        dimension = "requirements"
    else:
        dimension = None
    return {
        "central": dependents > 0 or requirements,
        "dimension": dimension,
        "dependents": dependents,
        "weight": dependents + (1 if requirements else 0),
    }


def assess_deferral_criticality(
    conflict: Conflict,
    left: Proposition,
    right: Proposition | None = None,
    *,
    left_centrality: dict[str, Any] | None = None,
    right_centrality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Operational blocking-ness for progress — never Model correctness (ADR-0002).

    ``central_proposition`` means the defined concept (ticket 16): a party
    whose centrality assessment reads central — derivation subtree or
    Requirements activity — not merely an Accepted one. ``unavoidable``
    remains ``critical ∧ L4``, hence still exactly L4.
    """
    left_centrality = left_centrality or assess_centrality(left, 0)
    if right is None:
        right_centrality = None
    else:
        right_centrality = right_centrality or assess_centrality(right, 0)
    reasons: list[str] = []
    if conflict.level in ("L2", "L3", "L4"):
        reasons.append("high_conflict_level")
    parties = [{"id": left.id, "centrality": left_centrality}]
    if right is not None:
        parties.append({"id": right.id, "centrality": right_centrality})
    if any(p["centrality"]["central"] for p in parties):
        reasons.append("central_proposition")
    critical = bool(reasons)
    unavoidable = is_unavoidable(conflict.level, critical=critical)
    return {
        "critical": critical,
        "recommend_against": critical,
        "deferrable": not unavoidable,
        "unavoidable": unavoidable,
        "reasons": reasons,
        "parties": parties,
    }


class InferenceEngine:
    """Reconciliation, Assertion Tests, Batches, and Probes."""

    def __init__(self, backend: BackendProtocol) -> None:
        self._backend = backend
        self._propositions = PropositionStore(backend)
        self._coverage = CoverageStore(backend)
        self._notifications = NotificationService(backend)

    def current_pass(self) -> int:
        """Pass 1 is the Opening-seeded pass; increments after each probed Batch."""
        probed = sum(1 for b in self._load_batches() if b.status == "probed")
        return probed + 1

    def reconcile(self, findings: list[dict[str, Any]]) -> list[Conflict]:
        """Surface latent L2/L3 conflicts from the latest ingest (pass 2+ only).

        An empty run is a valid outcome, not an error: it records that
        Reconciliation ran and surfaced nothing, which satisfies the
        pre-Scenario gate for the pass — findings are never fabricated.
        """
        self._require_no_pending_batch()
        pass_no = self.current_pass()
        if pass_no < 2:
            raise Refusal(
                "Reconciliation applies from pass 2 onward",
                ["scenarios", "assertion_tests", "door"],
            )

        state = self._load_inference_state()
        if state.get("reconciliation_pass") == pass_no:
            raise Refusal(
                f"Reconciliation already completed for pass {pass_no}",
                ["scenarios", "assertion_tests", "probe", "door"],
            )

        if not findings:
            state["reconciliation_pass"] = pass_no
            state.setdefault("blocked_proposition_ids", [])
            self._save_inference_state(state)
            return []

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
        self._coverage.add_conflicts(pass_no, len(surfaced))
        return surfaced

    def record_scenarios(
        self,
        proposition_id: str,
        scenarios: list[dict[str, Any]],
    ) -> list[Scenario]:
        self._require_no_pending_batch()
        self._require_proposition(proposition_id)
        self._require_need()
        self._require_reconciliation_before_scenarios()
        if proposition_id in self._blocked_proposition_ids():
            raise Refusal(
                "Scenario generation skipped: Proposition "
                f"{proposition_id} was contradicted by Reconciliation",
                ["probe", "defer"],
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
        self.touch_propositions(proposition_id)
        return recorded

    def run_assertion_tests(
        self,
        proposition_id: str,
        outcomes: list[dict[str, Any]],
    ) -> list[Conflict]:
        self._require_no_pending_batch()
        self._require_proposition(proposition_id)
        self._require_reconciliation_before_scenarios()
        if proposition_id in self._blocked_proposition_ids():
            raise Refusal(
                "Assertion Tests skipped: Proposition "
                f"{proposition_id} was contradicted by Reconciliation",
                ["probe", "defer"],
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
        record: list[dict[str, Any]] = []
        conflicts = self._load_conflicts()
        for raw in outcomes:
            scenario_id = raw.get("scenario_id")
            if scenario_id not in scenarios:
                raise ValueError(
                    f"Unknown Scenario {scenario_id!r} for Proposition {proposition_id}"
                )
            scenario = scenarios[scenario_id]
            survives = raw.get("survives")
            if survives is not True and survives is not False:
                raise ValueError("Outcome.survives must be a boolean")
            # Every outcome enters the record (socrates-seam ticket 02) —
            # survivals included: the run is nothing, the record is the
            # lapidation. A survival used to `continue` straight into
            # nothing, and the specimen's rubber stamps left no trace.
            record.append(
                {
                    "proposition_id": proposition_id,
                    "scenario_id": scenario_id,
                    "survives": survives,
                }
            )
            if survives is True:
                continue
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
        # Saved only once every outcome has validated — the step stays
        # transactional, no partial record on a malformed batch.
        self._save_assertions(record)
        self._coverage.add_conflicts(self.current_pass(), len(surfaced))
        for conflict in surfaced:
            self._maybe_notify_unavoidable(conflict)
        self.touch_propositions(proposition_id)
        return surfaced

    def probe_batch(self) -> dict[str, Any]:
        """ASK: gather open L1–L3 Conflicts into a Batch and return the
        pending question (AskHuman, ticket 28). L4 is Iteration, not Probe.

        The Batch is created and its question persisted; the resolutions
        arrive on a later ``probe_resume`` call. Re-calling while the probe
        question is pending re-presents it unchanged (one Batch per
        question); any other asking verb while it is pending is refused.
        """
        # The guard fingerprint is the subject the payload carries (the
        # Batch id), derived from the Batch's own record — a re-ask
        # re-presents the standing question, whose Batch is the one still
        # open; the pending marker never gets to define its own identity.
        open_batch_id = next(
            (b.id for b in self._load_batches() if b.status == "open"),
            None,
        )
        existing = guard_pending(self._backend, "probe", open_batch_id)
        if existing is not None:
            return existing

        conflicts = self._load_conflicts()
        open_conflicts = [
            c
            for c in conflicts
            if c.status == "open" and c.batch_id is None and c.level != "L4"
        ]
        if not open_conflicts:
            l4_open = any(
                c.status == "open" and c.batch_id is None and c.level == "L4"
                for c in conflicts
            )
            raise Refusal(
                "No Probe-resolvable Conflicts (L1–L3); "
                "L4 Conflicts require Iteration via run_iteration",
                ["iteration"] if l4_open else ["door"],
            )

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

        return begin_pending(
            self._backend,
            {
                "kind": "probe",
                "subject": batch.id,
                "batch_id": batch.id,
                "question": (
                    f"Batch {batch.id} holds {len(open_conflicts)} open "
                    "Conflict(s) — resolve every one:"
                ),
                "conflicts": [
                    self._probe_conflict_payload(c) for c in open_conflicts
                ],
                "accepted_answers": PROBE_ACCEPTED_ANSWERS,
                "resume_contract": PROBE_RESUME_CONTRACT,
            },
        )

    def probe_resume(self, answer: Any) -> dict[str, Any]:
        """APPLY: apply the resumed resolutions to the pending Batch.

        Transactional across the split: a malformed resume rolls the Model
        back to the asked state (the Batch stays presented, its conflicts
        open) and raises — the conductor repairs and resumes the same
        Batch instead of stranding it half-applied.
        """
        pending = require_pending(self._backend, "probe")
        canonical, raw = parse_envelope(answer)
        snapshot = self._snapshot_state()
        try:
            applied = self._apply_resolutions(pending["batch_id"], canonical)
        except Exception:
            # Transactional across the split on ANY failure — a TypeError
            # from a malformed resolution is as unwelcome mid-apply as a
            # ValueError: the Model rolls back to the asked state and the
            # Batch stays presented for a repaired resume.
            self._restore_state(snapshot)
            raise
        clear_pending(self._backend)
        return {
            "batch_id": pending["batch_id"],
            "conflict_ids": [c["conflict_id"] for c in applied],
            "applied": applied,
            "notifications": self._propositions.list_notifications(),
            "answer": {"canonical": canonical, "raw": raw},
        }

    def run_iteration(self, conflict_id: str) -> dict[str, Any]:
        """ASK: hand an L4 Conflict to Iteration — propose the activity and
        return the pending confirmation question (AskHuman, ticket 28)."""
        existing = guard_pending(self._backend, "iteration", conflict_id)
        if existing is not None:
            return existing

        conflicts = self._load_conflicts()
        conflict = next((c for c in conflicts if c.id == conflict_id), None)
        if conflict is None:
            raise ValueError(f"Unknown Conflict {conflict_id!r}")
        if conflict.level != "L4":
            raise ValueError(
                f"Iteration is only for L4 Conflicts; {conflict_id} is {conflict.level}"
            )
        if conflict.status != "open":
            raise ValueError(f"Conflict {conflict_id} is not open")
        if not conflict.other_proposition_id:
            raise ValueError("L4 Conflict requires other_proposition_id")

        left = self._propositions.get(conflict.proposition_id)
        right = self._propositions.get(conflict.other_proposition_id)
        proposed = propose_iteration_activity(left, right)

        return begin_pending(
            self._backend,
            {
                "kind": "iteration",
                "subject": conflict.id,
                "conflict_id": conflict.id,
                "proposed_activity": proposed,
                "summary": conflict.summary,
                "parties": [
                    {
                        "id": left.id,
                        "statement": left.statement,
                        "activity": left.activity,
                        "status": left.status,
                        "centrality": self._centrality_for(left),
                    },
                    {
                        "id": right.id,
                        "statement": right.statement,
                        "activity": right.activity,
                        "status": right.status,
                        "centrality": self._centrality_for(right),
                    },
                ],
                "question": (
                    f"L4 Conflict {conflict.id} invalidates established beliefs. "
                    f"Confirm reopening Modeling Activity '{proposed}'?"
                ),
                "accepted_answers": _iteration_answers(proposed),
                "resume_contract": _ITERATION_RESUME_CONTRACT,
            },
        )

    def iteration_resume(self, answer: Any) -> dict[str, Any]:
        """APPLY: confirm the proposal (or its override) and reopen the phase.

        A non-canonical confirm is a structured refusal — the question
        stays pending and the conductor repairs in conversation.
        """
        pending = require_pending(self._backend, "iteration")
        canonical, raw = parse_envelope(answer)
        proposed = pending["proposed_activity"]
        try:
            confirmed = _parse_iteration_confirm(canonical, proposed)
        except ValueError as exc:
            raise token_refusal(pending, str(exc)) from exc

        conflicts = self._load_conflicts()
        conflict = next(
            (c for c in conflicts if c.id == pending["conflict_id"]), None
        )
        if conflict is None:
            raise ValueError(f"Unknown Conflict {pending['conflict_id']!r}")
        if conflict.status != "open":
            raise ValueError(f"Conflict {conflict.id} is not open")

        pipeline = PipelineStore(self._backend).reopen(confirmed)

        conflict.status = "resolved"
        conflict.resolution = {
            "action": "iterate",
            "proposed_activity": proposed,
            "activity": confirmed,
        }
        self._save_conflicts(conflicts)
        clear_pending(self._backend)

        return {
            "conflict_id": conflict.id,
            "proposed_activity": proposed,
            "confirmed_activity": confirmed,
            "pipeline": pipeline,
            "answer": {"canonical": canonical, "raw": raw},
        }

    def defer_conflict(self, conflict_id: str) -> dict[str, Any]:
        """Park an open Conflict for later — refused when unavoidable (ticket 10)."""
        conflicts = self._load_conflicts()
        conflict = next((c for c in conflicts if c.id == conflict_id), None)
        if conflict is None:
            raise ValueError(f"Unknown Conflict {conflict_id!r}")
        if conflict.status != "open":
            raise ValueError(f"Conflict {conflict_id} is not open")
        criticality = self._criticality_for(conflict)
        if criticality.get("unavoidable"):
            raise Refusal(
                f"Conflict {conflict_id} is unavoidable (non-deferrable, blocks "
                "progress); resolve via Iteration or Probe — Notification already "
                "surfaced it outside Interview flow",
                ["iteration"],
            )
        conflict.status = "deferred"
        conflict.re_raised = False
        conflict.batch_id = None
        conflict.resolution = {"action": "defer", "criticality": criticality}
        self._save_conflicts(conflicts)
        # Deferral never blocks the current pass (CONTEXT) — standalone or
        # in-Batch, deferring unblocks the quarantined new Proposition.
        if conflict.source == "reconciliation":
            self._unblock_propositions({conflict.proposition_id})
        return {
            "conflict_id": conflict.id,
            "status": "deferred",
            "criticality": criticality,
        }

    def touch_propositions(self, *proposition_ids: str) -> list[Conflict]:
        """Re-raise deferred Conflicts whose parties are touched by new information."""
        touched = {pid for pid in proposition_ids if pid}
        if not touched:
            return []
        conflicts = self._load_conflicts()
        raised: list[Conflict] = []
        for conflict in conflicts:
            if conflict.status != "deferred":
                continue
            parties = {conflict.proposition_id}
            if conflict.other_proposition_id:
                parties.add(conflict.other_proposition_id)
            if not parties & touched:
                continue
            conflict.status = "open"
            conflict.batch_id = None
            conflict.re_raised = True
            conflict.resolution = None
            raised.append(conflict)
        if raised:
            self._save_conflicts(conflicts)
        return raised

    def satisfaction_warning(
        self,
        *,
        visiting: ModelingActivity | None = None,
    ) -> dict[str, Any] | None:
        """Non-blocking, criticality-weighted warning for open deferred Conflicts.

        Entries are graded by structural load (ticket 16): weight descending —
        blast radius decides what is read first — with ties resolving to the
        Requirements side. Weighing is payload only: the Deferral
        recommendation stays boolean and the warning never blocks (ADR-0002).

        Ticket 20: the warning also names the chapters never visited, so an
        early Satisfaction (the door's third answer) is informed, never
        surprised. Visited means begun or completed, derived from the
        pipeline facts at read time (ADR-0001). ``visiting``
        is the door's own activity when the warning is asked from a door:
        the chapter whose door carries the question was self-evidently
        visited, vacuous chapter or not (``begin`` only persists at close).

        Ticket 23 / spec `need-refinement`: the session's Need amendments
        ride alongside — an early close is informed about the Relevance
        Filter's history, not just its conflicts. The amendments are read
        from the Need file's record at read time (ADR-0001) and count in
        the emptiness rule: with them on record there is something to say
        even with nothing deferred.
        """
        deferred = [c for c in self._load_conflicts() if c.status == "deferred"]
        amendments = read_amendments(self._backend)
        # One look weighs everything: the fast-answer signal and the
        # unreadable condition come from the same whole-file read — a
        # second walk of the log is a second chance to disagree with
        # the first.
        log_read = read_log(self._backend)
        self_answered = self._self_answered(log_read)
        log_unreadable = log_read.unreadable
        pipeline = PipelineStore(self._backend).snapshot()
        completed = pipeline.get("completed", ())
        active = pipeline.get("active")
        never_visited = [
            activity
            for activity in ACTIVITIES_IN_ORDER
            if activity not in completed
            and activity != active
            and activity != visiting
        ]
        if (
            not deferred
            and not never_visited
            and not amendments
            and not self_answered
            and not log_unreadable
        ):
            return None
        entries: list[dict[str, Any]] = []
        for c in deferred:
            criticality = self._criticality_for(c)
            centrality = [p["centrality"] for p in criticality["parties"]]
            entries.append(
                {
                    "id": c.id,
                    "level": c.level,
                    "summary": c.summary,
                    "proposition_id": c.proposition_id,
                    "other_proposition_id": c.other_proposition_id,
                    "criticality": criticality,
                    # A parked Conflict is as heavy as its heaviest party.
                    "dependents": max((a["dependents"] for a in centrality), default=0),
                    "weight": max((a["weight"] for a in centrality), default=0),
                    "requirements": any(
                        a["dimension"] in _REQUIREMENTS_DIMENSIONS
                        for a in centrality
                    ),
                }
            )
        # Weight descending; ties to the Requirements side; id for determinism.
        entries.sort(key=lambda e: (-e["weight"], not e["requirements"], e["id"]))
        warning = {
            "kind": "deferred_conflicts",
            "blocking": False,
            "conflicts": entries,
            "chapters_never_visited": never_visited,
            "amendments": amendments,
        }
        if self_answered:
            # The signal is present or absent — never a zero-filled count
            # (socrates-seam ticket 01).
            warning["self_answered"] = {
                "count": len(self_answered),
                "answers": self_answered,
            }
        if log_unreadable:
            # The unreadable and the empty never look alike
            # (answer-log-integrity): the condition rides present-or-
            # absent, now and after any repair (the marker).
            warning["answer_log_unreadable"] = True
        return warning

    def _self_answered(self, log_read: AnswerLogRead) -> list[dict[str, Any]]:
        """The recorded answers that arrived faster than a human can read
        their question — the ask–answer binding weighed at the end.

        Pairs without a stamp (an older marker) cannot be judged and are
        skipped; the window is generous to the honest relay, and nothing
        anywhere refuses on it — this is the user's information, not a
        gate (socrates-seam ticket 01).
        """
        fast: list[dict[str, Any]] = []
        for entry in log_read.entries or ():
            if not isinstance(entry, dict):
                continue
            asked = _parse_iso(entry.get("asked_at"))
            answered = _parse_iso(entry.get("answered_at"))
            if asked is None or answered is None:
                continue
            delta = (answered - asked).total_seconds()
            # A negative delta is clock skew between the two stamps (the
            # resumed-session case), not evidence — unjudgeable pairs are
            # skipped, never guessed into the record.
            if 0 <= delta < FAST_ANSWER_WINDOW_SECONDS:
                fast.append(entry)
        return fast

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
            if not isinstance(raw, dict):
                raise ValueError("Each resolution must be an object")
            conflict_id = raw.get("conflict_id")
            action = raw.get("action")
            if conflict_id not in batch_conflict_ids:
                raise ValueError(
                    f"Conflict {conflict_id!r} is not in open Batch {batch_id}"
                )
            if conflict_id in resolved_ids:
                raise ValueError(
                    f"Duplicate resolution for {conflict_id!r} — one entry "
                    "per Conflict of the Batch"
                )
            conflict = by_id[conflict_id]
            if conflict.level == "L4":
                raise ValueError(
                    "L4 Conflicts are handed to Iteration, not Probe-resolved; "
                    "use run_iteration"
                )
            if conflict.level == "L3" and action not in ("dismiss", "defer"):
                raise ValueError(
                    "L3 conflicts are blocked by the Rejection Guardrail; "
                    "only dismiss or defer is allowed"
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
            elif action == "defer":
                criticality = self._criticality_for(conflict)
                if criticality.get("unavoidable"):
                    raise ValueError(
                        f"Conflict {conflict_id} is unavoidable (non-deferrable); "
                        "cannot defer"
                    )
                conflict.status = "deferred"
                conflict.re_raised = False
                conflict.resolution = {"action": "defer", "criticality": criticality}
                applied.append(
                    {
                        "conflict_id": conflict_id,
                        "action": "defer",
                        "status": "deferred",
                        "criticality": criticality,
                    }
                )
                resolved_ids.add(conflict_id)
                # Deferral never blocks the current pass (CONTEXT): unblock
                # the new Proposition the finding had quarantined.
                if conflict.source == "reconciliation":
                    unblocked.add(conflict.proposition_id)
                continue
            else:
                raise ValueError(
                    f"Unknown Probe action {action!r}; expected one of "
                    f"revise_proposition, add_proposition, supersede, dismiss, defer"
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
            self._unblock_propositions(unblocked)

        return applied

    # Every file a Probe application may mutate — snapshotted so a
    # malformed resume rolls back atomically (see probe_batch).
    _STATE_PATHS = (
        PROPOSITIONS_PATH,
        CONFLICTS_PATH,
        BATCHES_PATH,
        INFERENCE_STATE_PATH,
        NOTIFICATIONS_PATH,
    )

    def _snapshot_state(self) -> dict[str, str | None]:
        """Raw pre-Batch contents; ``None`` marks an absent file."""
        snapshot: dict[str, str | None] = {}
        for path in self._STATE_PATHS:
            result = self._backend.read(path)
            snapshot[path] = (
                None
                if result.error or result.file_data is None
                else result.file_data["content"]
            )
        return snapshot

    def _restore_state(self, snapshot: dict[str, str | None]) -> None:
        for path, content in snapshot.items():
            if content is None:
                self._backend.delete(path)
            else:
                self._backend.write(path, content)

    def _unblock_propositions(self, proposition_ids: set[str]) -> None:
        """Drop ids from the Reconciliation block so Scenarios may proceed."""
        if not proposition_ids:
            return
        state = self._load_inference_state()
        blocked = set(state.get("blocked_proposition_ids", [])) - proposition_ids
        state["blocked_proposition_ids"] = sorted(blocked)
        self._save_inference_state(state)

    def _require_reconciliation_before_scenarios(self) -> None:
        pass_no = self.current_pass()
        if pass_no < 2:
            return
        state = self._load_inference_state()
        if state.get("reconciliation_pass") != pass_no:
            raise Refusal(
                "Reconciliation must run before Scenario generation / "
                f"Assertion Tests from pass 2 (current pass {pass_no})",
                ["reconcile"],
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

    def _centrality_for(self, proposition: Proposition) -> dict[str, Any]:
        """Central Proposition assessment from the current graph (ticket 16)."""
        dependents = self._propositions.transitive_dependents(proposition.id)
        return assess_centrality(proposition, len(dependents))

    def _criticality_for(self, conflict: Conflict) -> dict[str, Any]:
        left = self._propositions.get(conflict.proposition_id)
        right = (
            self._propositions.get(conflict.other_proposition_id)
            if conflict.other_proposition_id
            else None
        )
        return assess_deferral_criticality(
            conflict,
            left,
            right,
            left_centrality=self._centrality_for(left),
            right_centrality=(
                self._centrality_for(right) if right is not None else None
            ),
        )

    def _maybe_notify_unavoidable(self, conflict: Conflict) -> None:
        criticality = self._criticality_for(conflict)
        if not criticality.get("unavoidable"):
            return
        self._notifications.emit(
            "unavoidable_conflict",
            conflict_id=conflict.id,
            level=conflict.level,
            summary=conflict.summary,
            proposition_id=conflict.proposition_id,
            other_proposition_id=conflict.other_proposition_id,
            criticality=criticality,
            blocks_progress=True,
            deferrable=False,
        )

    def _probe_conflict_payload(self, conflict: Conflict) -> dict[str, Any]:
        criticality = self._criticality_for(conflict)
        return {
            "id": conflict.id,
            "proposition_id": conflict.proposition_id,
            "other_proposition_id": conflict.other_proposition_id,
            "scenario_id": conflict.scenario_id,
            "kind": conflict.kind,
            "summary": conflict.summary,
            "level": conflict.level,
            "source": conflict.source,
            "routing": _probe_routing(conflict.level),
            "re_raised": conflict.re_raised,
            "deferral": criticality,
        }

    def _require_need(self) -> str:
        # The live Need — the file's body, never its amendment record
        # (ticket 22: the filter is amendable; the record is audit).
        need = read_need(self._backend)
        if not need:
            raise Refusal(
                "Need must be persisted before generating Scenarios",
                ["opening"],
            )
        return need

    def _require_no_pending_batch(self) -> None:
        # The Batch glossary rule, made mechanical for every surface
        # (review 3): "the user clarifies every Conflict in it before the
        # next pass runs". A presented Batch carries its pending
        # question, so the one admissible move is to answer it.
        if any(b.status == "open" for b in self._load_batches()):
            raise Refusal(
                "a Probe Batch still awaits the user — no new pass runs "
                "until every Conflict in the pending Batch is resolved "
                "or deferred",
                ["resume"],
            )

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
            data.setdefault("re_raised", False)
            loaded.append(Conflict(**data))
        return loaded

    def _save_conflicts(self, conflicts: list[Conflict]) -> None:
        self._backend.write(
            CONFLICTS_PATH,
            json.dumps({"conflicts": [asdict(c) for c in conflicts]}, indent=2),
        )

    def _save_assertions(self, record: list[dict[str, Any]]) -> None:
        """Append one assertion batch to the record (socrates-seam ticket 02)."""
        existing = self._read_json(ASSERTIONS_PATH) or {}
        entries = existing.get("assertions", [])
        entries.extend(record)
        self._backend.write(
            ASSERTIONS_PATH,
            json.dumps({"assertions": entries}, indent=2),
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


def _probe_routing(level: ConflictLevel) -> str:
    if level == "L1":
        return "inline"
    if level == "L2":
        return "supersede"
    if level == "L3":
        return "blocked"
    return "iteration"


def _parse_iteration_confirm(
    answer: Any,
    proposed: ModelingActivity,
) -> ModelingActivity:
    """Accept yes/proposed, or an explicit Modeling Activity override."""
    if answer is True or answer == "yes":
        return proposed
    if isinstance(answer, dict):
        if answer.get("confirm") is True or answer.get("confirm") == "yes":
            activity = answer.get("activity", proposed)
        else:
            activity = answer.get("activity") or answer.get("confirmed_activity")
        if activity is None:
            raise ValueError(
                "Iteration confirm must accept the proposal or name an activity"
            )
        answer = activity
    if isinstance(answer, str):
        activity = answer.strip()
        if activity in ACTIVITIES_IN_ORDER:
            return activity  # type: ignore[return-value]
        if activity in ("yes", "confirm", "true"):
            return proposed
    raise ValueError(
        "Iteration resume must confirm the proposed activity "
        f"or name one of {list(ACTIVITIES_IN_ORDER)}"
    )
