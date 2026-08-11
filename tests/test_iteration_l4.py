"""Orchestration test for ticket 07 — Iteration for L4 Conflicts.

Seam: session orchestration with the model provider stubbed.
Covers L4→Iteration (not Probe), most-upstream activity proposal from party
nature (activity tags), user confirmation, and re-running the reopened
activity against the current Model.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.paths import CONFLICTS_PATH, NEED_PATH, PIPELINE_PATH, PROPOSITIONS_PATH
from socrates.pipeline import ACTIVITIES_IN_ORDER


def _thread_config() -> dict:
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


def _tool_call(name: str, args: dict, call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": name,
                "args": args,
                "id": call_id,
                "type": "tool_call",
            }
        ],
    )


def _load_json(files: dict, path: str) -> dict:
    return json.loads(files[path]["content"])


def _activity_stub(*, propose_statement: str, label: str) -> StubChatModel:
    return StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": propose_statement},
                f"{label}-propose",
            ),
            _tool_call("complete_modeling_activity", {}, f"{label}-complete"),
            AIMessage(content=f"{label} activity complete."),
        ],
        label=label,
    )


def test_l4_iteration_proposes_upstream_confirms_and_reruns():
    need = "Marketplace checkout payments domain."
    req_statement = "Checkout must capture payment authorization."
    domain_statement = "A Payment belongs to exactly one Order."
    behavioral_statement = (
        "One Payment yields at least one Notification to the payer."
    )
    # After Iteration reopens Requirements, specialist revises against current Model.
    revised_req = "Checkout must capture authorization and capture."

    requirements_model = StubChatModel(
        responses=[
            # First pass
            _tool_call(
                "propose_proposition",
                {"statement": req_statement},
                "req-propose",
            ),
            _tool_call("complete_modeling_activity", {}, "req-complete"),
            AIMessage(content="req activity complete."),
            # Re-run after Iteration
            _tool_call(
                "propose_proposition",
                {"statement": revised_req},
                "req-revise",
            ),
            _tool_call("complete_modeling_activity", {}, "req-complete-2"),
            AIMessage(content="req activity re-run complete."),
        ],
        label="req",
    )
    domain_model = _activity_stub(
        propose_statement=domain_statement,
        label="dom",
    )
    behavioral_model = _activity_stub(
        propose_statement=behavioral_statement,
        label="beh",
    )

    main_model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "task",
                {
                    "subagent_type": "requirements",
                    "description": "Run Requirements.",
                },
                "task-req",
            ),
            _tool_call(
                "task",
                {
                    "subagent_type": "domain-modeling",
                    "description": "Run Domain Modeling.",
                },
                "task-dom",
            ),
            _tool_call(
                "task",
                {
                    "subagent_type": "behavioral-specification",
                    "description": "Run Behavioral Specification.",
                },
                "task-beh",
            ),
            # Accept Need-assumption (p1) and entity (p2) — mixed activities.
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "acc-p1"),
            _tool_call("accept_proposition", {"proposition_id": "p2"}, "acc-p2"),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(
                        [
                            {
                                "description": "Intersection of Need and ownership",
                                "edge": "intersection",
                                "need_relevant": True,
                            },
                            {
                                "description": "Authorization captured once",
                                "edge": "one",
                                "need_relevant": True,
                            },
                        ]
                    ),
                },
                "sc-l4",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p1",
                    "outcomes_json": json.dumps(
                        [
                            {
                                "scenario_id": "s1",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": (
                                    "Accepted Need-assumption clashes with "
                                    "Accepted ownership entity."
                                ),
                                "other_proposition_id": "p2",
                            },
                            {"scenario_id": "s2", "survives": True},
                        ]
                    ),
                },
                "assert-l4",
            ),
            # Probe must refuse L4-only work — Iteration handles it.
            _tool_call("probe_batch", {}, "probe-l4-only"),
            _tool_call("run_iteration", {"conflict_id": "c1"}, "iterate"),
            _tool_call(
                "task",
                {
                    "subagent_type": "requirements",
                    "description": "Re-run Requirements after Iteration.",
                },
                "task-req-rerun",
            ),
            AIMessage(content="Iteration complete."),
        ],
        label="main",
    )

    agent = create_socrates_session(
        model=main_model,
        activity_models={
            "requirements": requirements_model,
            "domain_modeling": domain_model,
            "behavioral_specification": behavioral_model,
        },
    )
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start")]},
        config=config,
    )
    assert opening["__interrupt__"][0].value["kind"] == "opening"

    r = agent.invoke(Command(resume=need), config=config)
    assert r["files"][NEED_PATH]["content"] == need
    # accept p1
    assert r["__interrupt__"][0].value["proposition_id"] == "p1"
    r = agent.invoke(Command(resume="yes"), config=config)
    # accept p2
    assert r["__interrupt__"][0].value["proposition_id"] == "p2"
    r = agent.invoke(Command(resume="yes"), config=config)

    pipeline_before = _load_json(r["files"], PIPELINE_PATH)
    assert pipeline_before["completed"] == list(ACTIVITIES_IN_ORDER)
    assert pipeline_before["active"] is None

    # probe_batch with only L4 open returns an error ToolMessage (not Probe).
    probe_err = [
        m
        for m in r["messages"]
        if isinstance(m, ToolMessage)
        and isinstance(m.content, str)
        and '"ok":false' in m.content.replace(" ", "")
        and "Iteration" in m.content
    ]
    assert probe_err

    conflicts = _load_json(r["files"], CONFLICTS_PATH)["conflicts"]
    assert len(conflicts) == 1
    assert conflicts[0]["level"] == "L4"
    assert conflicts[0]["status"] == "open"
    assert conflicts[0]["id"] == "c1"

    iteration = r["__interrupt__"][0].value
    assert iteration["kind"] == "iteration"
    assert iteration["conflict_id"] == "c1"
    # Most upstream of requirements × domain_modeling → requirements
    assert iteration["proposed_activity"] == "requirements"
    assert {p["activity"] for p in iteration["parties"]} == {
        "requirements",
        "domain_modeling",
    }

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    # Current Model still present; reopened activity re-ran and completed again.
    assert finished["files"][NEED_PATH]["content"] == need
    props = {
        p["statement"]: p
        for p in _load_json(finished["files"], PROPOSITIONS_PATH)["propositions"]
    }
    assert req_statement in props
    assert domain_statement in props
    assert behavioral_statement in props
    assert revised_req in props
    assert props[revised_req]["activity"] == "requirements"

    conflict = _load_json(finished["files"], CONFLICTS_PATH)["conflicts"][0]
    assert conflict["status"] == "resolved"
    assert conflict["resolution"]["action"] == "iterate"
    assert conflict["resolution"]["activity"] == "requirements"
    assert conflict["resolution"]["proposed_activity"] == "requirements"

    pipeline_after = _load_json(finished["files"], PIPELINE_PATH)
    # Re-run completed Requirements; Domain/Behavioral still need re-running.
    assert pipeline_after["completed"] == ["requirements"]
    assert pipeline_after["active"] is None

    tool_texts = [
        m.content
        for m in finished["messages"]
        if isinstance(m, ToolMessage) and isinstance(m.content, str)
    ]
    assert any("req activity re-run complete" in t for t in tool_texts)


def test_l4_iteration_proposes_domain_for_entity_vs_behavior():
    """Entity (domain) × behavior → most-upstream is Domain Modeling."""
    need = "Marketplace checkout payments domain."
    domain_statement = "Payment is a domain entity with a status."
    behavioral_statement = "Payment status transitions Authorized to Settled."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "propose_proposition",
                {"statement": domain_statement, "activity": "domain_modeling"},
                "prop-p1",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "acc-p1"),
            _tool_call(
                "propose_proposition",
                {
                    "statement": behavioral_statement,
                    "activity": "behavioral_specification",
                },
                "prop-p2",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p2"}, "acc-p2"),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(
                        [
                            {
                                "description": "Entity and behavior together",
                                "edge": "intersection",
                                "need_relevant": True,
                            },
                            {
                                "description": "Status edge",
                                "edge": "one",
                                "need_relevant": True,
                            },
                        ]
                    ),
                },
                "sc",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p1",
                    "outcomes_json": json.dumps(
                        [
                            {
                                "scenario_id": "s1",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "Accepted entity vs Accepted behavior.",
                                "other_proposition_id": "p2",
                            },
                            {"scenario_id": "s2", "survives": True},
                        ]
                    ),
                },
                "assert",
            ),
            _tool_call("run_iteration", {"conflict_id": "c1"}, "iterate"),
            AIMessage(content="done"),
        ]
    )
    agent = create_socrates_session(model=model)
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start")]},
        config=config,
    )
    r = agent.invoke(Command(resume=need), config=config)
    r = agent.invoke(Command(resume="yes"), config=config)
    r = agent.invoke(Command(resume="yes"), config=config)

    iteration = r["__interrupt__"][0].value
    assert iteration["kind"] == "iteration"
    assert iteration["proposed_activity"] == "domain_modeling"

    finished = agent.invoke(
        Command(resume={"activity": "domain_modeling"}),
        config=config,
    )
    assert finished.get("__interrupt__") is None
    pipeline = _load_json(finished["files"], PIPELINE_PATH)
    assert pipeline["active"] == "domain_modeling"
    assert pipeline["completed"] == ["requirements"]
