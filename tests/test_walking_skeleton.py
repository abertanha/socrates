"""Orchestration test for ticket 01 — walking skeleton.

Seam: session orchestration with the model provider stubbed.
Asserts Opening interrupt, Need FS persistence (ADR-0001), and
Satisfaction-terminated session (ADR-0002).
"""

from __future__ import annotations

import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.paths import NEED_PATH
from socrates.tools import OPENING_QUESTION, SATISFACTION_QUESTION


def _thread_config() -> dict:
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


def _scripted_skeleton_model() -> StubChatModel:
    return StubChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "run_opening",
                        "args": {},
                        "id": "call-opening",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "await_satisfaction",
                        "args": {},
                        "id": "call-satisfaction",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Mapping ended at user Satisfaction."),
        ]
    )


def test_walking_skeleton_opening_need_satisfaction_persists_need():
    need = "Marketplace checkout payments domain."
    agent = create_socrates_session(model=_scripted_skeleton_model())
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start a modeling session.")]},
        config=config,
    )
    assert "__interrupt__" in opening
    opening_interrupt = opening["__interrupt__"][0].value
    assert opening_interrupt["kind"] == "opening"
    assert opening_interrupt["question"] == OPENING_QUESTION

    after_need = agent.invoke(Command(resume=need), config=config)
    assert after_need["files"][NEED_PATH]["content"] == need
    assert "__interrupt__" in after_need
    satisfaction_interrupt = after_need["__interrupt__"][0].value
    assert satisfaction_interrupt["kind"] == "satisfaction"
    assert satisfaction_interrupt["question"] == SATISFACTION_QUESTION

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()
    assert finished["files"][NEED_PATH]["content"] == need
