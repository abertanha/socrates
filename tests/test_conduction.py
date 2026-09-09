"""Tickets 13–14 — Conduction core + the pulse moving into the chapters.

Seam: the pure availability rule tested directly (facts in → redirect or
admission), plus the declared orchestration seam (StubChatModel session)
asserting the redirect payloads the model would actually see — the Need
gate, `run_opening` once, wrong-chapter `task` attempts, the pulse's
tail-only admission on the orchestrator surface, and a full pass running
inside a chapter specialist.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.conduction import ConductionState, conduction_check
from socrates.coverage import RECURSION_LIMIT_LEAN
from socrates.paths import CONFLICTS_PATH, COVERAGE_PATH, PIPELINE_PATH


def _thread_config() -> dict:
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


def _tool_call(name: str, args: dict, call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}],
    )


def _tool_result(messages: list, call_id: str) -> dict:
    for m in messages:
        if isinstance(m, ToolMessage) and m.tool_call_id == call_id:
            return json.loads(m.content)
    raise AssertionError(f"no ToolMessage with id {call_id}")


# ---------------------------------------------------------------- pure rule


def test_pre_opening_admits_only_the_opening() -> None:
    state = ConductionState(
        need_registered=False, active=None, completed=()
    )
    assert conduction_check(state, "run_opening", {}) is None
    for tool in (
        "propose_proposition",
        "accept_proposition",
        "reconcile",
        "probe_batch",
        "select_exploration_budget",
        "await_satisfaction",
        "task",
    ):
        redirect = conduction_check(state, tool, {})
        assert redirect is not None, tool
        assert redirect["ok"] is False
        assert redirect["conduction"]["state"] == "pre-opening"
        assert "run_opening" in redirect["conduction"]["admissible_next"]


def test_task_is_gated_pre_opening_too() -> None:
    state = ConductionState(
        need_registered=False, active=None, completed=()
    )
    redirect = conduction_check(
        state, "task", {"subagent_type": "requirements"}
    )
    assert redirect is not None
    assert redirect["conduction"]["state"] == "pre-opening"


def test_opening_runs_once_only() -> None:
    state = ConductionState(
        need_registered=True, active=None, completed=()
    )
    redirect = conduction_check(state, "run_opening", {})
    assert redirect is not None
    assert redirect["ok"] is False
    assert redirect["conduction"]["state"] == "between-chapters"
    assert "task: requirements" in redirect["conduction"]["admissible_next"]


def test_task_admits_only_the_expected_chapter() -> None:
    fresh = ConductionState(
        need_registered=True, active=None, completed=()
    )
    assert conduction_check(fresh, "task", {"subagent_type": "requirements"}) is None
    redirect = conduction_check(
        fresh, "task", {"subagent_type": "behavioral-specification"}
    )
    assert redirect is not None
    assert redirect["conduction"]["attempted"] == "task(behavioral-specification)"
    assert redirect["conduction"]["admissible_next"] == ["task: requirements"]

    mid = ConductionState(
        need_registered=True,
        active="domain_modeling",
        completed=("requirements",),
    )
    assert conduction_check(mid, "task", {"subagent_type": "domain-modeling"}) is None
    # A completed chapter is never re-enterable by task.
    assert conduction_check(mid, "task", {"subagent_type": "requirements"}) is not None


def test_tail_admits_no_chapter_tasks() -> None:
    state = ConductionState(
        need_registered=True,
        active=None,
        completed=(
            "requirements",
            "domain_modeling",
            "behavioral_specification",
        ),
    )
    assert state.label == "tail"
    for subagent in ("requirements", "domain-modeling", "behavioral-specification"):
        assert conduction_check(state, "task", {"subagent_type": subagent}) is not None
    # In-state calls stay admitted — this ticket changes no other behavior.
    assert conduction_check(state, "await_satisfaction", {}) is None
    assert conduction_check(state, "probe_batch", {}) is None


def test_check_is_deterministic() -> None:
    state = ConductionState(
        need_registered=False, active=None, completed=()
    )
    first = conduction_check(state, "probe_batch", {})
    second = conduction_check(state, "probe_batch", {})
    assert first == second


# ------------------------------------------------- ticket 14: the pulse


PULSE_TOOLS = (
    "select_exploration_budget",
    "reconcile",
    "record_scenarios",
    "run_assertion_tests",
    "probe_batch",
    "defer_conflict",
)


def test_pulse_redirects_between_chapters_to_the_next_door() -> None:
    state = ConductionState(
        need_registered=True, active=None, completed=()
    )
    for tool in PULSE_TOOLS:
        redirect = conduction_check(state, tool, {})
        assert redirect is not None, tool
        assert redirect["ok"] is False
        assert redirect["conduction"]["state"] == "between-chapters"
        assert redirect["conduction"]["admissible_next"] == ["task: requirements"]


def test_pulse_redirects_to_the_open_chapter() -> None:
    state = ConductionState(
        need_registered=True,
        active="domain_modeling",
        completed=("requirements",),
    )
    assert state.label == "chapter:domain_modeling"
    redirect = conduction_check(state, "probe_batch", {})
    assert redirect is not None
    assert redirect["conduction"]["state"] == "chapter:domain_modeling"
    assert redirect["conduction"]["attempted"] == "probe_batch"
    assert redirect["conduction"]["admissible_next"] == ["task: domain-modeling"]


def test_pulse_is_admitted_in_the_tail() -> None:
    state = ConductionState(
        need_registered=True,
        active=None,
        completed=(
            "requirements",
            "domain_modeling",
            "behavioral_specification",
        ),
    )
    assert state.label == "tail"
    for tool in PULSE_TOOLS:
        assert conduction_check(state, tool, {}) is None, tool


def test_run_iteration_is_admitted_in_any_post_opening_state() -> None:
    """Iteration is a door move (D6 row 4) — orchestrator-level, any state."""
    between = ConductionState(
        need_registered=True, active=None, completed=()
    )
    chapter = ConductionState(
        need_registered=True,
        active="requirements",
        completed=(),
    )
    assert conduction_check(between, "run_iteration", {"conflict_id": "c1"}) is None
    assert conduction_check(chapter, "run_iteration", {"conflict_id": "c1"}) is None


# ---------------------------------------------------------- orchestration


def test_need_gate_redirects_before_opening_and_admits_after() -> None:
    model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Premature.", "activity": "domain_modeling"},
                "bad-propose",
            ),
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "propose_proposition",
                {"statement": "Scoped.", "activity": "requirements"},
                "ok-propose",
            ),
            AIMessage(content="Proceeding with requirements."),
        ],
        label="main",
    )
    agent = create_socrates_session(model=model)
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"

    # The premature proposal was redirected with the pre-Opening state.
    redirected = _tool_result(r["messages"], "bad-propose")
    assert redirected["ok"] is False
    assert redirected["conduction"]["state"] == "pre-opening"
    assert redirected["conduction"]["attempted"] == "propose_proposition"
    assert "run_opening" in redirected["conduction"]["admissible_next"]

    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    assert r.get("__interrupt__") is None

    # Same tool, now in-state: no conduction payload, normal behavior.
    payload = _tool_result(r["messages"], "ok-propose")
    assert payload["ok"] is True
    assert "conduction" not in payload


def test_opening_once_and_wrong_chapter_task_redirect() -> None:
    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must capture payment authorization."},
                "req-propose",
            ),
            _tool_call("complete_modeling_activity", {}, "req-complete"),
            AIMessage(content="req activity complete."),
        ],
        label="req",
    )
    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call("run_opening", {}, "reopen"),
            _tool_call(
                "task",
                {
                    "subagent_type": "behavioral-specification",
                    "description": "Skip ahead.",
                },
                "wrong-task",
            ),
            _tool_call(
                "task",
                {"subagent_type": "requirements", "description": "Run it."},
                "right-task",
            ),
            AIMessage(content="Chapter one under way."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        model=model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(
        Command(resume="A marketplace checkout."), config=config
    )
    assert r.get("__interrupt__") is None

    # run_opening is done exactly once.
    reopened = _tool_result(r["messages"], "reopen")
    assert reopened["ok"] is False
    assert reopened["conduction"]["state"] == "between-chapters"
    assert "task: requirements" in reopened["conduction"]["admissible_next"]

    # Wrong-chapter task redirected, naming the expected chapter.
    wrong = _tool_result(r["messages"], "wrong-task")
    assert wrong["ok"] is False
    assert wrong["conduction"]["attempted"] == "task(behavioral-specification)"
    assert wrong["conduction"]["admissible_next"] == ["task: requirements"]

    # The behavioral chapter never ran; the requirements chapter did.
    task_results = [
        m
        for m in r["messages"]
        if isinstance(m, ToolMessage) and m.tool_call_id == "right-task"
    ]
    assert task_results and "req activity complete." in task_results[0].content

    pipeline = json.loads(r["files"][PIPELINE_PATH]["content"])
    assert pipeline["completed"] == ["requirements"]
    assert pipeline["active"] is None


# ------------------------------------------- ticket 14: pulse conduction


def _chapter_close_stub(label: str) -> StubChatModel:
    """A specialist that walks in and closes its chapter door — no ground."""
    return StubChatModel(
        responses=[
            _tool_call("complete_modeling_activity", {}, f"{label}-complete"),
            AIMessage(content=f"{label} activity complete."),
        ],
        label=label,
    )


def test_orchestrator_pulse_redirects_outside_the_tail() -> None:
    requirements_model = _chapter_close_stub("req")
    main_model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            # The pulse no longer lives on the orchestrator surface mid-walk.
            _tool_call("probe_batch", {}, "early-probe"),
            _tool_call("select_exploration_budget", {}, "early-budget"),
            _tool_call(
                "task",
                {"subagent_type": "requirements", "description": "Run it."},
                "right-task",
            ),
            AIMessage(content="Chapter one under way."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        model=main_model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    assert r.get("__interrupt__") is None

    early_probe = _tool_result(r["messages"], "early-probe")
    assert early_probe["ok"] is False
    assert early_probe["conduction"]["state"] == "between-chapters"
    assert early_probe["conduction"]["attempted"] == "probe_batch"
    assert early_probe["conduction"]["admissible_next"] == ["task: requirements"]

    early_budget = _tool_result(r["messages"], "early-budget")
    assert early_budget["ok"] is False
    assert early_budget["conduction"]["admissible_next"] == ["task: requirements"]

    # The chapter task itself proceeded untouched.
    task_results = [
        m
        for m in r["messages"]
        if isinstance(m, ToolMessage) and m.tool_call_id == "right-task"
    ]
    assert task_results and "req activity complete." in task_results[0].content


def test_full_pass_runs_inside_a_chapter() -> None:
    """AC 1 + AC 2: propose → budget → Scenarios → Assertion Tests → Probe,
    all inside the chapter specialist — with the chapter's Acceptance and
    Probe interrupts surfacing to the user and the Coverage-selected limit
    propagating to the next subagent spawn."""
    need = "Marketplace checkout payments domain."
    foundation = "A Payment belongs to exactly one Order."
    cand_a = "Candidate A: tax included in total."
    cand_b = "Candidate B: tax excluded from total."

    domain_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition", {"statement": foundation}, "dom-prop-p1"
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "dom-acc-p1"),
            _tool_call("propose_proposition", {"statement": cand_a}, "dom-prop-p2"),
            _tool_call("propose_proposition", {"statement": cand_b}, "dom-prop-p3"),
            _tool_call("select_exploration_budget", {}, "dom-budget"),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p2",
                    "scenarios_json": json.dumps(
                        [
                            {
                                "description": "Tax edge one",
                                "edge": "one",
                                "need_relevant": True,
                            },
                            {
                                "description": "Tax edge many",
                                "edge": "many",
                                "need_relevant": True,
                            },
                        ]
                    ),
                },
                "dom-scenarios",
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
                "dom-assertions",
            ),
            _tool_call("probe_batch", {}, "dom-probe"),
            _tool_call("complete_modeling_activity", {}, "dom-complete"),
            AIMessage(content="domain activity complete."),
        ],
        label="dom",
    )
    main_model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "task",
                {"subagent_type": "requirements", "description": "Requirements."},
                "task-req",
            ),
            _tool_call(
                "task",
                {"subagent_type": "domain-modeling", "description": "Structure."},
                "task-dom",
            ),
            _tool_call(
                "task",
                {"subagent_type": "behavioral-specification", "description": "Rules."},
                "task-beh",
            ),
            AIMessage(content="All chapters done."),
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

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume=need), config=config)

    # The chapter's Acceptance interrupt surfaces from inside the specialist.
    accept = r["__interrupt__"][0].value
    assert accept["kind"] == "accept"
    assert accept["proposition_id"] == "p1"
    r = agent.invoke(Command(resume="yes"), config=config)

    # The chapter's Probe interrupt surfaces with the same payload shape.
    probe = r["__interrupt__"][0].value
    assert probe["kind"] == "probe"
    assert probe["batch_id"] == "b1"
    assert len(probe["conflicts"]) == 1
    conflict = probe["conflicts"][0]
    assert conflict["level"] == "L1"
    assert conflict["other_proposition_id"] == "p3"

    finished = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {"conflict_id": conflict["id"], "action": "dismiss"}
                ]
            }
        ),
        config=config,
    )
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    pipeline = json.loads(finished["files"][PIPELINE_PATH]["content"])
    assert pipeline["completed"] == [
        "requirements",
        "domain_modeling",
        "behavioral_specification",
    ]

    conflicts = json.loads(finished["files"][CONFLICTS_PATH]["content"])[
        "conflicts"
    ]
    assert len(conflicts) == 1
    assert conflicts[0]["status"] == "resolved"

    # The budget was selected inside the chapter and rode the pass: the
    # next subagent spawn carried it explicitly (never the silent 25).
    # Ticket 15: the selection ran before any Conflict existed, and an
    # empty series reads mature by vacuity — so the carried limit is lean.
    coverage = json.loads(finished["files"][COVERAGE_PATH]["content"])
    assert coverage["conflicts_per_pass"] == {"1": 1}
    propagation = coverage["subagent_propagations"][-1]
    assert propagation["subagent"] == "behavioral-specification"
    assert propagation["recursion_limit"] == RECURSION_LIMIT_LEAN
    assert propagation["silent_fallback_avoided"] is True
    assert coverage["last_subagent_recursion_limit"] == RECURSION_LIMIT_LEAN

    task_results = [
        m.content
        for m in finished["messages"]
        if isinstance(m, ToolMessage) and m.tool_call_id == "task-dom"
    ]
    assert task_results and "domain activity complete." in task_results[0]


def test_left_open_chapter_redirects_pulse_to_itself() -> None:
    """A chapter its specialist left open (proposed, never declared complete)
    keeps the orchestrator's pulse redirected back into it."""
    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must capture payment authorization."},
                "req-propose",
            ),
            AIMessage(content="Still working on the Need."),
        ],
        label="req",
    )
    main_model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "task",
                {"subagent_type": "requirements", "description": "Requirements."},
                "task-req",
            ),
            # The specialist returned without closing the door — the pulse
            # must redirect back into the still-open chapter.
            _tool_call("probe_batch", {}, "mid-chapter-probe"),
            AIMessage(content="Chapter still open."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        model=main_model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    assert r.get("__interrupt__") is None

    pipeline = json.loads(r["files"][PIPELINE_PATH]["content"])
    assert pipeline["active"] == "requirements"
    assert pipeline["completed"] == []

    redirected = _tool_result(r["messages"], "mid-chapter-probe")
    assert redirected["ok"] is False
    assert redirected["conduction"]["state"] == "chapter:requirements"
    assert redirected["conduction"]["admissible_next"] == ["task: requirements"]
