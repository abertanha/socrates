"""User-facing Opening presentation: greeting and first question.

The greeting invites the developer to answer in their own words — the harness's
own vocabulary and design rationale stay out of what the user reads.
"""

from __future__ import annotations

OPENING_GREETING = (
    "Hey — I'm Socrates.\n"
    "The way I work is simple: I ask, you answer, and we keep at it until the "
    "picture of what you're building actually holds up. You decide what stays "
    "in and what goes.\n\n"
    "Nothing formal needed here. Answer in your own words, think out loud, "
    'and just say "I don\'t know" whenever that\'s the honest answer — that\'s '
    "usually the interesting part anyway."
)

OPENING_QUESTION = "So, what are you building — and what should it make possible?"


def render_opening() -> str:
    """Compose the Opening as the user sees it: greeting, then question."""
    return f"{OPENING_GREETING}\n\n{OPENING_QUESTION}"
