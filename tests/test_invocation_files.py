"""The invocation files and their JSON contract — ticket 29 (socrates-hybrid).

Seam: the invocation files' entry functions, called in-process with argv
and a temporary working directory, asserting on the JSON they return —
never on engine internals (the approved seam). One thin file per engine
mutation plus the read verbs; JSON in (argument or stdin), JSON out,
errors as structured JSON, never a stack trace. Order violations refuse
with the reason and the admissible next verbs. The tracer bullet runs a
full pass — Need, propositions accepted, reconciliation, scenarios,
assertion tests, a probe that returns its pending question and resumes
with a canonical answer, a door closed — driven end to end by calling
nothing but the files.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from deepagents.backends.filesystem import FilesystemBackend

from socrates.invocations import INVOCATIONS
from socrates.proposition import PropositionStore
from socrates.inference import InferenceEngine

NEED = "Marketplace checkout payments domain."
ROOT_FLAGS = "--root"


def _root(tmp_path: Path) -> list[str]:
    return [ROOT_FLAGS, str(tmp_path)]


def _call(module, tmp_path: Path, data: dict | None = None):
    argv = _root(tmp_path) + ([json.dumps(data)] if data is not None else [])
    return module.main(argv)


# --- One thin file per verb ---------------------------------------------------


def test_declared_verbs_match_the_files_on_disk():
    import socrates.invocations as pkg

    directory = Path(pkg.__file__).parent
    on_disk = {p.stem for p in directory.glob("*.py")} - {"__init__"}
    assert set(INVOCATIONS) == on_disk


EXPECTED_MUTATIONS = {
    "opening",
    "amend_need",
    "propose",
    "accept",
    "reject",
    "reconcile",
    "scenarios",
    "assertion_tests",
    "probe",
    "iteration",
    "defer",
    "door",
    "satisfaction",
    "resume",
    "materialize",
}
EXPECTED_READS = {"pipeline_status", "current_pass", "pending_question",
                  "audit_charge"}


def test_the_verb_surface_is_the_engine_plus_the_reads():
    assert set(INVOCATIONS) == EXPECTED_MUTATIONS | EXPECTED_READS


def test_every_file_is_thin_no_transport_of_its_own():
    """Parse, one engine call, serialize — the transport lives in
    invocation.py alone: no invocation file prints, parses JSON, or
    touches argv/stdin itself."""
    import socrates.invocations as pkg

    directory = Path(pkg.__file__).parent
    for path in sorted(directory.glob("*.py")):
        if path.stem == "__init__":
            continue
        source = path.read_text()
        for forbidden in ("import json", "import sys", "print(", "sys.argv", "os."):
            assert forbidden not in source, f"{path.stem}: {forbidden!r}"


# --- The JSON contract ---------------------------------------------------------


def test_opening_ask_returns_the_question_and_writes_the_need_on_resume(tmp_path):
    from socrates.invocations import opening, pending_question, resume

    payload = _call(opening, tmp_path)
    assert payload["kind"] == "opening"
    assert payload["question"]
    assert payload["resume_contract"]

    shown = _call(pending_question, tmp_path)
    assert shown["ok"] is True
    assert shown["pending"] == payload

    answered = _call(resume, tmp_path, {"canonical": NEED, "raw": "mercado"})
    assert answered["ok"] is True
    # State is on the session directory's disk — a closed terminal never
    # ends the session (user story 10).
    assert (tmp_path / "model" / "need.md").read_text() == NEED
    assert _call(pending_question, tmp_path)["pending"] is None


def test_input_also_arrives_on_stdin(tmp_path, monkeypatch):
    from socrates.invocations import opening, resume

    assert _call(opening, tmp_path)["kind"] == "opening"
    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"canonical": NEED, "raw": ""}))
    )
    answered = resume.main(_root(tmp_path))
    assert answered["ok"] is True
    assert (tmp_path / "model" / "need.md").read_text() == NEED


def test_errors_are_structured_json_never_stack_traces(tmp_path):
    from socrates.invocations import accept, scenarios

    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write("/model/need.md", NEED)

    # Unknown Proposition: refused before asking, as data.
    refused = _call(accept, tmp_path, {"proposition_id": "pX"})
    assert refused["ok"] is False
    assert "error" in refused

    # Mis-shaped input: a structured error, not a KeyError traceback.
    bad = _call(scenarios, tmp_path, {"proposition_id": "p1"})
    assert bad["ok"] is False
    assert "error" in bad

    # Non-JSON input: structured, not a JSONDecodeError traceback.
    broken = scenarios.main(_root(tmp_path) + ["{not json"])
    assert broken["ok"] is False
    assert "error" in broken


def test_wrong_order_is_refused_with_reason_and_admissible_next(tmp_path):
    from socrates.invocations import reconcile, scenarios

    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write("/model/need.md", NEED)
    store = PropositionStore(backend)
    store.propose("Payment status is always Authorized or Settled.", "domain_modeling")

    # Pass 1: Reconciliation does not apply yet — the pass-1 pulse is.
    early = _call(reconcile, tmp_path, {"findings": []})
    assert early["ok"] is False
    assert early["refused"] is True
    assert early["reason"]
    assert early["admissible_next"] == ["scenarios", "assertion_tests", "door"]

    # Pass 2 without Reconciliation: Scenarios refuse naming the gate.
    backend.write(
        "/model/batches.json",
        json.dumps(
            {"batches": [{"id": "b1", "conflict_ids": [], "status": "probed"}]}
        ),
    )
    blocked = _call(
        scenarios,
        tmp_path,
        {
            "proposition_id": "p1",
            "scenarios": [
                {"description": "edge one", "edge": "one", "need_relevant": True},
                {"description": "edge many", "edge": "many", "need_relevant": True},
            ],
        },
    )
    assert blocked["ok"] is False
    assert blocked["refused"] is True
    assert blocked["admissible_next"] == ["reconcile"]

    # The gate satisfied: the same call now proceeds.
    stamped = _call(reconcile, tmp_path, {"findings": []})
    assert stamped["ok"] is True
    recorded = _call(
        scenarios,
        tmp_path,
        {
            "proposition_id": "p1",
            "scenarios": [
                {"description": "edge one", "edge": "one", "need_relevant": True},
                {"description": "edge many", "edge": "many", "need_relevant": True},
            ],
        },
    )
    assert recorded["ok"] is True


def test_the_reads_report_pipeline_pass_and_pending(tmp_path):
    from socrates.invocations import (
        current_pass,
        door,
        pending_question,
        pipeline_status,
        resume,
    )

    assert _call(pipeline_status, tmp_path)["pipeline"] == {
        "completed": [],
        "active": None,
    }
    assert _call(current_pass, tmp_path)["pass"] == 1

    _call(door, tmp_path, {"activity": "requirements"})
    pending = _call(pending_question, tmp_path)["pending"]
    assert pending["kind"] == "door"

    _call(resume, tmp_path, {"canonical": "close"})
    assert _call(pipeline_status, tmp_path)["pipeline"] == {
        "completed": ["requirements"],
        "active": None,
    }


def test_probe_pending_question_resumes_through_the_files(tmp_path):
    from socrates.invocations import probe, resume

    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write("/model/need.md", NEED)
    store = PropositionStore(backend)
    store.propose("Payment status is always Authorized or Settled.", "domain_modeling")
    engine = InferenceEngine(backend)
    engine.record_scenarios(
        "p1",
        [
            {"description": "edge one", "edge": "one", "need_relevant": True},
            {"description": "edge many", "edge": "many", "need_relevant": True},
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
                "summary": "Many breaks one.",
            },
        ],
    )

    asked = _call(probe, tmp_path)
    assert asked["kind"] == "probe"
    assert asked["batch_id"] == "b1"

    applied = _call(
        resume,
        tmp_path,
        {
            "canonical": {
                "resolutions": [{"conflict_id": "c1", "action": "dismiss"}]
            },
            "raw": "dispensa",
        },
    )
    assert applied["ok"] is True
    assert applied["answer"]["raw"] == "dispensa"


def test_one_pending_question_gates_the_other_asking_verbs(tmp_path):
    from socrates.invocations import accept, door, propose, reject

    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write("/model/need.md", NEED)
    PropositionStore(backend).propose(
        "Payment status is always Authorized or Settled.", "domain_modeling"
    )

    asked = _call(accept, tmp_path, {"proposition_id": "p1"})
    assert asked["kind"] == "accept"

    # A second asking verb refuses — as structured JSON, never a traceback.
    second = _call(door, tmp_path, {"activity": "requirements"})
    assert second["ok"] is False
    assert second["refused"] is True
    assert second["pending"]["kind"] == "accept"

    same_kind_other_subject = _call(accept, tmp_path, {"proposition_id": "pX"})
    assert same_kind_other_subject["ok"] is False
    assert same_kind_other_subject["refused"] is True


# --- The tracer bullet ---------------------------------------------------------


def test_tracer_need_to_door_through_the_files_alone(tmp_path):
    from socrates.invocations import (
        accept,
        assertion_tests,
        current_pass,
        door,
        opening,
        pending_question,
        pipeline_status,
        probe,
        propose,
        reconcile,
        resume,
        scenarios,
    )

    def call(module, data=None):
        return _call(module, tmp_path, data)

    # Opening: the question returns as data; the resume writes the Need.
    assert call(opening)["kind"] == "opening"
    assert call(resume, {"canonical": NEED, "raw": "checkout"})["ok"] is True

    # Pass 1: reconcile refuses — the pass-1 pulse is Scenarios first.
    call(propose, {"statement": "A Payment belongs to exactly one Order.",
                   "activity": "requirements"})
    refused = call(reconcile, {"findings": []})
    assert refused["refused"] is True

    call(accept, {"proposition_id": "p1"})
    call(resume, {"canonical": "confirm", "raw": "sim"})

    call(scenarios, {
        "proposition_id": "p1",
        "scenarios": [
            {"description": "edge one", "edge": "one", "need_relevant": True},
            {"description": "edge many", "edge": "many", "need_relevant": True},
        ],
    })
    surfaced = call(assertion_tests, {
        "proposition_id": "p1",
        "outcomes": [
            {"scenario_id": "s1", "survives": True},
            {"scenario_id": "s2", "survives": False,
             "kind": "contrariety", "summary": "Many breaks one."},
        ],
    })
    assert surfaced["conflicts"][0]["level"] == "L1"

    # The Probe returns its pending question; the resume applies it.
    asked = call(probe)
    assert asked["kind"] == "probe"
    assert asked["batch_id"] == "b1"
    applied = call(resume, {
        "canonical": {"resolutions": [
            {"conflict_id": "c1", "action": "dismiss"}]},
        "raw": "dispensa",
    })
    assert applied["ok"] is True
    assert call(current_pass)["pass"] == 2

    # Pass 2: Reconciliation runs before anything else (empty is valid).
    assert call(reconcile, {"findings": []})["ok"] is True

    # The chapter door: asked as data, resumed with the canonical token.
    assert call(door, {"activity": "requirements"})["kind"] == "door"
    closed = call(resume, {"canonical": "close", "raw": "fecha"})
    assert closed["ok"] is True
    assert closed["door"] == "close"

    # The pass is done: nothing pending, pipeline moved, all state on disk.
    assert call(pending_question)["pending"] is None
    assert call(pipeline_status)["pipeline"]["completed"] == ["requirements"]
