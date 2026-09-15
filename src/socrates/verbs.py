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
    AskRefusal,
    begin_pending,
    clear_pending,
    guard_pending,
    parse_envelope,
    read_pending,
    refresh_pending,
    require_pending,
    token_refusal,
    validate_token,
)
from socrates.deliverable import DeliverableComposer
from socrates.conduction import TAIL, read_conduction_state
from socrates.inference import InferenceEngine
from socrates.need import read_need, write_amendment
from socrates.opening import OPENING_GREETING, OPENING_QUESTION, render_opening
from socrates.paths import NEED_PATH
from socrates.pipeline import ModelingActivity, PipelineStore
from socrates.proposition import PropositionStore, proposition_payload
from socrates.refusal import Refusal

# The door's three answers (ticket 17 / D3-D4) — the canonical tokens the
# resume validates, shown in the payload so every surface spells the
# door's second answer the one way the engine accepts.
DOOR_ANSWERS = ("close", "not_yet", "satisfaction")

SATISFACTION_QUESTION = (
    "Does this feel right to you as it stands, or is there more to work through?"
)


def _answer(canonical: Any, raw: Any) -> dict[str, Any]:
    return {"canonical": canonical, "raw": raw}


def propose(
    backend: BackendProtocol,
    statement: str,
    activity: ModelingActivity,
    *,
    touch: bool = False,
) -> dict[str, Any]:
    """Propose a Proposition — the orchestrator-style surface re-raises
    the deferred Conflicts its new ground touches (``touch=True``); the
    chapter surface does not (ticket 17's one-regime ruling)."""
    _gate_propose(backend)
    prop = PropositionStore(backend).propose(statement, activity=activity)
    payload = proposition_payload(prop)
    if touch:
        raised = InferenceEngine(backend).touch_propositions(prop.id)
        if raised:
            payload["re_raised_conflict_ids"] = [c.id for c in raised]
    return payload


def _gate_propose(backend: BackendProtocol) -> None:
    """The propose ordering, engine-side (review 3): the skin retired its
    ordering prose on the premise that the engine refuses what is not
    admissible — so it does, here, on every surface. No modeling exists
    before the Need (the session middleware holds the same gate for the
    tool surface); the treadmill holds the next propose until the open
    chapter's unlapidated ground is lapidated. On this surface chapters
    are implicit until their door — the walk's chapter is whichever the
    precedence expects — so the treadmill reads the same facts the
    middleware's chapter-scoped rule reads, minus the active marker this
    surface does not carry."""
    if read_need(backend) is None:
        pending = read_pending(backend)
        raise Refusal(
            "the Need is not registered yet — the Opening elicits and "
            "persists it before any modeling exists",
            ["resume"] if pending is not None else ["opening"],
        )
    state = read_conduction_state(backend)
    if state.label != TAIL and state.unlapidated:
        owed = ", ".join(pid for pid, _ in state.unlapidated)
        raise Refusal(
            f"treadmill: Proposition(s) {owed} have never been through "
            "a pass — lapidate them (Scenarios, then Assertion Tests) "
            "before proposing the next one; only ground born from Probe "
            "resolution enters without waiting",
            ["scenarios", "assertion_tests"],
        )


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
            "subject": f"{proposed_need}\n{reason}",
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
    # The one-pending law negotiates first: a question already standing is
    # named by the refusal even when the new ask is itself mis-addressed.
    guard_pending(backend, "accept", proposition_id)
    store = PropositionStore(backend)
    store.get(proposition_id)  # never ask the user about an unknown Proposition
    return begin_pending(
        backend,
        {
            "kind": "accept",
            "subject": proposition_id,
            "proposition_id": proposition_id,
            "via_proposition_id": via_proposition_id or None,
            "question": (
                f"Do you Accept Proposition {proposition_id} into the Model?"
            ),
            "accepted_answers": CONFIRM_ACCEPTED_ANSWERS,
            "resume_contract": CONFIRM_RESUME_CONTRACT,
        },
    )


def resume_accept(
    backend: BackendProtocol,
    answer: Any,
    *,
    touch: bool = False,
) -> dict[str, Any]:
    return _resume_lifecycle(backend, answer, "accept", touch=touch)


def ask_reject(
    backend: BackendProtocol,
    proposition_id: str,
    reason: str,
) -> dict[str, Any]:
    guard_pending(backend, "reject", proposition_id)
    store = PropositionStore(backend)
    store.get(proposition_id)
    return begin_pending(
        backend,
        {
            "kind": "reject",
            "subject": proposition_id,
            "proposition_id": proposition_id,
            "reason": reason,
            "question": (
                f"Do you Reject Proposition {proposition_id}? Reason: {reason}"
            ),
            "accepted_answers": CONFIRM_ACCEPTED_ANSWERS,
            "resume_contract": CONFIRM_RESUME_CONTRACT,
        },
    )


def resume_reject(
    backend: BackendProtocol,
    answer: Any,
    *,
    touch: bool = False,
) -> dict[str, Any]:
    return _resume_lifecycle(backend, answer, "reject", touch=touch)


def _resume_lifecycle(
    backend: BackendProtocol,
    answer: Any,
    kind: str,
    *,
    touch: bool = False,
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
    try:
        if kind == "accept":
            prop = store.accept(
                proposition_id,
                via_proposition_id=pending.get("via_proposition_id") or None,
            )
        else:
            prop = store.reject(proposition_id, pending["reason"])
    except (ValueError, KeyError) as exc:
        # The apply failed but the answer was not consumed: the question
        # stays pending (as the Probe's rollback keeps its Batch), so the
        # conductor can repair and re-resume instead of re-asking the user.
        return {"ok": False, "error": str(exc), "answer": _answer(canonical, raw)}
    clear_pending(backend)
    payload = proposition_payload(prop)
    if touch:
        # The orchestrator-style surface re-raises the deferred Conflicts
        # the applied ground touches; the chapter surface does not.
        raised = InferenceEngine(backend).touch_propositions(proposition_id)
        if raised:
            payload["re_raised_conflict_ids"] = [c.id for c in raised]
    return {**payload, "answer": _answer(canonical, raw)}


# --- The chapter door ------------------------------------------------------------


def ask_door(backend: BackendProtocol, activity: ModelingActivity) -> dict[str, Any]:
    return begin_pending(
        backend,
        {
            "kind": "door",
            "subject": activity,
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
    pipeline = PipelineStore(backend)
    try:
        # A chapter with no Propositions is vacuously quiet (D3): its
        # declaration opens and closes the door in one step.
        pipeline.begin(activity)
        pipeline.complete(activity)
    except ValueError as exc:
        # The close failed but the answer was not consumed: the question
        # stays pending, so the conductor can repair and re-resume.
        return {"ok": False, "error": str(exc), "answer": answer_echo}
    clear_pending(backend)
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
    existing = guard_pending(backend, "satisfaction")
    payload = {
        "kind": "satisfaction",
        "question": SATISFACTION_QUESTION,
        "deferred_warning": warning,
        "accepted_answers": SATISFACTION_ACCEPTED_ANSWERS,
        "resume_contract": SATISFACTION_RESUME_CONTRACT,
    }
    if existing is not None:
        # Re-presenting the standing question — but the warning is
        # derived state: refreshed so the user never confirms
        # Satisfaction on a picture of a session that has moved on.
        return refresh_pending(backend, payload)
    return begin_pending(backend, payload)


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


def materialize_deliverable(backend: BackendProtocol) -> dict[str, Any]:
    """Compose the deliverable from the recorded ground (ticket 31).

    The engine's authorship: every accepted statement ships verbatim,
    each row citing the ground identifier it derives from — the
    dropped-relationship class dies by construction. Composition is a
    pure derivation over the ground, so calling it again recomposes —
    the deliverable audit's cure for a finding runs through here, never
    through a hand edit.
    """
    if read_need(backend) is None:
        raise Refusal(
            "No Need is recorded yet: materialization derives the "
            "deliverable from the recorded ground, and there is none.",
            ["opening"],
        )
    paths = DeliverableComposer(backend).materialize()
    joined = ", ".join(sorted(paths))
    return {
        "ok": True,
        "materialized": sorted(paths),
        "message": f"Conceptual Domain Model composed at {joined}.",
    }


# --- The one resume: dispatched on the pending kind -----------------------------


def resume_pending(backend: BackendProtocol, answer: Any) -> dict[str, Any]:
    """Resume whichever question is pending — one entry, per kind.

    The pending payload carries its kind, so the caller never has to know
    which resume verb matches: it answers the question it was shown. The
    invocation surface resumes orchestrator-style — accepts and rejections
    re-raise the deferred Conflicts the applied ground touches
    (``touch=True``, ticket 17's one-regime ruling).
    """
    pending = read_pending(backend)
    if pending is None:
        raise AskRefusal(
            {
                "ok": False,
                "refused": True,
                "reason": "No pending question to resume",
                "pending": None,
                "ask_again": False,
            }
        )
    kind = pending["kind"]
    if kind == "probe":
        result = InferenceEngine(backend).probe_resume(answer)
    elif kind == "iteration":
        result = InferenceEngine(backend).iteration_resume(answer)
    elif kind == "accept":
        result = resume_accept(backend, answer, touch=True)
    elif kind == "reject":
        result = resume_reject(backend, answer, touch=True)
    elif kind == "opening":
        result = resume_opening(backend, answer)
    elif kind == "amend_need":
        result = resume_amend_need(backend, answer)
    elif kind == "door":
        result = resume_door(backend, answer)
    elif kind == "satisfaction":
        result = resume_satisfaction(backend, answer)
    else:
        raise Refusal(
            f"Pending question of unknown kind {kind!r}",
            ["pending_question"],
        )
    # The engine's apply results state their success as data; the Probe's
    # and Iteration's ride bare — the resume door normalizes them.
    result.setdefault("ok", True)
    return result
