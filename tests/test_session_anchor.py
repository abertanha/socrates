"""Ticket 04 (socrates-seam) — the session's anchor.

The session stopped living where the conductor happened to be, and the
first question stopped costing 35k tokens. Three duties join the skin:
BEFORE the first verb the conductor establishes with the user where the
session's directory lives (the working directory's ``.socrates/`` is the
offered default, never a silent choice — the fifth specimen's Model
landed in the user's home because nobody asked); every invocation then
passes that same root (the standing rule gains its missing first half);
and absent state at the expected root is a question — resume elsewhere,
or start fresh — never a silent re-greet. The skin also teaches the
invocation recipe it used to make the conductor discover by spelunking
engine source: each verb file is a program, executed with the session
root and the JSON payload as its arguments — runtime unnamed, no console
command invented, transport unchanged.

Seam: the skill artifact, pinned the established way — one read, many
small flattened-phrase assertions, mechanism scans. Prior art: the v3
skin pin file.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "socrates" / "SKILL.md"


def _flat() -> str:
    return " ".join(SKILL.read_text().split())


def _head_flat() -> str:
    text = SKILL.read_text()
    return " ".join(text[: text.index("### The deliverable audit")].split())


# --- The root is established, never assumed ----------------------------------------


def test_the_root_is_established_with_the_user_before_the_first_verb():
    flat = _head_flat()
    assert "establish with the user where this session's directory lives" in flat, (
        "the root is never agreed with the user"
    )
    assert "Before the session's first verb" in flat, (
        "the establishment has no moment"
    )
    assert "the default you offer" in flat, (
        "the working directory's convention is not an offer"
    )
    assert "never a choice you make silently" in flat, (
        "the silent choice that landed a Model in HOME is still available"
    )


def test_the_establishment_and_the_same_root_rule_pin_as_one_conduct():
    flat = _head_flat()
    assert "every invocation of the session passes that same root" in flat, (
        "the establishment does not feed the standing same-root rule"
    )


# --- Absent state is a question, never a re-greet -----------------------------------


def test_absent_state_at_the_expected_root_is_a_question():
    flat = _head_flat()
    assert "holds no session state" in flat, "the missing-state case is unnamed"
    assert "that absence is itself a question" in flat, (
        "the absence is not a question"
    )
    assert "never a silent re-greet" in flat, "the re-greet door is still open"
    assert "never an improvised new session" in flat, (
        "the improvised-session door is still open"
    )


# --- The invocation recipe is taught, not discovered ---------------------------------


def test_the_recipe_teaches_verb_files_are_programs():
    flat = _head_flat()
    assert "each file is a program" in flat, "the recipe's shape is untaught"
    assert "the JSON payload as its further argument" in flat, (
        "the recipe's arguments are untaught"
    )
    assert "--root" in flat, "the root argument is unnamed"
    assert "you never read the engine's source" in flat, (
        "the spelunking door is still open"
    )


def test_the_recipe_names_no_runtime_and_invents_no_console_command():
    flat = _flat().casefold()
    for named in ("python", "bash", "shell", "console", "uvx", "terminal"):
        assert named not in flat, f"a runtime mechanism is named: {named!r}"
    assert re.search(r"\bcli\b", flat) is None, "a runtime mechanism is named: CLI"
