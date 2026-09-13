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
from typing import Any

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import PENDING_QUESTION_PATH

# Canonical tokens — closed, English, language-agnostic core. The session
# language lives outside the engine; free replies are classified into
# these tokens by the conductor, with the raw words preserved.
DOOR_TOKENS: tuple[str, ...] = ("close", "not_yet", "satisfaction")
CONFIRM_TOKENS: tuple[str, ...] = ("confirm", "decline")
SATISFACTION_TOKENS: tuple[str, ...] = ("satisfied", "not_satisfied")

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


class AskRefusal(Exception):
    """A structured refusal of the asking protocol — JSON-ready.

    Carries the reason, the pending question it names, and (for token
    refusals) the accepted tokens, so the conductor repairs in
    conversation instead of guessing around the refusal.
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload["reason"])
        self.payload = payload


def read_pending(backend: BackendProtocol) -> dict[str, Any] | None:
    """The persisted pending-question payload, or ``None`` when none stands."""
    result = backend.read(PENDING_QUESTION_PATH)
    if result.error or result.file_data is None:
        return None
    content = result.file_data["content"]
    if not content.strip():
        return None
    return json.loads(content)


def begin_pending(backend: BackendProtocol, payload: dict[str, Any]) -> dict[str, Any]:
    """Persist the pending question and return its payload.

    Re-asking the same kind re-presents the persisted question unchanged
    (idempotence — a Batch is never created twice for one question); any
    other asking verb refuses naming the pending one.
    """
    existing = read_pending(backend)
    if existing is None:
        backend.write(PENDING_QUESTION_PATH, json.dumps(payload, indent=2))
        return payload
    if existing["kind"] == payload["kind"]:
        return existing
    raise AskRefusal(_one_pending_payload(existing, payload["kind"]))


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
            }
        )
    if existing["kind"] != kind:
        raise AskRefusal(_one_pending_payload(existing, kind))
    return existing


def guard_pending(backend: BackendProtocol, kind: str) -> dict[str, Any] | None:
    """The re-presented payload when ``kind`` re-asks its own pending
    question; ``None`` when no question is pending; refusal for any other
    kind. Askers call this BEFORE mutating state, so a re-ask never
    duplicates its own work (a Batch is never created twice for one
    question)."""
    existing = read_pending(backend)
    if existing is None:
        return None
    if existing["kind"] == kind:
        return existing
    raise AskRefusal(_one_pending_payload(existing, kind))


def clear_pending(backend: BackendProtocol) -> None:
    backend.delete(PENDING_QUESTION_PATH)


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
    }
