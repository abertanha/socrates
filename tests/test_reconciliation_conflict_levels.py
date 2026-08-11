"""Orchestration test for ticket 05 — Reconciliation + Conflict Levels.

Seam: session orchestration with the model provider stubbed.
Covers pass-2 Reconciliation (L2/L3 only) before Assertion Tests, L1–L4
classification, L4 only from intersection Assertion Tests on two Accepted
Propositions, and Scenario skip for Reconciliation-contradicted material.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.paths import CONFLICTS_PATH, NEED_PATH, SCENARIOS_PATH


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


def _two_scenarios(prefix: str) -> list[dict]:
    return [
        {
            "description": f"{prefix} edge one",
            "edge": "one",
            "need_relevant": True,
        },
        {
            "description": f"{prefix} edge many",
            "edge": "many",
            "need_relevant": True,
        },
    ]


def test_reconciliation_levels_and_scenario_skip():
    need = "Marketplace checkout payments domain."
    p1 = "A Payment belongs to exactly one Order."
    p2 = "Payment status is Authorized or Settled."
    rejected = "Cash is the only allowed tender."
    new_vs_accepted = "A Payment may belong to many Orders."
    new_vs_guardrail = "cash is the only allowed tender."

    # Pass 1: seed Accepted p1/p2, reject→guardrail, L1 assertion conflict, Probe.
    # Pass 2: reconcile L2+L3, skip scenarios on blocked props, L4 via intersection.
    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "propose_proposition",
                {"statement": p1, "activity": "domain_modeling"},
                "prop-p1",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "acc-p1"),
            _tool_call(
                "propose_proposition",
                {"statement": p2, "activity": "domain_modeling"},
                "prop-p2",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p2"}, "acc-p2"),
            _tool_call(
                "propose_proposition",
                {"statement": rejected, "activity": "requirements"},
                "prop-rej",
            ),
            _tool_call(
                "reject_proposition",
                {
                    "proposition_id": "p3",
                    "reason": "Out of scope for marketplace checkout.",
                },
                "rej-p3",
            ),
            _tool_call(
                "propose_proposition",
                {
                    "statement": "Candidate A: Order totals include tax.",
                    "activity": "domain_modeling",
                },
                "prop-cand-a",
            ),
            _tool_call(
                "propose_proposition",
                {
                    "statement": "Candidate B: Order totals exclude tax.",
                    "activity": "domain_modeling",
                },
                "prop-cand-b",
            ),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p4",
                    "scenarios_json": json.dumps(_two_scenarios("cand-a")),
                },
                "sc-p4",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p4",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s1", "survives": True},
                            {
                                "scenario_id": "s2",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "Candidates A and B cannot both hold.",
                                "other_proposition_id": "p5",
                            },
                        ]
                    ),
                },
                "assert-l1",
            ),
            _tool_call("probe_batch", {}, "probe-1"),
            # --- pass 2 ---
            _tool_call(
                "propose_proposition",
                {"statement": new_vs_accepted, "activity": "domain_modeling"},
                "prop-l2",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": new_vs_guardrail, "activity": "requirements"},
                "prop-l3",
            ),
            _tool_call(
                "reconcile",
                {
                    "findings_json": json.dumps(
                        [
                            {
                                "new_proposition_id": "p6",
                                "against_kind": "accepted",
                                "against_id": "p1",
                                "kind": "contradiction",
                                "summary": "Many-Orders contradicts exclusive ownership.",
                            },
                            {
                                "new_proposition_id": "p7",
                                "against_kind": "guardrail",
                                "against_id": "p3",
                                "kind": "contradiction",
                                "summary": "Reintroduces rejected cash-only tender.",
                            },
                        ]
                    )
                },
                "reconcile-pass2",
            ),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p6",
                    "scenarios_json": json.dumps(_two_scenarios("blocked")),
                },
                "sc-blocked",
            ),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(
                        [
                            {
                                "description": "Intersection of exclusive Order and status",
                                "edge": "intersection",
                                "need_relevant": True,
                            },
                            {
                                "description": "One Payment one Order baseline",
                                "edge": "one",
                                "need_relevant": True,
                            },
                        ]
                    ),
                },
                "sc-p1-l4",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p1",
                    "outcomes_json": json.dumps(
                        [
                            {
                                "scenario_id": "s3",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "Accepted ownership vs Accepted status clash.",
                                "other_proposition_id": "p2",
                            },
                            {"scenario_id": "s4", "survives": True},
                        ]
                    ),
                },
                "assert-l4",
            ),
            _tool_call("probe_batch", {}, "probe-2"),
            AIMessage(content="Reconciliation pass complete."),
        ]
    )
    agent = create_socrates_session(model=model)
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
    # reject p3
    assert r["__interrupt__"][0].value["kind"] == "reject"
    r = agent.invoke(Command(resume="yes"), config=config)
    # probe 1 (L1)
    probe1 = r["__interrupt__"][0].value
    assert probe1["kind"] == "probe"
    assert len(probe1["conflicts"]) == 1
    assert probe1["conflicts"][0]["level"] == "L1"
    assert probe1["conflicts"][0]["source"] == "assertion_test"

    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {"conflict_id": probe1["conflicts"][0]["id"], "action": "dismiss"}
                ]
            }
        ),
        config=config,
    )
    # probe 2 after reconcile + L4
    probe2 = r["__interrupt__"][0].value
    assert probe2["kind"] == "probe"
    by_level = {c["level"]: c for c in probe2["conflicts"]}
    assert set(by_level) == {"L2", "L3", "L4"}
    assert by_level["L2"]["source"] == "reconciliation"
    assert by_level["L3"]["source"] == "reconciliation"
    assert by_level["L4"]["source"] == "assertion_test"
    assert by_level["L4"]["other_proposition_id"] == "p2"
    assert by_level["L2"]["proposition_id"] == "p6"
    assert by_level["L3"]["proposition_id"] == "p7"

    # Scenario skip for Reconciliation-blocked p6
    skip_msgs = [
        m
        for m in r["messages"]
        if isinstance(m, ToolMessage)
        and isinstance(m.content, str)
        and "Scenario generation skipped" in m.content
        and "p6" in m.content
    ]
    assert skip_msgs

    # p1 scenarios were recorded (not blocked); no scenarios for p6
    scenarios = _load_json(r["files"], SCENARIOS_PATH)["scenarios"]
    assert any(s["proposition_id"] == "p1" for s in scenarios)
    assert all(s["proposition_id"] != "p6" for s in scenarios)

    finished = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {"conflict_id": by_level["L2"]["id"], "action": "dismiss"},
                    {"conflict_id": by_level["L3"]["id"], "action": "dismiss"},
                    {"conflict_id": by_level["L4"]["id"], "action": "dismiss"},
                ]
            }
        ),
        config=config,
    )
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    conflicts = _load_json(finished["files"], CONFLICTS_PATH)["conflicts"]
    levels = {c["id"]: c["level"] for c in conflicts}
    assert "L1" in levels.values()
    assert "L2" in levels.values()
    assert "L3" in levels.values()
    assert "L4" in levels.values()
    assert all(
        c["source"] == "reconciliation" for c in conflicts if c["level"] in ("L2", "L3")
    )
    assert all(
        c["source"] == "assertion_test" for c in conflicts if c["level"] in ("L1", "L4")
    )
