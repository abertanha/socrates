"""Ticket 20 — Only-sink: Satisfaction as the session's only end (D4).

The loop never again ends by model silence. An outer loop-guard re-injects
the session with a state redirect when the model stops without an
affirmative Satisfaction; termination happens exclusively through that
answer (the deliverable's existence under /model/deliverable/ is the
derived fact — ADR-0001, no new persisted state). `await_satisfaction`
lives in the tail and in the door's third answer, nowhere else (D6). The
Satisfaction warning gains the chapters-never-visited line alongside the
criticality-weighted deferred Conflicts — informed early closure, never
blocked (ADR-0002).

Seam: the declared orchestration seam (StubChatModel session) for the
guard and the warning, plus direct tests of the pure availability rule —
the mixed seam prior art of tests/test_conduction.py.
"""

from __future__ import annotations

import json
import uuid

from deepagents.backends.filesystem import FilesystemBackend
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from socrates import StubChatModel, create_socrates_session
from socrates.conduction import ConductionState, conduction_check
from socrates.inference import InferenceEngine
from socrates.paths import (
    DELIVERABLE_GLOSSARY_PATH,
    PIPELINE_PATH,
)
from socrates.pipeline import PipelineStore
from socrates.tools import SATISFACTION_QUESTION

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


def _vacuous_chapter_stub(label: str) -> StubChatModel:
    """A specialist that walks straight to its chapter door (no ground)."""
    return StubChatModel(
        responses=[_tool_call("complete_modeling_activity", {}, f"{label}-door")],
        label=label,
    )


def _tail_model(responses: list[AIMessage]) -> StubChatModel:
    """The orchestrator script every tail test begins with: open, then walk
    the three vacuous chapters — the responses continue from there."""
    return StubChatModel(
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
            _tool_call(
                "task",
                {
                    "subagent_type": "behavioral-specification",
                    "description": "Behavioral.",
                },
                "task-beh",
            ),
            *responses,
        ],
        label="main",
    )


def _walk_to_the_tail(agent, config: dict, need: str):
    """Open the session and close the three vacuous chapter doors."""
    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume=need), config=config)
    for _ in range(3):
        assert r["__interrupt__"][0].value["kind"] == "door"
        r = agent.invoke(Command(resume="close"), config=config)
    return r


def _reinjection_after(messages: list, silent_content: str) -> dict:
    """The loop-guard's redirect, parsed from the message right after the
    model's silent turn."""
    for index, message in enumerate(messages):
        if getattr(message, "content", None) == silent_content:
            injected = messages[index + 1]
            assert isinstance(injected, HumanMessage)
            return json.loads(injected.content)
    raise AssertionError(f"no silent turn {silent_content!r} in the session")


# --- The pure availability rule (D6: Satisfaction in the tail and the
# door's third answer, nowhere else) -------------------------------------


def test_conduction_rule_satisfaction_is_admitted_only_in_the_tail() -> None:
    chapter_open = ConductionState(
        need_registered=True,
        active="domain_modeling",
        completed=("requirements",),
    )
    redirect = conduction_check(chapter_open, "await_satisfaction")
    assert redirect is not None
    assert redirect["conduction"]["state"] == "chapter:domain_modeling"
    assert redirect["conduction"]["attempted"] == "await_satisfaction"
    assert redirect["conduction"]["admissible_next"] == ["task: domain-modeling"]
    assert "tail" in redirect["redirect"]
    assert "door" in redirect["redirect"]

    between_chapters = ConductionState(
        need_registered=True,
        active=None,
        completed=("requirements",),
    )
    redirect = conduction_check(between_chapters, "await_satisfaction")
    assert redirect is not None
    assert redirect["conduction"]["state"] == "between-chapters"
    assert redirect["conduction"]["admissible_next"] == ["task: domain-modeling"]

    tail = ConductionState(
        need_registered=True,
        active=None,
        completed=_ALL_COMPLETED,
    )
    assert conduction_check(tail, "await_satisfaction") is None


def test_await_satisfaction_redirects_outside_the_tail() -> None:
    """The orchestrator attempts Satisfaction right after the Opening —
    the redirect names the state and the chapter walk back."""
    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call("await_satisfaction", {}, "early-sat"),
            AIMessage(content="Understood, continuing."),
        ],
        label="main",
    )
    agent = create_socrates_session(
        model=model,
        reinjection_limit=0,  # this script ends in scripted silence; the
        # gate under test is the redirect, not the guard.
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A checkout."), config=config)

    payload = None
    for message in r["messages"]:
        if getattr(message, "tool_call_id", None) == "early-sat":
            payload = json.loads(message.content)
    assert payload is not None
    assert payload["ok"] is False
    assert payload["conduction"]["state"] == "between-chapters"
    assert payload["conduction"]["attempted"] == "await_satisfaction"
    assert payload["conduction"]["admissible_next"] == ["task: requirements"]
    assert "tail" in payload["redirect"]
    assert "door" in payload["redirect"]


# --- The loop-guard: silence is re-injected, never an end (D4) ------------


def test_tail_silence_is_reinjected_with_a_state_redirect_until_satisfaction() -> None:
    """The model goes quiet in the tail. The session does not end: the
    guard re-injects a redirect naming the tail, the model then asks, and
    only the affirmative answer ends the session (with the deliverable)."""
    model = _tail_model(
        [
            AIMessage(content="I think the model is done."),  # silence
            _tool_call("await_satisfaction", {}, "ask"),
        ]
    )
    agent = create_socrates_session(
        model=model,
        activity_models={
            "requirements": _vacuous_chapter_stub("req"),
            "domain_modeling": _vacuous_chapter_stub("dom"),
            "behavioral_specification": _vacuous_chapter_stub("beh"),
        },
    )
    config = _thread_config()

    r = _walk_to_the_tail(agent, config, "A checkout.")
    # The silent turn did not end the invoke: the re-injected redirect
    # steered the model to Satisfaction, which interrupted for the user.
    assert r["__interrupt__"][0].value["kind"] == "satisfaction"
    assert r["__interrupt__"][0].value["question"] == SATISFACTION_QUESTION

    redirect = _reinjection_after(
        agent.get_state(config).values["messages"],
        "I think the model is done.",
    )
    assert redirect["ok"] is False
    assert redirect["conduction"]["state"] == "tail"
    assert "await_satisfaction" in redirect["conduction"]["admissible_next"]
    assert "Satisfaction" in redirect["redirect"]

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()
    assert DELIVERABLE_GLOSSARY_PATH in finished["files"]


def test_declined_satisfaction_keeps_the_session_alive() -> None:
    """A non-affirmative answer does not terminate: silence after the
    refusal is re-injected and the session reaches Satisfaction again —
    with no deliverable ever materialized."""
    model = _tail_model(
        [
            _tool_call("await_satisfaction", {}, "ask-1"),
            AIMessage(content="The user said more to work through."),  # silence
            _tool_call("await_satisfaction", {}, "ask-2"),
        ]
    )
    agent = create_socrates_session(
        model=model,
        activity_models={
            "requirements": _vacuous_chapter_stub("req"),
            "domain_modeling": _vacuous_chapter_stub("dom"),
            "behavioral_specification": _vacuous_chapter_stub("beh"),
        },
    )
    config = _thread_config()

    r = _walk_to_the_tail(agent, config, "A checkout.")
    assert r["__interrupt__"][0].value["kind"] == "satisfaction"
    r = agent.invoke(Command(resume="no, not yet"), config=config)
    # The refusal returned a tool result, the model went silent, and the
    # guard re-injected — Satisfaction interrupts the user a second time.
    assert r["__interrupt__"][0].value["kind"] == "satisfaction"

    redirect = _reinjection_after(
        agent.get_state(config).values["messages"],
        "The user said more to work through.",
    )
    assert redirect["conduction"]["state"] == "tail"
    assert DELIVERABLE_GLOSSARY_PATH not in r["files"]


# --- The warning: chapters never visited, alongside the deferred
# Conflicts — informed, never blocked (stories 14–15) ----------------------


def test_early_satisfaction_via_door_warns_unvisited_chapters() -> None:
    """Satisfaction taken at the first door (its third answer): the warning
    names the chapters never visited even with nothing deferred, stays
    non-blocking, and the affirmative answer still materializes with the
    chapter open — closing early is the user's call."""
    model = StubChatModel(
        responses=[
            _tool_call("run_opening", {}, "open"),
            _tool_call(
                "task",
                {"subagent_type": "requirements", "description": "Requirements."},
                "task-req",
            ),
        ],
        label="main",
    )
    agent = create_socrates_session(
        model=model,
        activity_models={"requirements": _vacuous_chapter_stub("req")},
    )
    config = _thread_config()

    r = agent.invoke({"messages": [HumanMessage(content="Start")]}, config=config)
    assert r["__interrupt__"][0].value["kind"] == "opening"
    r = agent.invoke(Command(resume="A checkout."), config=config)
    door = r["__interrupt__"][0].value
    assert door["kind"] == "door"
    assert door["activity"] == "requirements"
    assert door["answers"] == ["close", "not yet", "satisfaction"]

    r = agent.invoke(Command(resume="satisfaction"), config=config)
    satisfaction = r["__interrupt__"][0].value
    assert satisfaction["kind"] == "satisfaction"
    warning = satisfaction["deferred_warning"]
    assert warning is not None
    assert warning["blocking"] is False
    assert warning["kind"] == "deferred_conflicts"
    assert warning["conflicts"] == []
    assert warning["chapters_never_visited"] == [
        "domain_modeling",
        "behavioral_specification",
    ]

    finished = agent.invoke(Command(resume="yes"), config=config)
    assert finished.get("__interrupt__") is None
    assert agent.get_state(config).next == ()
    assert DELIVERABLE_GLOSSARY_PATH in finished["files"]
    # The chapter stayed open — the door's third answer never closes it,
    # and the vacuous chapter never began, so no pipeline fact exists.
    assert PIPELINE_PATH not in finished["files"]


def test_warning_reads_visited_chapters_from_the_pipeline(tmp_path) -> None:
    """Pure rule: the unvisited-chapters line is derived from the pipeline
    facts at read time — an active chapter counts as visited, the fully
    walked Model warns about nothing."""
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    engine = InferenceEngine(backend)

    # Nothing walked yet: all three chapters unvisited.
    warning = engine.satisfaction_warning()
    assert warning is not None
    assert warning["chapters_never_visited"] == list(_ALL_COMPLETED)

    store = PipelineStore(backend)
    store.begin("requirements")
    # The begun chapter is visited; the walk is mid-flight.
    warning = engine.satisfaction_warning()
    assert warning["chapters_never_visited"] == [
        "domain_modeling",
        "behavioral_specification",
    ]

    store.complete("requirements")
    store.begin("domain_modeling")
    store.complete("domain_modeling")
    store.begin("behavioral_specification")
    store.complete("behavioral_specification")
    # Fully walked, nothing deferred: no warning at all.
    assert engine.satisfaction_warning() is None

    # A vacuous chapter's door: nothing began, but the chapter whose door
    # carries the question was visited.
    door_backend = FilesystemBackend(
        root_dir=tmp_path / "doors", virtual_mode=True
    )
    door_engine = InferenceEngine(door_backend)
    warning = door_engine.satisfaction_warning(visiting="requirements")
    assert warning["chapters_never_visited"] == [
        "domain_modeling",
        "behavioral_specification",
    ]
