"""Orchestration test for ticket 11 — Deliverable composition.

Seam: session orchestration with the model provider stubbed.
At Satisfaction, the persisted Model is materialized as Glossary + Structure
+ conceptual Rules, respecting Implementation-Independence.
"""

from __future__ import annotations

import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.paths import (
    DELIVERABLE_GLOSSARY_PATH,
    DELIVERABLE_RULES_PATH,
    DELIVERABLE_STRUCTURE_PATH,
    NEED_PATH,
)
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


def test_satisfaction_materializes_glossary_structure_rules():
    need = "Marketplace checkout payments domain."
    glossary_term = "Payment is the transfer of value that settles an Order."
    structure_rel = "A Payment belongs to exactly one Order."
    conceptual_rule = (
        "One Payment yields at least one Notification to the payer."
    )
    # Implementation-dependent — must not enter the deliverable.
    tech_specific = "Notification is delivered via push to the payer device."
    concrete_param = "The Payment Window is 120 minutes."
    # Platform Parameter nature is conceptual — belongs in Rules.
    parameterized_rule = (
        "The Payment Window is an admin-configurable duration."
    )

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "propose_proposition",
                {"statement": glossary_term, "activity": "domain_modeling"},
                "prop-gloss",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "acc-p1"),
            _tool_call(
                "propose_proposition",
                {"statement": structure_rel, "activity": "domain_modeling"},
                "prop-struct",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p2"}, "acc-p2"),
            _tool_call(
                "propose_proposition",
                {
                    "statement": conceptual_rule,
                    "activity": "behavioral_specification",
                },
                "prop-rule",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p3"}, "acc-p3"),
            _tool_call(
                "propose_proposition",
                {
                    "statement": tech_specific,
                    "activity": "behavioral_specification",
                },
                "prop-tech",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p4"}, "acc-p4"),
            _tool_call(
                "propose_proposition",
                {
                    "statement": concrete_param,
                    "activity": "behavioral_specification",
                },
                "prop-param",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p5"}, "acc-p5"),
            _tool_call(
                "propose_proposition",
                {
                    "statement": parameterized_rule,
                    "activity": "behavioral_specification",
                },
                "prop-ok-param",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p6"}, "acc-p6"),
            _tool_call("await_satisfaction", {}, "sat"),
            AIMessage(content="Conceptual Domain Model delivered."),
        ]
    )

    agent = create_socrates_session(model=model)
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start a modeling session.")]},
        config=config,
    )
    assert opening["__interrupt__"][0].value["kind"] == "opening"

    state = agent.invoke(Command(resume=need), config=config)
    # Accept p1
    assert state["__interrupt__"][0].value["kind"] == "accept"
    state = agent.invoke(Command(resume="yes"), config=config)
    # Accept p2
    assert state["__interrupt__"][0].value["kind"] == "accept"
    state = agent.invoke(Command(resume="yes"), config=config)
    # Accept p3
    assert state["__interrupt__"][0].value["kind"] == "accept"
    state = agent.invoke(Command(resume="yes"), config=config)
    # Accept p4 (tech — later filtered from deliverable)
    assert state["__interrupt__"][0].value["kind"] == "accept"
    state = agent.invoke(Command(resume="yes"), config=config)
    # Accept p5 (concrete param — filtered)
    assert state["__interrupt__"][0].value["kind"] == "accept"
    state = agent.invoke(Command(resume="yes"), config=config)
    # Accept p6
    assert state["__interrupt__"][0].value["kind"] == "accept"
    state = agent.invoke(Command(resume="yes"), config=config)

    assert "__interrupt__" in state
    satisfaction = state["__interrupt__"][0].value
    assert satisfaction["kind"] == "satisfaction"
    assert satisfaction["question"] == SATISFACTION_QUESTION

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()
    assert finished["files"][NEED_PATH]["content"] == need

    glossary = finished["files"][DELIVERABLE_GLOSSARY_PATH]["content"]
    structure = finished["files"][DELIVERABLE_STRUCTURE_PATH]["content"]
    rules = finished["files"][DELIVERABLE_RULES_PATH]["content"]

    # Settled layout: three composed parts under /model/deliverable/
    assert DELIVERABLE_GLOSSARY_PATH == "/model/deliverable/glossary.md"
    assert DELIVERABLE_STRUCTURE_PATH == "/model/deliverable/structure.md"
    assert DELIVERABLE_RULES_PATH == "/model/deliverable/rules.md"

    assert "# Glossary" in glossary
    assert need in glossary
    assert glossary_term in glossary
    assert structure_rel not in glossary

    assert "# Structure" in structure
    assert structure_rel in structure
    assert glossary_term not in structure

    assert "# Rules" in rules
    assert conceptual_rule in rules
    assert parameterized_rule in rules

    # Implementation-Independence: technologies and concrete values stay out.
    for part in (glossary, structure, rules):
        assert tech_specific not in part
        assert concrete_param not in part
        assert "via push" not in part
        assert "120 minutes" not in part
