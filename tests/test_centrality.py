"""Orchestration test for ticket 16 — Centrality signal + honest criticality reason.

Seam: session orchestration with the model provider stubbed (tickets 14+17
shape: close-only chapter specialists via ``activity_models`` — each closing
through its door — then the orchestrator proposes in the tail, where it
keeps the pulse). Covers: the Central Proposition signal (transitive
derivation subtree in the ``accepted_via`` graph ∨ Requirements activity,
derived at assessment time and never stored), the honest
``central_proposition`` reason, the graded Satisfaction warning (weight
descending, ties to the Requirements side), L4 stakes decoration (never
gating), and recompute after a Supersede cascade.
"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.paths import (
    CONFLICTS_PATH,
    NEED_PATH,
    NOTIFICATIONS_PATH,
    PIPELINE_PATH,
    PROPOSITIONS_PATH,
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


def _load_json(files: dict, path: str) -> dict:
    return json.loads(files[path]["content"])


def _two_scenarios(prefix: str, *, first_edge: str = "one") -> list[dict]:
    return [
        {
            "description": f"{prefix} edge {first_edge}",
            "edge": first_edge,
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


def _three_chapter_walk() -> list[AIMessage]:
    """Walk the three chapters so the orchestrator reaches the tail."""
    return [
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
                "description": "Run Rules.",
            },
            "task-beh",
        ),
    ]


def _close_stubs() -> dict:
    return {
        "requirements": _chapter_close_stub("req"),
        "domain_modeling": _chapter_close_stub("dom"),
        "behavioral_specification": _chapter_close_stub("beh"),
    }


def _walk_doors(agent, config, r) -> dict:
    """Answer "close" at each of the three chapter doors (ticket 17)."""
    for activity in ("requirements", "domain_modeling", "behavioral_specification"):
        door = r["__interrupt__"][0].value
        assert door["kind"] == "door"
        assert door["activity"] == activity
        r = agent.invoke(Command(resume="close"), config=config)
    return r


def _accept_call(proposition_id: str, call_id: str, via: str = "") -> AIMessage:
    args = {"proposition_id": proposition_id}
    if via:
        args["via_proposition_id"] = via
    return _tool_call("accept_proposition", args, call_id)


def _defer_resolution(conflict_id: str) -> dict:
    return {
        "resolutions": [{"conflict_id": conflict_id, "action": "defer"}],
    }


def _centrality(central: bool, dimension: str | None, dependents: int, weight: int):
    return {
        "central": central,
        "dimension": dimension,
        "dependents": dependents,
        "weight": weight,
    }


def test_derivation_subtree_reads_central_and_leaf_reads_peripheral():
    """Transitive dependents make a party central; leaves do not flag risk."""
    need = "Marketplace checkout payments domain."
    ownly = "A Payment belongs to exactly one Order."
    total = "An Order total equals the sum of its Payments."
    refund = "A refunded Payment restores the Order total."
    cand_a = "Candidate A: tax included in total."
    cand_b = "Candidate B: tax excluded from total."
    many = "A Payment may belong to many Orders."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            *_three_chapter_walk(),
            _tool_call(
                "propose_proposition",
                {"statement": ownly, "activity": "domain_modeling"},
                "prop-p1",
            ),
            _accept_call("p1", "acc-p1"),
            _tool_call(
                "propose_proposition",
                {"statement": total, "activity": "domain_modeling"},
                "prop-p2",
            ),
            _accept_call("p2", "acc-p2", via="p1"),
            _tool_call(
                "propose_proposition",
                {"statement": refund, "activity": "domain_modeling"},
                "prop-p3",
            ),
            _accept_call("p3", "acc-p3", via="p2"),
            # Leaf skirmish: two candidates, nothing derived via either.
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
                    "scenarios_json": json.dumps(_two_scenarios("leaf")),
                },
                "sc-leaf",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p4",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s1", "survives": True},
                            {
                                "scenario_id": "s2",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "Leaf candidates clash.",
                                "other_proposition_id": "p5",
                            },
                        ]
                    ),
                },
                "assert-leaf",
            ),
            _tool_call("probe_batch", {}, "probe-leaf"),
            # Pass 2: the new information contradicts the subtree root.
            _tool_call(
                "propose_proposition",
                {"statement": many, "activity": "domain_modeling"},
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
                "reconcile-l2",
            ),
            _tool_call("probe_batch", {}, "probe-l2"),
            _tool_call("await_satisfaction", {}, "satisfaction"),
            AIMessage(content="Centrality read from the graph."),
        ]
    )
    agent = create_socrates_session(model=model, activity_models=_close_stubs())
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start")]},
        config=config,
    )
    assert opening["__interrupt__"][0].value["kind"] == "opening"

    r = agent.invoke(Command(resume=need), config=config)
    assert r["files"][NEED_PATH]["content"] == need
    r = _walk_doors(agent, config, r)
    r = agent.invoke(Command(resume="yes"), config=config)  # p1
    r = agent.invoke(Command(resume="yes"), config=config)  # p2 via p1
    r = agent.invoke(Command(resume="yes"), config=config)  # p3 via p2

    # Leaf parties read peripheral: no risk flag on their Conflict.
    probe_leaf = r["__interrupt__"][0].value
    assert probe_leaf["kind"] == "probe"
    leaf = probe_leaf["conflicts"][0]
    assert leaf["level"] == "L1"
    assert leaf["deferral"]["critical"] is False
    assert leaf["deferral"]["recommend_against"] is False
    assert leaf["deferral"]["reasons"] == []
    leaf_parties = {p["id"]: p["centrality"] for p in leaf["deferral"]["parties"]}
    assert leaf_parties == {
        "p4": _centrality(False, None, 0, 0),
        "p5": _centrality(False, None, 0, 0),
    }

    r = agent.invoke(Command(resume=_defer_resolution(leaf["id"])), config=config)

    # The subtree root reads central — dependents counted transitively
    # (p2 direct, p3 via p2), the same closure a Supersede would Degrade.
    probe_l2 = r["__interrupt__"][0].value
    assert probe_l2["kind"] == "probe"
    l2 = probe_l2["conflicts"][0]
    assert l2["level"] == "L2"
    assert l2["deferral"]["critical"] is True
    assert l2["deferral"]["recommend_against"] is True
    assert l2["deferral"]["reasons"] == ["high_conflict_level", "central_proposition"]
    parties = {p["id"]: p["centrality"] for p in l2["deferral"]["parties"]}
    assert parties == {
        "p6": _centrality(False, None, 0, 0),
        "p1": _centrality(True, "derivation", 2, 2),
    }

    r = agent.invoke(Command(resume=_defer_resolution(l2["id"])), config=config)

    # Satisfaction warning: heaviest structural risk first, still non-blocking,
    # recommendation still boolean.
    satisfaction = r["__interrupt__"][0].value
    assert satisfaction["kind"] == "satisfaction"
    assert satisfaction["question"] == SATISFACTION_QUESTION
    warning = satisfaction["deferred_warning"]
    assert warning["kind"] == "deferred_conflicts"
    assert warning["blocking"] is False
    assert [c["id"] for c in warning["conflicts"]] == [l2["id"], leaf["id"]]
    heavy, light = warning["conflicts"]
    assert heavy["weight"] == 2
    assert heavy["dependents"] == 2
    assert heavy["criticality"]["recommend_against"] is True
    assert light["weight"] == 0
    assert light["criticality"]["recommend_against"] is False

    finished = agent.invoke(Command(resume="not yet"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()

    # No new persisted state: centrality is derived, never stored beside the
    # Model. The Need stays a plain text filter, never a Proposition.
    raw_props = finished["files"][PROPOSITIONS_PATH]["content"]
    propositions = _load_json(finished["files"], PROPOSITIONS_PATH)["propositions"]
    assert "centrality" not in raw_props
    assert '"weight"' not in raw_props
    assert all(
        set(p) <= {"id", "statement", "status", "activity", "reason",
                   "flagged_against_id", "accepted_via"}
        for p in propositions
    )
    assert need not in {p["statement"] for p in propositions}
    assert finished["files"][NEED_PATH]["content"] == need


def test_requirements_proposition_reads_central_from_first_moment():
    """Requirements activity alone is central — before any Acceptance or via-edge."""
    need = "Marketplace checkout payments domain."
    need_synthesis = "Checkout exists to settle payments for marketplace orders."
    installment = "An Order may be settled in installments."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            *_three_chapter_walk(),
            _tool_call(
                "propose_proposition",
                {"statement": need_synthesis, "activity": "requirements"},
                "prop-p1",
            ),
            _tool_call(
                "propose_proposition",
                {"statement": installment, "activity": "domain_modeling"},
                "prop-p2",
            ),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(_two_scenarios("req")),
                },
                "sc-req",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p1",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s1", "survives": True},
                            {
                                "scenario_id": "s2",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "Settlement scope clashes.",
                                "other_proposition_id": "p2",
                            },
                        ]
                    ),
                },
                "assert-req",
            ),
            _tool_call("probe_batch", {}, "probe-req"),
            AIMessage(content="Requirements centrality observed."),
        ]
    )
    agent = create_socrates_session(model=model, activity_models=_close_stubs())
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start")]},
        config=config,
    )
    r = agent.invoke(Command(resume=need), config=config)
    r = _walk_doors(agent, config, r)

    probe = r["__interrupt__"][0].value
    assert probe["kind"] == "probe"
    conflict = probe["conflicts"][0]
    # L1: neither party is Accepted — so `central_proposition` here proves the
    # reason means the defined concept, not "any party Accepted".
    assert conflict["level"] == "L1"
    assert conflict["deferral"]["critical"] is True
    assert conflict["deferral"]["recommend_against"] is True
    assert conflict["deferral"]["reasons"] == ["central_proposition"]
    parties = {p["id"]: p["centrality"] for p in conflict["deferral"]["parties"]}
    assert parties == {
        "p1": _centrality(True, "requirements", 0, 1),
        "p2": _centrality(False, None, 0, 0),
    }

    finished = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {"conflict_id": conflict["id"], "action": "dismiss"},
                ]
            }
        ),
        config=config,
    )
    assert finished.get("__interrupt__") is None
    # First moment, verbatim on the filesystem: still a Candidate, no via-edge.
    props = {
        p["id"]: p
        for p in _load_json(finished["files"], PROPOSITIONS_PATH)["propositions"]
    }
    assert props["p1"]["status"] == "candidate"
    assert props["p1"]["accepted_via"] is None


def test_centrality_recomputes_after_supersede_cascade():
    """A Proposition that lost dependents to a cascade stops reading central."""
    need = "Marketplace checkout payments domain."
    ownly = "A Payment belongs to exactly one Order."
    total = "An Order total equals the sum of its Payments."
    refund = "A refunded Payment restores the Order total."
    cand_a = "Candidate A: tax included in total."
    cand_b = "Candidate B: tax excluded from total."
    many = "A Payment may belong to many Orders."
    fixed = "An Order total is fixed at checkout."
    several = "A Payment may settle several Orders."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            *_three_chapter_walk(),
            _tool_call(
                "propose_proposition",
                {"statement": ownly, "activity": "domain_modeling"},
                "prop-p1",
            ),
            _accept_call("p1", "acc-p1"),
            _tool_call(
                "propose_proposition",
                {"statement": total, "activity": "domain_modeling"},
                "prop-p2",
            ),
            _accept_call("p2", "acc-p2", via="p1"),
            _tool_call(
                "propose_proposition",
                {"statement": refund, "activity": "domain_modeling"},
                "prop-p3",
            ),
            _accept_call("p3", "acc-p3", via="p2"),
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
                    "scenarios_json": json.dumps(_two_scenarios("leaf")),
                },
                "sc-leaf",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p4",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s1", "survives": True},
                            {
                                "scenario_id": "s2",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "Leaf candidates clash.",
                                "other_proposition_id": "p5",
                            },
                        ]
                    ),
                },
                "assert-leaf",
            ),
            _tool_call("probe_batch", {}, "probe-1"),
            # Pass 2: L2 against the subtree root (dependents p2, p3).
            _tool_call(
                "propose_proposition",
                {"statement": many, "activity": "domain_modeling"},
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
                "reconcile-c2",
            ),
            _tool_call("probe_batch", {}, "probe-2"),
            # Pass 3: L2 against the mid-node (dependent p3) — Supersede it.
            _tool_call(
                "propose_proposition",
                {"statement": fixed, "activity": "domain_modeling"},
                "prop-p7",
            ),
            _tool_call(
                "reconcile",
                {
                    "findings_json": json.dumps(
                        [
                            {
                                "new_proposition_id": "p7",
                                "against_kind": "accepted",
                                "against_id": "p2",
                                "kind": "contradiction",
                                "summary": "Fixed total vs recomputed total.",
                            }
                        ]
                    )
                },
                "reconcile-c3",
            ),
            _tool_call("probe_batch", {}, "probe-3"),
            # Pass 4: L2 against the root again — its subtree is gone.
            _tool_call(
                "propose_proposition",
                {"statement": several, "activity": "domain_modeling"},
                "prop-p8",
            ),
            _tool_call(
                "reconcile",
                {
                    "findings_json": json.dumps(
                        [
                            {
                                "new_proposition_id": "p8",
                                "against_kind": "accepted",
                                "against_id": "p1",
                                "kind": "contradiction",
                                "summary": "Several Orders vs exclusive ownership.",
                            }
                        ]
                    )
                },
                "reconcile-c4",
            ),
            _tool_call("probe_batch", {}, "probe-4"),
            _tool_call("await_satisfaction", {}, "satisfaction"),
            AIMessage(content="Recompute observed."),
        ]
    )
    agent = create_socrates_session(model=model, activity_models=_close_stubs())
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start")]},
        config=config,
    )
    r = agent.invoke(Command(resume=need), config=config)
    r = _walk_doors(agent, config, r)
    r = agent.invoke(Command(resume="yes"), config=config)  # p1
    r = agent.invoke(Command(resume="yes"), config=config)  # p2 via p1
    r = agent.invoke(Command(resume="yes"), config=config)  # p3 via p2

    probe1 = r["__interrupt__"][0].value
    assert probe1["kind"] == "probe"
    leaf = probe1["conflicts"][0]
    assert leaf["level"] == "L1"
    r = agent.invoke(Command(resume=_defer_resolution(leaf["id"])), config=config)

    probe2 = r["__interrupt__"][0].value
    c2 = probe2["conflicts"][0]
    assert c2["deferral"]["parties"][1]["centrality"] == _centrality(
        True, "derivation", 2, 2
    )
    r = agent.invoke(Command(resume=_defer_resolution(c2["id"])), config=config)

    probe3 = r["__interrupt__"][0].value
    c3 = probe3["conflicts"][0]
    assert c3["deferral"]["parties"][1]["centrality"] == _centrality(
        True, "derivation", 1, 1
    )
    # Supersede the mid-node: the cascade Degrades its dependent p3.
    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": c3["id"],
                        "action": "supersede",
                        "reason": "Totals are fixed at checkout.",
                    }
                ]
            }
        ),
        config=config,
    )
    cascades = [
        n
        for n in _load_json(r["files"], NOTIFICATIONS_PATH)["notifications"]
        if n["kind"] == "supersede_cascade"
    ]
    assert len(cascades) == 1
    assert cascades[0]["superseded_id"] == "p2"
    assert cascades[0]["degraded_ids"] == ["p3"]

    probe4 = r["__interrupt__"][0].value
    c4 = probe4["conflicts"][0]
    # The root lost its whole subtree to the cascade: peripheral again, and
    # the level reason alone carries the (still boolean) recommendation.
    parties = {p["id"]: p["centrality"] for p in c4["deferral"]["parties"]}
    assert parties == {
        "p8": _centrality(False, None, 0, 0),
        "p1": _centrality(False, None, 0, 0),
    }
    assert c4["deferral"]["reasons"] == ["high_conflict_level"]
    assert c4["deferral"]["critical"] is True
    assert c4["deferral"]["recommend_against"] is True
    # Supersede resolves via the peripheral root — the cascade still notifies.
    r = agent.invoke(
        Command(
            resume={
                "resolutions": [
                    {
                        "conflict_id": c4["id"],
                        "action": "supersede",
                        "reason": "Payments may settle several Orders.",
                    }
                ]
            }
        ),
        config=config,
    )
    cascades = [
        n
        for n in _load_json(r["files"], NOTIFICATIONS_PATH)["notifications"]
        if n["kind"] == "supersede_cascade"
    ]
    assert len(cascades) == 2
    assert cascades[1]["superseded_id"] == "p1"
    assert cascades[1]["degraded_ids"] == []

    satisfaction = r["__interrupt__"][0].value
    assert satisfaction["kind"] == "satisfaction"
    warning = satisfaction["deferred_warning"]
    assert warning["blocking"] is False
    # The parked L2 re-weighs against the current graph: its root is
    # peripheral now, so both deferred Conflicts weigh zero (id order).
    assert [c["id"] for c in warning["conflicts"]] == [leaf["id"], c2["id"]]
    recomputed = {p["id"]: p for p in warning["conflicts"][1]["criticality"]["parties"]}
    assert recomputed["p1"]["centrality"] == _centrality(False, None, 0, 0)
    assert warning["conflicts"][1]["weight"] == 0

    finished = agent.invoke(Command(resume="not yet"), config=config)
    assert finished.get("__interrupt__") is None
    props = {
        p["id"]: p
        for p in _load_json(finished["files"], PROPOSITIONS_PATH)["propositions"]
    }
    assert props["p1"]["status"] == "superseded"
    assert props["p2"]["status"] == "superseded"
    assert props["p3"]["status"] == "candidate"
    assert props["p3"]["accepted_via"] is None


def test_warning_ties_resolve_to_requirements_side():
    """Equal weight: the Requirements-touching Conflict is read first."""
    need = "Marketplace checkout payments domain."
    ownly = "A Payment belongs to exactly one Order."
    total = "An Order total equals the sum of its Payments."
    need_synthesis = "Checkout exists to settle payments for marketplace orders."
    cand_a = "Candidate A: tax included in total."
    cand_b = "Candidate B: tax excluded from total."
    many = "A Payment may belong to many Orders."
    outside = "Checkout settles payments outside the marketplace."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            *_three_chapter_walk(),
            _tool_call(
                "propose_proposition",
                {"statement": ownly, "activity": "domain_modeling"},
                "prop-p1",
            ),
            _accept_call("p1", "acc-p1"),
            _tool_call(
                "propose_proposition",
                {"statement": total, "activity": "domain_modeling"},
                "prop-p2",
            ),
            _accept_call("p2", "acc-p2", via="p1"),
            _tool_call(
                "propose_proposition",
                {"statement": need_synthesis, "activity": "requirements"},
                "prop-p3",
            ),
            _accept_call("p3", "acc-p3"),
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
                    "scenarios_json": json.dumps(_two_scenarios("leaf")),
                },
                "sc-leaf",
            ),
            _tool_call(
                "run_assertion_tests",
                {
                    "proposition_id": "p4",
                    "outcomes_json": json.dumps(
                        [
                            {"scenario_id": "s1", "survives": True},
                            {
                                "scenario_id": "s2",
                                "survives": False,
                                "kind": "contradiction",
                                "summary": "Leaf candidates clash.",
                                "other_proposition_id": "p5",
                            },
                        ]
                    ),
                },
                "assert-leaf",
            ),
            _tool_call("probe_batch", {}, "probe-1"),
            # Pass 2: L2 against the derivation side (weight 1).
            _tool_call(
                "propose_proposition",
                {"statement": many, "activity": "domain_modeling"},
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
                "reconcile-c2",
            ),
            _tool_call("probe_batch", {}, "probe-2"),
            # Pass 3: L2 against the Requirements side (weight 1).
            _tool_call(
                "propose_proposition",
                {"statement": outside, "activity": "domain_modeling"},
                "prop-p7",
            ),
            _tool_call(
                "reconcile",
                {
                    "findings_json": json.dumps(
                        [
                            {
                                "new_proposition_id": "p7",
                                "against_kind": "accepted",
                                "against_id": "p3",
                                "kind": "contradiction",
                                "summary": "Outside settlement vs Need scope.",
                            }
                        ]
                    )
                },
                "reconcile-c3",
            ),
            _tool_call("probe_batch", {}, "probe-3"),
            _tool_call("await_satisfaction", {}, "satisfaction"),
            AIMessage(content="Tie observed."),
        ]
    )
    agent = create_socrates_session(model=model, activity_models=_close_stubs())
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start")]},
        config=config,
    )
    r = agent.invoke(Command(resume=need), config=config)
    r = _walk_doors(agent, config, r)
    r = agent.invoke(Command(resume="yes"), config=config)  # p1
    r = agent.invoke(Command(resume="yes"), config=config)  # p2 via p1
    r = agent.invoke(Command(resume="yes"), config=config)  # p3

    probe1 = r["__interrupt__"][0].value
    leaf = probe1["conflicts"][0]
    r = agent.invoke(Command(resume=_defer_resolution(leaf["id"])), config=config)

    probe2 = r["__interrupt__"][0].value
    c2 = probe2["conflicts"][0]
    r = agent.invoke(Command(resume=_defer_resolution(c2["id"])), config=config)

    probe3 = r["__interrupt__"][0].value
    c3 = probe3["conflicts"][0]
    parties3 = {p["id"]: p["centrality"] for p in c3["deferral"]["parties"]}
    assert parties3["p3"] == _centrality(True, "requirements", 0, 1)
    r = agent.invoke(Command(resume=_defer_resolution(c3["id"])), config=config)

    satisfaction = r["__interrupt__"][0].value
    assert satisfaction["kind"] == "satisfaction"
    warning = satisfaction["deferred_warning"]
    assert warning["blocking"] is False
    # c3 and c2 tie at weight 1 — Requirements edges ahead; the leaf reads last.
    assert [c["id"] for c in warning["conflicts"]] == [c3["id"], c2["id"], leaf["id"]]
    first, second, third = warning["conflicts"]
    assert first["weight"] == second["weight"] == 1
    assert first["requirements"] is True
    assert second["requirements"] is False
    assert third["weight"] == 0
    # Recommendation stays boolean while the evidence is graded.
    assert first["criticality"]["recommend_against"] is True
    assert second["criticality"]["recommend_against"] is True
    assert third["criticality"]["recommend_against"] is False

    finished = agent.invoke(Command(resume="not yet"), config=config)
    assert finished.get("__interrupt__") is None
    remaining = _load_json(finished["files"], CONFLICTS_PATH)["conflicts"]
    assert {c["id"]: c["status"] for c in remaining} == {
        leaf["id"]: "deferred",
        c2["id"]: "deferred",
        c3["id"]: "deferred",
    }


def test_l4_stakes_decorated_but_never_gated():
    """Unavoidable Notification and Iteration proposal carry centrality as stakes."""
    need = "Marketplace checkout payments domain."
    ownly = "A Payment belongs to exactly one Order."
    total = "An Order total equals the sum of its Payments."
    capture = "Checkout must capture payment authorization before settlement."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            *_three_chapter_walk(),
            _tool_call(
                "propose_proposition",
                {"statement": ownly, "activity": "domain_modeling"},
                "prop-p1",
            ),
            _accept_call("p1", "acc-p1"),
            _tool_call(
                "propose_proposition",
                {"statement": total, "activity": "domain_modeling"},
                "prop-p2",
            ),
            _accept_call("p2", "acc-p2", via="p1"),
            _tool_call(
                "propose_proposition",
                {"statement": capture, "activity": "requirements"},
                "prop-p3",
            ),
            _accept_call("p3", "acc-p3"),
            _tool_call(
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(
                        _two_scenarios("l4", first_edge="intersection")
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
                                "summary": "Ownership vs authorization capture.",
                                "other_proposition_id": "p3",
                            },
                            {"scenario_id": "s2", "survives": True},
                        ]
                    ),
                },
                "assert-l4",
            ),
            # Centrality buys no parking right: deferring an L4 still fails.
            _tool_call("defer_conflict", {"conflict_id": "c1"}, "defer-l4"),
            _tool_call("run_iteration", {"conflict_id": "c1"}, "iterate"),
            AIMessage(content="L4 stakes observed."),
        ]
    )
    agent = create_socrates_session(model=model, activity_models=_close_stubs())
    config = _thread_config()

    opening = agent.invoke(
        {"messages": [HumanMessage(content="Start")]},
        config=config,
    )
    r = agent.invoke(Command(resume=need), config=config)
    r = _walk_doors(agent, config, r)
    r = agent.invoke(Command(resume="yes"), config=config)  # p1
    r = agent.invoke(Command(resume="yes"), config=config)  # p2 via p1
    r = agent.invoke(Command(resume="yes"), config=config)  # p3

    # The unavoidable Notification carries both parties' centrality, and the
    # defer attempt failed — decoration, never a gate.
    notes = _load_json(r["files"], NOTIFICATIONS_PATH)["notifications"]
    unavoidable = next(n for n in notes if n["kind"] == "unavoidable_conflict")
    assert unavoidable["deferrable"] is False
    assert unavoidable["blocks_progress"] is True
    assert unavoidable["criticality"]["unavoidable"] is True
    stakes = {
        p["id"]: p["centrality"]
        for p in unavoidable["criticality"]["parties"]
    }
    assert stakes == {
        "p1": _centrality(True, "derivation", 1, 1),
        "p3": _centrality(True, "requirements", 0, 1),
    }
    defer_errs = [
        m
        for m in r["messages"]
        if isinstance(m, ToolMessage)
        and isinstance(m.content, str)
        and '"ok":false' in m.content.replace(" ", "")
        and "unavoidable" in m.content
    ]
    assert defer_errs

    # The Iteration proposal carries the same stakes at a glance.
    iteration = r["__interrupt__"][0].value
    assert iteration["kind"] == "iteration"
    assert iteration["proposed_activity"] == "requirements"
    it_stakes = {p["id"]: p["centrality"] for p in iteration["parties"]}
    assert it_stakes == {
        "p1": _centrality(True, "derivation", 1, 1),
        "p3": _centrality(True, "requirements", 0, 1),
    }

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()
    conflict = _load_json(finished["files"], CONFLICTS_PATH)["conflicts"][0]
    assert conflict["status"] == "resolved"
    assert conflict["resolution"]["action"] == "iterate"
    pipeline = _load_json(finished["files"], PIPELINE_PATH)
    assert pipeline["active"] == "requirements"
    assert pipeline["completed"] == []
