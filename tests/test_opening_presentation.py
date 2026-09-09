"""Orchestration test for the Opening presentation.

Seam: session orchestration with the model provider stubbed.
Asserts the greeting invites the developer informally and that the
greeting precedes the question that hands the floor over, and that none of
the harness's internals reach what the user reads.
"""

from __future__ import annotations

import uuid

from deepagents.backends import StateBackend
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.opening import (
    OPENING_GREETING,
    OPENING_QUESTION,
    render_opening,
)
from socrates.paths import NEED_PATH
from socrates.tools import build_session_tools

# Harness-internal vocabulary and rationale the user must never be shown.
INTERNAL_LEAKS = (
    "ADR",
    "Proposition",
    "Modeling Activity",
    "Conflict",
    "Coverage",
    "recursion_limit",
    "deepagents",
    "virtual filesystem",
)


def _thread_config() -> dict:
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


def _tool_call(name: str, call_id: str) -> dict:
    return {"name": name, "args": {}, "id": call_id, "type": "tool_call"}


def _scripted_model() -> StubChatModel:
    return StubChatModel(
        responses=[
            AIMessage(content="", tool_calls=[_tool_call("run_opening", "open")]),
            AIMessage(
                content="",
                tool_calls=[_tool_call("await_satisfaction", "satisfy")],
            ),
            AIMessage(content="Ended at the user's own signal."),
        ]
    )


def test_opening_presents_greeting_then_question():
    need = "A tool that tells me which of my cron jobs actually still matter."
    agent = create_socrates_session(model=_scripted_model(), reinjection_limit=0)  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start a modeling session.")]},
        config=config,
    )
    payload = opening["__interrupt__"][0].value
    assert payload["kind"] == "opening"

    # The Opening survives the round trip through the graph: greeting first,
    # then the question that hands the floor over.
    display = payload["display"]
    assert display == render_opening()
    assert display.index(OPENING_GREETING) < display.index(OPENING_QUESTION)
    assert payload["greeting"] == OPENING_GREETING
    assert payload["question"] == OPENING_QUESTION

    # Informal and inviting: first-person, addressed to the user, one question.
    assert "I'm Socrates" in OPENING_GREETING
    assert "your own words" in OPENING_GREETING
    assert OPENING_QUESTION.endswith("?")
    assert OPENING_QUESTION.count("?") == 1

    after_need = agent.invoke(Command(resume=need), config=config)
    assert after_need["files"][NEED_PATH]["content"] == need


def test_opening_and_tool_descriptions_cite_no_harness_internals():
    opening_text = render_opening()
    for leak in INTERNAL_LEAKS:
        assert leak not in opening_text, f"Opening leaks {leak!r} to the user"

    # Tool descriptions are model-visible, so rationale left in them comes back
    # out as justification to the user.
    descriptions = "\n".join(
        tool.description for tool in build_session_tools(StateBackend())
    )
    assert "ADR" not in descriptions
    assert "#1698" not in descriptions
