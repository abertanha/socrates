"""The AskHuman protocol — questions as data, answers as ``{canonical, raw}``.

Ticket 28 (socrates-hybrid): the engine's asking points never block and
never guess. An asking verb persists its pending question in the session
state and returns the payload — the question, the accepted canonical
answers with their meanings, and the resume contract. The resume arrives
on a later call carrying the canonical token (which alone drives the
machine) beside the user's raw words (provenance). Exactly one question
is pending at a time (the one-question-per-turn ruling): another asking
verb refuses naming the pending one, and re-asking the same kind
re-presents it unchanged. A non-canonical token is a structured refusal
(:class:`AskRefusal` carries the JSON-ready payload) — never a crash,
never a silent default.

The boundary is pluggable by construction: this module knows only the
backend, never who answers. The session layer's interrupt-backed adapter
and the invocation files are two implementations of the same seam.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import ANSWERS_PATH, PENDING_QUESTION_PATH

# Canonical tokens — closed, English, language-agnostic core. The session
# language lives outside the engine; free replies are classified into
# these tokens by the conductor, with the raw words preserved. One home:
# the token tuples are derived from the accepted-answers menus below, so
# the menu a conductor sees is exactly what the validator admits.
_ENVELOPE = (
    "Resume with {canonical, raw} — the canonical token drives the "
    "machine; the raw words ride as provenance."
)

DOOR_RESUME_CONTRACT = (
    f"{_ENVELOPE} canonical is one of: close, not_yet, satisfaction — "
    "between closing and satisfaction, ask, never guess."
)
CONFIRM_RESUME_CONTRACT = (
    f"{_ENVELOPE} canonical is one of: confirm, decline."
)
SATISFACTION_RESUME_CONTRACT = (
    f"{_ENVELOPE} canonical is one of: satisfied, not_satisfied."
)
FREE_TEXT_RESUME_CONTRACT = f"{_ENVELOPE} canonical is the answer text itself."


def _answers(*pairs: tuple[str, str]) -> list[dict[str, str]]:
    return [{"token": token, "meaning": meaning} for token, meaning in pairs]


def _tokens(accepted_answers: list[dict[str, str]]) -> tuple[str, ...]:
    return tuple(entry["token"] for entry in accepted_answers)


DOOR_ACCEPTED_ANSWERS = _answers(
    ("close", "complete the chapter — its door stays shut"),
    ("not_yet", "keep the chapter open — the maieutic valve stays live"),
    (
        "satisfaction",
        "route to the Satisfaction flow WITHOUT closing the chapter",
    ),
)
CONFIRM_ACCEPTED_ANSWERS = _answers(
    ("confirm", "proceed with the action as asked"),
    ("decline", "refuse it — the state stays exactly as it is"),
)
SATISFACTION_ACCEPTED_ANSWERS = _answers(
    (
        "satisfied",
        "it holds up as it stands — materialize the Conceptual Domain Model",
    ),
    (
        "not_satisfied",
        "there is more to work through — the session continues",
    ),
)
FREE_TEXT_ACCEPTED_ANSWERS = [
    {"token": "free-text", "meaning": "the answer in the user's own words"}
]

DOOR_TOKENS = _tokens(DOOR_ACCEPTED_ANSWERS)
CONFIRM_TOKENS = _tokens(CONFIRM_ACCEPTED_ANSWERS)
SATISFACTION_TOKENS = _tokens(SATISFACTION_ACCEPTED_ANSWERS)


class AskRefusal(Exception):
    """A structured refusal of the asking protocol — JSON-ready.

    Carries the reason, the pending question it names, and (for token
    refusals) the accepted tokens, so the conductor repairs in
    conversation instead of guessing around the refusal.
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload["reason"])
        self.payload = payload


# The fields each pending kind must carry for its resume to be
# answerable — the shape contract of the persisted payload. A marker
# missing them (a truncated write, a hand edit, an older schema) is no
# question anyone can answer: it self-heals like any other corruption
# instead of raising a raw KeyError out of a resume.
_PENDING_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "opening": (),
    "amend_need": ("proposed_need", "reason"),
    "accept": ("proposition_id",),
    "reject": ("proposition_id", "reason"),
    "door": ("activity",),
    "satisfaction": (),
    "probe": ("batch_id",),
    "iteration": ("conflict_id", "proposed_activity"),
}


def read_pending(backend: BackendProtocol) -> dict[str, Any] | None:
    """The persisted pending-question payload, or ``None`` when none stands.

    A corrupt marker is no question anyone can answer: it self-heals to
    none (the file is deleted) rather than deadlocking every later ask
    and resume on a record that cannot be honored. Corruption is
    unparseable JSON, a non-dict, a kindless dict — and a dict whose kind
    is missing its resume's required fields.
    """
    result = backend.read(PENDING_QUESTION_PATH)
    if result.error or result.file_data is None:
        return None
    content = result.file_data["content"]
    if not content.strip():
        return None
    try:
        pending = json.loads(content)
    except json.JSONDecodeError:
        backend.delete(PENDING_QUESTION_PATH)
        return None
    if not isinstance(pending, dict) or "kind" not in pending:
        backend.delete(PENDING_QUESTION_PATH)
        return None
    required = _PENDING_REQUIRED_FIELDS.get(pending["kind"])
    if required is None or any(
        pending.get(field) is None for field in required
    ):
        backend.delete(PENDING_QUESTION_PATH)
        return None
    return pending


def _now() -> str:
    """The moment, as a plain UTC ISO-8601 fact (socrates-seam ticket 01)."""
    return datetime.now(timezone.utc).isoformat()


def begin_pending(backend: BackendProtocol, payload: dict[str, Any]) -> dict[str, Any]:
    """Persist the pending question and return its payload.

    The payload is stamped with ``asked_at`` — the moment the question
    stood — so the answer can later be weighed against it. Re-asking the
    same kind about the same subject re-presents the persisted question
    unchanged (idempotence — a Batch is never created twice for one
    question) with its ORIGINAL stamp: the question has stood since it
    was first asked. The same kind about a DIFFERENT subject, or any
    other kind, refuses naming the pending one.
    """
    existing = read_pending(backend)
    if existing is None:
        payload = {**payload, "asked_at": _now()}
        backend.write(PENDING_QUESTION_PATH, json.dumps(payload, indent=2))
        return payload
    if existing["kind"] == payload["kind"] and existing.get(
        "subject"
    ) == payload.get("subject"):
        return existing
    raise AskRefusal(_one_pending_payload(existing, payload["kind"]))


def refresh_pending(backend: BackendProtocol, payload: dict[str, Any]) -> dict[str, Any]:
    """Overwrite the standing question with a refreshed payload.

    The question itself re-presents unchanged (same kind, same subject,
    same words); only its derived context is brought current — an
    advisory warning recomputed, never a stale picture of the session.
    The stamp comes current too: the user is being asked again now, and
    the answer they give answers this presentation.
    """
    payload = {**payload, "asked_at": _now()}
    backend.write(PENDING_QUESTION_PATH, json.dumps(payload, indent=2))
    return payload


def require_pending(backend: BackendProtocol, kind: str) -> dict[str, Any]:
    """The pending question of ``kind`` — refusing absent or foreign kinds."""
    existing = read_pending(backend)
    if existing is None:
        raise AskRefusal(
            {
                "ok": False,
                "refused": True,
                "reason": f"No pending question to resume (expected {kind!r})",
                "expected_kind": kind,
                "admissible_next": ["pending_question"],
            }
        )
    if existing["kind"] != kind:
        raise AskRefusal(_one_pending_payload(existing, kind))
    return existing


def guard_pending(
    backend: BackendProtocol,
    kind: str,
    subject: str | None = None,
) -> dict[str, Any] | None:
    """The re-presented payload when ``kind`` re-asks its own pending
    question (same ``subject``); ``None`` when no question is pending;
    refusal for any other kind — or the same kind about a different
    subject. Askers call this BEFORE mutating state, so a re-ask never
    duplicates its own work (a Batch is never created twice for one
    question)."""
    existing = read_pending(backend)
    if existing is None:
        return None
    if existing["kind"] == kind and existing.get("subject") == subject:
        return existing
    raise AskRefusal(_one_pending_payload(existing, kind))


def clear_pending(backend: BackendProtocol) -> None:
    backend.delete(PENDING_QUESTION_PATH)


def record_answered(
    backend: BackendProtocol,
    *,
    kind: str,
    subject: Any,
    asked_at: str | None,
    canonical: Any,
    raw: Any,
    answered_at: str | None = None,
) -> dict[str, Any]:
    """Append the answer event to the session's answer log.

    The ask–answer binding as data (socrates-seam ticket 01): when the
    answer was applied, against when its question was asked. Facts only —
    nothing reads the log to refuse or route anything; the Satisfaction
    warning weighs it, and nothing else. A question that was never
    stamped (an older marker) still logs its answer with ``asked_at``
    None: the pairing simply cannot be judged.

    ``canonical``/``raw`` are stored when they are words and left None
    when the answer rode as data (a Probe's resolutions), so the log
    stays a record of decisions, not payloads.
    """
    entry = {
        "kind": kind,
        "subject": subject,
        "asked_at": asked_at,
        "answered_at": answered_at or _now(),
        "canonical": canonical if isinstance(canonical, str) else None,
        "raw": raw if isinstance(raw, str) else None,
    }
    parsed, unreadable = _read_log(backend)
    if unreadable:
        # Preserve before rewriting (answer-log-integrity): the corrupt
        # bytes move aside whole, and the fresh log opens with the
        # marker that keeps the condition visible after the file parses
        # again — a session that lost a stretch of its record never
        # gets to forget it.
        _preserve_corrupt_log(backend)
        log: list[Any] = [_marker_entry(entry["answered_at"])]
    else:
        # Lossless: the writer appends to what the file actually holds
        # and never filters — skipping unjudgeable entries is the
        # reader-of-record's business, never the writer's.
        log = parsed
    log.append(entry)
    write = backend.write(ANSWERS_PATH, json.dumps(log, indent=2))
    if write.error:
        # The answer applied; its binding is not on record — declared on
        # the entry, never silent, never fatal (the log is data, never
        # enforcement).
        entry["recorded"] = False
        entry["record_error"] = write.error
    return entry


def _read_log(backend: BackendProtocol) -> tuple[list[Any] | None, bool]:
    """The raw parsed log and whether it is unreadable — ONE definition
    for every reader and the writer (answer-log-integrity). Unreadable
    means the file exists and does not parse as a JSON list, a zero-byte
    file included (that is the O_TRUNC-without-write signature). Absent
    is clean emptiness — a fresh session, no condition."""
    result = backend.read(ANSWERS_PATH)
    if result.error or result.file_data is None:
        return [], False
    try:
        parsed = json.loads(result.file_data["content"])
    except json.JSONDecodeError:
        return None, True
    if not isinstance(parsed, list):
        return None, True
    return parsed, False


def read_answer_log(backend: BackendProtocol) -> list[Any]:
    """The recorded answer events, oldest first, exactly as the file
    holds them; unreadable is empty. What goes back out is what came in
    — filtering happens where entries are weighed, never here."""
    parsed, unreadable = _read_log(backend)
    return [] if unreadable else parsed


# The marker that outlives the repair: when a corrupt log is preserved
# aside, the fresh log opens with this entry, so the condition stays
# visible after the file parses again. Same shape as a decision's entry,
# but it is not a decision — kind and the moment, nothing else.
ANSWER_LOG_MARKER_KIND = "answer_log_unreadable"


def _marker_entry(moment: str) -> dict[str, Any]:
    return {
        "kind": ANSWER_LOG_MARKER_KIND,
        "subject": None,
        "asked_at": None,
        "answered_at": moment,
        "canonical": None,
        "raw": None,
    }


def answer_log_unreadable(backend: BackendProtocol) -> bool:
    """Whether the answer log could not be read — now, or at any
    repaired point in the session (the marker outlives the repair).
    One definition, both states, the condition's single home."""
    parsed, unreadable = _read_log(backend)
    if unreadable:
        return True
    return any(
        isinstance(entry, dict)
        and entry.get("kind") == ANSWER_LOG_MARKER_KIND
        for entry in parsed
    )


def _preserve_corrupt_log(backend: BackendProtocol) -> None:
    """The corrupt bytes move aside whole before anything rewrites the
    log — the evidence survives whatever corrupted it. First come keeps
    the plain sidecar name; a second corruption numbers on."""
    result = backend.read(ANSWERS_PATH)
    content = result.file_data["content"] if result.file_data else ""
    sidecar = ANSWERS_PATH + ".corrupt"
    n = 0
    while _file_exists(backend, sidecar):
        n += 1
        sidecar = f"{ANSWERS_PATH}.corrupt.{n}"
    backend.write(sidecar, content)
    backend.delete(ANSWERS_PATH)


def _file_exists(backend: BackendProtocol, path: str) -> bool:
    result = backend.read(path)
    return not result.error and result.file_data is not None


def parse_envelope(answer: Any) -> tuple[Any, Any]:
    """Split a resume into ``(canonical, raw)``.

    A dict carrying ``canonical`` is the protocol envelope; anything else
    is a bare answer and stands as its own canonical (the session layer's
    legacy resumes) with itself as provenance.
    """
    if isinstance(answer, dict) and "canonical" in answer:
        return answer["canonical"], answer.get("raw", "")
    return answer, answer


def validate_token(
    pending: dict[str, Any],
    canonical: Any,
    tokens: tuple[str, ...] | list[str],
) -> str:
    """Return ``canonical`` when it is one of ``tokens``; refuse otherwise."""
    if isinstance(canonical, str) and canonical in tokens:
        return canonical
    raise token_refusal(
        pending, f"expected one of {list(tokens)}, got {canonical!r}"
    )


def token_refusal(pending: dict[str, Any], detail: str) -> AskRefusal:
    """The structured refusal for a non-canonical answer — the question
    stays open; the conductor asks again, never a silent default."""
    return AskRefusal(
        {
            "ok": False,
            "refused": True,
            "reason": f"Non-canonical answer — {detail}",
            "pending": {
                "kind": pending["kind"],
                "question": pending.get("question", ""),
            },
            "accepted_tokens": [
                entry["token"] for entry in pending.get("accepted_answers", [])
            ],
            "ask_again": True,
            "admissible_next": ["resume"],
        }
    )


def _one_pending_payload(
    pending: dict[str, Any], attempted_kind: str
) -> dict[str, Any]:
    return {
        "ok": False,
        "refused": True,
        "reason": (
            f"A question is already pending ({pending['kind']}) — one "
            "question at a time; answer it before asking another"
        ),
        "pending": {
            "kind": pending["kind"],
            "question": pending.get("question", ""),
        },
        "attempted_kind": attempted_kind,
        "admissible_next": ["resume"],
    }
