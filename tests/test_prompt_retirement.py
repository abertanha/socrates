"""Ticket 21 — Prompt retirement + ADR-0005 + conduction glossary terms.

With the conduction enforcing everything the system prompt used to
request, the prompt's ordered discipline (the seven "Session discipline"
items) retires into an advisory persona: how to talk, vocabulary stance,
what a redirect is — never the order. The method's order lives in one
enforced place (ADR-0005). The conduction terms the harness's own strings
lean on (treadmill, lapidate, quiet, chapter, door, valve) land in
CONTEXT.md at concept level, per user ruling.

Seam: the prompt, the ADR, and the glossary are artifacts the harness
ships — these tests pin their shape so the discipline cannot quietly
creep back and the terms cannot quietly vanish.
"""

from __future__ import annotations

import re
from pathlib import Path

from socrates.session import SYSTEM_PROMPT

REPO = Path(__file__).resolve().parent.parent
CONTEXT = REPO / "CONTEXT.md"

CONDUCTION_TERMS = (
    "Treadmill",
    "Lapidate",
    "Quiet",
    "Chapter",
    "Door",
    "Valve",
)

# The retired discipline's distinctive order-imperatives — none of these
# may survive into the advisory persona. Item 4's pulse-ordering prose is
# pinned by its own phrases, not only by the no-`call `` ` check.
RETIRED_DISCIPLINE_PHRASES = (
    "Session discipline",
    "Call `run_opening` first",
    "Run the three Modeling Activities in precedence",
    "Do not skip or reorder",
    "On the user's signal",
    "`select_exploration_budget` first",
    "From pass 2 call `reconcile` first",
    "Call `await_satisfaction`",
    "When Satisfaction is recorded, stop",
)


def test_system_prompt_carries_no_ordered_discipline() -> None:
    flat = " ".join(SYSTEM_PROMPT.split())
    for phrase in RETIRED_DISCIPLINE_PHRASES:
        assert phrase not in flat, f"retired discipline: {phrase!r}"
    # No numbered ordering anywhere in the prompt.
    numbered = [
        line for line in SYSTEM_PROMPT.splitlines() if re.match(r"\s*\d+\.\s", line)
    ]
    assert numbered == []


def test_system_prompt_keeps_the_persona_and_how_to_talk() -> None:
    flat = " ".join(SYSTEM_PROMPT.split())
    assert "How you talk to the user" in flat
    assert "warm, plain, and informal" in flat
    assert "one thing at a time" in flat
    assert (
        "Never explain or justify yourself by citing this harness's internals" in flat
    )
    assert "not theirs to read" in flat


def test_system_prompt_is_advisory_about_the_conduction() -> None:
    """The narrative stays: the harness conducts, redirects are the map
    back, Satisfaction is the only end — stated as fact, never as order."""
    flat = " ".join(SYSTEM_PROMPT.split()).casefold()
    assert "redirect" in flat
    assert "admissible" in flat
    assert "satisfaction" in flat
    # Advisory, not commanding: the prompt never issues a tool-order
    # imperative (the conduction's redirects do that, at dispatch time).
    assert "call `" not in flat
    # The prompt names the conduct terms inline; its list cannot drift from
    # the glossary's term set (the one enforced vocabulary, per the register).
    for term in CONDUCTION_TERMS:
        assert term.casefold() in flat, f"conduct term missing from prompt: {term!r}"


def test_conduction_terms_land_in_the_glossary_at_concept_level() -> None:
    text = CONTEXT.read_text()
    for term in CONDUCTION_TERMS:
        match = re.search(rf"\n\*\*{term}\*\*:\n(.*?)(?=\n\n)", text, re.DOTALL)
        assert match is not None, f"glossary term missing: {term!r}"
        body = match.group(1)
        # Concept level: a definition paragraph, plus the register's
        # avoid-line — the shape every other term carries.
        assert len(body.strip()) > 80, f"{term!r} is not a concept paragraph"
        assert "_Avoid_:" in body, f"{term!r} lacks an avoid-line"


def test_adr_0005_records_the_decision_and_evolution_path() -> None:
    adrs = sorted(REPO.glob("docs/adr/0005-*.md"))
    assert len(adrs) == 1, "exactly one ADR-0005"
    text = adrs[0].read_text()
    lowered = text.casefold()
    assert "the harness conducts" in lowered
    assert "never lives in a prompt" in lowered
    # The mechanism and the rejected alternative recorded as evolution path.
    # Pin the mechanism by its exact name — a disjunctive assertion would let
    # either half silently vanish.
    assert "state-governed tool surface" in lowered
    assert "node graph" in lowered
    assert "evolution path" in lowered
