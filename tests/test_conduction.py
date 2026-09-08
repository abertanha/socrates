"""Ticket 13 — Conduction core: derived state → availability → redirect.

Seam: the pure availability rule tested directly (facts in → redirect or
admission), plus the declared orchestration seam (StubChatModel session)
asserting the redirect payloads the model would actually see — the Need
gate, `run_opening` once, and wrong-chapter `task` attempts.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.conduction import ConductionState, conduction_check
from socrates.paths import PIPELINE_PATH


def _thread_config() -> dict:
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


def _tool_call(name: str, args: dict, call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}],
    )


def _tool_result(messages: list, call_id: str) -> dict:
    for m in messages:
        if isinstance(m, ToolMessage) and m.tool_call_id == call_id:
            return json.loads(m.content)
    raise AssertionError(f"no ToolMessage with id {call_id}")


# ---------------------------------------------------------------- pure rule


def test_pre_opening_admits_only_the_opening() -> None:
    state = ConductionState(
        need_registered=False, active=None, completed=()
    )
    assert conduction_check(state, "run_opening", {}) is None
    for tool in (
        "propose_proposition",
        "accept_proposition",
        "reconcile",
        "probe_batch",
        "select_exploration_budget",
        "await_satisfaction",
        "task",
    ):
        redirect = conduction_check(state, tool, {})
        assert redirect is not None, tool
        assert redirect["ok"] is False
        assert redirect["conduction"]["state"] == "pre-opening"
        assert "run_opening" in redirect["conduction"]["admissible_next"]


def test_task_is_gated_pre_opening_too() -> None:
    state = ConductionState(
        need_registered=False, active=None, completed=()
    )
    redirect = conduction_check(
        state, "task", {"subagent_type": "requirements"}
    )
    assert redirect is not None
    assert redirect["conduction"]["state"] == "pre-opening"


def test_opening_runs_once_only() -> None:
    state = ConductionState(
        need_registered=True, active=None, completed=()
    )
    redirect = conduction_check(state, "run_opening", {})
    assert redirect is not None
    assert redirect["ok"] is False
    assert redirect["conduction"]["state"] == "between-chapters"
    assert "task: requirements" in redirect["conduction"]["admissible_next"]


def test_task_admits_only_the_expected_chapter() -> None:
    fresh = ConductionState(
        need_registered=True, active=None, completed=()
    )
    assert conduction_check(fresh, "task", {"subagent_type": "requirements"}) is None
    redirect = conduction_check(
        fresh, "task", {"subagent_type": "behavioral-specification"}
    )
    assert redirect is not None
    assert redirect["conduction"]["attempted"] == "task(behavioral-specification)"
    assert redirect["conduction"]["admissible_next"] == ["task: requirements"]

    mid = ConductionState(
        need_registered=True,
        active="domain_modeling",
        completed=("requirements",),
    )
    assert conduction_check(mid, "task", {"subagent_type": "domain-modeling"}) is None
    # A completed chapter is never re-enterable by task.
    assert conduction_check(mid, "task", {"subagent_type": "requirements"}) is not None


def test_tail_admits_no_chapter_tasks() -> None:
    state = ConductionState(
        need_registered=True,
        active=None,
        completed=(
            "requirements",
            "domain_modeling",
            "behavioral_specification",
        ),
    )
    assert state.label == "tail"
    for subagent in ("requirements", "domain-modeling", "behavioral-specification"):
        assert conduction_check(state, "task", {"subagent_type": subagent}) is not None
    # In-state calls stay admitted — this ticket changes no other behavior.
    assert conduction_check(state, "await_satisfaction", {}) is None
    assert conduction_check(state, "probe_batch", {}) is None


def test_check_is_deterministic() -> None:
    state = ConductionState(
        need_registered=False, active=None, completed=()
    )
    first = conduction_check(state, "probe_batch", {})
    second = conduction_check(state, "probe_batch", {})
    assert first == second


# ---------------------------------------------------------- orchestration


def test_need_gate_redirects_before_opening_and_admits_after() -> None:
    model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Premature.", "activity": "domain_modeling"},
                "bad-propose",
            ),
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "propose_proposition",
                {"statement": "Scoped.", "activity": "requirements"},
                "ok-propose",
            ),
            AIMessage(content="Proceeding with requirements."),
        ],
        label="main",
    )
    agent = create_socrates_session(model=model)
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"

    # The premature proposal was redirected with the pre-Opening state.
    redirected = _tool_result(r["messages"], "bad-propose")
    assert redirected["ok"] is False
    assert redirected["conduction"]["state"] == "pre-opening"
    assert redirected["conduction"]["attempted"] == "propose_proposition"
    assert "run_opening" in redirected["conduction"]["admissible_next"]

    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    assert r.get("__interrupt__") is None

    # Same tool, now in-state: no conduction payload, normal behavior.
    payload = _tool_result(r["messages"], "ok-propose")
    assert payload["ok"] is True
    assert "conduction" not in payload


def test_opening_once_and_wrong_chapter_task_redirect() -> None:
    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must capture payment authorization."},
                "req-propose",
            ),
            _tool_call("complete_modeling_activity", {}, "req-complete"),
            AIMessage(content="req activity complete."),
        ],
        label="req",
    )
    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call("run_opening", {}, "reopen"),
            _tool_call(
                "task",
                {
                    "subagent_type": "behavioral-specification",
                    "description": "Skip ahead.",
                },
                "wrong-task",
            ),
            _tool_call(
                "task",
                {"subagent_type": "requirements", "description": "Run it."},
                "right-task",
            ),
            AIMessage(content="Chapter one under way."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        model=model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(
        Command(resume="A marketplace checkout."), config=config
    )
    assert r.get("__interrupt__") is None

    # run_opening is done exactly once.
    reopened = _tool_result(r["messages"], "reopen")
    assert reopened["ok"] is False
    assert reopened["conduction"]["state"] == "between-chapters"
    assert "task: requirements" in reopened["conduction"]["admissible_next"]

    # Wrong-chapter task redirected, naming the expected chapter.
    wrong = _tool_result(r["messages"], "wrong-task")
    assert wrong["ok"] is False
    assert wrong["conduction"]["attempted"] == "task(behavioral-specification)"
    assert wrong["conduction"]["admissible_next"] == ["task: requirements"]

    # The behavioral chapter never ran; the requirements chapter did.
    task_results = [
        m
        for m in r["messages"]
        if isinstance(m, ToolMessage) and m.tool_call_id == "right-task"
    ]
    assert task_results and "req activity complete." in task_results[0].content

    pipeline = json.loads(r["files"][PIPELINE_PATH]["content"])
    assert pipeline["completed"] == ["requirements"]
    assert pipeline["active"] is None
