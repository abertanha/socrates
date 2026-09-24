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


# --- A corrupt log never lies quietly ---------------------------------------------


def _corrupt(tmp_path: Path, payload: str = "{ this is not json") -> None:
    (tmp_path / "model" / "answers.json").write_text(payload)


def test_an_unreadable_log_names_itself_in_the_warning(tmp_path):
    """The unreadable and the empty must never look alike: a log that
    exists but does not parse is a condition the warning reports —
    present only when it holds, never zero-filled prose. And the reader
    reports, never repairs: the corrupt bytes stand untouched."""
    from socrates.invocations import satisfaction

    _seed_need(tmp_path)
    payload = _call(satisfaction, tmp_path)
    assert "answer_log_unreadable" not in payload["deferred_warning"], (
        "a clean session carried the signal"
    )
    _corrupt(tmp_path)
    payload = _call(satisfaction, tmp_path)
    assert payload["deferred_warning"].get("answer_log_unreadable") is True, (
        "an unreadable log read as an empty one"
    )
    assert (tmp_path / "model" / "answers.json").read_text() == (
        "{ this is not json"
    ), "the reader repaired what it should only have reported"


def test_a_zero_byte_log_is_the_signature_of_a_lost_write(tmp_path):
    """The backend truncates before it writes (O_TRUNC, no temp file):
    a zero-byte log is what a dead write leaves behind — unreadable,
    not empty."""
    from socrates.invocations import satisfaction

    _seed_need(tmp_path)
    (tmp_path / "model" / "answers.json").write_text("")
    payload = _call(satisfaction, tmp_path)
    assert payload["deferred_warning"].get("answer_log_unreadable") is True


def test_the_next_answer_preserves_the_corrupt_bytes(tmp_path):
    """The writer preserves before it rewrites: the corrupt log moves
    aside whole, and the fresh log opens with a marker that says so —
    a session that lost a stretch of its record never gets to forget it."""
    from socrates.invocations import accept, propose, resume, satisfaction

    _seed_need(tmp_path)
    _corrupt(tmp_path, "CORRUPT PAYLOAD")
    _call(propose, tmp_path, {
        "statement": "A Payment is the transfer of value.",
        "activity": "requirements",
    })
    _call(accept, tmp_path, {"proposition_id": "p1"})
    payload = _call(resume, tmp_path, {"canonical": "confirm", "raw": "sim"})
    assert payload.get("ok") is not False, payload

    sidecar = tmp_path / "model" / "answers.json.corrupt"
    assert sidecar.read_text() == "CORRUPT PAYLOAD", (
        "the evidence was overwritten"
    )
    log = _answers_log(tmp_path)
    assert log[0]["kind"] == "answer_log_unreadable", (
        "the fresh log forgot its own repair"
    )
    assert log[-1]["kind"] == "accept"
    # The marker outlives the repair: the warning still names it.
    payload = _call(satisfaction, tmp_path)
    assert payload["deferred_warning"].get("answer_log_unreadable") is True


def test_a_second_corruption_numbers_its_sidecar(tmp_path):
    """One sidecar per corruption event: a second unreadable stretch
    never overwrites the first."""
    from socrates.invocations import door, resume

    _seed_need(tmp_path)
    _call(door, tmp_path, {"activity": "requirements"})
    _corrupt(tmp_path, "FIRST")
    _call(resume, tmp_path, {"canonical": "not_yet", "raw": "espera"})
    _corrupt(tmp_path, "SECOND")
    _call(door, tmp_path, {"activity": "requirements"})
    _call(resume, tmp_path, {"canonical": "not_yet", "raw": "espera"})
    model = tmp_path / "model"
    assert (model / "answers.json.corrupt").read_text() == "FIRST"
    assert (model / "answers.json.corrupt.1").read_text() == "SECOND"


def test_a_failed_write_is_declared_never_fatal(tmp_path):
    """The answer applied; the binding is data, never enforcement: a
    write that cannot land fails the recording, not the resume — and
    the failure rides the payload, never silence."""
    import os

    from socrates.invocations import accept, propose, resume

    _seed_need(tmp_path)
    _call(propose, tmp_path, {
        "statement": "A Payment is the transfer of value.",
        "activity": "requirements",
    })
    _call(accept, tmp_path, {"proposition_id": "p1"})
    # The backend's O_TRUNC open fails deterministically on a directory.
    os.remove(tmp_path / "model" / "answers.json")
    (tmp_path / "model" / "answers.json").mkdir()
    payload = _call(resume, tmp_path, {"canonical": "confirm", "raw": "sim"})
    assert payload.get("ok") is not False, "the recording failed the resume"
    assert payload.get("answer_recorded") is False, payload
    assert payload.get("answer_record_error"), "the failure rode in silence"


def test_the_writer_appends_to_what_the_file_holds(tmp_path):
    """Lossless rewrite: a malformed element inside a parseable list
    stays in the file — the skip happens where entries are weighed (the
    warning's reader), never where they are written."""
    from socrates.invocations import accept, propose, resume

    _seed_need(tmp_path)
    log = _answers_log(tmp_path)
    log.append("not an entry")
    (tmp_path / "model" / "answers.json").write_text(json.dumps(log))
    _call(propose, tmp_path, {
        "statement": "A Payment is the transfer of value.",
        "activity": "requirements",
    })
    _call(accept, tmp_path, {"proposition_id": "p1"})
    _call(resume, tmp_path, {"canonical": "confirm", "raw": "sim"})
    assert "not an entry" in _answers_log(tmp_path), (
        "the writer filtered what it rewrote"
    )
    assert _answers_log(tmp_path)[-1]["kind"] == "accept"


# --- The reads see the whole file, the writes never destroy ----------------------


def _entries(count: int) -> list[dict]:
    """Valid log entries in the documented shape, a minute apart."""
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


def test_a_healthy_log_beyond_the_page_limit_survives_intact(tmp_path):
    """The backend paginates reads — 2000 lines by default, the window
    carrying no mark of its own truncation — so a reader that trusts one
    read sees a broken half-log and the writer, reading corruption,
    preserved the truncation and threw the tail away. The reader walks
    the pagination instead: a log the page limit outgrew appends whole
    (the review's empirically reproduced destruction)."""
    from socrates.invocations import door, resume

    _seed_need(tmp_path)
    surviving = _entries(400)
    (tmp_path / "model" / "answers.json").write_text(
        json.dumps(surviving, indent=2)
    )
    content = (tmp_path / "model" / "answers.json").read_text()
    assert content.count("\n") > 2000, "the crafted log never crossed the page"

    _call(door, tmp_path, {"activity": "requirements"})
    payload = _call(resume, tmp_path, {"canonical": "not_yet", "raw": "espera"})
    assert payload.get("ok") is not False, payload

    log = _answers_log(tmp_path)
    assert len(log) == 401, "the log lost its tail to the page limit"
    assert log[0] == surviving[0] and log[399] == surviving[399], (
        "a preserved truncation replaced the real history"
    )
    assert log[-1]["kind"] == "door"
    assert not (tmp_path / "model" / "answers.json.corrupt").exists(), (
        "a healthy log was preserved aside as corruption"
    )


def test_a_failing_preserve_never_touches_the_log(tmp_path):
    """Preserve is a precondition, never a ceremony: the sidecar write's
    result is checked, and a preserve that cannot land leaves the log
    exactly as it stands — the answer is declared unrecorded instead of
    an unchecked delete destroying the only copy (the review's second
    reproduced destruction)."""
    from socrates.invocations import door, resume

    _seed_need(tmp_path)
    _call(door, tmp_path, {"activity": "requirements"})
    _corrupt(tmp_path, "CORRUPT PAYLOAD")
    (tmp_path / "model" / "answers.json.corrupt").mkdir()

    payload = _call(resume, tmp_path, {"canonical": "not_yet", "raw": "espera"})
    assert payload.get("refused") is not True, payload
    assert payload.get("answer_recorded") is False, payload
    assert payload.get("answer_record_error"), "the failed preserve rode in silence"
    assert (tmp_path / "model" / "answers.json").read_text() == "CORRUPT PAYLOAD", (
        "the only copy was deleted on an unchecked sidecar write"
    )


def test_a_read_error_is_never_an_empty_log(tmp_path):
    """The not-found and the unreadable are different facts: bytes the
    reader cannot decode (a legacy non-UTF-8 stretch) mean the log
    STANDS — the writer declares and leaves the evidence, it never
    starts a fresh log over it (the review's third reproduced
    destruction: an error read as absence is a silent reset)."""
    from socrates.invocations import door, resume

    _seed_need(tmp_path)
    _call(door, tmp_path, {"activity": "requirements"})
    (tmp_path / "model" / "answers.json").write_bytes(b"\xff\xfe\x00not utf-8")

    payload = _call(resume, tmp_path, {"canonical": "not_yet", "raw": "espera"})
    assert payload.get("refused") is not True, payload
    assert payload.get("answer_recorded") is False, payload
    assert payload.get("answer_record_error"), "the undeclarable read rode in silence"
    assert (tmp_path / "model" / "answers.json").read_bytes() == (
        b"\xff\xfe\x00not utf-8"
    ), "an unreadable log was silently reset to a fresh one"


def test_the_preserve_uses_the_bytes_the_reader_saw(tmp_path):
    """One sight is the whole truth: the preserved evidence is the
    content the reader saw, not a second look at a file the session
    could have changed in between (the review's TOCTOU)."""
    from deepagents.backends.filesystem import FilesystemBackend

    from socrates.asking import record_answered

    class _Tampering(FilesystemBackend):
        """Rewrites the log after its first read, mid-ceremony."""

        def __init__(self, root_dir, log_path, **kwargs):
            super().__init__(root_dir=root_dir, **kwargs)
            self._log_path = log_path
            self._struck = False

        def read(self, file_path, offset=0, limit=2000):
            result = super().read(file_path, offset=offset, limit=limit)
            if file_path == "/model/answers.json" and not self._struck:
                self._struck = True
                self._log_path.write_text("TAMPERED AFTER THE FIRST SIGHT")
            return result

    log_path = tmp_path / "model" / "answers.json"
    (tmp_path / "model").mkdir()
    log_path.write_text("CORRUPT PAYLOAD")
    backend = _Tampering(tmp_path, log_path, virtual_mode=True)

    entry = record_answered(
        backend,
        kind="door",
        subject=None,
        asked_at=None,
        canonical="not_yet",
        raw="espera",
    )
    assert entry.get("recorded") is not False, entry
    sidecar = tmp_path / "model" / "answers.json.corrupt"
    assert sidecar.read_text() == "CORRUPT PAYLOAD", (
        "the evidence was re-read instead of using what the reader saw"
    )
    log = json.loads(log_path.read_text())
    assert log[0]["kind"] == "answer_log_unreadable"
    assert log[-1]["kind"] == "door", "the fresh log never landed"


def test_a_failed_fresh_write_leaves_the_evidence_standing(tmp_path):
    """Nothing destructive runs before the new content is on disk: the
    old delete-before-rewrite turned a failed fresh write into a
    vanished log — the marker and all. The rewrite replaces in place
    (the backend truncates on open), so a failed write leaves the
    previous bytes standing and the loss declared."""
    from deepagents.backends.filesystem import FilesystemBackend
    from deepagents.backends.protocol import WriteResult

    from socrates.asking import record_answered

    class _LosingWrite(FilesystemBackend):
        """The fresh log's write fails once, mid-ceremony."""

        def __init__(self, root_dir, **kwargs):
            super().__init__(root_dir=root_dir, **kwargs)
            self._failed = False

        def write(self, file_path, content):
            if file_path == "/model/answers.json" and not self._failed:
                self._failed = True
                return WriteResult(error="simulated loss of the fresh write")
            return super().write(file_path, content)

    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "answers.json").write_text("CORRUPT PAYLOAD")
    backend = _LosingWrite(tmp_path, virtual_mode=True)

    entry = record_answered(
        backend,
        kind="door",
        subject=None,
        asked_at=None,
        canonical="not_yet",
        raw="espera",
    )
    assert entry.get("recorded") is False, entry
    assert entry.get("record_error"), "the lost write rode in silence"
    assert (tmp_path / "model" / "answers.json").read_text() == "CORRUPT PAYLOAD", (
        "the delete ran before the rewrite was safe"
    )
    assert (tmp_path / "model" / "answers.json.corrupt").read_text() == (
        "CORRUPT PAYLOAD"
    )


def test_satisfaction_reads_the_log_once(tmp_path):
    """One look weighs everything: the fast-answer signal and the
    unreadable condition come from the same read — the warning never
    walks the log twice (a second walk is a second chance to disagree
    with the first)."""
    from deepagents.backends.filesystem import FilesystemBackend

    from socrates.inference import InferenceEngine

    class _Counting(FilesystemBackend):
        """Remembers how often the answer log was read."""

        def __init__(self, root_dir, **kwargs):
            super().__init__(root_dir=root_dir, **kwargs)
            self.log_reads = 0

        def read(self, file_path, offset=0, limit=2000):
            if file_path == "/model/answers.json":
                self.log_reads += 1
            return super().read(file_path, offset=offset, limit=limit)

    _seed_need(tmp_path)
    backend = _Counting(tmp_path, virtual_mode=True)
    warning = InferenceEngine(backend).satisfaction_warning()
    assert warning is not None, "the recorded opening carried no warning"
    assert backend.log_reads == 1, (
        f"the log was walked {backend.log_reads} times for one weighing"
    )


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
