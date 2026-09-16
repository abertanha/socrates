"""Ticket 02 (socrates-seam) — lapidation leaves a record.

The fifth specimen ran 36 Assertion Tests and every outcome shipped
``survives: true`` — and the engine discarded survivals by design, so
the rubber stamp left no trace. Now the record exists: every outcome is
persisted, each citing its scenario, and lapidation requires it — the
ticket-17 ruling amended on specimen evidence that the record, not the
run, is what the engine can trust. One definition everywhere: the
treadmill gate, the door's quiet rule — including on the invocation
surface, where the door close had NO quiet gate at all (the middleware
held it only for the session surface) — and the propose-ordering gate.

The Scenario minimum stays two, a floor never a ceiling.

Seam: the invocation files, in-process with argv and a temporary
working directory, asserting on the JSON — the approved seam.
"""

from __future__ import annotations

import json
from pathlib import Path

STATEMENT = (
    "A Payment is the transfer of value that settles an Order."
)


def _call(module, tmp_path: Path, data=None):
    argv = ["--root", str(tmp_path)]
    if data is not None:
        argv.append(json.dumps(data))
    return module.main(argv)


def _seed_scenarios(tmp_path: Path, statement: str = STATEMENT) -> list[str]:
    """A proposed Proposition with its two recorded Scenarios — the ids
    returned, so outcomes can cite them."""
    from socrates.invocations import opening, propose, resume, scenarios

    _call(opening, tmp_path)
    _call(resume, tmp_path, {"canonical": "A checkout flow.", "raw": "x"})
    _call(propose, tmp_path, {"statement": statement, "activity": "requirements"})
    _call(scenarios, tmp_path, {
        "proposition_id": "p1",
        "scenarios": [
            {"description": "edge one", "edge": "one", "need_relevant": True},
            {"description": "edge many", "edge": "many", "need_relevant": True},
        ],
    })
    state = json.loads((tmp_path / "model" / "scenarios.json").read_text())
    return [s["id"] for s in state["scenarios"]]


def _assertions(tmp_path: Path) -> list:
    path = tmp_path / "model" / "assertions.json"
    assert path.exists(), "the assertion record is missing"
    return json.loads(path.read_text())["assertions"]


# --- The record exists ------------------------------------------------------------


def test_surviving_outcomes_leave_a_record(tmp_path):
    from socrates.invocations import assertion_tests

    scenario_ids = _seed_scenarios(tmp_path)
    payload = _call(assertion_tests, tmp_path, {
        "proposition_id": "p1",
        "outcomes": [
            {"scenario_id": sid, "survives": True} for sid in scenario_ids
        ],
    })
    assert payload["ok"] is True, payload
    record = _assertions(tmp_path)
    assert len(record) == 2, "a survival was discarded again"
    assert {entry["scenario_id"] for entry in record} == set(scenario_ids)
    assert all(entry["survives"] is True for entry in record)
    assert all(entry["proposition_id"] == "p1" for entry in record)


def test_breaking_outcomes_surface_conflicts_and_are_recorded(tmp_path):
    from socrates.invocations import assertion_tests

    scenario_ids = _seed_scenarios(tmp_path)
    payload = _call(assertion_tests, tmp_path, {
        "proposition_id": "p1",
        "outcomes": [
            {"scenario_id": scenario_ids[0], "survives": True},
            {
                "scenario_id": scenario_ids[1],
                "survives": False,
                "kind": "contrariety",
                "summary": "at many, the settlement double-counts",
            },
        ],
    })
    assert payload["ok"] is True, payload
    assert len(payload["conflicts"]) == 1, "the break stopped surfacing"
    record = _assertions(tmp_path)
    assert len(record) == 2, "the break was recorded but the survival lost"
    by_scenario = {entry["scenario_id"]: entry for entry in record}
    assert by_scenario[scenario_ids[1]]["survives"] is False


def test_a_malformed_outcome_records_nothing(tmp_path):
    """The step stays transactional: an invalid outcome leaves no partial
    record behind."""
    from socrates.invocations import assertion_tests

    scenario_ids = _seed_scenarios(tmp_path)
    payload = _call(assertion_tests, tmp_path, {
        "proposition_id": "p1",
        "outcomes": [
            {"scenario_id": scenario_ids[0], "survives": True},
            {"scenario_id": scenario_ids[1], "survives": "perhaps"},
        ],
    })
    assert payload.get("ok") is False or payload.get("refused"), payload
    assert not (tmp_path / "model" / "assertions.json").exists(), (
        "a malformed batch half-recorded"
    )


# --- One definition, every surface -------------------------------------------------


def test_the_treadmill_holds_until_the_record_exists(tmp_path):
    from socrates.invocations import assertion_tests, propose

    _seed_scenarios(tmp_path)
    payload = _call(propose, tmp_path, {
        "statement": "An Order is a customer's request to buy.",
        "activity": "requirements",
    })
    assert payload.get("refused") is True, payload
    assert "p1" in payload["reason"], "the treadmill lost the Proposition"
    scenario_ids = [
        s["id"]
        for s in json.loads(
            (tmp_path / "model" / "scenarios.json").read_text()
        )["scenarios"]
    ]
    _call(assertion_tests, tmp_path, {
        "proposition_id": "p1",
        "outcomes": [
            {"scenario_id": sid, "survives": True} for sid in scenario_ids
        ],
    })
    payload = _call(propose, tmp_path, {
        "statement": "An Order is a customer's request to buy.",
        "activity": "requirements",
    })
    assert payload.get("refused") is not True, payload


def test_the_door_refuses_to_close_without_the_record(tmp_path):
    from socrates.invocations import door, pending_question, resume

    _seed_scenarios(tmp_path)
    _call(door, tmp_path, {"activity": "requirements"})
    payload = _call(resume, tmp_path, {"canonical": "close", "raw": "fecha"})
    assert payload.get("refused") is True, payload
    assert "p1" in payload["reason"]
    assert payload["admissible_next"] == ["scenarios", "assertion_tests"]
    standing = _call(pending_question, tmp_path)
    assert standing["pending"]["kind"] == "door", (
        "the close consumed the answer without closing"
    )


def test_the_door_proceeds_once_the_record_exists(tmp_path):
    from socrates.invocations import assertion_tests, door, resume

    scenario_ids = _seed_scenarios(tmp_path)
    _call(door, tmp_path, {"activity": "requirements"})
    _call(resume, tmp_path, {"canonical": "close", "raw": "fecha"})
    _call(assertion_tests, tmp_path, {
        "proposition_id": "p1",
        "outcomes": [
            {"scenario_id": sid, "survives": True} for sid in scenario_ids
        ],
    })
    payload = _call(resume, tmp_path, {"canonical": "close", "raw": "fecha"})
    assert payload.get("ok") is True, payload
    assert payload.get("door") == "close", payload


def test_the_scenario_minimum_stays_two(tmp_path):
    from socrates.invocations import assertion_tests, scenarios

    _seed_scenarios(tmp_path)
    _call(scenarios, tmp_path, {
        "proposition_id": "p1",
        "scenarios": [
            {"description": "third edge", "edge": "zero",
             "need_relevant": True},
        ],
    })
    payload = _call(assertion_tests, tmp_path, {
        "proposition_id": "p1",
        "outcomes": [{"scenario_id": "s3", "survives": True}],
    })
    assert payload.get("ok") is False or payload.get("refused"), (
        "the two-Scenario floor did not hold"
    )


# --- The skin pins the conduct the engine cannot hold ------------------------------


def _flat() -> str:
    skill = (
        Path(__file__).resolve().parent.parent
        / ".claude" / "skills" / "socrates" / "SKILL.md"
    )
    return " ".join(skill.read_text().split())


def test_the_skin_pins_scenarios_before_tests_with_the_user():
    flat = _flat()
    assert "play the Scenarios out with the user" in flat, (
        "the conversational stretch is unpinned"
    )
    assert "before recording the Assertion Tests" in flat, (
        "the ordering of the stretch is unstated"
    )


def test_the_skin_pins_the_floor_never_a_ceiling():
    flat = _flat()
    assert "a floor, never a ceiling" in flat, (
        "the recorded minimum became a verdict"
    )
    assert "never invoke the recorded count against" in flat, (
        "the conductor may refuse demanded stretch"
    )
