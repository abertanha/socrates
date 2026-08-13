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
    PROPOSITIONS_PATH,
)
from socrates.tools import SATISFACTION_QUESTION

DELIVERABLE_PATHS = (
    DELIVERABLE_GLOSSARY_PATH,
    DELIVERABLE_STRUCTURE_PATH,
    DELIVERABLE_RULES_PATH,
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
    # Requirements bound the Need and are composed into the Glossary.
    requirement_scope = "Every Model must cover settlement of a buyer's Order."

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
            _tool_call(
                "propose_proposition",
                {"statement": requirement_scope, "activity": "requirements"},
                "prop-req",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p7"}, "acc-p7"),
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
    # Accept p7 (requirements — bounds the Need)
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
    assert requirement_scope in glossary
    assert structure_rel not in glossary
    assert conceptual_rule not in glossary

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


def test_non_affirmative_satisfaction_leaves_deliverable_unwritten():
    """Materialization is gated on the user's affirmative signal (ADR-0002)."""
    need = "Marketplace checkout payments domain."
    term = "Payment is the transfer of value that settles an Order."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "propose_proposition",
                {"statement": term, "activity": "domain_modeling"},
                "prop-gloss",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "acc-p1"),
            _tool_call("await_satisfaction", {}, "sat"),
            AIMessage(content="Still more to work through."),
        ]
    )

    agent = create_socrates_session(model=model)
    config = _thread_config()

    agent.invoke(
        {"messages": [HumanMessage(content="Start a modeling session.")]},
        config=config,
    )
    state = agent.invoke(Command(resume=need), config=config)
    assert state["__interrupt__"][0].value["kind"] == "accept"
    state = agent.invoke(Command(resume="yes"), config=config)
    assert state["__interrupt__"][0].value["kind"] == "satisfaction"

    finished = agent.invoke(
        Command(resume="not yet, there's more to work through"),
        config=config,
    )
    files = finished["files"]

    # The Model persists; only the composed deliverable is withheld.
    assert PROPOSITIONS_PATH in files
    assert term in files[PROPOSITIONS_PATH]["content"]
    for path in DELIVERABLE_PATHS:
        assert path not in files, f"{path} materialized without Satisfaction"


def test_deliverable_draws_accepted_propositions_only():
    """Candidate and Rejected Propositions stay out of the deliverable."""
    need = "Marketplace checkout payments domain."
    # All three are definitional domain_modeling and Implementation-Independent,
    # so only lifecycle state can keep the latter two out of the Glossary.
    accepted_term = "Order is the buyer's request that a Payment settles."
    candidate_term = "Basket is the buyer's provisional selection before Order."
    rejected_term = "Invoice is the receipt issued after settlement."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "propose_proposition",
                {"statement": accepted_term, "activity": "domain_modeling"},
                "prop-acc",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "acc-p1"),
            _tool_call(
                "propose_proposition",
                {"statement": candidate_term, "activity": "domain_modeling"},
                "prop-cand",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": rejected_term, "activity": "domain_modeling"},
                "prop-rej",
            ),
            _tool_call(
                "reject_proposition",
                {"proposition_id": "p3", "reason": "Invoicing sits outside the Need."},
                "rej-p3",
            ),
            _tool_call("await_satisfaction", {}, "sat"),
            AIMessage(content="Conceptual Domain Model delivered."),
        ]
    )

    agent = create_socrates_session(model=model)
    config = _thread_config()

    agent.invoke(
        {"messages": [HumanMessage(content="Start a modeling session.")]},
        config=config,
    )
    state = agent.invoke(Command(resume=need), config=config)
    assert state["__interrupt__"][0].value["kind"] == "accept"
    state = agent.invoke(Command(resume="yes"), config=config)
    assert state["__interrupt__"][0].value["kind"] == "reject"
    state = agent.invoke(Command(resume="yes"), config=config)
    assert state["__interrupt__"][0].value["kind"] == "satisfaction"

    finished = agent.invoke(Command(resume="yes"), config=config)
    parts = [finished["files"][path]["content"] for path in DELIVERABLE_PATHS]

    assert accepted_term in finished["files"][DELIVERABLE_GLOSSARY_PATH]["content"]
    for part in parts:
        assert candidate_term not in part, "Candidate entered the deliverable"
        assert rejected_term not in part, "Rejected entered the deliverable"
