"""Orchestration test for ticket 09 — Coverage-driven exploration budget.

Seam: session orchestration with the model provider stubbed (ticket 14
shape: the whole pass/Probe pulse runs inside the Domain Modeling chapter
specialist). Covers pass-over-pass Coverage from declining Conflict signals,
recursion_limit ∝ 1/Coverage, explicit subagent propagation (not silent 25
— #1698), and that the budget is an exploration allowance not a quality
gate.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.coverage import (
    RECURSION_LIMIT_GENEROUS,
    SILENT_SUBAGENT_FALLBACK,
    measure_coverage,
    recursion_limit_for,
)
from socrates.paths import COVERAGE_PATH, NEED_PATH


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


def test_coverage_budget_scales_inversely_and_propagates_to_subagents():
    need = "Marketplace checkout payments domain."
    foundation = "A Payment belongs to exactly one Order."
    cand_a = "Candidate A: tax included."
    cand_b = "Candidate B: tax excluded."
    cand_c = "Candidate C: tips included."
    new_vs_accepted = "A Payment may belong to many Orders."

    # Sparse pass 1: three Conflicts → low Coverage → generous budget.
    # Mature pass 2: one Reconciliation Conflict → higher Coverage → leaner
    # budget. The whole pulse runs inside the Domain Modeling specialist;
    # the final Behavioral spawn proves #1698 propagation of the
    # chapter-selected limit.
    domain_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": foundation},
                "prop-found",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "acc-found"),
            _tool_call("propose_proposition", {"statement": cand_a}, "p2"),
            _tool_call("propose_proposition", {"statement": cand_b}, "p3"),
            _tool_call("propose_proposition", {"statement": cand_c}, "p4"),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p2",
                    "scenarios_json": json.dumps(_two_scenarios("a")),
                },
                "sc-a",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p2",
                    "outcomes_json": json.dumps(
                        [
                            {
                                "scenario_id": "s1",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "A vs B.",
                                "other_proposition_id": "p3",
                            },
                            {
                                "scenario_id": "s2",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "A vs C.",
                                "other_proposition_id": "p4",
                            },
                        ]
                    ),
                },
                "assert-2",
            ),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p3",
                    "scenarios_json": json.dumps(_two_scenarios("b")),
                },
                "sc-b",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p3",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s3", "survives": True},
                            {
                                "scenario_id": "s4",
                                "survives": False,
                                "kind": "ambiguity",
                                "summary": "B vs C unsettled.",
                                "other_proposition_id": "p4",
                            },
                        ]
                    ),
                },
                "assert-1-more",
            ),
            _tool_call("select_exploration_budget", {}, "budget-sparse"),
            _tool_call("probe_batch", {}, "probe-1"),
            # Pass 2: one L2 via Reconciliation only (no Scenarios required).
            _tool_call("propose_proposition", {"statement": new_vs_accepted}, "prop-l2"),
            _tool_call(
                "reconcile",
                {
                    "findings_json": json.dumps(
                        [
                            {
                                "new_proposition_id": "p5",
                                "against_kind": "accepted",
                                "against_id": "p1",
                                "kind": "contradiction",
                                "summary": "Many-Orders vs exclusive ownership.",
                            }
                        ]
                    )
                },
                "reconcile-pass2",
            ),
            _tool_call("select_exploration_budget", {}, "budget-mature"),
            _tool_call("probe_batch", {}, "probe-2"),
            _tool_call("complete_modeling_activity", {}, "dom-complete"),
            AIMessage(content="dom activity complete."),
        ],
        label="dom",
    )

    main_model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
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
                    "description": "Run Rules under the current budget.",
                },
                "task-beh",
            ),
            AIMessage(content="Coverage budget pass complete."),
        ],
        label="main",
    )

    agent = create_socrates_session(
        model=main_model,
        activity_models={
            "requirements": _chapter_close_stub("req"),
            "domain_modeling": domain_model,
            "behavioral_specification": _chapter_close_stub("beh"),
        },
    )
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
    assert len(probe1["conflicts"]) == 3

    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {"conflict_id": c["id"], "action": "dismiss"}
                    for c in probe1["conflicts"]
                ]
            }
        ),
        config=config,
    )

    probe2 = r["__interrupt__"][0].value
    assert probe2["kind"] == "probe"
    assert len(probe2["conflicts"]) == 1
    assert probe2["conflicts"][0]["level"] == "L2"

    finished = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": probe2["conflicts"][0]["id"],
                        "action": "dismiss",
                    }
                ]
            }
        ),
        config=config,
    )
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    # The chapter's budget selections surface once the task merges its
    # filesystem back: sparse pass 1 (3 Conflicts), mature pass 2 (1 L2).
    final_coverage = _load_json(finished["files"], COVERAGE_PATH)
    assert final_coverage["conflicts_per_pass"] == {"1": 3, "2": 1}
    expected_coverage = measure_coverage(final_coverage["conflicts_per_pass"])
    assert final_coverage["coverage"] == expected_coverage
    assert expected_coverage == 1.0 - (1 / 3)
    mature_limit = final_coverage["recursion_limit"]
    assert mature_limit == recursion_limit_for(expected_coverage)
    # Inverse scaling: fewer Conflicts → higher Coverage → leaner limit.
    sparse_limit = recursion_limit_for(0.0)
    assert sparse_limit == RECURSION_LIMIT_GENEROUS
    assert mature_limit < sparse_limit
    assert mature_limit != SILENT_SUBAGENT_FALLBACK
    assert final_coverage["quality_gate"] is False
    assert final_coverage["role"] == "exploration_allowance"
    assert final_coverage["relevance_anchored"] is True

    # Subagent received the Coverage-selected limit — not silent 25 (#1698).
    # The budget was selected inside the Domain Modeling chapter; the
    # Behavioral spawn that followed carried the mature limit.
    props = final_coverage["subagent_propagations"]
    assert props, "expected BudgetAwareSubagent to record propagation"
    last = props[-1]
    assert last["subagent"] == "behavioral-specification"
    assert last["recursion_limit"] == mature_limit
    assert last["silent_fallback_avoided"] is True
    assert final_coverage["last_subagent_recursion_limit"] == mature_limit

    tool_texts = [
        m.content
        for m in finished["messages"]
        if isinstance(m, ToolMessage) and isinstance(m.content, str)
    ]
    assert any("dom activity complete" in t for t in tool_texts)
