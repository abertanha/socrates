"""Ticket 01 (socrates-seam) — the ask–answer binding becomes data.

The fifth specimen's compound self-answers (`ask && resume` in one
command, stale raws, one "ok" becoming three accepts) were invisible to
the engine because the binding between a question and its answer carried
no time. Now it does: the pending marker records when the ask was
recorded, every invocation-surface resume logs when the answer was
applied against it, and the Satisfaction warning counts the answers that
arrived faster than a human can read their question — information the
user weighs before ending the session. Data, never enforcement: no gate
reads the timestamps, a fast answer is never refused.

The recording lives on the invocation resume door only — the seam the
specimen's conductor drove. The session surface's interrupts are
structurally human; recording there would add noise, not honesty.

Seam: the invocation files, in-process with argv and a temporary
working directory, asserting on the JSON — the approved seam.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parent.parent
    / ".claude" / "skills" / "socrates" / "SKILL.md"
)
NEED = "A checkout flow for a small store."


def _call(module, tmp_path: Path, data=None):
    argv = ["--root", str(tmp_path)]
    if data is not None:
        argv.append(json.dumps(data))
    return module.main(argv)


def _answers_log(tmp_path: Path) -> list:
    path = tmp_path / "model" / "answers.json"
    assert path.exists(), "the answer log is missing"
    return json.loads(path.read_text())


def _seed_need(tmp_path: Path) -> None:
    """Opening asked and answered back-to-back — fast by construction."""
    from socrates.invocations import opening, resume

    _call(opening, tmp_path)
    _call(resume, tmp_path, {"canonical": NEED, "raw": "checkout"})


# --- The timestamps exist and are honest ----------------------------------------


def test_the_ask_stamps_when_it_was_recorded(tmp_path):
    from socrates.invocations import opening

    _call(opening, tmp_path)
    pending = json.loads(
        (tmp_path / "model" / "pending_question.json").read_text()
    )
    asked = datetime.fromisoformat(pending["asked_at"])
    assert asked.tzinfo is not None, "the ask time is not a plain fact"


def test_the_resume_logs_when_the_answer_arrived(tmp_path):
    from socrates.invocations import resume

    _seed_need(tmp_path)
    log = _answers_log(tmp_path)
    assert len(log) == 1
    entry = log[0]
    assert entry["kind"] == "opening"
    asked = datetime.fromisoformat(entry["asked_at"])
    answered = datetime.fromisoformat(entry["answered_at"])
    assert answered >= asked, "the answer predates its question"
    assert entry["raw"] == "checkout", "the provenance did not ride"


def test_a_failed_apply_never_logs_an_answer(tmp_path):
    """A refused token answers nothing — the question stands, no event."""
    from socrates.invocations import accept, propose, resume

    _seed_need(tmp_path)
    _call(propose, tmp_path, {
        "statement": "A Payment is the transfer of value that settles "
        "an Order.",
        "activity": "requirements",
    })
    _call(accept, tmp_path, {"proposition_id": "p1"})
    payload = _call(resume, tmp_path, {"canonical": "bogus", "raw": "x"})
    # At this seam an AskRefusal is a returned payload, not a raise.
    assert payload.get("refused") is True, payload
    kinds = [entry["kind"] for entry in _answers_log(tmp_path)]
    assert kinds == ["opening"], "a refusal logged an answer"


# --- The warning counts and names the fast answers -------------------------------


def test_back_to_back_answers_are_counted_and_named(tmp_path):
    from socrates.invocations import accept, propose, resume, satisfaction

    _seed_need(tmp_path)
    _call(propose, tmp_path, {
        "statement": "A Payment is the transfer of value that settles "
        "an Order.",
        "activity": "requirements",
    })
    _call(accept, tmp_path, {"proposition_id": "p1"})
    _call(resume, tmp_path, {"canonical": "confirm", "raw": "sim"})

    payload = _call(satisfaction, tmp_path)
    warning = payload["deferred_warning"]
    assert warning is not None, "the fast answers carried no warning"
    signal = warning["self_answered"]
    kinds = {entry["kind"] for entry in signal["answers"]}
    assert "opening" in kinds and "accept" in kinds, kinds
    accept_entry = next(
        e for e in signal["answers"] if e["kind"] == "accept"
    )
    assert accept_entry["subject"] == "p1"
    assert accept_entry["raw"] == "sim"
    assert signal["count"] == len(signal["answers"])
    assert signal["count"] >= 2


def test_an_honest_gap_is_never_counted(tmp_path):
    """A slow pair (state crafted through the documented format — no
    clock seam) is absent from the signal: the key, not a zero count."""
    from socrates.invocations import resume, satisfaction

    _seed_need(tmp_path)
    now = datetime.now(timezone.utc)
    (tmp_path / "model" / "answers.json").write_text(json.dumps([
        {
            "kind": "opening",
            "subject": None,
            "asked_at": now.isoformat(),
            "answered_at": (now + timedelta(seconds=90)).isoformat(),
            "canonical": NEED,
            "raw": "checkout",
        },
    ]))
    payload = _call(satisfaction, tmp_path)
    warning = payload["deferred_warning"]
    assert warning is not None, "mid-walk the warning still informs"
    assert "self_answered" not in warning, (
        "a human-paced answer surfaced as self-answered"
    )


def test_an_untimestamped_entry_is_skipped_not_counted(tmp_path):
    from socrates.invocations import resume, satisfaction

    _seed_need(tmp_path)
    log = _answers_log(tmp_path)
    log[0]["asked_at"] = None
    (tmp_path / "model" / "answers.json").write_text(json.dumps(log))
    payload = _call(satisfaction, tmp_path)
    warning = payload["deferred_warning"]
    assert warning is not None
    assert "self_answered" not in warning


def test_every_log_entry_names_its_subject(tmp_path):
    """The warning says WHAT was self-answered, not just that something
    was: the probe payload carries its Batch as the subject (the kind the
    fifth specimen abused), and the Opening names the Need."""
    from deepagents.backends.filesystem import FilesystemBackend

    from socrates.inference import InferenceEngine
    from socrates.invocations import probe, resume
    from socrates.proposition import PropositionStore

    _seed_need(tmp_path)
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    store = PropositionStore(backend)
    store.propose("Payment status is always Authorized.", "domain_modeling")
    engine = InferenceEngine(backend)
    engine.record_scenarios("p1", [
        {"description": "edge one", "edge": "one", "need_relevant": True},
        {"description": "edge many", "edge": "many", "need_relevant": True},
    ])
    engine.run_assertion_tests("p1", [
        {"scenario_id": "s1", "survives": True},
        {"scenario_id": "s2", "survives": False,
         "kind": "contrariety", "summary": "Many breaks one."},
    ])

    _call(probe, tmp_path)
    _call(resume, tmp_path, {
        "canonical": {"resolutions": [
            {"conflict_id": "c1", "action": "dismiss"}
        ]},
        "raw": "dispensa",
    })

    log = _answers_log(tmp_path)
    subjects = [(entry["kind"], entry["subject"]) for entry in log]
    assert subjects == [("opening", "need"), ("probe", "b1")], (
        "an entry lost its subject"
    )


def test_a_declined_answer_is_logged_like_any_answer(tmp_path):
    """A decline is an applied answer (the review's blind spot): the
    compound `accept && resume "decline"` pattern must leave the same
    trace an acceptance does — the binding log is about the ask–answer
    pair, not about the answer's polarity."""
    from socrates.invocations import accept, propose, resume

    _seed_need(tmp_path)
    _call(propose, tmp_path, {
        "statement": "A Payment is the transfer of value.",
        "activity": "requirements",
    })
    _call(accept, tmp_path, {"proposition_id": "p1"})
    _call(resume, tmp_path, {"canonical": "decline", "raw": "não"})

    log = _answers_log(tmp_path)
    assert [entry["canonical"] for entry in log] == [NEED, "decline"], (
        "the decline vanished from the record"
    )
    assert log[-1]["raw"] == "não"


def test_a_clock_skewed_pair_is_never_counted(tmp_path):
    """A negative delta (the answer stamped before the ask — clock skew
    across a resumed session) is unjudgeable, not evidence: the signal
    skips it rather than naming a human a self-answerer."""
    from socrates.invocations import satisfaction

    _seed_need(tmp_path)
    now = datetime.now(timezone.utc)
    (tmp_path / "model" / "answers.json").write_text(json.dumps([
        {
            "kind": "opening",
            "subject": None,
            "asked_at": (now + timedelta(seconds=30)).isoformat(),
            "answered_at": now.isoformat(),
            "canonical": NEED,
            "raw": "checkout",
        },
    ]))
    payload = _call(satisfaction, tmp_path)
    warning = payload["deferred_warning"]
    assert warning is not None, "mid-walk the warning still informs"
    assert "self_answered" not in warning, (
        "clock skew surfaced as a self-answer"
    )


def test_a_malformed_log_entry_is_skipped_not_fatal(tmp_path):
    """A valid-JSON log holding a non-dict element (a hand edit gone
    wrong) never kills the Satisfaction ask: the unjudgeable element is
    skipped, never guessed from."""
    from socrates.invocations import satisfaction

    _seed_need(tmp_path)
    log = _answers_log(tmp_path)
    log.append("not an entry")
    (tmp_path / "model" / "answers.json").write_text(json.dumps(log))
    payload = _call(satisfaction, tmp_path)
    assert payload.get("refused") is not True, payload
    warning = payload["deferred_warning"]
    assert warning is not None


def test_a_fast_answer_is_never_refused(tmp_path):
    """Data, not enforcement: the compound signature records; it does
    not gate."""
    from socrates.invocations import accept, propose, resume

    _seed_need(tmp_path)
    _call(propose, tmp_path, {
        "statement": "A Payment is the transfer of value that settles "
        "an Order.",
        "activity": "requirements",
    })
    _call(accept, tmp_path, {"proposition_id": "p1"})
    payload = _call(resume, tmp_path, {"canonical": "confirm", "raw": "sim"})
    # Answered instantly after the ask — the fact is recorded; the
    # answer still applies.
    assert payload.get("ok") is not False, payload


# --- The resume result carries the moment ----------------------------------------


def test_the_resume_echo_carries_when_it_was_applied(tmp_path):
    from socrates.invocations import accept, propose, resume

    _seed_need(tmp_path)
    _call(propose, tmp_path, {
        "statement": "A Payment is the transfer of value that settles "
        "an Order.",
        "activity": "requirements",
    })
    _call(accept, tmp_path, {"proposition_id": "p1"})
    r = _call(resume, tmp_path, {"canonical": "confirm", "raw": "sim"})
    assert r["ok"] is True
    assert "answered_at" in r, "the resume did not say when it applied"


# --- The skin pins the conduct the engine cannot hold -----------------------------


def _flat() -> str:
    return " ".join(SKILL.read_text().split())


def test_the_skin_pins_the_wait_rule():
    flat = _flat()
    assert "never answer an ask in the same command that asked it" in flat, (
        "the compound-answer prohibition is unpinned"
    )
    assert "render the question, end your turn, and wait" in flat, (
        "the wait discipline is unstated"
    )


def test_the_skin_keeps_the_warning_relay_duty():
    """The warning is rendered as information — the existing duty already
    covers the new signal; pinned here so it survives skin edits."""
    flat = _flat()
    assert "everything it names, nothing it does not" in flat, (
        "the warning relay duty drifted"
    )
