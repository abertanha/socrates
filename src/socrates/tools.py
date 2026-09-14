"""Interview, Proposition-lifecycle, and Modeling Activity tools.

The session layer is an interrupt-backed adapter over the AskHuman
boundary (ticket 28): every asking tool runs its verb's ask — persisting
the pending question in the session state — surfaces the payload through
a langgraph interrupt, classifies the resume into a canonical token with
this layer's legacy English vocabulary (the hybrid's conductor classifies
instead), and drives the verb's resume. A resume that classifies to
nothing is a structured refusal the conductor repairs by asking again —
never a silent default (the improvised-vocabulary failures the boundary
exists to kill).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from typing import Any

from deepagents.backends.protocol import BackendProtocol
from langchain_core.tools import BaseTool, StructuredTool
from langchain.tools import tool
from langgraph.types import interrupt

from socrates.asking import AskRefusal, parse_envelope
from socrates.coverage import CoverageStore
from socrates.deliverable import is_affirmative_satisfaction
from socrates.inference import InferenceEngine
from socrates.opening import OPENING_QUESTION
from socrates.pipeline import ModelingActivity, PipelineStore
from socrates.proposition import PropositionStore, proposition_payload
from socrates.refusal import Refusal, refusal_payload
from socrates.verbs import (
    SATISFACTION_QUESTION,
    ask_accept,
    ask_amend_need,
    ask_door,
    ask_opening,
    ask_reject,
    ask_satisfaction,
    propose as propose_verb,
    resume_accept,
    resume_amend_need,
    resume_door,
    resume_opening,
    resume_reject,
    resume_satisfaction,
)

# The pass/Probe pulse, stated once for every chapter specialist: one
# regime per chapter — propose, lapidate, resolve under one roof (D1).
_ACTIVITY_PULSE = (
    " Run the pass/Probe pulse inside this chapter: call "
    "`select_exploration_budget` at the start of each pass so Coverage sets "
    "the exploration allowance — an allowance, never a quality gate; from "
    "pass 2, `reconcile` first (L2/L3 only — an empty findings array is "
    "valid, never fabricate findings); then `record_scenarios` → "
    "`run_assertion_tests` (L1/L4) → `probe_batch` for L1–L3. Deferrable "
    "Conflicts may be deferred. L4 Conflicts are unavoidable — never defer "
    "or Probe them; surface them and let the orchestrator carry them to "
    "Iteration. The treadmill keeps one unlapidated Proposition at a time: "
    "lapidate each Proposition (Scenarios, Assertion Tests) before proposing "
    "the next — ground born from Probe resolution is exempt and enters "
    "immediately. Call `complete_modeling_activity` when the chapter is "
    "quiet; the user then answers at the door: close, not yet, or "
    "Satisfaction."
)

ACTIVITY_PROMPTS: dict[ModelingActivity, str] = {
    "requirements": (
        "You are the Requirements specialist. Elicit and bound the Need: what "
        "every later Model must include and exclude. Propose Need-scoped "
        "Propositions only." + _ACTIVITY_PULSE
    ),
    "domain_modeling": (
        "You are the Domain Modeling specialist. Bound the Subject Domain and "
        "establish ubiquitous language and entities — what the domain is — "
        "within the Need. Propose structural Propositions only." + _ACTIVITY_PULSE
    ),
    "behavioral_specification": (
        "You are the Behavioral Specification specialist. Infer conceptual "
        "behavior and relationships between entities as domain rules — what "
        "the domain does. Never propose functional requirements "
        "('the system shall...')." + _ACTIVITY_PULSE
    ),
}

_GENERIC_CONFIRMS = frozenset(
    {"yes", "y", "confirm", "confirmed", "ok", "true"}
)

# Polarity-specific affirmations confirm only their own action; the
# opposite word declines it, leaving the Proposition's status preserved.
_ACTION_CONFIRMS: dict[str, frozenset[str]] = {
    "accept": _GENERIC_CONFIRMS | {"accept", "accepted"},
    "reject": _GENERIC_CONFIRMS | {"reject", "rejected"},
}

# Explicit declines for the three-way classifier: a word that is neither
# an affirmation nor a decline classifies to nothing and the conductor
# asks again (ticket 28 — never a silent default).
_DECLINE_WORDS = frozenset(
    {
        "no",
        "n",
        "nope",
        "decline",
        "declined",
        "not now",
        "later",
        "hold on",
        "stop",
        "keep as is",
    }
)


def _normalize_answer(text: str) -> str:
    """Casefolded, whitespace-collapsed form of a resume answer."""
    return " ".join(text.strip().casefold().split())


def _classify_confirmation(answer: Any, action: str) -> str | None:
    """Legacy resume vocabulary → canonical confirm/decline (None = unrecognized).

    Affirmations are contextual to the action's polarity: for the
    lifecycle actions, "reject" never confirms an Acceptance (and
    "accept" never confirms a Rejection) — the cross-polarity word
    declines the action instead; for every other action those words are
    just off-vocabulary and refuse. A decline is an exact word, never a
    prefix: "No problem, go ahead" affirms nothing decidable and "not
    sure" decides nothing — hedged sentences refuse and the conductor
    asks again (ticket 28's ask-never-guess). English-only, as this
    adapter's classifier (the hybrid's conductor is the language
    boundary).
    """
    if answer is True:
        return "confirm"
    if answer is False:
        return "decline"
    if not isinstance(answer, str):
        return None
    normalized = _normalize_answer(answer)
    if not normalized:
        return None
    if normalized.startswith("yes") or normalized in _ACTION_CONFIRMS.get(
        action, _GENERIC_CONFIRMS
    ):
        return "confirm"
    words = normalized.split()
    if len(words) == 1 and words[0] in {"no", "n", "nope"}:
        return "decline"
    if normalized in _DECLINE_WORDS:
        return "decline"
    if action in _ACTION_CONFIRMS:
        other = "reject" if action == "accept" else "accept"
        if normalized in _ACTION_CONFIRMS[other]:
            return "decline"
    return None


# The door's answer vocabulary (ticket 17) — contextual polarity like
# accept/reject: "yes" closes, "no" keeps the chapter open, a Satisfaction
# word routes to the Satisfaction flow. Matching is exact-word: the
# "satisf" substring is dead ("dissatisfied" is a NEGATION, and negated
# Satisfaction words like "not satisfied" keep the chapter open), and a
# hedged compound refuses rather than silently deciding. An unrecognized
# answer classifies to nothing and the conductor asks again (ticket 28's
# ask-never-guess: the door never closes, never routes, and never
# silently defaults on a mumble). English-only, consistent with the
# classifier above. Kept in step with _classify_satisfaction: every word
# that routes here classifies as "satisfied" at the question it routes
# to — one vocabulary, two speech acts.
_DOOR_SATISFACTION_WORDS = frozenset(
    {
        "satisfaction",
        "satisfied",
        "im satisfied",
        "i am satisfied",
        "enough",
        "stop here",
        "terminate",
    }
)
_DOOR_CLOSE_WORDS = _GENERIC_CONFIRMS | {
    "close",
    "closed",
    "done",
    "proceed",
    "move on",
}
_DOOR_NOT_YET_WORDS = frozenset(
    {
        "not yet",
        "not_yet",
        "no",
        "n",
        "later",
        "wait",
        "not now",
        "not satisfied",
        "dissatisfied",
        "unsatisfied",
        "keep open",
        "keep it open",
        "continue",
        "keep going",
    }
)


def _parse_door_answer(answer: Any) -> str | None:
    """Map a door resume to its canonical token ("close" / "not_yet" /
    "satisfaction"), or ``None`` when nothing recognized. The payload's
    own advertised spelling ("not_yet") is always recognized."""
    if isinstance(answer, bool):
        return "close" if answer else "not_yet"
    if not isinstance(answer, str):
        return None
    normalized = _normalize_answer(answer)
    if not normalized:
        return None
    if normalized in _DOOR_NOT_YET_WORDS:
        return "not_yet"
    if normalized in _DOOR_SATISFACTION_WORDS:
        return "satisfaction"
    if normalized in _DOOR_CLOSE_WORDS:
        return "close"
    if normalized.startswith("yes"):
        return "close"
    return None


def _classify_satisfaction(answer: Any) -> str | None:
    """Legacy resume vocabulary → canonical satisfied/not_satisfied.

    Kept in step with the door's routing vocabulary: a word that routes
    to this flow at the door (— "enough", "stop here" —) classifies as
    "satisfied" here, so repeating the word the system itself accepted
    never loops."""
    if answer is True:
        return "satisfied"
    if answer is False:
        return "not_satisfied"
    if not isinstance(answer, str):
        return None
    normalized = _normalize_answer(answer)
    if not normalized:
        return None
    if is_affirmative_satisfaction(normalized):
        return "satisfied"
    if normalized.startswith(("no", "not")) or "more to work" in normalized:
        return "not_satisfied"
    if normalized in _DOOR_SATISFACTION_WORDS:
        return "satisfied"
    return None


def _conduct(resume: Callable[[Any], dict], answer: Any) -> dict:
    """Drive one resume over the AskHuman boundary.

    A non-canonical answer is a structured refusal naming the pending
    question and its accepted tokens — the conductor asks again, never a
    silent default. A wrong-order ``Refusal`` keeps its shape (refused +
    admissible_next, the same JSON the invocation files emit); a
    semantic ValueError surfaces as the shape the asking verbs have
    always refused with.
    """
    try:
        return resume(answer)
    except AskRefusal as refusal:
        return refusal.payload
    except Refusal as refusal:
        return refusal_payload(refusal)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}


def _ask(ask: Callable[[], dict]) -> dict:
    """Run one ask over the AskHuman boundary.

    A protocol refusal (a question already pending) and a semantic
    ``ValueError`` both surface as the structured JSON the conductor
    repairs — ``AskRefusal`` is not a ``ValueError``, so catching it here
    is what keeps the one-pending refusal from escaping as a raw
    traceback (review fix).
    """
    try:
        return ask()
    except AskRefusal as refusal:
        return refusal.payload
    except Refusal as refusal:
        return refusal_payload(refusal)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}


def _envelope(answer: Any, canonical: Any) -> dict:
    """The {canonical, raw} resume envelope — one writer, no hand-built
    literals drifting."""
    return {"canonical": canonical, "raw": answer}


def _session_resume(
    answer: Any,
    classify: Callable[[Any], Any],
    resume: Callable[[Any], dict],
) -> dict:
    """One block for every session resume — the seam's two grammatical
    halves made to agree (review fix).

    The answer crosses ``parse_envelope`` FIRST, so the session surface
    honors the very {canonical, raw} contract its payloads advertise;
    the canonical alone is classified against the legacy vocabulary; and
    the envelope is rebuilt with the raw words riding as provenance. An
    unclassifiable answer reaches the engine as canonical ``None`` and
    comes back as the structured token refusal — never a silent
    default, never a double wrap.
    """
    canonical, raw = parse_envelope(answer)
    decided = classify(canonical)
    return _conduct(resume, _envelope(raw, decided))


def build_session_tools(backend: BackendProtocol) -> Sequence[BaseTool]:
    """Tools for the main Socrates orchestrator.

    The pass/Probe pulse is composed in too (the tail's passes); the
    conduction governor admits it on this surface only in the tail and
    redirects out-of-state attempts into the chapters.
    """
    inference = InferenceEngine(backend)

    @tool
    def run_opening() -> str:
        """Open the session: show the banner and greeting, then ask what the user is building.

        Call this before writing any prose of your own — it is the first thing
        the user sees, and it already does the greeting for you.
        """
        payload = _ask(lambda: ask_opening(backend))
        if payload.get("refused") or payload.get("ok") is False:
            return json.dumps(payload)
        answer = interrupt(payload)
        return json.dumps(
            _session_resume(
                answer,
                lambda c: c.strip() if isinstance(c, str) and c.strip() else None,
                lambda a: resume_opening(backend, a),
            )
        )

    @tool
    def await_satisfaction() -> str:
        """Ask the user, in plain words, whether the Model is right as it stands.

        Surfaces a non-blocking warning when deferred Conflicts remain open. On
        an affirmative answer, materializes the Conceptual Domain Model as
        Glossary + Structure + Rules under /model/deliverable/.
        """
        payload = _ask(lambda: ask_satisfaction(backend))
        if payload.get("refused") or payload.get("ok") is False:
            return json.dumps(payload)
        answer = interrupt(payload)
        return json.dumps(
            _session_resume(
                answer,
                _classify_satisfaction,
                lambda a: resume_satisfaction(backend, a),
            )
        )

    @tool
    def amend_need(proposed_need: str, reason: str) -> str:
        """Propose reshaping the Need — the Relevance Filter judging every Proposition.

        Admitted while the Requirements chapter is open. The user confirms at
        an interrupt comparing the current Need with the proposed one; on
        confirmation the Need is rewritten with the amendment recorded beneath
        it (the superseded shape and the reason survive, newest last). A
        declined amendment leaves the Need exactly as it was.
        """
        payload = _ask(lambda: ask_amend_need(backend, proposed_need, reason))
        if payload.get("refused") or payload.get("ok") is False:
            return json.dumps(payload)
        answer = interrupt(payload)
        return json.dumps(
            _session_resume(
                answer,
                lambda c: _classify_confirmation(c, "amend"),
                lambda a: resume_amend_need(backend, a),
            )
        )

    @tool
    def propose_proposition(statement: str, activity: ModelingActivity) -> str:
        """Propose a Proposition tagged with the Modeling Activity that produced it."""
        try:
            payload = propose_verb(backend, statement, activity, touch=True)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(payload)

    @tool
    def accept_proposition(
        proposition_id: str,
        via_proposition_id: str = "",
    ) -> str:
        """Accept a Candidate into the Model after the user's direct Acceptance signal.

        Optional via_proposition_id marks indirect Acceptance (foundation for cascades).
        """
        payload = _ask(
            lambda: ask_accept(backend, proposition_id, via_proposition_id)
        )
        if payload.get("refused") or payload.get("ok") is False:
            return json.dumps(payload)
        answer = interrupt(payload)
        return json.dumps(
            _session_resume(
                answer,
                lambda c: _classify_confirmation(c, "accept"),
                lambda a: resume_accept(backend, a, touch=True),
            )
        )

    @tool
    def reject_proposition(proposition_id: str, reason: str) -> str:
        """Reject a Proposition with an explicit reason; records it in the Rejection Guardrail."""
        payload = _ask(lambda: ask_reject(backend, proposition_id, reason))
        if payload.get("refused") or payload.get("ok") is False:
            return json.dumps(payload)
        answer = interrupt(payload)
        return json.dumps(
            _session_resume(
                answer,
                lambda c: _classify_confirmation(c, "reject"),
                lambda a: resume_reject(backend, a, touch=True),
            )
        )

    @tool
    def run_iteration(conflict_id: str) -> str:
        """Hand an L4 Conflict to Iteration: propose phase, confirm, reopen activity."""
        payload = _ask(lambda: inference.run_iteration(conflict_id))
        if payload.get("refused") or payload.get("ok") is False:
            return json.dumps(payload)
        answer = interrupt(payload)
        result = _session_resume(
            answer,
            lambda c: c,  # the engine parses its own confirm grammar
            lambda a: inference.iteration_resume(a),
        )
        return json.dumps({"ok": True, **result})

    return [
        run_opening,
        await_satisfaction,
        amend_need,
        propose_proposition,
        accept_proposition,
        reject_proposition,
        run_iteration,
        *build_pulse_tools(backend),
    ]


def build_pulse_tools(backend: BackendProtocol) -> Sequence[BaseTool]:
    """The pass/Probe pulse — one regime per chapter, and the tail's passes.

    Shared by the chapter specialists (unconditional) and the main
    orchestrator, where the conduction governor admits it only in the tail.
    """
    inference = InferenceEngine(backend)
    coverage = CoverageStore(backend)

    @tool
    def reconcile(findings_json: str) -> str:
        """From pass 2, surface latent L2/L3 Conflicts before Scenarios / Assertion Tests.

        An empty findings array is valid — it records that Reconciliation ran
        and surfaced nothing. Never fabricate findings to satisfy the gate.
        """
        try:
            findings = json.loads(findings_json)
            if not isinstance(findings, list):
                raise ValueError("findings_json must be a JSON array")
            surfaced = inference.reconcile(findings)
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(
            {
                "ok": True,
                "pass": inference.current_pass(),
                "conflicts": [c.__dict__ for c in surfaced],
            }
        )

    @tool
    def record_scenarios(proposition_id: str, scenarios_json: str) -> str:
        """Record several Need-relevant Scenarios for a Proposition (Relevance Filter enforced)."""
        try:
            scenarios = json.loads(scenarios_json)
            if not isinstance(scenarios, list):
                raise ValueError("scenarios_json must be a JSON array")
            recorded = inference.record_scenarios(proposition_id, scenarios)
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(
            {
                "ok": True,
                "proposition_id": proposition_id,
                "scenarios": [s.__dict__ for s in recorded],
            }
        )

    @tool
    def run_assertion_tests(proposition_id: str, outcomes_json: str) -> str:
        """Run Assertion Tests for a Proposition; non-surviving Scenarios surface Conflicts."""
        try:
            outcomes = json.loads(outcomes_json)
            if not isinstance(outcomes, list):
                raise ValueError("outcomes_json must be a JSON array")
            surfaced = inference.run_assertion_tests(proposition_id, outcomes)
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(
            {
                "ok": True,
                "proposition_id": proposition_id,
                "conflicts": [c.__dict__ for c in surfaced],
            }
        )

    @tool
    def probe_batch() -> str:
        """Gather open L1–L3 Conflicts into one Batch and Probe the user.

        The Batch's question returns as a pending-question payload; the
        resumed resolutions apply on the same call (the session adapter),
        transactionally — a malformed resume rolls back and re-presents.
        L4 Conflicts are not Probe-resolved — use run_iteration.
        """
        payload = _ask(lambda: inference.probe_batch())
        if payload.get("refused") or payload.get("ok") is False:
            return json.dumps(payload)
        answer = interrupt(payload)
        result = _session_resume(
            answer,
            lambda c: c,  # resolutions ride their own shape
            lambda a: inference.probe_resume(a),
        )
        return json.dumps({"ok": True, **result})

    @tool
    def defer_conflict(conflict_id: str) -> str:
        """Defer an open Conflict (any level) to resolve later; may re-raise on touch."""
        try:
            result = inference.defer_conflict(conflict_id)
        except (ValueError, KeyError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps({"ok": True, **result})

    @tool
    def select_exploration_budget() -> str:
        """Set this pass's recursion_limit from Coverage (∝ 1/Coverage).

        Coverage rises as Conflicts-per-pass decline. The budget is an
        exploration allowance only — never a quality gate. Subagents receive
        the same limit.
        """
        # Allowance, not a grader (ADR-0002/0004); propagation guards #1698.
        try:
            budget = coverage.select_budget()
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps({"ok": True, **budget})

    return [
        reconcile,
        record_scenarios,
        run_assertion_tests,
        probe_batch,
        defer_conflict,
        select_exploration_budget,
    ]


def build_activity_tools(
    backend: BackendProtocol,
    activity: ModelingActivity,
) -> Sequence[BaseTool]:
    """Chapter specialist tools: Proposition lifecycle + the pass/Probe pulse.

    One regime per Modeling Activity (D1) — propose, lapidate, resolve under
    one roof. The pulse composes in unconditionally here; conduction governs
    it only on the orchestrator surface. The chapter door (ticket 17) lives
    in `complete_modeling_activity`: when the chapter is quiet, its
    declaration asks the user with three answers — close / not yet /
    Satisfaction.
    """
    store = PropositionStore(backend)
    pipeline = PipelineStore(backend)

    def propose_proposition(statement: str) -> str:
        try:
            pipeline.begin(activity)
            prop = store.propose(statement, activity=activity)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(proposition_payload(prop))

    def accept_proposition(
        proposition_id: str,
        via_proposition_id: str = "",
    ) -> str:
        payload = _ask(
            lambda: ask_accept(backend, proposition_id, via_proposition_id)
        )
        if payload.get("refused") or payload.get("ok") is False:
            return json.dumps(payload)
        answer = interrupt(payload)
        return json.dumps(
            _session_resume(
                answer,
                lambda c: _classify_confirmation(c, "accept"),
                lambda a: resume_accept(backend, a),
            )
        )

    def reject_proposition(proposition_id: str, reason: str) -> str:
        payload = _ask(lambda: ask_reject(backend, proposition_id, reason))
        if payload.get("refused") or payload.get("ok") is False:
            return json.dumps(payload)
        answer = interrupt(payload)
        return json.dumps(
            _session_resume(
                answer,
                lambda c: _classify_confirmation(c, "reject"),
                lambda a: resume_reject(backend, a),
            )
        )

    def complete_modeling_activity() -> str:
        """Declare the chapter complete — the user answers at the door.

        The conduction governor has already established the chapter is quiet
        (every Proposition born in it through ≥1 pass, no Batch pending);
        quiet is bookkeeping, "good enough to close" is the user's judgment
        (ADR-0002). The declaration asks with three answers (D3/D4):
        "close" completes the chapter, "not_yet" keeps it open (the maieutic
        valve stays live), "satisfaction" routes to the Satisfaction flow
        WITHOUT closing the chapter.
        """
        payload = _ask(lambda: ask_door(backend, activity))
        if payload.get("refused") or payload.get("ok") is False:
            return json.dumps(payload)
        answer = interrupt(payload)
        result = _session_resume(
            answer,
            _parse_door_answer,
            lambda a: resume_door(backend, a),
        )
        if result.get("door") == "satisfaction" and "pending" in result:
            # The door's third answer chains the Satisfaction question —
            # same turn, its own interrupt (ticket 17's shared flow).
            follow = result.pop("pending")
            follow_answer = interrupt(follow)
            result["satisfaction"] = _session_resume(
                follow_answer,
                _classify_satisfaction,
                lambda a: resume_satisfaction(backend, a),
            )
        return json.dumps(result)

    return [
        StructuredTool.from_function(
            func=propose_proposition,
            name="propose_proposition",
            description=(
                f"Propose a Proposition in the {activity} Modeling Activity. "
                "Triages to Candidate, or Flagged if it resembles the Rejection Guardrail."
            ),
        ),
        StructuredTool.from_function(
            func=accept_proposition,
            name="accept_proposition",
            description=(
                "Accept a Candidate into the Model after the user's direct "
                "Acceptance signal."
            ),
        ),
        StructuredTool.from_function(
            func=reject_proposition,
            name="reject_proposition",
            description=(
                "Reject a Proposition with an explicit reason; records it in "
                "the Rejection Guardrail."
            ),
        ),
        StructuredTool.from_function(
            func=complete_modeling_activity,
            name="complete_modeling_activity",
            description=(
                f"Declare the {activity} Modeling Activity complete when the "
                "chapter is quiet — every Proposition born in it has been "
                "through a pass (Scenarios / Assertion Tests) and no Batch "
                "awaits the user. The declaration opens the door: the user "
                "answers close, not yet, or Satisfaction."
            ),
        ),
        *build_pulse_tools(backend),
    ]
