"""Engine verbs — the ask/apply pairs of the AskHuman protocol (ticket 28).

Every human decision is two engine calls: the ask persists the pending
question in the session state and returns its payload; the resume carries
``{canonical, raw}`` and applies the canonical token alone — the raw
words ride as provenance in the result. Resumes are parameterless beside
the answer: the ask's context rides inside the persisted payload, so a
session is resumable from the state files alone (user story 10).

The verbs are thin compositions over the domain stores — one home per
concept stays: the Need in ``need``, Propositions in ``proposition``, the
pipeline in ``pipeline``, the deliverable in ``deliverable``, the
Satisfaction warning in ``inference``. Who answers is not this module's
business: the session layer's interrupt-backed adapter (tools) and the
invocation files are two implementations of the seam.
"""

from __future__ import annotations

from typing import Any

from deepagents.backends.protocol import BackendProtocol

from socrates.asking import (
    CONFIRM_ACCEPTED_ANSWERS,
    CONFIRM_RESUME_CONTRACT,
    CONFIRM_TOKENS,
    DOOR_ACCEPTED_ANSWERS,
    DOOR_RESUME_CONTRACT,
    DOOR_TOKENS,
    FREE_TEXT_ACCEPTED_ANSWERS,
    FREE_TEXT_RESUME_CONTRACT,
    SATISFACTION_ACCEPTED_ANSWERS,
    SATISFACTION_RESUME_CONTRACT,
    SATISFACTION_TOKENS,
    begin_pending,
    clear_pending,
    parse_envelope,
    require_pending,
    token_refusal,
    validate_token,
)
from socrates.deliverable import DeliverableComposer
from socrates.inference import InferenceEngine
from socrates.need import read_need, write_amendment
from socrates.opening import OPENING_GREETING, OPENING_QUESTION, render_opening
from socrates.paths import NEED_PATH
from socrates.pipeline import ModelingActivity, PipelineStore
from socrates.proposition import PropositionStore, proposition_payload

# The door's three answers (ticket 17 / D3-D4), kept for the payload's
# legacy display list: close the chapter, keep it open, or route to the
# Satisfaction flow without closing it.
DOOR_ANSWERS = ("close", "not yet", "satisfaction")

SATISFACTION_QUESTION = (
    "Does this feel right to you as it stands, or is there more to work through?"
)


def _answer(canonical: Any, raw: Any) -> dict[str, Any]:
    return {"canonical": canonical, "raw": raw}


def _declined(action: str, proposition_id: str, status: str) -> dict[str, Any]:
    return {
        "ok": False,
        "declined": True,
        "proposition_id": proposition_id,
        "status": status,
        "error": (
            f"User declined {action}; Proposition {proposition_id} "
            f"remains {status}"
        ),
    }


# --- Opening ------------------------------------------------------------------


def ask_opening(backend: BackendProtocol) -> dict[str, Any]:
    """Ask the Opening question — the Need, free-text, in the user's words."""
    return begin_pending(
        backend,
        {
            "kind": "opening",
            "greeting": OPENING_GREETING,
            "question": OPENING_QUESTION,
            "display": render_opening(),
            "accepted_answers": FREE_TEXT_ACCEPTED_ANSWERS,
            "resume_contract": FREE_TEXT_RESUME_CONTRACT,
        },
    )


def resume_opening(backend: BackendProtocol, answer: Any) -> dict[str, Any]:
    pending = require_pending(backend, "opening")
    canonical, raw = parse_envelope(answer)
    if not isinstance(canonical, str) or not canonical.strip():
        raise token_refusal(pending, "the Need must be the answer text itself")
    backend.write(NEED_PATH, canonical)
    clear_pending(backend)
    return {
        "ok": True,
        "need_path": NEED_PATH,
        "answer": _answer(canonical, raw),
    }


# --- Need amendments -----------------------------------------------------------


def ask_amend_need(
    backend: BackendProtocol,
    proposed_need: str,
    reason: str,
) -> dict[str, Any]:
    """Ask confirmation of a Need amendment — the Relevance Filter reshaped."""
    if not proposed_need.strip() or not reason.strip():
        # A mis-shaped proposal never reaches the user: an empty shape
        # confirmed would corrupt the artifact (US4 read strictly).
        raise ValueError("An amendment needs both a reshaped Need and a reason")
    current = read_need(backend)
    if current is None:
        # Defensive: conduction redirects pre-Opening attempts, so an
        # absent Need here is a race, not a path.
        raise ValueError("No Need is registered to amend yet")
    return begin_pending(
        backend,
        {
            "kind": "amend_need",
            "current_need": current,
            "proposed_need": proposed_need,
            "reason": reason,
            "question": (
                f"Reason: {reason}. Reshape what we're building to "
                "the proposed shape?"
            ),
            "accepted_answers": CONFIRM_ACCEPTED_ANSWERS,
            "resume_contract": CONFIRM_RESUME_CONTRACT,
        },
    )


def resume_amend_need(backend: BackendProtocol, answer: Any) -> dict[str, Any]:
    pending = require_pending(backend, "amend_need")
    canonical, raw = parse_envelope(answer)
    validate_token(pending, canonical, CONFIRM_TOKENS)
    if canonical == "decline":
        clear_pending(backend)
        return {
            "ok": False,
            "declined": True,
            "error": "User declined the Need amendment; the Need stays as it is",
            "answer": _answer(canonical, raw),
        }
    write_amendment(backend, pending["proposed_need"], pending["reason"])
    clear_pending(backend)
    return {
        "ok": True,
        "need_path": NEED_PATH,
        "answer": _answer(canonical, raw),
    }


# --- Proposition lifecycle ------------------------------------------------------


def ask_accept(
    backend: BackendProtocol,
    proposition_id: str,
    via_proposition_id: str = "",
) -> dict[str, Any]:
    store = PropositionStore(backend)
    store.get(proposition_id)  # never ask the user about an unknown Proposition
    return begin_pending(
        backend,
        {
            "kind": "accept",
            "proposition_id": proposition_id,
            "via_proposition_id": via_proposition_id or None,
            "question": (
                f"Do you Accept Proposition {proposition_id} into the Model?"
            ),
            "accepted_answers": CONFIRM_ACCEPTED_ANSWERS,
            "resume_contract": CONFIRM_RESUME_CONTRACT,
        },
    )


def resume_accept(backend: BackendProtocol, answer: Any) -> dict[str, Any]:
    return _resume_lifecycle(backend, answer, "accept")


def ask_reject(
    backend: BackendProtocol,
    proposition_id: str,
    reason: str,
) -> dict[str, Any]:
    store = PropositionStore(backend)
    store.get(proposition_id)
    return begin_pending(
        backend,
        {
            "kind": "reject",
            "proposition_id": proposition_id,
            "reason": reason,
            "question": (
                f"Do you Reject Proposition {proposition_id}? Reason: {reason}"
            ),
            "accepted_answers": CONFIRM_ACCEPTED_ANSWERS,
            "resume_contract": CONFIRM_RESUME_CONTRACT,
        },
    )


def resume_reject(backend: BackendProtocol, answer: Any) -> dict[str, Any]:
    return _resume_lifecycle(backend, answer, "reject")


def _resume_lifecycle(
    backend: BackendProtocol,
    answer: Any,
    kind: str,
) -> dict[str, Any]:
    pending = require_pending(backend, kind)
    canonical, raw = parse_envelope(answer)
    validate_token(pending, canonical, CONFIRM_TOKENS)
    store = PropositionStore(backend)
    proposition_id = pending["proposition_id"]
    if canonical == "decline":
        clear_pending(backend)
        try:
            status = store.get(proposition_id).status
        except ValueError:
            status = "unknown"
        action = "Acceptance" if kind == "accept" else "Rejection"
        return {
            **_declined(action, proposition_id, status),
            "answer": _answer(canonical, raw),
        }
    clear_pending(backend)
    try:
        if kind == "accept":
            prop = store.accept(
                proposition_id,
                via_proposition_id=pending.get("via_proposition_id") or None,
            )
        else:
            prop = store.reject(proposition_id, pending["reason"])
    except (ValueError, KeyError) as exc:
        return {"ok": False, "error": str(exc), "answer": _answer(canonical, raw)}
    return {**proposition_payload(prop), "answer": _answer(canonical, raw)}


# --- The chapter door ------------------------------------------------------------


def ask_door(backend: BackendProtocol, activity: ModelingActivity) -> dict[str, Any]:
    return begin_pending(
        backend,
        {
            "kind": "door",
            "activity": activity,
            "question": f"Confirm closing Modeling Activity '{activity}'?",
            "answers": list(DOOR_ANSWERS),
            "accepted_answers": DOOR_ACCEPTED_ANSWERS,
            "resume_contract": DOOR_RESUME_CONTRACT,
        },
    )


def resume_door(backend: BackendProtocol, answer: Any) -> dict[str, Any]:
    pending = require_pending(backend, "door")
    canonical, raw = parse_envelope(answer)
    validate_token(pending, canonical, DOOR_TOKENS)
    activity = pending["activity"]
    answer_echo = _answer(canonical, raw)
    if canonical == "not_yet":
        clear_pending(backend)
        return {
            "ok": True,
            "door": "not_yet",
            "activity": activity,
            "chapter_open": True,
            "answer": answer_echo,
        }
    if canonical == "satisfaction":
        # The door's question is answered; the Satisfaction question takes
        # over (the chapter stays open — D4, the third answer never closes).
        clear_pending(backend)
        follow = ask_satisfaction(backend, visiting=activity)
        return {
            "ok": True,
            "door": "satisfaction",
            "activity": activity,
            "chapter_open": True,
            "pending": follow,
            "answer": answer_echo,
        }
    clear_pending(backend)
    pipeline = PipelineStore(backend)
    try:
        # A chapter with no Propositions is vacuously quiet (D3): its
        # declaration opens and closes the door in one step.
        pipeline.begin(activity)
        pipeline.complete(activity)
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "answer": answer_echo}
    return {
        "ok": True,
        "completed": activity,
        "door": "close",
        "answer": answer_echo,
    }


# --- Satisfaction ----------------------------------------------------------------


def ask_satisfaction(
    backend: BackendProtocol,
    *,
    visiting: ModelingActivity | None = None,
) -> dict[str, Any]:
    """Ask the Satisfaction question, warning first (never blocking — ADR-0002).

    ``visiting`` is the door's own activity on the door's third answer:
    the chapter whose door carries the question counts as visited
    (ticket 20).
    """
    warning = InferenceEngine(backend).satisfaction_warning(visiting=visiting)
    return begin_pending(
        backend,
        {
            "kind": "satisfaction",
            "question": SATISFACTION_QUESTION,
            "deferred_warning": warning,
            "accepted_answers": SATISFACTION_ACCEPTED_ANSWERS,
            "resume_contract": SATISFACTION_RESUME_CONTRACT,
        },
    )


def resume_satisfaction(backend: BackendProtocol, answer: Any) -> dict[str, Any]:
    pending = require_pending(backend, "satisfaction")
    canonical, raw = parse_envelope(answer)
    validate_token(pending, canonical, SATISFACTION_TOKENS)
    clear_pending(backend)
    answer_echo = _answer(canonical, raw)
    if canonical == "not_satisfied":
        return {
            "ok": True,
            "satisfied": False,
            "message": f"Satisfaction signal received: {raw or canonical}",
            "answer": answer_echo,
        }
    paths = DeliverableComposer(backend).materialize()
    joined = ", ".join(paths)
    return {
        "ok": True,
        "satisfied": True,
        "materialized": sorted(paths),
        "message": (
            f"Satisfaction signal received: {raw or canonical}. "
            f"Conceptual Domain Model materialized at {joined}."
        ),
        "answer": answer_echo,
    }
