"""The AskHuman protocol — ticket 28 (socrates-hybrid spec).

Seam: engine verbs and engine methods over ``FilesystemBackend`` — no
graph, no langgraph. The engine asks by returning a pending-question
payload and persisting the marker in the session state; the resume
arrives on a later call carrying ``{canonical, raw}`` (the token drives
the machine, the raw words ride as provenance). These tests pin the
protocol itself: the payload contract, one pending question at a time,
same-kind re-presentation, canonical-driven resumes, structured refusal
on non-canonical tokens, the door's ask-never-guess rule, and the Probe's
transactional application across the split. The session layer's
interrupt-backed adapter over this same boundary is pinned by the
existing orchestration suite.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest
from deepagents.backends.filesystem import FilesystemBackend

from socrates.asking import AskRefusal, read_pending
from socrates.inference import InferenceEngine
from socrates.paths import (
    BATCHES_PATH,
    CONFLICTS_PATH,
    DELIVERABLE_GLOSSARY_PATH,
    NEED_PATH,
    PENDING_QUESTION_PATH,
    PIPELINE_PATH,
    PROPOSITIONS_PATH,
)
from socrates.proposition import PropositionStore
from socrates.verbs import (
    ask_accept,
    ask_amend_need,
    ask_door,
    ask_opening,
    ask_satisfaction,
    resume_accept,
    resume_amend_need,
    resume_door,
    resume_opening,
    resume_satisfaction,
)


def _backend(tmp_path: Path) -> FilesystemBackend:
    return FilesystemBackend(root_dir=tmp_path, virtual_mode=True)


def _load(backend: FilesystemBackend, path: str) -> dict:
    return json.loads(backend.read(path).file_data["content"])


def _propose(backend: FilesystemBackend, statement: str, activity: str) -> str:
    store = PropositionStore(backend)
    prop = store.propose(statement, activity)
    return prop.id


def _l1_engine(backend: FilesystemBackend) -> InferenceEngine:
    """One open L1 Conflict, ready to Probe: candidate + Scenarios + a
    non-surviving Scenario with no second party."""
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    _propose(
        backend, "Payment status is always Authorized or Settled.", "domain_modeling"
    )
    engine = InferenceEngine(backend)
    engine.record_scenarios(
        "p1",
        [
            {
                "description": "Authorized Payment awaiting capture",
                "edge": "one",
                "need_relevant": True,
            },
            {
                "description": "Void is not covered by Authorized|Settled.",
                "edge": "many",
                "need_relevant": True,
            },
        ],
    )
    engine.run_assertion_tests(
        "p1",
        [
            {"scenario_id": "s1", "survives": True},
            {
                "scenario_id": "s2",
                "survives": False,
                "kind": "contrariety",
                "summary": "Void breaks the Authorized|Settled dichotomy.",
            },
        ],
    )
    return engine


def _l4_engine(backend: FilesystemBackend) -> InferenceEngine:
    """One open L4 Conflict, ready for Iteration: two Accepted parties
    colliding on an intersection Scenario."""
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    store = PropositionStore(backend)
    store.propose("A Payment belongs to exactly one Order.", "requirements")
    store.accept("p1")
    store.propose("Payment status is always Authorized or Settled.", "domain_modeling")
    store.accept("p2")
    engine = InferenceEngine(backend)
    engine.record_scenarios(
        "p2",
        [
            {
                "description": "Authorized Payment awaiting capture",
                "edge": "one",
                "need_relevant": True,
            },
            {
                "description": "Intersection: Authorized Payment voided at checkout",
                "edge": "intersection",
                "need_relevant": True,
            },
        ],
    )
    engine.run_assertion_tests(
        "p2",
        [
            {"scenario_id": "s1", "survives": True},
            {
                "scenario_id": "s2",
                "survives": False,
                "kind": "omission",
                "summary": "Void is not covered by Authorized|Settled.",
                "other_proposition_id": "p1",
            },
        ],
    )
    return engine


# --- The payload contract ----------------------------------------------------


def _ask_factories() -> dict[str, Callable[[FilesystemBackend], dict[str, Any]]]:
    def _accept(backend: FilesystemBackend) -> dict[str, Any]:
        backend.write(NEED_PATH, "Marketplace checkout payments domain.")
        _propose(
            backend,
            "Payment status is always Authorized or Settled.",
            "domain_modeling",
        )
        return ask_accept(backend, "p1")

    def _amend(backend: FilesystemBackend) -> dict[str, Any]:
        backend.write(NEED_PATH, "Marketplace checkout payments domain.")
        return ask_amend_need(backend, "A refund marketplace.", "Refunds are in scope.")

    def _probe(backend: FilesystemBackend) -> dict[str, Any]:
        return _l1_engine(backend).probe_batch()

    def _iteration(backend: FilesystemBackend) -> dict[str, Any]:
        return _l4_engine(backend).run_iteration("c1")

    return {
        "opening": ask_opening,
        "accept": _accept,
        "amend_need": _amend,
        "door": lambda backend: ask_door(backend, "requirements"),
        "satisfaction": ask_satisfaction,
        "probe": _probe,
        "iteration": _iteration,
    }


def _resumers() -> dict[str, Callable[[FilesystemBackend], Any]]:
    return {
        "opening": lambda backend: resume_opening(
            backend, {"canonical": "A marketplace.", "raw": "a marketplace"}
        ),
        "accept": lambda backend: resume_accept(
            backend, {"canonical": "decline", "raw": "no"}
        ),
        "amend_need": lambda backend: resume_amend_need(
            backend, {"canonical": "decline", "raw": "no"}
        ),
        "door": lambda backend: resume_door(
            backend, {"canonical": "not_yet", "raw": "not yet"}
        ),
        "satisfaction": lambda backend: resume_satisfaction(
            backend, {"canonical": "not_satisfied", "raw": "no"}
        ),
        "probe": lambda backend: InferenceEngine(backend).probe_resume(
            {
                "canonical": {
                    "resolutions": [{"conflict_id": "c1", "action": "dismiss"}]
                },
                "raw": "dismiss",
            }
        ),
        "iteration": lambda backend: InferenceEngine(backend).iteration_resume(
            {"canonical": True, "raw": "yes"}
        ),
    }


@pytest.mark.parametrize("kind", sorted(_ask_factories()))
def test_every_ask_returns_the_payload_contract_and_persists_it(
    tmp_path, kind
):
    backend = _backend(tmp_path)
    payload = _ask_factories()[kind](backend)

    assert payload["kind"] == kind
    assert payload["question"]
    assert payload["accepted_answers"]
    assert all(
        entry["token"] and entry["meaning"] for entry in payload["accepted_answers"]
    )
    assert "canonical" in payload["resume_contract"]

    # The marker is session state (ADR-0001): the whole payload persists.
    assert read_pending(backend) == payload
    assert _load(backend, PENDING_QUESTION_PATH) == payload

    # And the canonical resume clears it, completing the cycle.
    _resumers()[kind](backend)
    assert read_pending(backend) is None


# --- One pending question at a time -----------------------------------------


def test_second_asking_verb_refuses_naming_the_pending_question(tmp_path):
    backend = _backend(tmp_path)
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    _propose(
        backend, "Payment status is always Authorized or Settled.", "domain_modeling"
    )
    door = ask_door(backend, "requirements")

    with pytest.raises(AskRefusal) as exc:
        ask_accept(backend, "p1")
    refusal = exc.value.payload
    assert refusal["ok"] is False
    assert refusal["refused"] is True
    assert refusal["pending"]["kind"] == "door"
    assert refusal["pending"]["question"] == door["question"]

    # The refusal leaves the pending question untouched.
    assert read_pending(backend) == door


def test_re_asking_the_same_kind_re_presents_unchanged(tmp_path):
    backend = _backend(tmp_path)
    engine = _l1_engine(backend)

    first = engine.probe_batch()
    again = engine.probe_batch()
    assert again == first
    # One Batch, not two — the question idempotent, the state unmoved.
    assert len(_load(backend, BATCHES_PATH)["batches"]) == 1


def test_re_asking_the_same_kind_about_a_different_subject_refuses(tmp_path):
    backend = _backend(tmp_path)
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    _propose(backend, "Payment status is always Authorized or Settled.", "domain_modeling")
    _propose(backend, "A Payment belongs to exactly one Order.", "requirements")
    ask_accept(backend, "p1")

    # Same kind, different Proposition: a DIFFERENT question — refused,
    # the pending one named (review fix: idempotence never crosses subjects).
    with pytest.raises(AskRefusal) as exc:
        ask_accept(backend, "p2")
    assert exc.value.payload["pending"]["kind"] == "accept"

    with pytest.raises(AskRefusal):
        ask_door(backend, "requirements")


def test_corrupt_pending_marker_self_heals_to_no_question(tmp_path):
    backend = _backend(tmp_path)
    backend.write(PENDING_QUESTION_PATH, "{truncated json")

    # A corrupt marker is no question anyone can answer: it heals instead
    # of deadlocking every later ask and resume (review fix).
    assert read_pending(backend) is None
    payload = ask_opening(backend)
    assert payload["kind"] == "opening"


# --- Resume: {canonical, raw} -------------------------------------------------


def test_opening_resume_writes_need_and_clears_the_marker(tmp_path):
    backend = _backend(tmp_path)
    ask_opening(backend)

    result = resume_opening(
        backend,
        {"canonical": "Um marketplace de pagamentos.", "raw": "um marketplace"},
    )
    assert result["ok"] is True
    assert result["need_path"] == NEED_PATH
    assert (
        backend.read(NEED_PATH).file_data["content"]
        == "Um marketplace de pagamentos."
    )
    # Provenance rides beside the token that drove the machine.
    assert result["answer"] == {
        "canonical": "Um marketplace de pagamentos.",
        "raw": "um marketplace",
    }
    assert read_pending(backend) is None


def test_probe_resume_envelope_applies_resolutions(tmp_path):
    backend = _backend(tmp_path)
    engine = _l1_engine(backend)
    payload = engine.probe_batch()
    assert payload["kind"] == "probe"
    assert payload["batch_id"] == "b1"
    assert [c["id"] for c in payload["conflicts"]] == ["c1"]
    assert "revise_proposition" in [e["token"] for e in payload["accepted_answers"]]

    result = engine.probe_resume(
        {
            "canonical": {"resolutions": [{"conflict_id": "c1", "action": "dismiss"}]},
            "raw": "o c1 não se sustenta",
        }
    )
    assert result["applied"][0]["action"] == "dismiss"
    assert result["answer"]["canonical"] == {
        "resolutions": [{"conflict_id": "c1", "action": "dismiss"}]
    }
    assert result["answer"]["raw"] == "o c1 não se sustenta"
    assert _load(backend, BATCHES_PATH)["batches"][0]["status"] == "probed"
    assert _load(backend, CONFLICTS_PATH)["conflicts"][0]["status"] == "resolved"
    assert read_pending(backend) is None


def test_amend_decline_preserves_the_need(tmp_path):
    backend = _backend(tmp_path)
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    ask_amend_need(backend, "A refund marketplace.", "Refunds are in scope.")

    result = resume_amend_need(backend, {"canonical": "decline", "raw": "no"})
    assert result["ok"] is False
    assert result["declined"] is True
    assert (
        backend.read(NEED_PATH).file_data["content"]
        == "Marketplace checkout payments domain."
    )
    assert read_pending(backend) is None


def test_accept_confirm_applies_and_returns_the_proposition(tmp_path):
    backend = _backend(tmp_path)
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    _propose(
        backend, "Payment status is always Authorized or Settled.", "domain_modeling"
    )
    ask_accept(backend, "p1")

    result = resume_accept(backend, {"canonical": "confirm", "raw": "yes"})
    assert result["ok"] is True
    assert result["id"] == "p1"
    assert result["status"] == "accepted"
    assert result["answer"]["canonical"] == "confirm"
    assert (
        _load(backend, PROPOSITIONS_PATH)["propositions"][0]["status"] == "accepted"
    )


def test_iteration_ask_then_canonical_activity_resume(tmp_path):
    backend = _backend(tmp_path)
    engine = _l4_engine(backend)

    payload = engine.run_iteration("c1")
    assert payload["kind"] == "iteration"
    assert payload["conflict_id"] == "c1"
    assert payload["proposed_activity"] == "requirements"
    # The menu is exactly what the validator admits (review fix): confirm,
    # or an activity NAME — no third grammar.
    assert [e["token"] for e in payload["accepted_answers"]] == [
        "confirm",
        "requirements",
        "domain_modeling",
        "behavioral_specification",
    ]

    result = engine.iteration_resume(
        {"canonical": {"activity": "domain_modeling"}, "raw": "reabra a modelagem"}
    )
    assert result["confirmed_activity"] == "domain_modeling"
    assert result["answer"]["raw"] == "reabra a modelagem"
    assert _load(backend, CONFLICTS_PATH)["conflicts"][0]["status"] == "resolved"
    assert _load(backend, PIPELINE_PATH)["active"] == "domain_modeling"
    assert read_pending(backend) is None


# --- Non-canonical tokens: structured refusal, never a default ----------------


def test_door_non_canonical_token_refuses_and_applies_nothing(tmp_path):
    backend = _backend(tmp_path)
    door = ask_door(backend, "requirements")

    with pytest.raises(AskRefusal) as exc:
        resume_door(backend, {"canonical": "kind of satisfied maybe", "raw": "hm"})
    refusal = exc.value.payload
    assert refusal["ok"] is False
    assert refusal["accepted_tokens"] == ["close", "not_yet", "satisfaction"]
    assert refusal["pending"]["question"] == door["question"]
    # The question stays open; the chapter was neither closed nor routed.
    assert read_pending(backend) == door
    result = backend.read(PIPELINE_PATH)
    if result.file_data is not None:
        assert "requirements" not in json.loads(result.file_data["content"]).get(
            "completed", []
        )


def test_door_ambiguity_asks_never_guesses(tmp_path):
    """A Satisfaction-flavoured word is not the satisfaction token: between
    closing and satisfaction the engine refuses to guess — only exact
    canonical tokens route."""
    backend = _backend(tmp_path)
    ask_door(backend, "requirements")

    with pytest.raises(AskRefusal):
        resume_door(backend, {"canonical": "satisfied", "raw": "satisfied"})
    with pytest.raises(AskRefusal):
        resume_door(backend, {"canonical": "satisfeito", "raw": "satisfeito"})
    assert read_pending(backend)["kind"] == "door"


def test_opening_empty_answer_refuses(tmp_path):
    backend = _backend(tmp_path)
    ask_opening(backend)
    with pytest.raises(AskRefusal):
        resume_opening(backend, {"canonical": "   ", "raw": " "})
    assert read_pending(backend)["kind"] == "opening"


def test_iteration_garbage_token_refuses_and_keeps_the_question(tmp_path):
    backend = _backend(tmp_path)
    engine = _l4_engine(backend)
    engine.run_iteration("c1")

    with pytest.raises(AskRefusal):
        engine.iteration_resume({"canonical": "levitation", "raw": "levitation"})
    assert read_pending(backend)["kind"] == "iteration"
    assert _load(backend, CONFLICTS_PATH)["conflicts"][0]["status"] == "open"

    # The conductor repairs in conversation and resumes canonically.
    result = engine.iteration_resume({"canonical": True, "raw": "sim"})
    assert result["confirmed_activity"] == "requirements"


def test_resume_without_pending_question_refuses(tmp_path):
    backend = _backend(tmp_path)
    with pytest.raises(AskRefusal):
        resume_door(backend, {"canonical": "close", "raw": "close"})


def test_resume_of_a_different_pending_kind_refuses(tmp_path):
    backend = _backend(tmp_path)
    ask_door(backend, "requirements")
    with pytest.raises(AskRefusal) as exc:
        resume_accept(backend, {"canonical": "confirm", "raw": "yes"})
    assert exc.value.payload["pending"]["kind"] == "door"


# --- Probe application stays transactional across the split -------------------


def test_probe_malformed_resume_rolls_back_and_keeps_the_question(tmp_path):
    backend = _backend(tmp_path)
    engine = _l1_engine(backend)
    engine.probe_batch()

    with pytest.raises(ValueError, match="Duplicate resolution"):
        engine.probe_resume(
            {
                "canonical": {
                    "resolutions": [
                        {
                            "conflict_id": "c1",
                            "action": "revise_proposition",
                            "statement": "Half-applied shape.",
                        },
                        {"conflict_id": "c1", "action": "acao_invalida"},
                    ]
                },
                "raw": "…",
            }
        )

    # Rollback to the asked state: nothing half-applied persists.
    conflicts = _load(backend, CONFLICTS_PATH)["conflicts"]
    assert conflicts[0]["status"] == "open"
    assert conflicts[0]["batch_id"] == "b1"
    assert (
        _load(backend, PROPOSITIONS_PATH)["propositions"][0]["statement"]
        == "Payment status is always Authorized or Settled."
    )
    # The Batch stays presented and the question stays pending.
    assert _load(backend, BATCHES_PATH)["batches"][0]["status"] == "open"
    assert read_pending(backend)["kind"] == "probe"

    # The same Batch resumes cleanly once the answer is repaired.
    result = engine.probe_resume(
        {
            "canonical": {"resolutions": [{"conflict_id": "c1", "action": "dismiss"}]},
            "raw": "dispensa",
        }
    )
    assert result["applied"][0]["action"] == "dismiss"
    assert read_pending(backend) is None


def test_lifecycle_apply_failure_keeps_the_question_pending(tmp_path):
    backend = _backend(tmp_path)
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    store = PropositionStore(backend)
    store.propose("Payment status is always Authorized or Settled.", "domain_modeling")
    ask_accept(backend, "p1", via_proposition_id="p9")

    # The apply fails (unknown via-proposition), but the answer is not
    # consumed: the question stays pending (review fix — as the Probe's
    # rollback keeps its Batch).
    result = resume_accept(backend, {"canonical": "confirm", "raw": "yes"})
    assert result["ok"] is False
    assert "error" in result
    assert read_pending(backend)["kind"] == "accept"

    # The conductor repairs in conversation — here, declining clears the
    # question without re-asking the user.
    result = resume_accept(backend, {"canonical": "decline", "raw": "no"})
    assert result["declined"] is True
    assert read_pending(backend) is None


def test_door_close_failure_keeps_the_question_pending(tmp_path):
    backend = _backend(tmp_path)
    backend.write(
        PIPELINE_PATH,
        json.dumps({"completed": [], "active": "domain_modeling"}),
    )
    ask_door(backend, "requirements")

    # Precedence violated: the close fails, the answer is not consumed.
    result = resume_door(backend, {"canonical": "close", "raw": "close"})
    assert result["ok"] is False
    assert "still active" in result["error"]
    assert read_pending(backend)["kind"] == "door"


def test_probe_duplicate_resolution_refuses_and_rolls_back(tmp_path):
    backend = _backend(tmp_path)
    engine = _l1_engine(backend)
    engine.probe_batch()

    with pytest.raises(ValueError, match="Duplicate resolution"):
        engine.probe_resume(
            {
                "canonical": {
                    "resolutions": [
                        {"conflict_id": "c1", "action": "dismiss"},
                        {"conflict_id": "c1", "action": "dismiss"},
                    ]
                },
                "raw": "…",
            }
        )
    # Rollback to the asked state, question intact.
    assert _load(backend, CONFLICTS_PATH)["conflicts"][0]["status"] == "open"
    assert read_pending(backend)["kind"] == "probe"


# --- The door's third answer opens the Satisfaction question ------------------


def test_door_satisfaction_answer_chains_the_satisfaction_question(tmp_path):
    backend = _backend(tmp_path)
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    ask_door(backend, "requirements")

    result = resume_door(backend, {"canonical": "satisfaction", "raw": "satisfaction"})
    assert result["ok"] is True
    assert result["door"] == "satisfaction"
    assert result["chapter_open"] is True
    # The door's question is answered; the Satisfaction question takes over.
    pending = read_pending(backend)
    assert pending["kind"] == "satisfaction"
    assert [e["token"] for e in pending["accepted_answers"]] == [
        "satisfied",
        "not_satisfied",
    ]
    assert result["pending"] == pending

    declined = resume_satisfaction(
        backend, {"canonical": "not_satisfied", "raw": "no, more to work through"}
    )
    assert declined["ok"] is True
    assert declined["satisfied"] is False
    assert backend.read(DELIVERABLE_GLOSSARY_PATH).file_data is None
    assert read_pending(backend) is None


def test_satisfaction_satisfied_materializes_the_deliverable(tmp_path):
    backend = _backend(tmp_path)
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    ask_satisfaction(backend)

    result = resume_satisfaction(backend, {"canonical": "satisfied", "raw": "yes"})
    assert result["ok"] is True
    assert result["satisfied"] is True
    assert backend.read(DELIVERABLE_GLOSSARY_PATH).file_data is not None
    assert read_pending(backend) is None
