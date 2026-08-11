"""Orchestration test for ticket 02 — Proposition lifecycle.

Seam: session orchestration with the model provider stubbed.
Covers Candidate triage, Accept / Reject, Rejection Guardrail persistence,
and Guardrail resemblance flagging.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage
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
                {"statement": accepted_statement},
                "c-propose-1",
            ),
            _tool_call(
                "accept_proposition",
                {"proposition_id": "p1"},
                "c-accept-1",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": rejected_statement},
                "c-propose-2",
            ),
            _tool_call(
                "reject_proposition",
                {"proposition_id": "p2", "reason": rejection_reason},
                "c-reject-2",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": resembling_statement},
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

    # Opening resume → propose p1 → accept interrupts; p1 must be Candidate.
    at_accept = agent.invoke(Command(resume=need), config=config)
    assert at_accept["files"][NEED_PATH]["content"] == need
    assert at_accept["__interrupt__"][0].value["kind"] == "accept"
    assert at_accept["__interrupt__"][0].value["proposition_id"] == "p1"
    assert _by_id(at_accept["files"])["p1"]["status"] == "candidate"
    assert _by_id(at_accept["files"])["p1"]["statement"] == accepted_statement

    # User Accept signal → p1 Accepted; then propose p2 → reject interrupts.
    at_reject = agent.invoke(Command(resume="yes"), config=config)
    assert _by_id(at_reject["files"])["p1"]["status"] == "accepted"
    assert at_reject["__interrupt__"][0].value["kind"] == "reject"
    assert at_reject["__interrupt__"][0].value["proposition_id"] == "p2"
    assert at_reject["__interrupt__"][0].value["reason"] == rejection_reason
    assert _by_id(at_reject["files"])["p2"]["status"] == "candidate"
    assert _by_id(at_reject["files"])["p2"]["statement"] == rejected_statement

    # User Reject signal → Guardrail entry; resembling propose → Flagged; done.
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
