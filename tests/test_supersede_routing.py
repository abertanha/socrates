"""Orchestration test for ticket 06 — Supersede routing.

Seam: session orchestration with the model provider stubbed (ticket 14
shape: the three chapters run first via `task`, so the Supersede sagas live
in the tail, where the orchestrator keeps the pulse). Covers L2 Supersede
(displaced recorded; new → Candidate), cascade Degrade of indirectly
Accepted dependents with notification (not permission), L1 in-line Probe
resolution, and L3 blocked by the Rejection Guardrail.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.paths import NEED_PATH, NOTIFICATIONS_PATH, PROPOSITIONS_PATH


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


def test_supersede_cascade_l1_inline_l3_blocked():
    need = "Marketplace checkout payments domain."
    foundation = "A Payment belongs to exactly one Order."
    dependent = "Order total equals sum of its Payments."
    rejected = "Cash is the only allowed tender."
    new_vs_accepted = "A Payment may belong to many Orders."
    new_vs_guardrail = "cash is the only allowed tender."
    cand_a = "Candidate A: tax included in total."
    cand_b = "Candidate B: tax excluded from total."

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
                {"statement": dependent, "activity": "domain_modeling"},
                "prop-p2",
            ),
            _tool_call(
                "accept_proposition",
                {"proposition_id": "p2", "via_proposition_id": "p1"},
                "acc-p2",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": rejected, "activity": "requirements"},
                "prop-p3",
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
                {"statement": cand_a, "activity": "domain_modeling"},
                "prop-p4",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": cand_b, "activity": "domain_modeling"},
                "prop-p5",
            ),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p4",
                    "scenarios_json": json.dumps(_two_scenarios("l1")),
                },
                "sc-l1",
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
                                "summary": "Candidates A and B conflict.",
                                "other_proposition_id": "p5",
                            },
                        ]
                    ),
                },
                "assert-l1",
            ),
            _tool_call("probe_batch", {}, "probe-1"),
            _tool_call(
                "propose_proposition",
                {"statement": new_vs_accepted, "activity": "domain_modeling"},
                "prop-p6",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": new_vs_guardrail, "activity": "requirements"},
                "prop-p7",
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
                                "summary": "Many-Orders vs exclusive ownership.",
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
                "reconcile",
            ),
            _tool_call("probe_batch", {}, "probe-2"),
            AIMessage(content="Supersede routing pass complete."),
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
    assert r["__interrupt__"][0].value["proposition_id"] == "p2"
    r = agent.invoke(Command(resume="yes"), config=config)
    assert r["__interrupt__"][0].value["kind"] == "reject"
    r = agent.invoke(Command(resume="yes"), config=config)

    probe1 = r["__interrupt__"][0].value
    assert probe1["kind"] == "probe"
    assert len(probe1["conflicts"]) == 1
    assert probe1["conflicts"][0]["level"] == "L1"
    assert probe1["conflicts"][0]["routing"] == "inline"

    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": probe1["conflicts"][0]["id"],
                        "action": "revise_proposition",
                        "statement": "Order tax treatment is unsettled.",
                    }
                ]
            }
        ),
        config=config,
    )

    probe2 = r["__interrupt__"][0].value
    assert probe2["kind"] == "probe"
    by_level = {c["level"]: c for c in probe2["conflicts"]}
    assert set(by_level) == {"L2", "L3"}
    assert by_level["L2"]["routing"] == "supersede"
    assert by_level["L3"]["routing"] == "blocked"

    finished = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": by_level["L2"]["id"],
                        "action": "supersede",
                        "reason": "Multi-Order payments are in scope.",
                    },
                    {
                        "conflict_id": by_level["L3"]["id"],
                        "action": "dismiss",
                    },
                ]
            }
        ),
        config=config,
    )
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    props = {
        p["id"]: p
        for p in _load_json(finished["files"], PROPOSITIONS_PATH)["propositions"]
    }
    assert props["p1"]["status"] == "superseded"
    assert props["p1"]["reason"] == "Multi-Order payments are in scope."
    assert props["p6"]["status"] == "candidate"
    assert props["p2"]["status"] == "candidate"
    assert props["p2"]["accepted_via"] is None
    assert props["p7"]["status"] == "flagged"

    notifications = _load_json(finished["files"], NOTIFICATIONS_PATH)["notifications"]
    cascade = [n for n in notifications if n["kind"] == "supersede_cascade"]
    assert len(cascade) == 1
    assert cascade[0]["superseded_id"] == "p1"
    assert cascade[0]["new_proposition_id"] == "p6"
    assert "p2" in cascade[0]["degraded_ids"]
    # Cascade notify is a recorded Notification — not a permission interrupt.
    assert not any(
        isinstance(m, dict) and m.get("kind") == "supersede_cascade"
        for m in []
    )


def test_l3_supersede_rejected_by_guardrail_routing():
    """L3 cannot be Superseded — Probe returns an error, Guardrail holds."""
    need = "Marketplace checkout payments domain."
    rejected = "Cash is the only allowed tender."
    again = "cash is the only allowed tender."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            *_three_chapter_walk(),
            _tool_call(
                "propose_proposition",
                {"statement": "Seed Accepted.", "activity": "requirements"},
                "seed",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "acc"),
            _tool_call(
                "propose_proposition",
                {"statement": rejected, "activity": "requirements"},
                "rej-prop",
            ),
            _tool_call(
                "reject_proposition",
                {"proposition_id": "p2", "reason": "Out of scope."},
                "rej",
            ),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(_two_scenarios("seed")),
                },
                "sc",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p1",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s1", "survives": True},
                            {
                                "scenario_id": "s2",
                                "survives": False,
                                "kind": "omission",
                                "summary": "Seed needs a pass-1 Probe.",
                            },
                        ]
                    ),
                },
                "assert",
            ),
            _tool_call("probe_batch", {}, "probe-1"),
            _tool_call(
                "propose_proposition",
                {"statement": again, "activity": "requirements"},
                "again",
            ),
            _tool_call(
                "reconcile",
                {
                    "findings_json": json.dumps(
                        [
                            {
                                "new_proposition_id": "p3",
                                "against_kind": "guardrail",
                                "against_id": "p2",
                                "kind": "contradiction",
                                "summary": "Blocked by Rejection Guardrail.",
                            }
                        ]
                    )
                },
                "recon",
            ),
            _tool_call("probe_batch", {}, "probe-2"),
            AIMessage(content="done"),
        ]
    )
    agent = create_socrates_session(model=model, activity_models=_close_stubs())
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage("Start")]}, config=config)
    r = agent.invoke(Command(resume=need), config=config)
    r = agent.invoke(Command(resume="yes"), config=config)  # accept p1
    r = agent.invoke(Command(resume="yes"), config=config)  # reject p2
    assert r["__interrupt__"][0].value["kind"] == "probe"
    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": r["__interrupt__"][0].value["conflicts"][0]["id"],
                        "action": "dismiss",
                    }
                ]
            }
        ),
        config=config,
    )
    probe = r["__interrupt__"][0].value
    assert probe["conflicts"][0]["level"] == "L3"
    assert probe["conflicts"][0]["routing"] == "blocked"

    finished = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": probe["conflicts"][0]["id"],
                        "action": "supersede",
                        "reason": "should be blocked",
                    }
                ]
            }
        ),
        config=config,
    )
    errors = [
        m.content
        for m in finished["messages"]
        if isinstance(m, ToolMessage)
        and isinstance(m.content, str)
        and "Rejection Guardrail" in m.content
        and '"ok":false' in m.content.replace(" ", "").casefold()
    ]
    assert errors
