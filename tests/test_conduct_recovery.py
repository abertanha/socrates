"""Ticket 06 (socrates-seam) — conduct and recovery rules.

The conductor's remaining disciplines — the ones the writing-to-agents
evaluation flagged and the specimens bore out — become pinned conduct
instead of good intentions. A real engine error that is not a structured
refusal STOPS the conductor: re-run the reads, tell the user in plain
language, never improvise state surgery; unreadable state is said to be
unreadable. The ask-never-guess loop gains its exit: after two failed
re-presentations the question is reformulated as one open question —
still not a guess, still not a menu. The session's language follows the
user from the moment they switch. A conductor returning from a
summarized context re-runs the reads before the next verb (the third
specimen reused a stale charge through a compaction boundary —
re-anchoring becomes mandatory instead of lucky). And each chapter
boundary carries a brief orientation in the domain's own terms — the
user-facing half of "etapas não são claras", no machinery vocabulary in
it.

Seam: the skill artifact, pinned the established way. Prior art: the v3
skin pin file and the session-anchor pin file.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "socrates" / "SKILL.md"


def _skill() -> str:
    return SKILL.read_text()


def _flat() -> str:
    return " ".join(_skill().split())


def _head_flat() -> str:
    text = _skill()
    return " ".join(text[: text.index("### The deliverable audit")].split())


def _paragraph_of(phrase: str) -> str:
    """The raw paragraph holding a phrase — for scans scoped to one site."""
    for para in _skill().split("\n\n"):
        if phrase in " ".join(para.split()):
            return " ".join(para.split())
    raise AssertionError(f"no paragraph holds the phrase: {phrase!r}")


# --- Real failures stop the conductor ----------------------------------------------


def test_a_real_failure_stops_the_conductor():
    flat = _head_flat()
    assert "A failure that is not a structured refusal stops you" in flat, (
        "the error path is untaught"
    )
    assert "re-run the reads" in flat, "recovery ignores the reads"
    assert "tell the user in plain language what failed" in flat, (
        "the failure would stay silent"
    )
    assert "never improvise state surgery" in flat, (
        "the surgery door is open"
    )
    assert "never press on as if nothing happened" in flat, (
        "the failure can be steamrolled"
    )


def test_unreadable_state_is_said_to_be_unreadable():
    flat = _head_flat()
    assert "say it is unreadable" in flat, "the unreadable would be glossed"
    assert "you do not repair it by hand" in flat, (
        "the hand-repair door is open"
    )


# --- The re-ask loop gains its exit --------------------------------------------------


def test_the_re_ask_loop_gains_its_exit():
    flat = _head_flat()
    assert "asked twice and still unresolved" in flat, (
        "the loop has no exit condition"
    )
    assert "one open question" in flat, "the exit is not an open question"
    assert "Still never a guess" in flat, "the exit could become a guess"
    assert "still never a menu" in flat, "the exit could become a menu"


# --- The language follows the user ----------------------------------------------------


def test_the_language_follows_the_user_when_they_switch():
    flat = _head_flat()
    assert "If the user switches mid-session" in flat, (
        "the switch case is untaught"
    )
    assert "the session's language follows them" in flat, (
        "the amendment path is missing"
    )
    assert "every rendering switches with them" in flat, (
        "the rendering duty does not follow the switch"
    )


# --- Post-compaction re-anchoring is mandatory -----------------------------------------


def test_a_summarized_context_re_runs_the_reads():
    flat = _head_flat()
    assert "return from a summarized context" in flat, (
        "the compaction boundary is unnamed"
    )
    assert "re-run the reads before your next verb" in flat, (
        "re-anchoring is optional"
    )
    assert "never from memory of them" in flat, (
        "the stale-charge door is open"
    )


# --- Chapter boundaries orient, in the domain's terms -----------------------------------


def test_the_chapter_boundary_orients_in_domain_terms():
    flat = _head_flat()
    assert "orient the user briefly" in flat, "the orientation duty is missing"
    assert "what this stretch of the conversation is for" in flat, (
        "the orientation's content is untaught"
    )
    assert "no method vocabulary" in flat, "the leak guard is unstated"


def test_the_orientation_paragraph_carries_no_machinery_vocabulary():
    para = _paragraph_of("orient the user briefly")
    for noun in (
        "Proposition",
        "Conflict",
        "Batch",
        "door",
        "Door",
        "treadmill",
        "Treadmill",
        "quiet",
        "lapidat",
        "Coverage",
        "pipeline",
    ):
        assert noun not in para, f"machinery vocabulary in the orientation: {noun!r}"


# --- The scans still hold ---------------------------------------------------------------


def test_no_runtime_mechanism_is_named_in_the_new_rules():
    flat = _flat().casefold()
    for named in ("python", "bash", "shell", "console", "uvx", "terminal"):
        assert named not in flat, f"a runtime mechanism is named: {named!r}"
    import re

    assert re.search(r"\bcli\b", flat) is None, "a runtime mechanism is named: CLI"
