"""Orchestration test for ticket 01 — walking skeleton.

Seam: session orchestration with the model provider stubbed.
Asserts Opening interrupt, Need FS persistence (ADR-0001), and
Satisfaction-terminated session (ADR-0002). Tickets 17/20 made the
minimum legal path the conducted one: the three chapter doors close
before the tail's Satisfaction — the session's only sink.
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


def _tool_call(name: str, call_id: str, args: dict | None = None) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {"name": name, "args": args or {}, "id": call_id, "type": "tool_call"}
        ],
    )


def _task_call(subagent_type: str, call_id: str) -> AIMessage:
    return _tool_call(
        "task",
        call_id,
        {"subagent_type": subagent_type, "description": subagent_type.title()},
    )


def _door_only_specialist(label: str) -> StubChatModel:
    """A chapter specialist that walks straight to its door (vacuous)."""
    return StubChatModel(
        responses=[_tool_call("complete_modeling_activity", f"{label}-door")],
        label=label,
    )


def _scripted_skeleton_model() -> StubChatModel:
    return StubChatModel(
        responses=[
            _tool_call("run_opening", "call-opening"),
            _task_call("requirements", "call-task-req"),
            _task_call("domain-modeling", "call-task-dom"),
            _task_call("behavioral-specification", "call-task-beh"),
            _tool_call("await_satisfaction", "call-satisfaction"),
            AIMessage(content="Mapping ended at user Satisfaction."),
        ]
    )


def test_walking_skeleton_opening_need_satisfaction_persists_need():
    need = "Marketplace checkout payments domain."
    agent = create_socrates_session(
        model=_scripted_skeleton_model(),
        activity_models={
            "requirements": _door_only_specialist("req"),
            "domain_modeling": _door_only_specialist("dom"),
            "behavioral_specification": _door_only_specialist("beh"),
        },
    )
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
    # The three chapter doors, each closed by the user.
    r = after_need
    for _ in range(3):
        assert r["__interrupt__"][0].value["kind"] == "door"
        r = agent.invoke(Command(resume="close"), config=config)

    assert "__interrupt__" in r
    satisfaction_interrupt = r["__interrupt__"][0].value
    assert satisfaction_interrupt["kind"] == "satisfaction"
    assert satisfaction_interrupt["question"] == SATISFACTION_QUESTION

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()
    assert finished["files"][NEED_PATH]["content"] == need
