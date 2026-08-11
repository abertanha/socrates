"""Orchestration test for ticket 10 — Notification policy (quiet by default).

Seam: session orchestration with the model provider stubbed.
Covers: routine Probe/Interview produce no Notification; unavoidable
(non-deferrable, blocks progress) Conflicts notify; Supersede cascade notifies;
delivery channels are stubbed behind the Notification boundary.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.notifications import ALLOWED_KINDS, CHANNEL_NAMES
from socrates.paths import NEED_PATH, NOTIFICATIONS_PATH


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


def test_notification_policy_quiet_unavoidable_cascade_and_stubbed_channels():
    need = "Marketplace checkout payments domain."
    foundation = "A Payment belongs to exactly one Order."
    dependent = "Order total equals sum of its Payments."
    cand_a = "Candidate A: tax included."
    cand_b = "Candidate B: tax excluded."
    status = "Payment status is Authorized or Settled."
    new_vs_accepted = "A Payment may belong to many Orders."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
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
                {"statement": status, "activity": "domain_modeling"},
                "prop-p3",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p3"}, "acc-p3"),
            # Unavoidable L4 (Accepted × Accepted) → Notification
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(
                        [
                            {
                                "description": "Ownership vs status intersection",
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
                                "summary": "Accepted ownership vs Accepted status.",
                                "other_proposition_id": "p3",
                            },
                            {"scenario_id": "s2", "survives": True},
                        ]
                    ),
                },
                "assert-l4",
            ),
            # Routine L1 Probe — Interview flow, must not add Probe Notifications
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
                            {"scenario_id": "s3", "survives": True},
                            {
                                "scenario_id": "s4",
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
            _tool_call("probe_batch", {}, "probe-l1"),
            # Pass 2: Supersede cascade Notification
            _tool_call(
                "propose_proposition",
                {"statement": new_vs_accepted, "activity": "domain_modeling"},
                "prop-p6",
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
                            }
                        ]
                    )
                },
                "reconcile",
            ),
            _tool_call("probe_batch", {}, "probe-l2"),
            AIMessage(content="Notification policy pass complete."),
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
    r = agent.invoke(Command(resume="yes"), config=config)  # p1
    r = agent.invoke(Command(resume="yes"), config=config)  # p2
    r = agent.invoke(Command(resume="yes"), config=config)  # p3

    # After L4 Assertion Tests + L1 Probe interrupt:
    probe_l1 = r["__interrupt__"][0].value
    assert probe_l1["kind"] == "probe"
    # Probe batches only L1 (L4 is Iteration, not Probe).
    assert all(c["level"] == "L1" for c in probe_l1["conflicts"])

    notes = _load_json(r["files"], NOTIFICATIONS_PATH)["notifications"]
    # Unavoidable L4 notified; routine Probe added nothing else.
    assert {n["kind"] for n in notes} == {"unavoidable_conflict"}
    unavoidable = notes[0]
    assert unavoidable["level"] == "L4"
    assert unavoidable["deferrable"] is False
    assert unavoidable["blocks_progress"] is True
    assert unavoidable["conflict_id"] == "c1"
    delivery_channels = {d["channel"] for d in unavoidable["deliveries"]}
    assert delivery_channels == set(CHANNEL_NAMES)
    assert all(d["status"] == "stubbed" for d in unavoidable["deliveries"])
    assert "probe" not in {n["kind"] for n in notes}
    assert {n["kind"] for n in notes} <= ALLOWED_KINDS

    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": probe_l1["conflicts"][0]["id"],
                        "action": "dismiss",
                    }
                ]
            }
        ),
        config=config,
    )

    probe_l2 = r["__interrupt__"][0].value
    assert probe_l2["kind"] == "probe"
    assert probe_l2["conflicts"][0]["level"] == "L2"
    # Still only the unavoidable Notification — Probe did not notify.
    assert {
        n["kind"] for n in _load_json(r["files"], NOTIFICATIONS_PATH)["notifications"]
    } == {"unavoidable_conflict"}

    finished = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": probe_l2["conflicts"][0]["id"],
                        "action": "supersede",
                        "reason": "Multi-Order payments are in scope.",
                    }
                ]
            }
        ),
        config=config,
    )
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    final_notes = _load_json(finished["files"], NOTIFICATIONS_PATH)["notifications"]
    assert {n["kind"] for n in final_notes} == {
        "unavoidable_conflict",
        "supersede_cascade",
    }
    cascade = next(n for n in final_notes if n["kind"] == "supersede_cascade")
    assert cascade["superseded_id"] == "p1"
    assert cascade["new_proposition_id"] == "p6"
    assert "p2" in cascade["degraded_ids"]
    assert {d["channel"] for d in cascade["deliveries"]} == set(CHANNEL_NAMES)
    assert all(d["status"] == "stubbed" for d in cascade["deliveries"])
