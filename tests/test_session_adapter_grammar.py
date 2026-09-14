"""The session adapter's grammar — the review cycle's vocabulary pins.

The session classifier and the contract the payloads advertise were two
grammars never tested against each other (review on dbe414d..HEAD).
These pins hold them to one: exact words decide, hedged compounds
refuse (ask-never-guess), the payload's own advertised spellings are
always recognized, the door's routing vocabulary classifies at the
question it routes to, wrong-order Refusals keep their
refused/admissible_next shape, and every resume crosses parse_envelope
before classification — the session surface honors the {canonical, raw}
contract it advertises.
"""

from __future__ import annotations

import json

import pytest
from deepagents.backends.filesystem import FilesystemBackend

from socrates.asking import AskRefusal, read_pending
from socrates.inference import InferenceEngine
from socrates.paths import PENDING_QUESTION_PATH
from socrates.proposition import PropositionStore
from socrates.refusal import Refusal
from socrates.tools import (
    _ask,
    _classify_confirmation,
    _classify_satisfaction,
    _parse_door_answer,
    _session_resume,
)
from socrates.verbs import (
    ask_accept,
    ask_amend_need,
    ask_door,
    ask_satisfaction,
    resume_accept,
    resume_amend_need,
    resume_door,
)

NEED = "Marketplace checkout payments domain."


def _backend(tmp_path):
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write("/model/need.md", NEED)
    return backend


# --- Exact words decide; hedged compounds refuse (never a silent default) -----


@pytest.mark.parametrize(
    ("answer", "action", "expected"),
    [
        # A hedge decides nothing — it refuses, the conductor asks again.
        ("No problem, go ahead", "accept", None),
        ("not sure", "accept", None),
        ("hm, what?", "accept", None),
        # Exact words decide.
        ("no", "accept", "decline"),
        ("nope", "accept", "decline"),
        ("hold on", "accept", "decline"),
        ("yes", "accept", "confirm"),
        ("confirm", "accept", "confirm"),
        # Cross-polarity is lifecycle-specific: "reject" answering an
        # Acceptance declines it.
        ("reject", "accept", "decline"),
        ("accept", "reject", "decline"),
        # ...but answering an amendment, those words are off-vocabulary.
        ("accept", "amend", None),
        ("reject", "amend", None),
    ],
)
def test_confirmation_grammar(answer, action, expected):
    assert _classify_confirmation(answer, action) == expected


# --- The door recognizes its own advertised spelling --------------------------


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("not_yet", "not_yet"),  # the token the payload advertises
        ("not yet", "not_yet"),  # the legacy spelling
        ("dissatisfied", "not_yet"),  # a negation, never a Satisfaction route
        ("im dissatisfied with this, keep going", None),  # hedged: refuse
        ("enough", "satisfaction"),
        ("close", "close"),
        ("yes", "close"),
    ],
)
def test_door_grammar(answer, expected):
    assert _parse_door_answer(answer) == expected


# --- The door's routing vocabulary classifies at the question it routes to ----


@pytest.mark.parametrize("answer", ["enough", "stop here", "terminate"])
def test_routed_satisfaction_words_classify_at_the_question(answer):
    # Repeating the word the system itself accepted never loops.
    assert _classify_satisfaction(answer) == "satisfied"


def test_satisfaction_negations_still_decline():
    assert _classify_satisfaction("not satisfied") == "not_satisfied"
    assert _classify_satisfaction("there is more to work through") == (
        "not_satisfied"
    )


# --- Wrong-order refusals keep their shape on the session surface -------------


def test_ask_surfaces_refusal_with_admissible_next(tmp_path):
    backend = _backend(tmp_path)
    payload = _ask(lambda: InferenceEngine(backend).probe_batch())
    assert payload["ok"] is False
    assert payload["refused"] is True
    assert payload["reason"]
    assert payload["admissible_next"] == ["door"]


def test_conduct_surfaces_refusal_with_admissible_next(tmp_path):
    backend = _backend(tmp_path)

    def resume(_answer):
        raise Refusal("Reconciliation applies from pass 2 onward", ["scenarios"])

    payload = _session_resume("whatever", lambda c: c, resume)
    assert payload["refused"] is True
    assert payload["admissible_next"] == ["scenarios"]


# --- The session surface honors the {canonical, raw} contract it advertises ---


def test_envelope_resume_classifies_the_canonical_not_the_envelope(tmp_path):
    backend = _backend(tmp_path)
    PropositionStore(backend).propose(
        "Payment status is always Authorized or Settled.", "requirements"
    )
    ask_accept(backend, "p1")

    # Resumed exactly as the resume_contract advertises.
    result = _session_resume(
        {"canonical": "confirm", "raw": "sim"},
        lambda c: _classify_confirmation(c, "accept"),
        lambda a: resume_accept(backend, a, touch=True),
    )
    assert result["ok"] is True
    assert result["answer"] == {"canonical": "confirm", "raw": "sim"}


def test_envelope_resume_on_amend_declines_by_the_canonical_alone(tmp_path):
    backend = _backend(tmp_path)
    ask_amend_need(backend, "A marketplace ledger domain.", "scope sharpened")

    result = _session_resume(
        {"canonical": "decline", "raw": "ainda não"},
        lambda c: _classify_confirmation(c, "amend"),
        lambda a: resume_amend_need(backend, a),
    )
    assert result["declined"] is True
    assert read_pending(backend) is None


# --- A truncated-but-valid marker is corruption: it self-heals ----------------


def test_truncated_marker_self_heals_instead_of_keyerror(tmp_path):
    backend = _backend(tmp_path)
    backend.write(PENDING_QUESTION_PATH, json.dumps({"kind": "iteration"}))

    # No question anyone can answer: healed to none, refused as data.
    assert read_pending(backend) is None
    with pytest.raises(AskRefusal, match="No pending question"):
        resume_door(backend, {"canonical": "close", "raw": "close"})

    # And the session moves on — a fresh ask works.
    assert ask_door(backend, "requirements")["kind"] == "door"
