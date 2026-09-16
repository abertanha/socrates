"""Coverage reading and exploration-budget tests (ticket 15) — read the trend.

Seam one (pure function): Coverage = clamp(1 − EMA_short / EMA_long) over the
conflicts-per-pass series. The named scenarios — flood-decay, oscillation,
decline, rework-rise, vacuity, zeros-invisible — pin the reading and its
smoothing constants; no peak exists, so no burst can hold the signal hostage.
Seam two (virtual FS): the CoverageStore keeps silent passes unrecorded and
persists no derived signal. Seam three (orchestration, stubbed provider,
tickets 14+17 shape — the pulse runs inside the Domain Modeling chapter on
the treadmill, and each chapter closes through its door): recursion_limit ∝
1/Coverage, explicit subagent propagation (not silent 25 — #1698), and the
budget as an exploration allowance, never a quality gate.
"""

from __future__ import annotations

import json
import uuid

import pytest
from deepagents.backends.filesystem import FilesystemBackend
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.coverage import (
    EMA_LONG_ALPHA,
    EMA_LONG_SPAN,
    EMA_SHORT_ALPHA,
    EMA_SHORT_SPAN,
    RECURSION_LIMIT_GENEROUS,
    RECURSION_LIMIT_LEAN,
    SILENT_SUBAGENT_FALLBACK,
    CoverageStore,
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


def _readings(counts: list[int]) -> list[float]:
    """Coverage measured after each pass — how the reading evolves pass-over-pass."""
    return [measure_coverage(counts[: i + 1]) for i in range(len(counts))]


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


def _close_door(agent, config, state, activity: str) -> dict:
    """Resume one chapter door with "close" (ticket 17)."""
    door = state["__interrupt__"][0].value
    assert door["kind"] == "door"
    assert door["activity"] == activity
    return agent.invoke(Command(resume="close"), config=config)


# ---------------------------------------------------------------------------
# Pure-function scenarios: series in → Coverage out
# ---------------------------------------------------------------------------


def test_smoothing_constants_are_pinned():
    # Fixed constants, pinned so the reading stays deterministic and
    # reproducible (recomputed from the persisted series, never stored).
    assert (EMA_SHORT_SPAN, EMA_LONG_SPAN) == (3, 9)
    assert EMA_SHORT_ALPHA == 0.5
    assert EMA_LONG_ALPHA == 0.2


def test_vacuity_never_surfaced_conflict_reads_mature():
    # Mature by vacuity — same edge as the retired peak <= 0 guard: an
    # empty domain leans out immediately.
    assert measure_coverage([]) == 1.0
    assert measure_coverage({}) == 1.0
    assert measure_coverage([0, 0, 0]) == 1.0
    assert recursion_limit_for(measure_coverage([])) == RECURSION_LIMIT_LEAN


def test_flood_decay_opening_burst_fades_no_immortal_peak():
    flood = [30] + [6] * 20
    readings = _readings(flood)

    # Pinned: three passes in, the burst is still recent history.
    assert readings[2] == pytest.approx(0.4382022471910112, abs=1e-9)

    # The old point reading pinned Coverage at 1 − 6/30 = 0.8 forever
    # (limit ~72) — an immortal peak. The crossover has no peak: both
    # averages wash the burst out and steady production reads sparse again.
    assert readings[-1] == pytest.approx(0.04408020484335362, abs=1e-9)
    assert readings[-1] < 0.1

    # Once past its high point the reading only declines as passes
    # accumulate — the burst's influence strictly fades.
    peak_at = readings.index(max(readings))
    tail = readings[peak_at:]
    assert all(later < earlier for earlier, later in zip(tail, tail[1:]))


def test_oscillation_alternating_series_yields_stable_budget():
    alternating = [8, 1] * 8
    readings = _readings(alternating)

    # Pinned readings for the first alternations.
    assert readings[1] == pytest.approx(0.3181818181818182, abs=1e-9)
    assert readings[3] == pytest.approx(0.3644810659186537, abs=1e-9)

    # The old reading swung 0.875 ↔ 0.0 every pass (limits 200 ↔ 60). Both
    # averages move slowly: the reading stays far from the old extremes and
    # the budget never leaves the generous half.
    assert max(readings[1:]) < 0.4
    limits = [recursion_limit_for(c) for c in readings]
    midpoint = (RECURSION_LIMIT_LEAN + RECURSION_LIMIT_GENEROUS) // 2
    assert min(limits) >= midpoint

    # No thrash: per-pass movement stays at most half the old swing of 140.
    swings = [abs(later - earlier) for earlier, later in zip(limits, limits[1:])]
    assert max(swings) <= 70


def test_decline_raises_coverage_smoothly():
    declining = [10, 8, 6, 4, 2]
    readings = _readings(declining)

    # The Model accounts for more of the domain → Coverage only rises.
    assert all(later > earlier for earlier, later in zip(readings, readings[1:]))
    steps = [later - earlier for earlier, later in zip(readings, readings[1:])]
    assert max(steps) < 0.2  # smooth — no single pass jumps the reading
    assert readings[-1] == pytest.approx(0.4236375535459306, abs=1e-9)

    # The budget leans out monotonically with the rising reading.
    limits = [recursion_limit_for(c) for c in readings]
    assert limits == [200, 190, 175, 156, 132]


def test_rework_rise_clamps_coverage_to_zero():
    # Rising production (the rework an Iteration reopens) crosses the short
    # average above the long one — the clamp pins Coverage to 0 and maximum
    # generosity falls out of the formula, with no special case.
    rising = [2, 4, 8, 16]
    assert _readings(rising) == [0.0, 0.0, 0.0, 0.0]
    assert recursion_limit_for(measure_coverage(rising)) == RECURSION_LIMIT_GENEROUS

    # A decline that reopens: Coverage had risen, and the rising tail clamps
    # it straight back to 0 — Iteration needs no reset.
    reopened = [6, 6, 4, 2, 6, 10]
    readings = _readings(reopened)
    assert readings[3] == pytest.approx(0.2827868852459018, abs=1e-9)
    assert readings[-1] == 0.0


def test_zero_conflict_passes_stay_invisible(tmp_path):
    # Silence neither raises nor lowers the signal (the refused defect —
    # ADR-0004's asymmetry): zeros are filtered before the averages run.
    assert measure_coverage([8, 1]) == measure_coverage([8, 0, 1])
    assert measure_coverage([8, 1]) == measure_coverage([0, 8, 0, 1, 0])
    # Numbering gaps left by silent passes do not distort the series.
    assert measure_coverage({"1": 8, "2": 1}) == measure_coverage({"1": 8, "3": 1})

    # The store keeps the same guard: a zero-conflict pass is never recorded.
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    store = CoverageStore(backend)
    store.add_conflicts(1, 8)
    store.add_conflicts(2, 0)
    assert store.snapshot()["conflicts_per_pass"] == {"1": 8}
    assert store.measure() == measure_coverage([8])
    # Measurement recomputes from the series — no derived signal (no
    # Coverage reading, no smoothing state) is persisted beside it.
    assert set(store.snapshot()) <= {"conflicts_per_pass", "subagent_propagations"}


# ---------------------------------------------------------------------------
# Orchestration: budget selection inside the chapter, propagation to subagents
# ---------------------------------------------------------------------------


def test_coverage_budget_scales_inversely_and_propagates_to_subagents():
    need = "Marketplace checkout payments domain."
    foundation = "A Payment belongs to exactly one Order."
    cand_a = "Candidate A: tax included."
    cand_b = "Candidate B: tax excluded."
    cand_c = "Candidate C: tips included."
    new_vs_accepted = "A Payment may belong to many Orders."

    # Sparse pass 1: three Conflicts → the seed pass reads 0.0 Coverage →
    # generous budget. Mature pass 2: one Reconciliation Conflict → the
    # trend reading rises → leaner budget. The whole pulse runs inside the
    # Domain Modeling specialist on the treadmill (each Proposition
    # lapidated before the next propose — ticket 17); the final Behavioral
    # spawn proves #1698 propagation of the chapter-selected limit.
    domain_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": foundation},
                "prop-found",
            ),
            _tool_call("accept_proposition", {"proposition_id": "p1"}, "acc-found"),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(_two_scenarios("found")),
                },
                "sc-found",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p1",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s1", "survives": True},
                            {"scenario_id": "s2", "survives": True},
                        ]
                    ),
                },
                "assert-found",
            ),
            _tool_call("propose_proposition", {"statement": cand_a}, "p2"),
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
                            {"scenario_id": "s3", "survives": True},
                            {"scenario_id": "s4", "survives": True},
                        ]
                    ),
                },
                "assert-a-quiet",
            ),
            _tool_call("propose_proposition", {"statement": cand_b}, "p3"),
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
                            {"scenario_id": "s5", "survives": True},
                            {"scenario_id": "s6", "survives": True},
                        ]
                    ),
                },
                "assert-b-quiet",
            ),
            _tool_call("propose_proposition", {"statement": cand_c}, "p4"),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p4",
                    "scenarios_json": json.dumps(_two_scenarios("c")),
                },
                "sc-c",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p4",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s7", "survives": True},
                            {"scenario_id": "s8", "survives": True},
                        ]
                    ),
                },
                "assert-c-quiet",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p2",
                    "outcomes_json": json.dumps(
                        [
                            {
                                "scenario_id": "s3",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "A vs B.",
                                "other_proposition_id": "p3",
                            },
                            {
                                "scenario_id": "s4",
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
                "run_assertion_tests",
                {
                    "proposition_id": "p3",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s5", "survives": True},
                            {
                                "scenario_id": "s6",
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
            # Pass 2: one L2 via Reconciliation; the proposed ground
            # lapidates after its Probe resolves (the treadmill — 17) so
            # the chapter goes quiet for the door.
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
            # The Probe resolution unblocks p5 (Reconciliation-contradicted
            # ground cannot lapidate while its Conflict is open) and opens
            # pass 3 — an empty Reconciliation satisfies the pass gate, then
            # p5 lapidates so the chapter goes quiet for the door (17).
            _tool_call("reconcile", {"findings_json": "[]"}, "reconcile-empty"),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p5",
                    "scenarios_json": json.dumps(_two_scenarios("l2")),
                },
                "sc-l2",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p5",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s9", "survives": True},
                            {"scenario_id": "s10", "survives": True},
                        ]
                    ),
                },
                "assert-l2",
            ),
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
        reinjection_limit=0,  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
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
    # The vacuous requirements chapter asks at its door before Domain
    # Modeling opens (ticket 17).
    r = _close_door(agent, config, r, "requirements")
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

    r = agent.invoke(
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
    # The Domain chapter's door — every Proposition lapidated on the
    # treadmill, no pending Batch — then the vacuous Behavioral chapter's.
    r = _close_door(agent, config, r, "domain_modeling")
    finished = _close_door(agent, config, r, "behavioral_specification")
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    # The chapter's budget selections surface once the task merges its
    # filesystem back: sparse pass 1 (3 Conflicts), mature pass 2 (1 L2).
    final_coverage = _load_json(finished["files"], COVERAGE_PATH)
    assert final_coverage["conflicts_per_pass"] == {"1": 3, "2": 1}
    expected_coverage = measure_coverage(final_coverage["conflicts_per_pass"])
    assert final_coverage["coverage"] == expected_coverage
    # The trend reading after 3 → 1: clamp(1 − EMA_3 / EMA_9) = 3/13 —
    # not the old point reading 1 − 1/3.
    assert expected_coverage == pytest.approx(3 / 13, abs=1e-9)
    mature_limit = final_coverage["recursion_limit"]
    assert mature_limit == recursion_limit_for(expected_coverage) == 163
    # Inverse scaling: fewer Conflicts → higher Coverage → leaner limit.
    sparse_limit = recursion_limit_for(0.0)
    assert sparse_limit == RECURSION_LIMIT_GENEROUS
    assert mature_limit < sparse_limit
    assert mature_limit != SILENT_SUBAGENT_FALLBACK
    assert final_coverage["quality_gate"] is False
    assert final_coverage["role"] == "exploration_allowance"
    assert final_coverage["relevance_anchored"] is True

    # Subagents received Coverage-selected limits — never silent 25 (#1698).
    props = final_coverage["subagent_propagations"]
    assert props, "expected BudgetAwareSubagent to record propagation"
    # Requirements ran before any Conflict existed: the vacuity edge at the
    # live seam — an empty series reads mature, so the lean limit propagated.
    first = props[0]
    assert first["subagent"] == "requirements"
    assert first["recursion_limit"] == RECURSION_LIMIT_LEAN
    # The budget was selected inside the Domain Modeling chapter; the
    # Behavioral spawn that followed carried the mature limit.
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
