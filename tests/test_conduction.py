"""Tickets 13–14 + 17 — Conduction core, the pulse in the chapters, and the
in-chapter rules: treadmill, quiet, and the three-answer door.

Seam: the pure availability rule tested directly (facts in → redirect or
admission), plus the declared orchestration seam (StubChatModel session)
asserting the redirect payloads the model would actually see — the Need
gate, `run_opening` once, wrong-chapter `task` attempts, the pulse's
tail-only admission on the orchestrator surface, and a full pass running
inside a chapter specialist. Ticket 17 adds the in-chapter rules: the
treadmill (≤1 unlapidated Proposition, with the maieutic valve for ground
born from Probe resolution), no new pass while a Batch awaits the user,
quiet-is-counting for the door's declaration, the three-answer door
interrupt (close / not yet / Satisfaction), and the orchestrator propose
tag-gate.
"""

from __future__ import annotations

import json
import uuid

from deepagents.backends.filesystem import FilesystemBackend
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.conduction import (
    CHAPTER,
    ConductionState,
    conduction_check,
    read_conduction_state,
)
from socrates.coverage import RECURSION_LIMIT_LEAN
from socrates.paths import (
    BATCHES_PATH,
    CONFLICTS_PATH,
    COVERAGE_PATH,
    DELIVERABLE_GLOSSARY_PATH,
    NEED_PATH,
    PIPELINE_PATH,
    PROPOSITIONS_PATH,
    SCENARIOS_PATH,
)
from socrates.tools import SATISFACTION_QUESTION

DOOR_ANSWERS = ["close", "not_yet", "satisfaction"]

_ALL_COMPLETED = (
    "requirements",
    "domain_modeling",
    "behavioral_specification",
)


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


def _subagent_messages(agent, config: dict) -> list:
    """A chapter specialist's own message history.

    The specialist runs inside the `task` tool, so its ToolMessages
    (redirect payloads, door results) never merge into the session's
    `messages` — the parent sees only the task ToolMessage carrying the
    specialist's final answer. The specialist's full history lives in its
    checkpoint namespace, which the session checkpointer retains.
    """
    thread = config["configurable"]["thread_id"]
    inner: list = []
    namespaces = {
        ck.config["configurable"].get("checkpoint_ns", "")
        for ck in agent.checkpointer.list(config)
    }
    for ns in (n for n in namespaces if n):
        sub = {"configurable": {"thread_id": thread, "checkpoint_ns": ns}}
        latest = next(iter(agent.checkpointer.list(sub)))
        inner.extend(
            latest.checkpoint.get("channel_values", {}).get("messages", [])
        )
    return inner


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


def _record_scenarios_call(proposition_id: str, prefix: str, call_id: str) -> AIMessage:
    return _tool_call(
        "record_scenarios",
        {
            "proposition_id": proposition_id,
            "scenarios_json": json.dumps(_two_scenarios(prefix)),
        },
        call_id,
    )


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
        completed=_ALL_COMPLETED,
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
        completed=_ALL_COMPLETED,
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


# ------------------------------------------- ticket 17: in-chapter rules


def _chapter_state(**overrides) -> ConductionState:
    defaults: dict = {
        "need_registered": True,
        "active": "requirements",
        "completed": (),
        "unlapidated": (),
        "pending_batch": False,
    }
    defaults.update(overrides)
    return ConductionState(**defaults)


def test_treadmill_redirects_a_second_propose_while_one_is_unlapidated() -> None:
    """D2 invariant: at most one unlapidated Proposition at any moment."""
    state = _chapter_state(unlapidated=(("p1", "requirements"),))
    redirect = conduction_check(
        state, "propose_proposition", {"statement": "Next."}, surface=CHAPTER
    )
    assert redirect is not None
    assert redirect["ok"] is False
    assert redirect["conduction"]["state"] == "chapter:requirements"
    assert redirect["conduction"]["attempted"] == "propose_proposition"
    assert "p1" in redirect["redirect"]
    # Once the predecessor is lapidated, the next propose opens.
    assert (
        conduction_check(
            _chapter_state(), "propose_proposition", {"statement": "Next."},
            surface=CHAPTER,
        )
        is None
    )


def test_treadmill_binds_the_orchestrator_and_is_off_outside_chapters() -> None:
    """The treadmill is an in-chapter rhythm (D2): it binds any surface
    proposing into an open chapter, and it never runs in the tail or
    between chapters, where the valve is the only propose rule."""
    open_chapter = _chapter_state(unlapidated=(("p1", "requirements"),))
    orchestrator_args = {"statement": "Next.", "activity": "requirements"}
    redirect = conduction_check(open_chapter, "propose_proposition", orchestrator_args)
    assert redirect is not None
    assert "p1" in redirect["redirect"]

    between = _chapter_state(active=None)
    assert (
        conduction_check(
            between,
            "propose_proposition",
            {"statement": "S.", "activity": "requirements"},
        )
        is None
    )
    tail = _chapter_state(
        active=None,
        completed=_ALL_COMPLETED,
        unlapidated=(("p9", "domain_modeling"),),
    )
    assert (
        conduction_check(
            tail,
            "propose_proposition",
            {"statement": "S.", "activity": "domain_modeling"},
        )
        is None
    )


def test_valve_proposing_never_waits_on_a_pending_batch() -> None:
    """What queues is the next pass, never the proposition (D2 valve)."""
    state = _chapter_state(pending_batch=True)
    assert (
        conduction_check(
            state, "propose_proposition", {"statement": "Fresh ground."},
            surface=CHAPTER,
        )
        is None
    )


def test_pass_attempts_redirect_while_a_batch_awaits_the_user() -> None:
    """D2 / Batch: "the user clarifies every Conflict in it before the next
    pass runs" — made mechanical on both pulse surfaces."""
    state = _chapter_state(pending_batch=True)
    for tool in (
        "select_exploration_budget",
        "reconcile",
        "record_scenarios",
        "run_assertion_tests",
        "probe_batch",
    ):
        redirect = conduction_check(state, tool, {}, surface=CHAPTER)
        assert redirect is not None, tool
        assert redirect["ok"] is False
        assert redirect["conduction"]["state"] == "chapter:requirements"
        assert redirect["conduction"]["attempted"] == tool
    # Deferral is a resolution move, not a pass — it stays available so a
    # pending Batch's Conflicts can be parked from the tool surface.
    assert (
        conduction_check(
            state, "defer_conflict", {"conflict_id": "c1"}, surface=CHAPTER
        )
        is None
    )
    # The same glossary rule holds on the orchestrator surface (tail passes).
    tail = _chapter_state(
        active=None, completed=_ALL_COMPLETED, pending_batch=True
    )
    assert conduction_check(tail, "probe_batch", {}) is not None


def test_quiet_is_counting_for_the_door() -> None:
    """D3: a chapter is quiet when every Proposition born in it has ≥1 pass
    and no Batch awaits the user — counting, never judgment (ADR-0002)."""
    state = _chapter_state(unlapidated=(("p2", "requirements"),))
    redirect = conduction_check(
        state, "complete_modeling_activity", {}, surface=CHAPTER,
        activity="requirements",
    )
    assert redirect is not None
    assert redirect["ok"] is False
    assert redirect["conduction"]["state"] == "chapter:requirements"
    assert redirect["conduction"]["attempted"] == "complete_modeling_activity"
    assert "p2" in redirect["redirect"]

    # Quiet counts only the chapter's own ground (D3: "born in it").
    other_ground = _chapter_state(unlapidated=(("p9", "domain_modeling"),))
    assert (
        conduction_check(
            other_ground, "complete_modeling_activity", {}, surface=CHAPTER,
            activity="requirements",
        )
        is None
    )

    # A pending Batch on ANY ground blocks the door (passes examine the
    # whole Model).
    pending = _chapter_state(pending_batch=True)
    assert (
        conduction_check(
            pending, "complete_modeling_activity", {}, surface=CHAPTER,
            activity="requirements",
        )
        is not None
    )

    # Deferred Conflicts are not even a fact the door reads — parking is
    # deliberate and never blocks (the orchestration test below proves the
    # ride to the Satisfaction warning).
    quiet = _chapter_state()
    assert (
        conduction_check(
            quiet, "complete_modeling_activity", {}, surface=CHAPTER,
            activity="requirements",
        )
        is None
    )


def test_orchestrator_propose_tag_gate() -> None:
    """D6 Chapter-k-open row: while a chapter is open (or next in
    precedence), an orchestrator propose is admitted only tagged with that
    chapter's Activity; in the tail any tag enters — the valve stays on."""
    open_chapter = _chapter_state(active="requirements")
    wrong = conduction_check(
        open_chapter,
        "propose_proposition",
        {"statement": "S.", "activity": "domain_modeling"},
    )
    assert wrong is not None
    assert wrong["ok"] is False
    assert wrong["conduction"]["state"] == "chapter:requirements"
    assert wrong["conduction"]["attempted"] == "propose_proposition"
    assert wrong["conduction"]["admissible_next"] == [
        "task: requirements",
        "propose_proposition (tag requirements)",
    ]
    right = conduction_check(
        open_chapter,
        "propose_proposition",
        {"statement": "S.", "activity": "requirements"},
    )
    assert right is None

    between = _chapter_state(active=None)
    assert (
        conduction_check(
            between,
            "propose_proposition",
            {"statement": "S.", "activity": "domain_modeling"},
        )
        is not None
    )
    assert (
        conduction_check(
            between,
            "propose_proposition",
            {"statement": "S.", "activity": "requirements"},
        )
        is None
    )

    tail = _chapter_state(active=None, completed=_ALL_COMPLETED)
    for tag in ("requirements", "domain_modeling", "behavioral_specification"):
        assert (
            conduction_check(
                tail,
                "propose_proposition",
                {"statement": "S.", "activity": tag},
            )
            is None
        )


def test_lapidation_and_pending_batch_are_derived_from_the_model(tmp_path) -> None:
    """ADR-0001: no new persisted fields — lapidation and the pending Batch
    are read facts. Ruling: a Proposition is lapidated once ≥1 Scenario is
    recorded for it; Rejected/Superseded ground is dead (it can never be
    lapidated) and never blocks the treadmill."""
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    backend.write(
        PROPOSITIONS_PATH,
        json.dumps(
            {
                "propositions": [
                    {
                        "id": "p1",
                        "statement": "Live, never passed.",
                        "status": "candidate",
                        "activity": "requirements",
                    },
                    {
                        "id": "p2",
                        "statement": "Live, through a pass.",
                        "status": "accepted",
                        "activity": "requirements",
                    },
                    {
                        "id": "p3",
                        "statement": "Dead by rejection.",
                        "status": "rejected",
                        "activity": "requirements",
                    },
                    {
                        "id": "p4",
                        "statement": "Dead by supersede.",
                        "status": "superseded",
                        "activity": "domain_modeling",
                    },
                    {
                        "id": "p5",
                        "statement": "Flagged, still owed a pass.",
                        "status": "flagged",
                        "activity": "requirements",
                    },
                ]
            }
        ),
    )
    backend.write(
        SCENARIOS_PATH,
        json.dumps(
            {
                "scenarios": [
                    {
                        "id": "s1",
                        "proposition_id": "p2",
                        "description": "Through a pass",
                        "edge": "one",
                        "need_relevant": True,
                    }
                ]
            }
        ),
    )
    backend.write(
        BATCHES_PATH,
        json.dumps(
            {"batches": [{"id": "b1", "conflict_ids": ["c1"], "status": "open"}]}
        ),
    )

    state = read_conduction_state(backend)
    assert state.need_registered is True
    assert state.unlapidated == (
        ("p1", "requirements"),
        ("p5", "requirements"),
    )
    assert state.pending_batch is True

    backend.write(
        BATCHES_PATH,
        json.dumps(
            {"batches": [{"id": "b1", "conflict_ids": ["c1"], "status": "probed"}]}
        ),
    )
    assert read_conduction_state(backend).pending_batch is False


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
    agent = create_socrates_session(model=model, reinjection_limit=0)  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
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
            _record_scenarios_call("p1", "authorization", "req-scenarios"),
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
        reinjection_limit=0,
        model=model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(
        Command(resume="A marketplace checkout."), config=config
    )
    # The chapter door interrupts for the user's answer (ticket 17).
    door = r["__interrupt__"][0].value
    assert door["kind"] == "door"
    r = agent.invoke(Command(resume="close"), config=config)
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
        reinjection_limit=0,
        model=main_model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    # The vacuous chapter is quiet by counting — its door still asks.
    assert r["__interrupt__"][0].value["kind"] == "door"
    r = agent.invoke(Command(resume="close"), config=config)
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
    """Tickets 14 + 17: the pulse inside the chapter specialist now runs on
    the treadmill — propose, lapidate (Scenarios + Assertion Tests), resolve,
    interleaved per Proposition — and the chapter closes through the door."""
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
            # Lapidate p1 before the next propose opens (the treadmill).
            _record_scenarios_call("p1", "foundation", "dom-scenarios-p1"),
            _tool_call("propose_proposition", {"statement": cand_a}, "dom-prop-p2"),
            _record_scenarios_call("p2", "cand-a", "dom-scenarios-p2"),
            _tool_call("propose_proposition", {"statement": cand_b}, "dom-prop-p3"),
            _record_scenarios_call("p3", "cand-b", "dom-scenarios-p3"),
            _tool_call("select_exploration_budget", {}, "dom-budget"),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p2",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s3", "survives": True},
                            {
                                "scenario_id": "s4",
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
        reinjection_limit=0,
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
    # Door of the vacuous requirements chapter.
    assert r["__interrupt__"][0].value["kind"] == "door"
    r = agent.invoke(Command(resume="close"), config=config)

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

    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {"conflict_id": conflict["id"], "action": "dismiss"}
                ]
            }
        ),
        config=config,
    )
    # The domain chapter's door, then the behavioral chapter's.
    assert r["__interrupt__"][0].value["kind"] == "door"
    r = agent.invoke(Command(resume="close"), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"
    finished = agent.invoke(Command(resume="close"), config=config)
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
        reinjection_limit=0,
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


# ---------------------------------- ticket 17: treadmill, quiet, the door


def test_door_interrupt_carries_three_answers_and_close_completes() -> None:
    """The door-close declaration interrupts with close / not yet /
    Satisfaction; a vacuous chapter is quiet by counting (D3) and its
    declaration still asks before closing."""
    main_model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "task",
                {"subagent_type": "requirements", "description": "Requirements."},
                "task-req",
            ),
            AIMessage(content="Chapter one closed."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,
        model=main_model,
        activity_models={"requirements": _chapter_close_stub("req")},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)

    door = r["__interrupt__"][0].value
    assert door["kind"] == "door"
    assert door["activity"] == "requirements"
    assert door["question"] == "Confirm closing Modeling Activity 'requirements'?"
    assert door["answers"] == DOOR_ANSWERS

    finished = agent.invoke(Command(resume="close"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    pipeline = json.loads(finished["files"][PIPELINE_PATH]["content"])
    assert pipeline["completed"] == ["requirements"]
    assert pipeline["active"] is None
    completed = _tool_result(_subagent_messages(agent, config), "req-complete")
    assert completed["ok"] is True
    assert completed["door"] == "close"
    assert completed["completed"] == "requirements"


def test_door_unrecognized_and_negated_answers_keep_the_chapter_open() -> None:
    """A mumble never closes (and never routes to Satisfaction), and a
    negated Satisfaction word declines the action's polarity instead of
    routing — the door parses contextually, like accept/reject."""
    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must capture payment authorization."},
                "req-propose-1",
            ),
            _record_scenarios_call("p1", "authorization", "req-scenarios-1"),
            _tool_call("complete_modeling_activity", {}, "req-complete-1"),
            # Mumble → not_yet: knock again.
            _tool_call("complete_modeling_activity", {}, "req-complete-2"),
            # "not satisfied" → not_yet (never the Satisfaction flow).
            _tool_call("complete_modeling_activity", {}, "req-complete-3"),
            AIMessage(content="req activity complete."),
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
            AIMessage(content="Chapter closed on the third knock."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,
        model=main_model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"

    # A mumble never closes and never routes — it is a structured refusal
    # (ticket 28's ask-never-guess): the pending door question stays open
    # and the conductor asks again, not the Satisfaction flow.
    r = agent.invoke(Command(resume="hm, what?"), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"
    mumble = _tool_result(_subagent_messages(agent, config), "req-complete-1")
    assert mumble["ok"] is False
    assert mumble["refused"] is True
    assert mumble["pending"]["kind"] == "door"
    assert mumble["accepted_tokens"] == ["close", "not_yet", "satisfaction"]
    assert mumble["ask_again"] is True

    # Negated Satisfaction declines the polarity: still the door, not the
    # Satisfaction interrupt.
    r = agent.invoke(Command(resume="not satisfied"), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"
    negated = _tool_result(_subagent_messages(agent, config), "req-complete-2")
    assert negated["door"] == "not_yet"
    assert negated["chapter_open"] is True

    finished = agent.invoke(Command(resume="close"), config=config)
    assert finished.get("__interrupt__") is None
    pipeline = json.loads(finished["files"][PIPELINE_PATH]["content"])
    assert pipeline["completed"] == ["requirements"]
    assert pipeline["active"] is None


def test_door_not_yet_keeps_the_chapter_open_with_the_valve_live() -> None:
    """"not yet" leaves the chapter open (D3) — proposing keeps working
    inside it, and the next declaration asks again."""
    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must capture payment authorization."},
                "req-propose-1",
            ),
            _record_scenarios_call("p1", "authorization", "req-scenarios-1"),
            _tool_call("complete_modeling_activity", {}, "req-complete-1"),
            # The door was answered "not yet" — the valve stays live.
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must also capture the buyer's email."},
                "req-propose-2",
            ),
            _record_scenarios_call("p2", "email", "req-scenarios-2"),
            _tool_call("complete_modeling_activity", {}, "req-complete-2"),
            AIMessage(content="req activity complete."),
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
            AIMessage(content="Chapter closed on the second knock."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,
        model=main_model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"

    r = agent.invoke(Command(resume="not yet"), config=config)
    # The chapter stayed open and the door asks again once it is quiet.
    assert r["__interrupt__"][0].value["kind"] == "door"
    kept_open = _tool_result(_subagent_messages(agent, config), "req-complete-1")
    assert kept_open["ok"] is True
    assert kept_open["door"] == "not_yet"
    assert kept_open["chapter_open"] is True
    # The valve stayed live: the second propose went through untouched.
    second = _tool_result(_subagent_messages(agent, config), "req-propose-2")
    assert second["ok"] is True
    assert second["id"] == "p2"

    finished = agent.invoke(Command(resume="close"), config=config)
    assert finished.get("__interrupt__") is None
    pipeline = json.loads(finished["files"][PIPELINE_PATH]["content"])
    assert pipeline["completed"] == ["requirements"]
    assert pipeline["active"] is None


def test_door_satisfaction_answer_routes_to_satisfaction_without_closing() -> None:
    """The door's third answer (D3/D4): Satisfaction terminates the ask at
    the Satisfaction flow — the chapter itself is NOT closed."""
    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must capture payment authorization."},
                "req-propose-1",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "req-acc-1"),
            _record_scenarios_call("p1", "authorization", "req-scenarios-1"),
            _tool_call("complete_modeling_activity", {}, "req-complete"),
            AIMessage(content="req activity stays open."),
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
            AIMessage(content="Ended at the door."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,
        model=main_model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    assert r["__interrupt__"][0].value["kind"] == "accept"
    r = agent.invoke(Command(resume="yes"), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"

    # Third answer: the Satisfaction flow, without the chapter closing.
    r = agent.invoke(Command(resume="satisfaction"), config=config)
    satisfaction = r["__interrupt__"][0].value
    assert satisfaction["kind"] == "satisfaction"
    assert satisfaction["question"] == SATISFACTION_QUESTION

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    pipeline = json.loads(finished["files"][PIPELINE_PATH]["content"])
    assert pipeline["active"] == "requirements"
    assert pipeline["completed"] == []
    door_result = _tool_result(_subagent_messages(agent, config), "req-complete")
    assert door_result["ok"] is True
    assert door_result["door"] == "satisfaction"
    assert door_result["chapter_open"] is True
    # The affirmative Satisfaction materialized the deliverable.
    assert DELIVERABLE_GLOSSARY_PATH in finished["files"]


def test_quiet_redirects_a_premature_completion_declaration() -> None:
    """Declaring completion with unlapidated Propositions redirects — quiet
    is counting; the door itself only opens once the count says quiet."""
    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must capture payment authorization."},
                "req-propose-1",
            ),
            # Premature: p1 has never been through a pass.
            _tool_call("complete_modeling_activity", {}, "req-complete-early"),
            _record_scenarios_call("p1", "authorization", "req-scenarios-1"),
            _tool_call("complete_modeling_activity", {}, "req-complete"),
            AIMessage(content="req activity complete."),
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
            AIMessage(content="Chapter one closed."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,
        model=main_model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    # The premature declaration redirected inside the specialist — the
    # first interrupt the session surfaces is the door of the quiet retry.
    assert r["__interrupt__"][0].value["kind"] == "door"
    finished = agent.invoke(Command(resume="close"), config=config)
    assert finished.get("__interrupt__") is None

    redirected = _tool_result(_subagent_messages(agent, config), "req-complete-early")
    assert redirected["ok"] is False
    assert redirected["conduction"]["state"] == "chapter:requirements"
    assert redirected["conduction"]["attempted"] == "complete_modeling_activity"
    assert "p1" in redirected["redirect"]

    pipeline = json.loads(finished["files"][PIPELINE_PATH]["content"])
    assert pipeline["completed"] == ["requirements"]


def test_treadmill_redirects_until_the_predecessor_is_lapidated() -> None:
    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must capture payment authorization."},
                "req-propose-1",
            ),
            # The treadmill: p1 is unlapidated, the next propose redirects.
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must also capture the buyer's email."},
                "req-propose-early",
            ),
            _record_scenarios_call("p1", "authorization", "req-scenarios-1"),
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must also capture the buyer's email."},
                "req-propose-2",
            ),
            _record_scenarios_call("p2", "email", "req-scenarios-2"),
            _tool_call("complete_modeling_activity", {}, "req-complete"),
            AIMessage(content="req activity complete."),
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
            AIMessage(content="Chapter one closed."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,
        model=main_model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"
    finished = agent.invoke(Command(resume="close"), config=config)
    assert finished.get("__interrupt__") is None

    treadmill = _tool_result(_subagent_messages(agent, config), "req-propose-early")
    assert treadmill["ok"] is False
    assert treadmill["conduction"]["state"] == "chapter:requirements"
    assert treadmill["conduction"]["attempted"] == "propose_proposition"
    assert "p1" in treadmill["redirect"]

    # After lapidation the same propose went through.
    second = _tool_result(_subagent_messages(agent, config), "req-propose-2")
    assert second["ok"] is True
    assert second["id"] == "p2"


def test_valve_ground_born_from_probe_resolution_enters_immediately() -> None:
    """D2's maieutic valve: a Probe resolution that adds ground births it on
    the spot (never tool-gated); the treadmill then demands lapidation of
    everything unlapidated before the next propose."""
    new_ground = "Checkout must also void an authorization."

    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must capture payment authorization."},
                "req-propose-1",
            ),
            _record_scenarios_call("p1", "authorization", "req-scenarios-1"),
            _tool_call(
                "propose_proposition",
                {"statement": "Candidate A: tax included in the total."},
                "req-propose-2",
            ),
            _record_scenarios_call("p2", "cand-a", "req-scenarios-2"),
            _tool_call(
                "propose_proposition",
                {"statement": "Candidate B: tax excluded from the total."},
                "req-propose-3",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p2",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s3", "survives": True},
                            {
                                "scenario_id": "s4",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "Candidates A and B conflict.",
                                "other_proposition_id": "p3",
                            },
                        ]
                    ),
                },
                "req-assertions",
            ),
            _tool_call("probe_batch", {}, "req-probe"),
            # The Probe resolution births new ground while p3 is unlapidated.
            _tool_call(
                "propose_proposition",
                {"statement": "One more ground before lapidating."},
                "req-propose-early",
            ),
            # The Probe closed pass 1; pass 2 reconciles before lapidation.
            _tool_call("reconcile", {"findings_json": "[]"}, "req-reconcile"),
            _record_scenarios_call("p3", "cand-b", "req-scenarios-3"),
            _record_scenarios_call("p4", "probe-born", "req-scenarios-4"),
            _tool_call("complete_modeling_activity", {}, "req-complete"),
            AIMessage(content="req activity complete."),
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
            AIMessage(content="Chapter one closed."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,
        model=main_model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)

    probe = r["__interrupt__"][0].value
    assert probe["kind"] == "probe"
    conflict = probe["conflicts"][0]

    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": conflict["id"],
                        "action": "add_proposition",
                        "statement": new_ground,
                        "activity": "requirements",
                    }
                ]
            }
        ),
        config=config,
    )
    # The probe-born ground entered while p3 was unlapidated (the valve),
    # so the next propose redirects naming BOTH unlapidated Propositions.
    assert r["__interrupt__"][0].value["kind"] == "door"
    finished = agent.invoke(Command(resume="close"), config=config)
    assert finished.get("__interrupt__") is None

    propositions = json.loads(
        finished["files"][PROPOSITIONS_PATH]["content"]
    )["propositions"]
    assert any(p["statement"] == new_ground for p in propositions)

    treadmill = _tool_result(_subagent_messages(agent, config), "req-propose-early")
    assert treadmill["ok"] is False
    assert treadmill["conduction"]["attempted"] == "propose_proposition"
    assert "p3" in treadmill["redirect"]
    assert "p4" in treadmill["redirect"]

    pipeline = json.loads(finished["files"][PIPELINE_PATH]["content"])
    assert pipeline["completed"] == ["requirements"]


def test_deferred_conflict_never_blocks_the_door_and_rides_to_the_warning() -> None:
    """AC: a deferred Conflict does not block the door — it rides to the
    Satisfaction warning (D3: "Deferring never blocks", extended to doors).
    Ticket 20: mid-walk `await_satisfaction` redirects (D6), so the warning
    is reached through the NEXT door's third answer."""
    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "Checkout must capture payment authorization."},
                "req-propose-1",
            ),
            _record_scenarios_call("p1", "authorization", "req-scenarios-1"),
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
                                "summary": "Authorization edge breaks under refund.",
                            },
                            {"scenario_id": "s2", "survives": True},
                        ]
                    ),
                },
                "req-assertions",
            ),
            _tool_call("defer_conflict", {"conflict_id": "c1"}, "req-defer"),
            _tool_call("complete_modeling_activity", {}, "req-complete"),
            AIMessage(content="req activity complete."),
        ],
        label="req",
    )
    domain_model = StubChatModel(
        responses=[
            _tool_call("complete_modeling_activity", {}, "dom-door"),
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
                {"subagent_type": "domain-modeling", "description": "Domain."},
                "task-dom",
            ),
            AIMessage(content="Warned at Satisfaction."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,
        model=main_model,
        activity_models={
            "requirements": requirements_model,
            "domain_modeling": domain_model,
        },
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    # The deferred Conflict does not gate the door — it opened and closed.
    assert r["__interrupt__"][0].value["kind"] == "door"
    r = agent.invoke(Command(resume="close"), config=config)

    # The next chapter's door carries the Satisfaction question (D6).
    assert r["__interrupt__"][0].value["kind"] == "door"
    r = agent.invoke(Command(resume="satisfaction"), config=config)
    satisfaction = r["__interrupt__"][0].value
    assert satisfaction["kind"] == "satisfaction"
    warning = satisfaction["deferred_warning"]
    assert warning is not None
    assert warning["blocking"] is False
    assert [c["id"] for c in warning["conflicts"]] == ["c1"]
    assert warning["chapters_never_visited"] == ["behavioral_specification"]

    finished = agent.invoke(Command(resume="no, more to work through"), config=config)
    assert finished.get("__interrupt__") is None
    pipeline = json.loads(finished["files"][PIPELINE_PATH]["content"])
    assert pipeline["completed"] == ["requirements"]
    # The parked Conflict is still parked — it rode, it did not block.
    conflicts = json.loads(finished["files"][CONFLICTS_PATH]["content"])[
        "conflicts"
    ]
    assert conflicts[0]["status"] == "deferred"


def test_orchestrator_propose_into_open_chapter_is_tag_gated() -> None:
    """D6: while the requirements chapter is open, the orchestrator's
    propose is admitted only tagged requirements."""
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
            _tool_call(
                "propose_proposition",
                {"statement": "A Payment belongs to many Orders.", "activity": "domain_modeling"},
                "wrong-tag",
            ),
            AIMessage(content="Redirected to the open chapter."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,
        model=main_model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A marketplace checkout."), config=config)
    assert r.get("__interrupt__") is None

    redirected = _tool_result(r["messages"], "wrong-tag")
    assert redirected["ok"] is False
    assert redirected["conduction"]["state"] == "chapter:requirements"
    assert redirected["conduction"]["attempted"] == "propose_proposition"
    assert redirected["conduction"]["admissible_next"] == [
        "task: requirements",
        "propose_proposition (tag requirements)",
    ]
    # The mistagged Proposition was never born — only the chapter's own p1.
    propositions = json.loads(r["files"][PROPOSITIONS_PATH]["content"])[
        "propositions"
    ]
    assert [p["id"] for p in propositions] == ["p1"]
    assert all(p["activity"] == "requirements" for p in propositions)
