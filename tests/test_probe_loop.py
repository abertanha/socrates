"""Orchestration test for ticket 04 — Probe loop.

Seam: session orchestration with the model provider stubbed (ticket 14
shape: the three chapters run first via `task`, so the Probe saga lives in
the tail, where the orchestrator keeps the pulse). Covers Need-relevant
Scenarios (several per Proposition), Assertion Tests surfacing Conflicts,
Batch presentation, and interrupt-gated Probe resolution that updates the
Model.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.inference import MIN_SCENARIOS_PER_PROPOSITION
from socrates.paths import (
    BATCHES_PATH,
    CONFLICTS_PATH,
    NEED_PATH,
    PROPOSITIONS_PATH,
    SCENARIOS_PATH,
)


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


def _chapter_close_stub(label: str) -> StubChatModel:
    """A specialist that declares its chapter complete — no ground born."""
    return StubChatModel(
        responses=[
            _tool_call("complete_modeling_activity", {}, f"{label}-complete"),
            AIMessage(content=f"{label} activity complete."),
        ],
        label=label,
    )


def _three_chapter_walk() -> list[AIMessage]:
    """Walk the three chapters so the orchestrator reaches the tail."""
    return [
        _tool_call(
            "task",
            {"subagent_type": "requirements", "description": "Run Requirements."},
            "task-req",
        ),
        _tool_call(
            "task",
            {"subagent_type": "domain-modeling", "description": "Run Structure."},
            "task-dom",
        ),
        _tool_call(
            "task",
            {
                "subagent_type": "behavioral-specification",
                "description": "Run Rules.",
            },
            "task-beh",
        ),
    ]


def _close_three_doors(agent, config, state) -> dict:
    """Resume the three chapter doors with "close" — the tail opens (17)."""
    for activity in ("requirements", "domain_modeling", "behavioral_specification"):
        door = state["__interrupt__"][0].value
        assert door["kind"] == "door"
        assert door["activity"] == activity
        state = agent.invoke(Command(resume="close"), config=config)
    return state


def test_probe_loop_scenarios_assertion_batch_and_model_update():
    need = "Marketplace checkout payments domain."
    p1_statement = "A Payment belongs to exactly one Order."
    p2_statement = "Payment status is always Authorized or Settled."
    revised_p1 = "A Payment belongs to exactly one Order, or to a refunded Order."
    new_ground = "A Payment may be Void before settlement."

    p1_scenarios = [
        {
            "description": "Zero payments on an open Order",
            "edge": "zero",
            "need_relevant": True,
        },
        {
            "description": "One Payment settles one Order",
            "edge": "one",
            "need_relevant": True,
        },
        {
            "description": "Many partial Payments against one Order",
            "edge": "many",
            "need_relevant": True,
        },
    ]
    p2_scenarios = [
        {
            "description": "Authorized Payment awaiting capture",
            "edge": "one",
            "need_relevant": True,
        },
        {
            "description": "Intersection: Authorized Payment voided at checkout",
            "edge": "intersection",
            "need_relevant": True,
        },
    ]
    irrelevant = [
        {
            "description": "Warehouse packing slip fonts",
            "edge": "one",
            "need_relevant": False,
        },
        {
            "description": "Another irrelevant case",
            "edge": "many",
            "need_relevant": False,
        },
    ]

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            *_three_chapter_walk(),
            _tool_call(
                "propose_proposition",
                {"statement": p1_statement, "activity": "domain_modeling"},
                "propose-p1",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "accept-p1"),
            _tool_call(
                "propose_proposition",
                {"statement": p2_statement, "activity": "domain_modeling"},
                "propose-p2",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p2"}, "accept-p2"),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(irrelevant),
                },
                "scenarios-p1-bad",
            ),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(p1_scenarios),
                },
                "scenarios-p1",
            ),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p2",
                    "scenarios_json": json.dumps(p2_scenarios),
                },
                "scenarios-p2",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p1",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s1", "survives": True},
                            {"scenario_id": "s2", "survives": True},
                            {
                                "scenario_id": "s3",
                                "survives": False,
                                "kind": "contrariety",
                                "summary": "Many partial Payments break exclusive ownership.",
                            },
                        ]
                    ),
                },
                "assert-p1",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p2",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s4", "survives": True},
                            {
                                "scenario_id": "s5",
                                "survives": False,
                                "kind": "omission",
                                "summary": "Void is not covered by Authorized|Settled.",
                            },
                        ]
                    ),
                },
                "assert-p2",
            ),
            _tool_call("probe_batch", {}, "probe"),
            AIMessage(content="Probe pass complete."),
        ]
    )
    agent = create_socrates_session(
        model=model,
        activity_models={
            "requirements": _chapter_close_stub("req"),
            "domain_modeling": _chapter_close_stub("dom"),
            "behavioral_specification": _chapter_close_stub("beh"),
        },
    )
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start a modeling session.")]},
        config=config,
    )
    assert opening["__interrupt__"][0].value["kind"] == "opening"

    after_need = agent.invoke(Command(resume=need), config=config)
    assert after_need["files"][NEED_PATH]["content"] == need
    # The vacuous chapters each ask at the door before the tail opens (17).
    after_need = _close_three_doors(agent, config, after_need)
    assert after_need["__interrupt__"][0].value["kind"] == "accept"
    assert after_need["__interrupt__"][0].value["proposition_id"] == "p1"

    after_p1 = agent.invoke(Command(resume="yes"), config=config)
    assert after_p1["__interrupt__"][0].value["kind"] == "accept"
    assert after_p1["__interrupt__"][0].value["proposition_id"] == "p2"

    at_probe = agent.invoke(Command(resume="yes"), config=config)
    probe = at_probe["__interrupt__"][0].value
    assert probe["kind"] == "probe"
    assert probe["batch_id"] == "b1"
    assert {c["id"] for c in probe["conflicts"]} == {"c1", "c2"}
    assert len(probe["conflicts"]) == 2

    scenarios = _load_json(at_probe["files"], SCENARIOS_PATH)["scenarios"]
    by_prop: dict[str, list] = {}
    for scenario in scenarios:
        by_prop.setdefault(scenario["proposition_id"], []).append(scenario)
        assert scenario["need_relevant"] is True
    assert len(by_prop["p1"]) >= MIN_SCENARIOS_PER_PROPOSITION
    assert len(by_prop["p2"]) >= MIN_SCENARIOS_PER_PROPOSITION
    assert {s["edge"] for s in by_prop["p1"]} >= {"zero", "one", "many"}

    # Relevance Filter rejected the irrelevant batch before real Scenarios landed.
    filter_rejects = [
        m
        for m in at_probe["messages"]
        if isinstance(m, ToolMessage)
        and isinstance(m.content, str)
        and "Relevance Filter" in m.content
        and '"ok":false' in m.content.replace(" ", "").casefold()
    ]
    assert filter_rejects

    finished = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": "c1",
                        "action": "revise_proposition",
                        "statement": revised_p1,
                    },
                    {
                        "conflict_id": "c2",
                        "action": "add_proposition",
                        "statement": new_ground,
                        "activity": "domain_modeling",
                    },
                ]
            }
        ),
        config=config,
    )
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    batches = _load_json(finished["files"], BATCHES_PATH)["batches"]
    assert batches == [
        {"id": "b1", "conflict_ids": ["c1", "c2"], "status": "probed"}
    ]

    conflicts = _load_json(finished["files"], CONFLICTS_PATH)["conflicts"]
    assert all(c["status"] == "resolved" for c in conflicts)
    assert {c["id"] for c in conflicts} == {"c1", "c2"}

    props = {
        p["id"]: p
        for p in _load_json(finished["files"], PROPOSITIONS_PATH)["propositions"]
    }
    assert props["p1"]["statement"] == revised_p1
    assert props["p1"]["status"] == "candidate"  # Degraded from Accepted
    assert any(p["statement"] == new_ground for p in props.values())
