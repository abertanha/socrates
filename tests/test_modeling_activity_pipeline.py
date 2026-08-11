"""Orchestration test for ticket 03 — Modeling Activity pipeline.

Seam: session orchestration with the model provider stubbed.
Asserts Requirements → Domain Modeling → Behavioral Specification precedence,
per-activity subagents, activity tags on Propositions, and rejection of
functional ('the system shall...') statements in Behavioral Specification.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.paths import NEED_PATH, PIPELINE_PATH, PROPOSITIONS_PATH
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


def _activity_stub(
    *,
    propose_statement: str,
    label: str,
    extra_proposes: list[str] | None = None,
) -> StubChatModel:
    responses: list[AIMessage] = [
        _tool_call(
            "propose_proposition",
            {"statement": propose_statement},
            f"{label}-propose",
        ),
    ]
    for i, statement in enumerate(extra_proposes or []):
        responses.append(
            _tool_call(
                "propose_proposition",
                {"statement": statement},
                f"{label}-propose-extra-{i}",
            )
        )
    responses.append(
        _tool_call("complete_modeling_activity", {}, f"{label}-complete")
    )
    responses.append(AIMessage(content=f"{label} activity complete."))
    return StubChatModel(responses=responses, label=label)


def test_modeling_activity_pipeline_precedence_tags_and_conceptual_rules():
    need = "Marketplace checkout payments domain."
    req_statement = "Checkout must capture payment authorization."
    domain_statement = "Payment is a domain entity with a status."
    functional_statement = "The system shall send an email on payment."
    behavioral_statement = (
        "One Payment yields at least one Notification to the payer."
    )

    requirements_model = _activity_stub(
        propose_statement=req_statement,
        label="req",
    )
    domain_model = _activity_stub(
        propose_statement=domain_statement,
        label="dom",
    )
    # Behavioral: first attempt is a functional requirement (must be rejected),
    # then a conceptual domain rule is accepted as Candidate.
    behavioral_model = _activity_stub(
        propose_statement=functional_statement,
        label="beh",
        extra_proposes=[behavioral_statement],
    )

    main_model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "main-open"),
            _tool_call(
                "task",
                {
                    "subagent_type": "requirements",
                    "description": "Run Requirements.",
                },
                "main-task-req",
            ),
            _tool_call(
                "task",
                {
                    "subagent_type": "domain-modeling",
                    "description": "Run Domain Modeling.",
                },
                "main-task-dom",
            ),
            _tool_call(
                "task",
                {
                    "subagent_type": "behavioral-specification",
                    "description": "Run Behavioral Specification.",
                },
                "main-task-beh",
            ),
            AIMessage(content="Pipeline complete."),
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
        {"messages": [HumanMessage(content="Start a modeling session.")]},
        config=config,
    )
    assert opening["__interrupt__"][0].value["kind"] == "opening"

    finished = agent.invoke(Command(resume=need), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()
    assert finished["files"][NEED_PATH]["content"] == need

    pipeline = _load_json(finished["files"], PIPELINE_PATH)
    assert pipeline["completed"] == list(ACTIVITIES_IN_ORDER)
    assert pipeline["active"] is None

    propositions = _load_json(finished["files"], PROPOSITIONS_PATH)["propositions"]
    by_statement = {p["statement"]: p for p in propositions}

    assert by_statement[req_statement]["activity"] == "requirements"
    assert by_statement[req_statement]["status"] == "candidate"
    assert by_statement[domain_statement]["activity"] == "domain_modeling"
    assert by_statement[behavioral_statement]["activity"] == "behavioral_specification"
    assert by_statement[behavioral_statement]["status"] == "candidate"
    assert functional_statement not in by_statement

    # Distinct subagents: each specialist returned its completion message via task.
    tool_texts = [
        m.content
        for m in finished["messages"]
        if isinstance(m, ToolMessage) and isinstance(m.content, str)
    ]
    assert any("req activity complete" in t for t in tool_texts)
    assert any("dom activity complete" in t for t in tool_texts)
    assert any("beh activity complete" in t for t in tool_texts)
