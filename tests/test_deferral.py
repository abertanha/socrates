"""Orchestration test for ticket 08 — Deferral.

Seam: session orchestration with the model provider stubbed (ticket 14
shape: the three chapters run first via `task`, so the Deferral saga and
its Satisfaction warning live in the tail, where the orchestrator keeps
the pulse). Covers defer of any surfaced Conflict, criticality
recommendation (operational blocking-ness, not correctness), event-driven
re-raise on touch, and a non-blocking criticality-weighted Satisfaction
warning.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.paths import CONFLICTS_PATH, NEED_PATH
from socrates.tools import SATISFACTION_QUESTION


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


def _close_stubs() -> dict:
    return {
        "requirements": _chapter_close_stub("req"),
        "domain_modeling": _chapter_close_stub("dom"),
        "behavioral_specification": _chapter_close_stub("beh"),
    }


def test_deferral_criticality_reraise_and_satisfaction_warning():
    need = "Marketplace checkout payments domain."
    foundation = "A Payment belongs to exactly one Order."
    cand_a = "Candidate A: tax included in total."
    cand_b = "Candidate B: tax excluded from total."
    new_vs_accepted = "A Payment may belong to many Orders."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            *_three_chapter_walk(),
            _tool_call(
                "propose_proposition",
                {"statement": foundation, "activity": "domain_modeling"},
                "prop-p1",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "acc-p1"),
            _tool_call(
                "propose_proposition",
                {"statement": cand_a, "activity": "domain_modeling"},
                "prop-p2",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": cand_b, "activity": "domain_modeling"},
                "prop-p3",
            ),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p2",
                    "scenarios_json": json.dumps(_two_scenarios("l1")),
                },
                "sc-l1",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p2",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s1", "survives": True},
                            {
                                "scenario_id": "s2",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "Candidates A and B conflict.",
                                "other_proposition_id": "p3",
                            },
                        ]
                    ),
                },
                "assert-l1",
            ),
            _tool_call("probe_batch", {}, "probe-1"),
            # Touch a deferred party → re-raise (event-driven).
            _tool_call(
                "reject_proposition",
                {
                    "proposition_id": "p3",
                    "reason": "Tax treatment parked pending Need clarity.",
                },
                "rej-touch",
            ),
            _tool_call("probe_batch", {}, "probe-reraise"),
            # Pass 2: critical L2 (high level; both parties are leaves — no
            # centrality reason under ticket 16's defined concept).
            _tool_call(
                "propose_proposition",
                {"statement": new_vs_accepted, "activity": "domain_modeling"},
                "prop-p4",
            ),
            _tool_call(
                "reconcile",
                {
                    "findings_json": json.dumps(
                        [
                            {
                                "new_proposition_id": "p4",
                                "against_kind": "accepted",
                                "against_id": "p1",
                                "kind": "contradiction",
                                "summary": "Many-Orders vs exclusive ownership.",
                            }
                        ]
                    )
                },
                "reconcile",
            ),
            _tool_call("probe_batch", {}, "probe-l2"),
            _tool_call("await_satisfaction", {}, "satisfaction"),
            AIMessage(content="Closed with deferred conflicts warned."),
        ]
    )
    agent = create_socrates_session(model=model, activity_models=_close_stubs())
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start")]},
        config=config,
    )
    assert opening["__interrupt__"][0].value["kind"] == "opening"

    r = agent.invoke(Command(resume=need), config=config)
    assert r["files"][NEED_PATH]["content"] == need
    assert r["__interrupt__"][0].value["proposition_id"] == "p1"
    r = agent.invoke(Command(resume="yes"), config=config)

    probe1 = r["__interrupt__"][0].value
    assert probe1["kind"] == "probe"
    assert len(probe1["conflicts"]) == 1
    l1 = probe1["conflicts"][0]
    assert l1["level"] == "L1"
    assert l1["deferral"]["critical"] is False
    assert l1["deferral"]["recommend_against"] is False

    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {"conflict_id": l1["id"], "action": "defer"},
                ]
            }
        ),
        config=config,
    )
    deferred = _load_json(r["files"], CONFLICTS_PATH)["conflicts"]
    assert deferred[0]["status"] == "deferred"
    assert deferred[0]["resolution"]["action"] == "defer"

    # Reject of a deferred party interrupts first, then touch re-raises.
    assert r["__interrupt__"][0].value["kind"] == "reject"
    assert r["__interrupt__"][0].value["proposition_id"] == "p3"
    r = agent.invoke(Command(resume="yes"), config=config)

    # After touch, Probe re-surfaces the Conflict.
    probe2 = r["__interrupt__"][0].value
    assert probe2["kind"] == "probe"
    assert len(probe2["conflicts"]) == 1
    assert probe2["conflicts"][0]["id"] == l1["id"]
    assert probe2["conflicts"][0]["re_raised"] is True

    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {"conflict_id": l1["id"], "action": "defer"},
                ]
            }
        ),
        config=config,
    )

    # L2 Probe: critical — recommend against deferring, but still allowed.
    probe_l2 = r["__interrupt__"][0].value
    assert probe_l2["kind"] == "probe"
    assert len(probe_l2["conflicts"]) == 1
    l2 = probe_l2["conflicts"][0]
    assert l2["level"] == "L2"
    assert l2["deferral"]["critical"] is True
    assert l2["deferral"]["recommend_against"] is True
    assert "high_conflict_level" in l2["deferral"]["reasons"]
    # Ticket 16: the accepted party here is a leaf (no dependents, not
    # Requirements) — `central_proposition` no longer proxies "Accepted".
    assert l2["deferral"]["reasons"] == ["high_conflict_level"]

    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {"conflict_id": l2["id"], "action": "defer"},
                ]
            }
        ),
        config=config,
    )

    satisfaction = r["__interrupt__"][0].value
    assert satisfaction["kind"] == "satisfaction"
    assert satisfaction["question"] == SATISFACTION_QUESTION
    warning = satisfaction["deferred_warning"]
    assert warning is not None
    assert warning["blocking"] is False
    assert warning["kind"] == "deferred_conflicts"
    by_id = {c["id"]: c for c in warning["conflicts"]}
    assert l1["id"] in by_id
    assert l2["id"] in by_id
    assert by_id[l1["id"]]["criticality"]["recommend_against"] is False
    assert by_id[l2["id"]]["criticality"]["recommend_against"] is True
    assert by_id[l2["id"]]["criticality"]["critical"] is True

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()
    # Deferred Conflicts remain parked — Satisfaction did not hard-block.
    remaining = _load_json(finished["files"], CONFLICTS_PATH)["conflicts"]
    assert {c["id"]: c["status"] for c in remaining} == {
        l1["id"]: "deferred",
        l2["id"]: "deferred",
    }


def test_l4_is_unavoidable_and_cannot_be_deferred():
    """Ticket 10 refines ticket 08: L4 is non-deferrable (blocks progress)."""
    need = "Marketplace checkout payments domain."
    p1 = "A Payment belongs to exactly one Order."
    p2 = "Payment status is Authorized or Settled."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            *_three_chapter_walk(),
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
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(
                        [
                            {
                                "description": "Intersection clash",
                                "edge": "intersection",
                                "need_relevant": True,
                            },
                            {
                                "description": "One Order baseline",
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
                                "summary": "Accepted ownership vs Accepted status.",
                                "other_proposition_id": "p2",
                            },
                            {"scenario_id": "s2", "survives": True},
                        ]
                    ),
                },
                "assert-l4",
            ),
            _tool_call("defer_conflict", {"conflict_id": "c1"}, "defer-l4"),
            AIMessage(content="L4 remains open."),
        ]
    )
    agent = create_socrates_session(model=model, activity_models=_close_stubs())
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start")]},
        config=config,
    )
    r = agent.invoke(Command(resume=need), config=config)
    r = agent.invoke(Command(resume="yes"), config=config)
    finished = agent.invoke(Command(resume="yes"), config=config)

    assert finished.get("__interrupt__") is None
    conflicts = _load_json(finished["files"], CONFLICTS_PATH)["conflicts"]
    assert len(conflicts) == 1
    assert conflicts[0]["level"] == "L4"
    assert conflicts[0]["status"] == "open"

    defer_errs = [
        m
        for m in finished["messages"]
        if isinstance(m, ToolMessage)
        and isinstance(m.content, str)
        and '"ok":false' in m.content.replace(" ", "")
        and "unavoidable" in m.content
    ]
    assert defer_errs
