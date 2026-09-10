"""Ticket 22 — amend_need: the gated Need amendment.

Seam: the pure availability rule tested directly (facts in → admission or
redirect), plus the declared orchestration seam (StubChatModel session)
asserting the amendment interrupt's comparison payload, the rewritten Need
with its amendment record (superseded shape + reason, newest last), the
declined amendment leaving the Need untouched, the redirects naming the
Opening (pre-Opening) and the Iteration path (anywhere else), and the live
filter — Scenarios recorded after an amendment run under the new Need.
"""

from __future__ import annotations

import json
import uuid

from deepagents.backends.filesystem import FilesystemBackend
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.conduction import ConductionState, conduction_check, read_conduction_state
from socrates.paths import (
    NEED_PATH,
    PIPELINE_PATH,
    PROPOSITIONS_PATH,
    SCENARIOS_PATH,
)
from socrates.pipeline import PipelineStore

_ALL_COMPLETED = (
    "requirements",
    "domain_modeling",
    "behavioral_specification",
)

_AMEND_ARGS = {"proposed_need": "A sharper Need.", "reason": "The first answer was broad."}


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


def _chapter_close_stub(label: str) -> StubChatModel:
    """A specialist that walks in and closes its chapter door — no ground."""
    return StubChatModel(
        responses=[
            _tool_call("complete_modeling_activity", {}, f"{label}-complete"),
            AIMessage(content=f"{label} activity complete."),
        ],
        label=label,
    )


# ---------------------------------------------------------------- pure rule


def test_amend_is_admitted_while_requirements_is_open_or_next() -> None:
    """First pass, both of its shapes: the chapter begun, and post-Opening
    before anything begins (expected in precedence, nothing completed)."""
    begun = ConductionState(
        need_registered=True, active="requirements", completed=()
    )
    assert conduction_check(begun, "amend_need", _AMEND_ARGS) is None

    fresh = ConductionState(need_registered=True, active=None, completed=())
    assert conduction_check(fresh, "amend_need", _AMEND_ARGS) is None


def test_amend_redirected_pre_opening_names_the_opening() -> None:
    state = ConductionState(need_registered=False, active=None, completed=())
    redirect = conduction_check(state, "amend_need", _AMEND_ARGS)
    assert redirect is not None
    assert redirect["ok"] is False
    assert redirect["conduction"]["state"] == "pre-opening"
    assert redirect["conduction"]["attempted"] == "amend_need"
    assert "run_opening" in redirect["conduction"]["admissible_next"]


def test_amend_redirected_elsewhere_names_the_iteration_path() -> None:
    """Any other chapter, between-chapters past Requirements, and the tail:
    the redirect names the Iteration path — a Need-level shift outside
    Requirements is an L4-grade event."""
    states = {
        "open domain chapter": ConductionState(
            need_registered=True,
            active="domain_modeling",
            completed=("requirements",),
        ),
        "past requirements": ConductionState(
            need_registered=True, active=None, completed=("requirements",)
        ),
        "tail": ConductionState(
            need_registered=True, active=None, completed=_ALL_COMPLETED
        ),
    }
    for label, state in states.items():
        redirect = conduction_check(state, "amend_need", _AMEND_ARGS)
        assert redirect is not None, label
        assert redirect["ok"] is False
        assert redirect["conduction"]["attempted"] == "amend_need"
        assert any(
            "run_iteration" in step
            for step in redirect["conduction"]["admissible_next"]
        ), label
        assert "Iteration" in redirect["redirect"], label


def test_iteration_reopen_of_requirements_readmits_the_amendment(tmp_path) -> None:
    """The reopen arm of admissibility, against the real pipeline facts:
    after Iteration reopens Requirements, the derived state admits the
    amendment again (ADR-0001 — the rule reads facts, nothing else)."""
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    backend.write(NEED_PATH, "Marketplace checkout payments domain.")
    pipeline = PipelineStore(backend)
    pipeline.begin("requirements")
    pipeline.complete("requirements")
    pipeline.begin("domain_modeling")

    mid_walk = read_conduction_state(backend)
    assert conduction_check(mid_walk, "amend_need", _AMEND_ARGS) is not None

    pipeline.reopen("requirements")
    reopened = read_conduction_state(backend)
    assert reopened.active == "requirements"
    assert conduction_check(reopened, "amend_need", _AMEND_ARGS) is None


# ---------------------------------------------------------- orchestration


def test_amend_interrupt_compares_and_confirmation_records_newest_last():
    """The interrupt carries the current and proposed Need plus the reason
    as one plain question; each confirmation rewrites the Need with the
    amendment recorded beneath it — superseded shape and reason surviving,
    newest last — and the next amendment compares against the live Need."""
    original = "A chatbot to assist lawyers."
    first = "A chatbot that assembles the complete legal basis for a civil action."
    second = (
        "A chatbot that assembles the complete legal basis and drafts the "
        "argument's rhetorical structure."
    )
    reason_one = "The first answer was too broad to filter with."
    reason_two = "The deliverable includes the draft structure, not just the basis."

    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "amend_need",
                {"proposed_need": first, "reason": reason_one},
                "amend-1",
            ),
            _tool_call(
                "amend_need",
                {"proposed_need": second, "reason": reason_two},
                "amend-2",
            ),
            AIMessage(content="Need sharpened."),
        ],
        label="main",
    )
    agent = create_socrates_session(model=model, reinjection_limit=0)  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume=original), config=config)

    # The comparison interrupt: current beside proposed, the reason, one
    # plain question — no machinery in what the user reads.
    amendment = r["__interrupt__"][0].value
    assert amendment["kind"] == "amend_need"
    assert amendment["current_need"] == original
    assert amendment["proposed_need"] == first
    assert amendment["reason"] == reason_one
    question = amendment["question"]
    assert question.endswith("?")
    assert question.count("?") == 1
    for leak in ("amend", "Amendment", "Relevance Filter", "Requirements"):
        assert leak not in question

    r = agent.invoke(Command(resume="yes"), config=config)
    first_result = _tool_result(r["messages"], "amend-1")
    assert first_result["ok"] is True

    # The second amendment compares against the LIVE Need — the record
    # never leaks into the filter's body.
    second_ask = r["__interrupt__"][0].value
    assert second_ask["current_need"] == first

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None

    content = finished["files"][NEED_PATH]["content"]
    # The body is the newest Need; the record rides beneath the separator.
    body, separator, record = content.partition("\n## Amendment record\n")
    assert separator
    assert body.strip() == second
    # Newest last: amendment one precedes amendment two, each keeping the
    # shape it superseded and the reason.
    assert record.index("Amendment 1") < record.index("Amendment 2")
    assert reason_one in record
    assert reason_two in record
    assert original in record
    assert first in record
    second_result = _tool_result(finished["messages"], "amend-2")
    assert second_result["ok"] is True


def test_declined_amendment_leaves_the_need_untouched():
    original = "A chatbot to assist lawyers."
    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "amend_need",
                {"proposed_need": "A mis-shaped proposal.", "reason": "Wrong."},
                "amend-declined",
            ),
            AIMessage(content="Carrying on with the Need as it is."),
        ],
        label="main",
    )
    agent = create_socrates_session(model=model, reinjection_limit=0)  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume=original), config=config)
    assert r["__interrupt__"][0].value["kind"] == "amend_need"

    finished = agent.invoke(Command(resume="no"), config=config)
    assert finished.get("__interrupt__") is None

    # Byte-for-byte untouched, and the decline returns to the model as a
    # normal declined action.
    assert finished["files"][NEED_PATH]["content"] == original
    declined = _tool_result(finished["messages"], "amend-declined")
    assert declined["ok"] is False
    assert declined["declined"] is True


def test_amend_redirected_before_the_opening_names_the_opening():
    model = StubChatModel(
        responses=[
            _tool_call("amend_need", _AMEND_ARGS, "amend-early"),
            _tool_call("run_opening", {}, "open"),
            AIMessage(content="Opened first, then sharpened."),
        ],
        label="main",
    )
    agent = create_socrates_session(model=model, reinjection_limit=0)  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    # The Opening still interrupts — the premature attempt only redirected.
    assert r["__interrupt__"][0].value["kind"] == "opening"
    redirected = _tool_result(r["messages"], "amend-early")
    assert redirected["ok"] is False
    assert redirected["conduction"]["state"] == "pre-opening"
    assert redirected["conduction"]["attempted"] == "amend_need"
    assert "run_opening" in redirected["conduction"]["admissible_next"]

    finished = agent.invoke(
        Command(resume="A chatbot to assist lawyers."), config=config
    )
    assert finished.get("__interrupt__") is None


def test_amend_redirected_after_requirements_closes_names_iteration():
    original = "A chatbot to assist lawyers."
    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "task",
                {"subagent_type": "requirements", "description": "Requirements."},
                "task-req",
            ),
            _tool_call("amend_need", _AMEND_ARGS, "amend-late"),
            AIMessage(content="Redirected to Iteration."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
        model=model,
        activity_models={"requirements": _chapter_close_stub("req")},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume=original), config=config)
    # The requirements chapter's door, then close.
    assert r["__interrupt__"][0].value["kind"] == "door"
    finished = agent.invoke(Command(resume="close"), config=config)
    assert finished.get("__interrupt__") is None

    redirected = _tool_result(finished["messages"], "amend-late")
    assert redirected["ok"] is False
    assert redirected["conduction"]["state"] == "between-chapters"
    assert redirected["conduction"]["attempted"] == "amend_need"
    assert any(
        "run_iteration" in step
        for step in redirected["conduction"]["admissible_next"]
    )
    assert "Iteration" in redirected["redirect"]

    # The Need never moved, and the walk advanced past Requirements.
    assert finished["files"][NEED_PATH]["content"] == original
    pipeline = json.loads(finished["files"][PIPELINE_PATH]["content"])
    assert pipeline["completed"] == ["requirements"]


def test_blank_amendment_is_refused_and_never_interrupts():
    """A mis-shaped proposal never reaches the user (US4 read strictly):
    an empty shape or an empty reason is refused before the interrupt —
    confirming a void shape would corrupt the Need's body."""
    original = "A chatbot to assist lawyers."
    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "amend_need",
                {"proposed_need": "   ", "reason": "An empty shape."},
                "amend-blank-need",
            ),
            _tool_call(
                "amend_need",
                {"proposed_need": "A reshaped Need.", "reason": "  "},
                "amend-blank-reason",
            ),
            AIMessage(content="Neither proposal was well-shaped."),
        ],
        label="main",
    )
    agent = create_socrates_session(model=model, reinjection_limit=0)  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    # No amendment interrupt ever fires — both refusals returned to the
    # model as tool results, and the session ran on to its scripted end.
    finished = agent.invoke(Command(resume=original), config=config)
    assert finished.get("__interrupt__") is None

    blank_need = _tool_result(finished["messages"], "amend-blank-need")
    assert blank_need["ok"] is False
    assert "reshaped Need" in blank_need["error"]
    blank_reason = _tool_result(finished["messages"], "amend-blank-reason")
    assert blank_reason["ok"] is False
    assert finished["files"][NEED_PATH]["content"] == original


def test_amendment_never_touches_recorded_ground():
    """US8: recorded Scenarios and Acceptances are the user's decisions —
    an amendment (here, mid-chapter with Requirements begun) rewrites the
    Need alone; the Model's recorded ground stands untouched."""
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
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(
                        [
                            {
                                "description": "hierarchy edge one",
                                "edge": "one",
                                "need_relevant": True,
                            },
                            {
                                "description": "hierarchy edge many",
                                "edge": "many",
                                "need_relevant": True,
                            },
                        ]
                    ),
                },
                "req-scenarios",
            ),
            AIMessage(content="Still working on the Need."),
        ],
        label="req",
    )
    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "task",
                {"subagent_type": "requirements", "description": "Requirements."},
                "task-req",
            ),
            _tool_call(
                "amend_need",
                {"proposed_need": amended, "reason": reason},
                "amend",
            ),
            AIMessage(content="Need sharpened mid-chapter."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
        model=model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume=original), config=config)

    # The chapter is open (Requirements begun) — the amendment compares.
    amendment = r["__interrupt__"][0].value
    assert amendment["kind"] == "amend_need"
    assert amendment["current_need"] == original
    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None

    # The Need moved — and nothing else did.
    content = finished["files"][NEED_PATH]["content"]
    body, separator, record = content.partition("\n## Amendment record\n")
    assert separator
    assert body.strip() == amended
    assert original in record

    scenarios = json.loads(finished["files"][SCENARIOS_PATH]["content"])[
        "scenarios"
    ]
    assert [s["description"] for s in scenarios] == [
        "hierarchy edge one",
        "hierarchy edge many",
    ]
    propositions = json.loads(
        finished["files"][PROPOSITIONS_PATH]["content"]
    )["propositions"]
    assert [p["id"] for p in propositions] == ["p1"]
    assert propositions[0]["status"] == "candidate"


def test_scenarios_recorded_after_an_amendment_run_under_the_new_need():
    """The filter is live, not cached: after a confirmed amendment the
    chapter's Scenarios record against the amended Need file — and the
    record beneath it never leaks into the filter's body."""
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
                "record_scenarios",
                {
                    "proposition_id": "p1",
                    "scenarios_json": json.dumps(
                        [
                            {
                                "description": "hierarchy edge one",
                                "edge": "one",
                                "need_relevant": True,
                            },
                            {
                                "description": "hierarchy edge many",
                                "edge": "many",
                                "need_relevant": True,
                            },
                        ]
                    ),
                },
                "req-scenarios",
            ),
            _tool_call("complete_modeling_activity", {}, "req-complete"),
            AIMessage(content="req activity complete."),
        ],
        label="req",
    )
    model = StubChatModel(
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
            AIMessage(content="Chapter one under the amended Need."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        reinjection_limit=0,  # only-sink guard off: scripted-silent ending (guard: test_only_sink.py)
        model=model,
        activity_models={"requirements": requirements_model},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume=original), config=config)
    assert r["__interrupt__"][0].value["kind"] == "amend_need"
    r = agent.invoke(Command(resume="yes"), config=config)

    # The chapter ran under the amended Need file: Scenarios recorded.
    assert r["__interrupt__"][0].value["kind"] == "door"
    finished = agent.invoke(Command(resume="close"), config=config)
    assert finished.get("__interrupt__") is None

    scenarios = json.loads(finished["files"][SCENARIOS_PATH]["content"])[
        "scenarios"
    ]
    assert [s["proposition_id"] for s in scenarios] == ["p1", "p1"]

    content = finished["files"][NEED_PATH]["content"]
    body, separator, record = content.partition("\n## Amendment record\n")
    assert separator
    assert body.strip() == amended
    assert original in record
    assert reason in record
