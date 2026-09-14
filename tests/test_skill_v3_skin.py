"""Ticket 30 — the skill rewrites as the conductor's skin over the engine.

The v2 skill carried the method's order as prose and asked the model to
hold it; the hybrid moves that order into the engine's refusals. The
skill's remaining job is threefold: open with the bootstrap gate (no
engine, no Socrates), teach when to invoke which verb (runtime-
agnostically, naming no mechanism), and carry the talking rules — now
including the language boundary (session language declared at the
Opening, payloads rendered in it, replies classified to canonical
tokens with the raw words preserved) and the ask-never-guess rule
between close and satisfaction. An ADR records the identity ruling.

Seam: the skill artifact and the ADR, pinned the established way — one
read, many small assertions, flattened-whitespace phrase checks — so
the gate cannot quietly vanish, the ordering prose cannot quietly creep
back, and the mechanism phrasing cannot quietly name a runtime.
"""

from __future__ import annotations

import re
from pathlib import Path

from socrates.invocations import INVOCATIONS

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "socrates" / "SKILL.md"
ADR = REPO / "docs" / "adr" / "0006-skill-conducts-engine-enforces.md"


def _skill() -> str:
    return SKILL.read_text()


def _flat() -> str:
    return " ".join(_skill().split())


def _head() -> str:
    """The skill up to the audit section — the skin the conductor lives
    in (the audit section has its own pin suite, which this rewrite
    keeps green verbatim)."""
    text = _skill()
    return text[: text.index("### The deliverable audit")]


def _head_flat() -> str:
    return " ".join(_head().split())


# --- The bootstrap gate --------------------------------------------------------


def test_the_bootstrap_gate_opens_the_skill() -> None:
    flat = _head_flat()
    assert "bootstrap gate" in flat, "the gate is missing"
    # The check is real: the engine imports from the skill's clone,
    # through the harness's own code execution.
    assert "code execution" in flat, "the check is not the harness's own"
    assert "importable" in flat, "the gate does not state what it verifies"
    assert "src" in flat, "the engine's location in the clone is unnamed"
    assert "socrates" in flat, "the engine package is unnamed"
    # Failure is refusal, with the way out printed.
    assert "no engine, no Socrates" in flat, "the gate has no teeth"
    assert "refuses to conduct" in flat, "the gate does not refuse"
    assert "installation steps" in flat, "the way out is missing"


def test_the_installation_steps_are_actionable_without_a_runtime() -> None:
    flat = _head_flat()
    assert "pyproject.toml" in flat, "the install source is unnamed"
    assert "import path" in flat, "no runtime-agnostic way in is offered"
    assert "gate" in flat, "the steps do not return to the gate"


# --- No runtime mechanism named, anywhere ---------------------------------------


def test_no_runtime_mechanism_is_named_anywhere() -> None:
    flat = " ".join(_skill().split()).casefold()
    for named in (
        "python",
        "bash",
        "shell",
        "mcp",
        "command line",
        "console-script",
        "curl",
        "http",
        "pip ",
        "pip.",
        "uvx",
        "terminal",
    ):
        assert named not in flat, f"a runtime mechanism is named: {named!r}"
    assert re.search(r"\bcli\b", flat) is None, "a runtime mechanism is named: CLI"


# --- The verb surface is taught, by name -----------------------------------------


def test_every_verb_the_engine_exposes_is_taught() -> None:
    flat = _flat()
    for verb in INVOCATIONS:
        assert verb in flat, f"the verb is not taught: {verb}"


def test_the_resume_is_one_verb_for_every_kind() -> None:
    flat = _head_flat()
    assert "one resume verb" in flat, "the resume splinters by kind"
    assert "canonical" in flat and "raw" in flat, (
        "the resume contract is not taught"
    )


def test_a_pending_question_is_data_the_conductor_renders() -> None:
    flat = _head_flat()
    assert "pending" in flat, "the pending-question cycle is untaught"
    assert "accepted answers" in flat, "the menu is not rendered faithfully"
    assert "meanings" in flat, "the answers' meanings are not taught"


# --- The language boundary --------------------------------------------------------


def test_the_language_boundary_is_taught() -> None:
    flat = _head_flat()
    assert "declared once at the Opening" in flat, (
        "the session language is not declared"
    )
    assert "session's language" in flat, "rendering has no target language"
    assert "classified into a canonical token" in flat, (
        "the classification duty is missing"
    )
    assert "provenance" in flat, "the raw words are not preserved"
    # The enums stay closed; the conductor is the only boundary.
    assert "only language boundary" in flat, "the boundary is not exclusive"


def test_ask_never_guess_between_close_and_satisfaction() -> None:
    flat = _head_flat()
    assert "ask, never guess" in flat, "the ambiguity rule is unstated"


def test_the_opening_is_the_engines_not_the_conductors() -> None:
    flat = _head_flat()
    assert "never improvise the opening" in flat, (
        "the conductor may author the greeting again"
    )


# --- Refusals are repaired, never argued with --------------------------------------


def test_refusals_are_information_the_conductor_repairs() -> None:
    flat = _head_flat()
    assert "refusal" in flat, "refusals are untaught"
    assert "admissible next verbs" in flat, "the refusal's payload is untaught"
    assert "never argue" in flat, "the repair stance is unstated"
    assert "never improvise around" in flat, "the workaround door is open"


# --- Ordering prose retired by omission ---------------------------------------------


RETIRED_ORDERING_PHRASES = (
    "The session's order",
    "in strict precedence",
    "Propose → lapidate → resolve",
    "reconcile first",
    "Reconcile first",
    "Do not pile a new pass",
    "at most one unlapidated",
    "reopens the walk",
    "No Proposition may be proposed before the Need exists",
    "don't skip or reorder",
    "Don't propose before the Need exists",
    "If you ever notice you have drifted out of order",
)


def test_ordering_prose_is_retired_by_omission() -> None:
    flat = _flat()
    for phrase in RETIRED_ORDERING_PHRASES:
        assert phrase not in flat, f"ordering prose survived: {phrase!r}"
    # No numbered walk anywhere — the method's order is not a list in
    # this file anymore.
    numbered = [
        line for line in _skill().splitlines() if re.match(r"\s*\d+\.\s", line)
    ]
    assert numbered == []


def test_the_engine_holds_the_order_and_the_skill_says_so() -> None:
    flat = _head_flat()
    assert "engine" in flat, "the engine is unmentioned"
    assert "refuses" in flat, "enforcement-by-refusal is unstated"


# --- The conductor never touches the state files -------------------------------------


def test_the_conductor_never_edits_the_session_files() -> None:
    flat = _head_flat()
    assert "never edit" in flat, "the conductor may hand-edit state"
    assert "engine writes" in flat, "atomic authorship is unattributed"
    assert ".socrates/" in flat, "the session's location on disk is unnamed"


def test_a_resume_reconstructs_through_the_reads_never_a_regreeting() -> None:
    flat = _head_flat()
    assert "never re-greet" in flat, "a resumed session greets again"
    assert "pending_question" in flat, "reconstruction ignores the pending cue"


# --- The ADR of the identity ruling ---------------------------------------------------


def test_the_identity_adr_exists_and_is_linked() -> None:
    assert ADR.exists(), "the identity ruling has no ADR"
    assert "docs/adr/0006" in _skill(), "the skill does not link the ADR"
    adr = " ".join(ADR.read_text().split())
    for phrase in (
        "skill-conducted",
        "engine-enforced",
        "host loop",
        "no CLI",
        "AskHuman",
        "the engine lives in the skill's clone",
    ):
        assert phrase.casefold() in adr.casefold(), f"ADR misses: {phrase!r}"
