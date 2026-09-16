"""Ticket 23 — amendments ride to the Satisfaction warning; the deliverable
grounds in the final Need.

Seam: the declared orchestration seam (StubChatModel session) for the
warning ride, plus direct tests of the warning's emptiness rule and the
deliverable composer over the Model's filesystem — the same external
payloads, no new seams (spec `need-refinement` testing decisions).
"""

from __future__ import annotations

import json
import uuid

from deepagents.backends.filesystem import FilesystemBackend
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.deliverable import DeliverableComposer
from socrates.inference import InferenceEngine
from socrates.paths import (
    DELIVERABLE_GLOSSARY_PATH,
    DELIVERABLE_STRUCTURE_PATH,
    NEED_PATH,
    PIPELINE_PATH,
)
from socrates.proposition import PropositionStore
from socrates.tools import SATISFACTION_QUESTION


def _thread_config() -> dict:
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


def _tool_call(name: str, args: dict, call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}],
    )


def _chapter_close_stub(label: str) -> StubChatModel:
    """A specialist that walks in and closes its chapter door — no ground."""
    return StubChatModel(
        responses=[
            _tool_call("complete_modeling_activity", {}, f"{label}-complete"),
            AIMessage(content=f"{label} activity complete."),
        ],
        label=label,
    )


def _record_scenarios_call(proposition_id: str, prefix: str, call_id: str) -> AIMessage:
    return _tool_call(
        "record_scenarios",
        {
            "proposition_id": proposition_id,
            "scenarios_json": json.dumps(
                [
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
            ),
        },
        call_id,
    )


# ---------------------------------------------------------- orchestration


def test_amendments_ride_to_the_satisfaction_warning_alongside_conflicts() -> None:
    """The warning is the early close's honest picture: the session's Need
    amendments with their reasons ride alongside the weighted deferred
    Conflicts and the chapters never visited — never a block."""
    original = "A chatbot to assist lawyers."
    amended = "A chatbot that assembles the complete legal basis for a civil action."
    reason = "The first answer was too broad to filter with."

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
    main_model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "amend_need",
                {"proposed_need": amended, "reason": reason},
                "amend",
            ),
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
        reinjection_limit=0,  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
        model=main_model,
        activity_models={
            "requirements": requirements_model,
            "domain_modeling": _chapter_close_stub("dom"),
        },
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume=original), config=config)

    amendment = r["__interrupt__"][0].value
    assert amendment["kind"] == "amend_need"
    r = agent.invoke(Command(resume="yes"), config=config)

    # The requirements door (deferred Conflict never blocks it), then the
    # domain door whose third answer carries the Satisfaction question.
    assert r["__interrupt__"][0].value["kind"] == "door"
    r = agent.invoke(Command(resume="close"), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"
    r = agent.invoke(Command(resume="satisfaction"), config=config)

    satisfaction = r["__interrupt__"][0].value
    assert satisfaction["kind"] == "satisfaction"
    assert satisfaction["question"] == SATISFACTION_QUESTION
    warning = satisfaction["deferred_warning"]
    assert warning is not None
    assert warning["blocking"] is False
    # Both histories ride: the parked Conflict and the Relevance Filter's
    # amendment.
    assert [c["id"] for c in warning["conflicts"]] == ["c1"]
    assert warning["amendments"] == [
        {
            "number": 1,
            "reason": reason,
            "superseded": original,
        }
    ]
    assert warning["chapters_never_visited"] == ["behavioral_specification"]

    # The warning informed, never blocked: continuing is the user's call.
    finished = agent.invoke(Command(resume="no, more to work through"), config=config)
    assert finished.get("__interrupt__") is None
    assert DELIVERABLE_GLOSSARY_PATH not in finished["files"]


def test_deliverable_after_amendments_grounded_in_the_final_need() -> None:
    """What ships reflects the last thing agreed: the materialized
    deliverable grounds in the final Need — never the superseded shapes,
    never the record."""
    original = "A chatbot to assist lawyers."
    amended = "A chatbot that assembles the complete legal basis for a civil action."
    reason = "The first answer was too broad to filter with."

    requirements_model = StubChatModel(
        responses=[
            _tool_call(
                "propose_proposition",
                {"statement": "The basis draws on the hierarchy of legal sources."},
                "req-propose",
            ),
            _tool_call(
                "accept_proposition", {"proposition_id": "p1"}, "req-accept"
            ),
            _record_scenarios_call("p1", "hierarchy", "req-scenarios"),
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
                "req-assertions",
            ),
            _tool_call("complete_modeling_activity", {}, "req-complete"),
            AIMessage(content="req activity complete."),
        ],
        label="req",
    )
    main_model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "amend_need",
                {"proposed_need": amended, "reason": reason},
                "amend",
            ),
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
            _tool_call(
                "task",
                {
                    "subagent_type": "behavioral-specification",
                    "description": "Behavior.",
                },
                "task-beh",
            ),
            _tool_call("await_satisfaction", {}, "satisfy"),
            AIMessage(content="Ended at the user's own signal."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
        model=main_model,
        activity_models={
            "requirements": requirements_model,
            "domain_modeling": _chapter_close_stub("dom"),
            "behavioral_specification": _chapter_close_stub("beh"),
        },
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume=original), config=config)
    assert r["__interrupt__"][0].value["kind"] == "amend_need"
    r = agent.invoke(Command(resume="yes"), config=config)
    # The chapter's Acceptance interrupt for p1.
    assert r["__interrupt__"][0].value["kind"] == "accept"
    r = agent.invoke(Command(resume="yes"), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"
    r = agent.invoke(Command(resume="close"), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"
    r = agent.invoke(Command(resume="close"), config=config)
    assert r["__interrupt__"][0].value["kind"] == "door"
    r = agent.invoke(Command(resume="close"), config=config)

    satisfaction = r["__interrupt__"][0].value
    assert satisfaction["kind"] == "satisfaction"
    # The tail path carries the amendments too — the same warning reaches
    # the close wherever it is asked from (the ride test covers the door).
    tail_warning = satisfaction["deferred_warning"]
    assert tail_warning is not None
    assert tail_warning["amendments"][0]["reason"] == reason
    assert tail_warning["blocking"] is False

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None

    glossary = finished["files"][DELIVERABLE_GLOSSARY_PATH]["content"]
    assert amended in glossary
    assert original not in glossary
    assert "Amendment record" not in glossary
    # The Need file itself keeps the full history.
    assert original in finished["files"][NEED_PATH]["content"]


# ---------------------------------------------------------------- direct


def test_multiline_reason_survives_whole_in_the_payload(tmp_path) -> None:
    """Reasons always survive — the writer makes the reason single-line
    (the heading grammar is one line), so the warning payload reads it
    whole instead of truncating at the first newline."""
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write(NEED_PATH, "The first Need.")
    from socrates.need import read_amendments, write_amendment

    write_amendment(
        backend,
        "The reshaped Need.",
        "The first answer was raw.\nThe deliverable is broader than said.",
    )
    amendments = read_amendments(backend)
    assert amendments == [
        {
            "number": 1,
            "reason": (
                "The first answer was raw. The deliverable is broader "
                "than said."
            ),
            "superseded": "The first Need.",
        }
    ]
    # A second amendment still numbers off the (single-line) record.
    write_amendment(backend, "The final Need.", "One more sharpening.")
    assert [a["number"] for a in read_amendments(backend)] == [1, 2]


def test_amendments_alone_make_the_warning_worth_showing(tmp_path) -> None:
    """The emptiness rule counts the Relevance Filter's history: with
    amendments on record the warning is not None even with nothing
    deferred and every chapter visited — and the flip side holds: the
    same facts without amendments warn nothing."""
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write(
        PIPELINE_PATH,
        json.dumps(
            {
                "completed": [
                    "requirements",
                    "domain_modeling",
                    "behavioral_specification",
                ],
                "active": None,
            }
        ),
    )
    backend.write(
        NEED_PATH,
        "The final Need.\n\n"
        "## Amendment record\n\n"
        "### Amendment 1 — the first answer was raw\n\n"
        "Superseded Need:\n\nA raw first answer.\n",
    )
    inference = InferenceEngine(backend)

    warned = inference.satisfaction_warning()
    assert warned is not None
    assert warned["blocking"] is False
    assert warned["conflicts"] == []
    assert warned["chapters_never_visited"] == []
    assert warned["amendments"] == [
        {
            "number": 1,
            "reason": "the first answer was raw",
            "superseded": "A raw first answer.",
        }
    ]

    # The flip side: nothing deferred, every chapter visited, no
    # amendments — nothing to warn about (the pre-ticket-23 shape).
    backend.write(NEED_PATH, "The final Need.")
    assert inference.satisfaction_warning() is None


def test_deliverable_grounds_in_the_body_not_the_record(tmp_path) -> None:
    """The composer reads the live Need through the same one home as every
    consumer — an amended Need file ships the final agreed Need."""
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write(
        NEED_PATH,
        "The final Need.\n\n"
        "## Amendment record\n\n"
        "### Amendment 1 — the first answer was raw\n\n"
        "Superseded Need:\n\nA raw first answer.\n",
    )
    store = PropositionStore(backend)
    prop = store.propose("A Payment belongs to exactly one Order.",
                         activity="domain_modeling")
    store.accept(prop.id)

    contents = DeliverableComposer(backend).materialize()
    glossary = contents[DELIVERABLE_GLOSSARY_PATH]
    assert "The final Need." in glossary
    assert "A raw first answer." not in glossary
    assert "Amendment record" not in glossary
    # "belongs to exactly one" is structural, not definitional — the
    # accepted ground ships in the structure part as usual.
    structure = contents[DELIVERABLE_STRUCTURE_PATH]
    assert "A Payment belongs to exactly one Order." in structure
    assert "A raw first answer." not in structure
