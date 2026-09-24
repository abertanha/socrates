"""The adversarial layer — the fifth review's conditions kept strung.

The review found its destructions outside the happy paths: a log the
page limit outgrew, a write that fails, bytes that do not decode, a
directory on a path. The fix pass netted the class; this layer keeps
the net strung — every answer-log read here walks the pagination four
lines at a window, whatever the file holds, so the walk is exercised
by logs that would never cross the real 2000-line boundary.

Seam: engine verbs called directly with an injected adversarial backend
(the transport only builds the backend; the reads live in the verbs).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

NEED = "A checkout flow for a small store."

# Past the fixture's 4-line page: corruption the pagination can bite,
# so these tests fail against a reader that trusts one window.
_CORRUPT = "\n".join(f"corrupt line {i}" for i in range(10))


def _entries(count: int) -> list[dict]:
    moment = datetime.now(timezone.utc)
    return [
        {
            "kind": "opening",
            "subject": None,
            "asked_at": (moment + timedelta(minutes=i)).isoformat(),
            "answered_at": (moment + timedelta(minutes=i, seconds=90)).isoformat(),
            "canonical": NEED,
            "raw": "checkout",
        }
        for i in range(count)
    ]


def test_a_small_log_is_still_whole_when_every_read_pages(
    tmp_path: Path, tiny_log_pages
):
    from socrates.verbs import ask_door, resume_pending

    entries = _entries(10)
    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "answers.json").write_text(json.dumps(entries, indent=2))

    ask_door(tiny_log_pages, "requirements")
    payload = resume_pending(
        tiny_log_pages, {"canonical": "not_yet", "raw": "espera"}
    )
    assert payload.get("refused") is not True, payload
    assert payload.get("answer_recorded") is not False, payload

    log = json.loads((tmp_path / "model" / "answers.json").read_text())
    assert len(log) == 11, "the walk lost its way between windows"
    assert log[:10] == entries, "a window slice replaced the real history"
    assert log[-1]["kind"] == "door"
    assert not (tmp_path / "model" / "answers.json.corrupt").exists(), (
        "a healthy log was preserved aside as corruption"
    )


def test_a_corrupt_log_is_preserved_whole_under_paging(
    tmp_path: Path, tiny_log_pages
):
    from socrates.verbs import ask_door, resume_pending

    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "answers.json").write_text(_CORRUPT)
    ask_door(tiny_log_pages, "requirements")

    payload = resume_pending(
        tiny_log_pages, {"canonical": "not_yet", "raw": "espera"}
    )
    assert payload.get("refused") is not True, payload
    assert payload.get("answer_recorded") is not False, payload

    sidecar = tmp_path / "model" / "answers.json.corrupt"
    assert sidecar.read_text() == _CORRUPT, (
        "a window slice passed for the evidence"
    )
    log = json.loads((tmp_path / "model" / "answers.json").read_text())
    assert log[0]["kind"] == "answer_log_unreadable", (
        "the fresh log forgot its own repair"
    )
    assert log[-1]["kind"] == "door"


def test_the_condition_names_itself_under_paging(tmp_path: Path, tiny_log_pages):
    from socrates.asking import answer_log_unreadable
    from socrates.inference import InferenceEngine
    from socrates.verbs import ask_door, resume_pending

    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "answers.json").write_text("CORRUPT PAYLOAD")
    ask_door(tiny_log_pages, "requirements")
    resume_pending(tiny_log_pages, {"canonical": "not_yet", "raw": "espera"})

    assert answer_log_unreadable(tiny_log_pages) is True, (
        "the marker scan missed what the windows held"
    )
    warning = InferenceEngine(tiny_log_pages).satisfaction_warning()
    assert warning is not None
    assert warning.get("answer_log_unreadable") is True, (
        "the warning lost the condition to the page size"
    )


def test_fast_answers_are_counted_when_reads_page(tmp_path: Path, tiny_log_pages):
    from socrates.inference import InferenceEngine

    moment = datetime.now(timezone.utc)
    fast = _entries(1)[0]
    fast["asked_at"] = moment.isoformat()
    fast["answered_at"] = (moment + timedelta(seconds=1)).isoformat()
    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "answers.json").write_text(json.dumps([fast], indent=2))

    warning = InferenceEngine(tiny_log_pages).satisfaction_warning()
    assert warning is not None, "the fast pair surfaced nowhere"
    signal = warning["self_answered"]
    assert signal["count"] == 1, (
        "the weighing missed what the windows held"
    )
