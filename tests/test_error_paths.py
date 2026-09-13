"""Engine-level tests for maieutic-loop error paths (post-MVP fixes).

Seam: deterministic harness logic over ``FilesystemBackend``, with the
Probe asked and resumed through the AskHuman split (ticket 28) — these
paths live below the session-orchestration seam the ticket tests
exercise. Covers: empty Reconciliation as a valid outcome, transactional
Probe application (a malformed resume rolls back to the asked state and
the same Batch re-presents), and Deferral never blocking the current
pass.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from deepagents.backends.filesystem import FilesystemBackend

from socrates.asking import read_pending
from socrates.inference import InferenceEngine
from socrates.paths import (
    BATCHES_PATH,
    CONFLICTS_PATH,
    INFERENCE_STATE_PATH,
    NEED_PATH,
)
from socrates.proposition import PropositionStore


def _engine(tmp_path: Path):
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    return backend, InferenceEngine(backend), PropositionStore(backend)


def _two_scenarios(prefix: str) -> list[dict]:
    return [
        {"description": f"{prefix} edge one", "edge": "one", "need_relevant": True},
        {"description": f"{prefix} edge many", "edge": "many", "need_relevant": True},
    ]


def _at_pass_two(backend, store) -> None:
    """Accepted foundation + probed Batch → the engine is at pass 2."""
    store.propose("A Payment belongs to exactly one Order.", "domain_modeling")
    store.accept("p1")
    backend.write(
        BATCHES_PATH,
        json.dumps(
            {"batches": [{"id": "b1", "conflict_ids": [], "status": "probed"}]}
        ),
    )


def _reconcile_many_orders(engine) -> list:
    """Surface the canonical L2: new many-Orders candidate vs Accepted p1."""
    return engine.reconcile(
        [
            {
                "new_proposition_id": "p2",
                "against_kind": "accepted",
                "against_id": "p1",
                "kind": "contradiction",
                "summary": "Many-Orders contradicts exclusive ownership.",
            }
        ]
    )


def _load(backend, path: str) -> dict:
    return json.loads(backend.read(path).file_data["content"])


def test_empty_reconciliation_stamps_pass_and_unblocks_scenarios(tmp_path):
    backend, engine, store = _engine(tmp_path)
    _at_pass_two(backend, store)
    store.propose("A Payment may be voided before settlement.", "domain_modeling")

    surfaced = engine.reconcile([])
    assert surfaced == []
    assert _load(backend, INFERENCE_STATE_PATH)["reconciliation_pass"] == 2

    # Gate satisfied — Scenarios proceed without fabricated findings.
    recorded = engine.record_scenarios("p2", _two_scenarios("void"))
    assert [s.edge for s in recorded] == ["one", "many"]

    # Still once per pass.
    with pytest.raises(ValueError, match="already completed"):
        engine.reconcile([])


def test_malformed_probe_resume_rolls_back_and_re_presents(tmp_path):
    backend, engine, store = _engine(tmp_path)
    _at_pass_two(backend, store)
    store.propose("A Payment may belong to many Orders.", "domain_modeling")
    conflicts = _reconcile_many_orders(engine)
    assert [c.id for c in conflicts] == ["c1"]

    asked = engine.probe_batch()
    assert asked["kind"] == "probe"
    assert asked["batch_id"] == "b2"

    # First resolution is valid, second is garbage — nothing may persist.
    with pytest.raises(ValueError, match="Unknown Probe action"):
        engine.probe_resume(
            {
                "resolutions": [
                    {
                        "conflict_id": "c1",
                        "action": "revise_proposition",
                        "statement": "Revised under a bad Batch.",
                    },
                    {"conflict_id": "c1", "action": "acao_invalida"},
                ]
            }
        )

    # Rollback to the asked state: conflict still open in its presented
    # Batch, no partial revise — and the question still pending.
    rolled = _load(backend, CONFLICTS_PATH)["conflicts"]
    assert rolled[0]["status"] == "open"
    assert rolled[0]["batch_id"] == "b2"
    batches = _load(backend, BATCHES_PATH)["batches"]
    assert batches == [
        {"id": "b1", "conflict_ids": [], "status": "probed"},
        {"id": "b2", "conflict_ids": ["c1"], "status": "open"},
    ]
    assert (
        _load(backend, "/model/propositions.json")["propositions"][1]["statement"]
        == "A Payment may belong to many Orders."
    )
    assert read_pending(backend)["kind"] == "probe"

    # Re-present: the same Batch re-presents unchanged (no b3), and the
    # repaired resume resolves it cleanly.
    again = engine.probe_batch()
    assert again == asked
    result = engine.probe_resume(
        {"resolutions": [{"conflict_id": "c1", "action": "dismiss"}]}
    )
    assert result["batch_id"] == "b2"
    assert result["applied"][0]["action"] == "dismiss"
    final = _load(backend, CONFLICTS_PATH)["conflicts"]
    assert final[0]["status"] == "resolved"
    assert read_pending(backend) is None


def test_probe_defer_of_reconciliation_conflict_unblocks(tmp_path):
    backend, engine, store = _engine(tmp_path)
    _at_pass_two(backend, store)
    store.propose("A Payment may belong to many Orders.", "domain_modeling")
    _reconcile_many_orders(engine)
    assert _load(backend, INFERENCE_STATE_PATH)["blocked_proposition_ids"] == ["p2"]

    engine.probe_batch()
    engine.probe_resume(
        {"resolutions": [{"conflict_id": "c1", "action": "defer"}]}
    )

    # Deferral never blocks the current pass (CONTEXT) — p2 released.
    assert _load(backend, INFERENCE_STATE_PATH)["blocked_proposition_ids"] == []
    # The probed Batch closed pass 2; pass 3 opens with its own (empty —
    # nothing new) Reconciliation, then Scenarios proceed on p2.
    assert engine.current_pass() == 3
    assert engine.reconcile([]) == []
    recorded = engine.record_scenarios("p2", _two_scenarios("deferred"))
    assert len(recorded) == 2
    # The parked Conflict is not dropped: recording Scenarios on its party
    # re-raises it for the next Batch (event-driven re-raise).
    conflicts = _load(backend, CONFLICTS_PATH)["conflicts"]
    assert conflicts[0]["status"] == "open"
    assert conflicts[0]["re_raised"] is True


def test_standalone_defer_conflict_unblocks(tmp_path):
    backend, engine, store = _engine(tmp_path)
    _at_pass_two(backend, store)
    store.propose("A Payment may belong to many Orders.", "domain_modeling")
    _reconcile_many_orders(engine)
    assert _load(backend, INFERENCE_STATE_PATH)["blocked_proposition_ids"] == ["p2"]

    engine.defer_conflict("c1")

    assert _load(backend, INFERENCE_STATE_PATH)["blocked_proposition_ids"] == []
    recorded = engine.record_scenarios("p2", _two_scenarios("standalone"))
    assert len(recorded) == 2
