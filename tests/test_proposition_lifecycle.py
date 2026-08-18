"""Orchestration test for ticket 02 — Proposition lifecycle.

Seam: session orchestration with the model provider stubbed.
Covers Candidate triage, Accept / Reject, Rejection Guardrail persistence,
and Guardrail resemblance flagging. Propositions are tagged with the
Modeling Activity that produced them.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.paths import (
    NEED_PATH,
    PROPOSITIONS_PATH,
    REJECTION_GUARDRAIL_PATH,
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


def _by_id(files: dict) -> dict:
    props = _load_json(files, PROPOSITIONS_PATH)["propositions"]
    return {p["id"]: p for p in props}


def test_proposition_lifecycle_candidate_accept_reject_guardrail_flag():
    need = "Marketplace checkout payments domain."
    accepted_statement = "A Payment belongs to exactly one Order."
    rejected_statement = "Cash is the only allowed tender."
    rejection_reason = "Out of scope for marketplace checkout."
    resembling_statement = "cash is the only allowed tender."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "c-open"),
            _tool_call(
                "propose_proposition",
                {"statement": accepted_statement, "activity": "requirements"},
                "c-propose-1",
            ),
            _tool_call(
                "accept_proposition",
                {"proposition_id": "p1"},
                "c-accept-1",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": rejected_statement, "activity": "requirements"},
                "c-propose-2",
            ),
            _tool_call(
                "reject_proposition",
                {"proposition_id": "p2", "reason": rejection_reason},
                "c-reject-2",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": resembling_statement, "activity": "requirements"},
                "c-propose-3",
            ),
            AIMessage(content="Lifecycle pass complete."),
        ]
    )
    agent = create_socrates_session(model=model)
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start a modeling session.")]},
        config=config,
    )
    assert opening["__interrupt__"][0].value["kind"] == "opening"

    at_accept = agent.invoke(Command(resume=need), config=config)
    assert at_accept["files"][NEED_PATH]["content"] == need
    assert at_accept["__interrupt__"][0].value["kind"] == "accept"
    assert at_accept["__interrupt__"][0].value["proposition_id"] == "p1"
    assert _by_id(at_accept["files"])["p1"]["status"] == "candidate"
    assert _by_id(at_accept["files"])["p1"]["statement"] == accepted_statement
    assert _by_id(at_accept["files"])["p1"]["activity"] == "requirements"

    at_reject = agent.invoke(Command(resume="yes"), config=config)
    assert _by_id(at_reject["files"])["p1"]["status"] == "accepted"
    assert at_reject["__interrupt__"][0].value["kind"] == "reject"
    assert at_reject["__interrupt__"][0].value["proposition_id"] == "p2"
    assert at_reject["__interrupt__"][0].value["reason"] == rejection_reason
    assert _by_id(at_reject["files"])["p2"]["status"] == "candidate"
    assert _by_id(at_reject["files"])["p2"]["statement"] == rejected_statement

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    by_id = _by_id(finished["files"])
    assert by_id["p1"]["status"] == "accepted"
    assert by_id["p2"]["status"] == "rejected"
    assert by_id["p2"]["reason"] == rejection_reason
    assert by_id["p3"]["statement"] == resembling_statement
    assert by_id["p3"]["status"] == "flagged"
    assert by_id["p3"]["flagged_against_id"] == "p2"

    guardrail = _load_json(finished["files"], REJECTION_GUARDRAIL_PATH)["entries"]
    assert guardrail == [
        {
            "proposition_id": "p2",
            "statement": rejected_statement,
            "reason": rejection_reason,
        }
    ]


def test_accept_and_reject_interrupts_honor_a_declined_answer():
    """The confirmation interrupt is a gate, not a rubber stamp: a declined
    answer leaves the Proposition untouched (post-MVP fix)."""
    need = "Marketplace checkout payments domain."
    p1 = "A Payment belongs to exactly one Order."
    p2 = "Cash is the only allowed tender."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "c-open"),
            _tool_call(
                "propose_proposition",
                {"statement": p1, "activity": "requirements"},
                "c-propose-1",
            ),
            # Declined, then confirmed on retry.
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "c-accept-1"),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "c-accept-1b"),
            _tool_call(
                "propose_proposition",
                {"statement": p2, "activity": "requirements"},
                "c-propose-2",
            ),
            # Rejection declined — the Proposition stays a Candidate.
            _tool_call(
                "reject_proposition",
                {"proposition_id": "p2", "reason": "Out of scope."},
                "c-reject-2",
            ),
            AIMessage(content="Lifecycle pass complete."),
        ]
    )
    agent = create_socrates_session(model=model)
    config = _thread_config()

    agent.invoke(
        {"messages": [HumanMessage(content="Start a modeling session.")]},
        config=config,
    )
    r = agent.invoke(Command(resume=need), config=config)
    assert r["__interrupt__"][0].value["kind"] == "accept"
    assert r["__interrupt__"][0].value["proposition_id"] == "p1"

    declined = agent.invoke(Command(resume="no, hold on"), config=config)
    # Declined: NOT accepted, and the tool result says so.
    assert _by_id(declined["files"])["p1"]["status"] == "candidate"
    declined_msgs = [
        m
        for m in declined["messages"]
        if isinstance(m, ToolMessage)
        and isinstance(m.content, str)
        and '"ok":false' in m.content.replace(" ", "")
        and "declined" in m.content
    ]
    assert declined_msgs
    # The agent re-asked; the user now confirms.
    assert declined["__interrupt__"][0].value["kind"] == "accept"

    r = agent.invoke(Command(resume="yes"), config=config)
    assert _by_id(r["files"])["p1"]["status"] == "accepted"
    assert r["__interrupt__"][0].value["kind"] == "reject"
    assert r["__interrupt__"][0].value["proposition_id"] == "p2"

    finished = agent.invoke(Command(resume="no"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()
    # Declined rejection: still a Candidate, Guardrail untouched.
    by_id = _by_id(finished["files"])
    assert by_id["p2"]["status"] == "candidate"
    assert REJECTION_GUARDRAIL_PATH not in finished["files"]
