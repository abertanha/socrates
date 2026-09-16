"""Ticket 05 (socrates-seam) — the end cannot be improvised.

The session's end stops being reachable by accident and its check stops
being skippable in silence. The door ask validates its activity against
the engine's modeling activities: the fifth specimen's fabricated
``{"activity": "satisfaction"}`` door — which the engine accepted and
which chained into the real Satisfaction question, landing the
protocol-correct end state by luck — is refused in the standard grammar,
reason and admissible next included. The materialization payloads name
the deliverable audit as the next step, admissible-next style: the
specimen's session ended with no audit at all, and the payload is the
channel the conductor demonstrably obeys. The audit instrument itself is
untouched; the skin gains the honesty clause — the weaker fallback
declared to the user before it runs, never silent.

Seam: the invocation files, in-process with argv and a temporary working
directory, asserting on the JSON; the skin pinned the established way.
"""

from __future__ import annotations

import json
from pathlib import Path

NEED = "A checkout flow for a small store."

ACTIVITIES = ["requirements", "domain_modeling", "behavioral_specification"]


def _call(module, tmp_path: Path, data=None):
    argv = ["--root", str(tmp_path)]
    if data is not None:
        argv.append(json.dumps(data))
    return module.main(argv)


def _seed_need(tmp_path: Path) -> None:
    from socrates.invocations import opening, resume

    _call(opening, tmp_path)
    _call(resume, tmp_path, {"canonical": NEED, "raw": "checkout"})


# --- The door validates its activity -----------------------------------------------


def test_a_fabricated_door_activity_refuses(tmp_path):
    from socrates.invocations import door, pending_question

    payload = _call(door, tmp_path, {"activity": "satisfaction"})
    assert payload.get("refused") is True, payload
    assert "satisfaction" in payload["reason"], payload
    assert payload["admissible_next"] == ACTIVITIES, payload
    standing = _call(pending_question, tmp_path)
    assert standing["pending"] is None, (
        "the fabricated door left a question pending"
    )


def test_a_fabricated_door_activity_refuses_on_a_seeded_session(tmp_path):
    """The specimen's session had a full Model behind the fabricated door —
    the refusal is identity, not state."""
    from socrates.invocations import door

    _seed_need(tmp_path)
    payload = _call(door, tmp_path, {"activity": "satisfaction"})
    assert payload.get("refused") is True, payload
    assert "satisfaction" in payload["reason"], payload


def test_a_missing_door_activity_refuses_with_the_same_grammar(tmp_path):
    from socrates.invocations import door

    payload = _call(door, tmp_path, {})
    assert payload.get("refused") is True, payload
    assert payload["admissible_next"] == ACTIVITIES, payload


def test_a_valid_door_activity_still_asks(tmp_path):
    from socrates.invocations import door

    _seed_need(tmp_path)
    payload = _call(door, tmp_path, {"activity": "requirements"})
    assert payload.get("refused") is not True, payload
    assert payload["kind"] == "door", payload


# --- The materialization names the audit as what comes next -------------------------


def test_the_materialize_payload_names_the_audit(tmp_path):
    from socrates.invocations import materialize

    _seed_need(tmp_path)
    payload = _call(materialize, tmp_path)
    assert payload["ok"] is True, payload
    assert payload["admissible_next"] == ["audit_charge"], payload
    assert "audit" in payload["message"], payload


def test_the_satisfaction_affirmative_names_the_audit(tmp_path):
    from socrates.invocations import resume, satisfaction

    _seed_need(tmp_path)
    _call(satisfaction, tmp_path)
    payload = _call(
        resume, tmp_path, {"canonical": "satisfied", "raw": "fechado"}
    )
    assert payload["ok"] is True, payload
    assert payload["satisfied"] is True, payload
    assert payload["admissible_next"] == ["audit_charge"], payload
    assert "audit" in payload["message"], payload


# --- The skin declares the degradation -----------------------------------------------


def _skill_flat() -> str:
    skill = (
        Path(__file__).resolve().parent.parent
        / ".claude" / "skills" / "socrates" / "SKILL.md"
    )
    return " ".join(skill.read_text().split())


def test_the_fallback_is_declared_to_the_user_before_it_runs():
    flat = _skill_flat()
    assert "say so to the user before you run" in flat, (
        "the fallback would run in silence"
    )
    assert "weaker" in flat, "the weaker guarantee is unnamed"
