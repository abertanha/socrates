"""Session conduction — derived state, pure availability, redirect payloads.

Ticket 13 / spec `session-conduction`: the harness conducts, the model asks.
The session's order stops living in the prompt: a governor derives the
conduction state from persisted facts at tool-dispatch time and out-of-state
calls receive an explaining redirect (current state + admissible next steps),
never a bare "no".

This module's enforced seams (the rest of the matrix lands with tickets 14+):
the Need gate (before the Opening only the Opening exists), `run_opening`
exactly once, and Modeling Activity precedence for `task` — made proactive,
where the pipeline store already enforced it reactively.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from deepagents.backends.protocol import BackendProtocol
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import ToolMessage

from socrates.paths import NEED_PATH
from socrates.pipeline import (
    ACTIVITIES_IN_ORDER,
    ACTIVITY_SUBAGENT_TYPE,
    ModelingActivity,
    PipelineStore,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from langgraph.prebuilt.tool_node import ToolCallRequest

PRE_OPENING = "pre-opening"
BETWEEN_CHAPTERS = "between-chapters"
TAIL = "tail"

OPENING_TOOL = "run_opening"
TASK_TOOL = "task"


@dataclass(frozen=True)
class ConductionState:
    """The session's conduction state, derived — never persisted (ADR-0001)."""

    need_registered: bool
    active: ModelingActivity | None
    completed: tuple[ModelingActivity, ...]

    @property
    def label(self) -> str:
        if not self.need_registered:
            return PRE_OPENING
        if len(self.completed) >= len(ACTIVITIES_IN_ORDER):
            return TAIL
        if self.active is not None:
            return f"chapter:{self.active}"
        return BETWEEN_CHAPTERS

    @property
    def expected_activity(self) -> ModelingActivity | None:
        """The next chapter in precedence, or None outside the chapter walk."""
        if not self.need_registered:
            return None
        index = len(self.completed)
        if index >= len(ACTIVITIES_IN_ORDER):
            return None
        return ACTIVITIES_IN_ORDER[index]


def read_conduction_state(backend: BackendProtocol) -> ConductionState:
    """Derive the conduction state from the Model's filesystem facts."""
    need = backend.read(NEED_PATH)
    pipeline = PipelineStore(backend).snapshot()
    return ConductionState(
        need_registered=not need.error and need.file_data is not None,
        active=pipeline.get("active"),
        completed=tuple(pipeline.get("completed", ())),
    )


def conduction_check(
    state: ConductionState,
    tool_name: str,
    tool_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Pure availability rule: None when admissible, else the redirect payload.

    Deterministic over the derived facts — same facts in, same decision out.
    """
    args = tool_args or {}
    if state.label == PRE_OPENING:
        if tool_name == OPENING_TOOL:
            return None
        return _redirect(
            state,
            tool_name,
            args,
            admissible_next=[OPENING_TOOL],
            reason=(
                "the Need is not registered yet — the Opening elicits and "
                "persists it before any modeling exists"
            ),
        )
    if tool_name == OPENING_TOOL:
        return _redirect(
            state,
            tool_name,
            args,
            admissible_next=_chapter_walk_next(state),
            reason=(
                "the Opening runs exactly once and the Need is already "
                "registered"
            ),
        )
    if tool_name == TASK_TOOL:
        expected = state.expected_activity
        if expected is None:
            return _redirect(
                state,
                tool_name,
                args,
                admissible_next=[_TAIL_NEXT],
                reason=(
                    "all Modeling Activities are completed — the session "
                    "continues in the tail until Satisfaction"
                ),
            )
        expected_task = f"task: {ACTIVITY_SUBAGENT_TYPE[expected]}"
        if args.get("subagent_type") != ACTIVITY_SUBAGENT_TYPE[expected]:
            return _redirect(
                state,
                tool_name,
                args,
                admissible_next=[expected_task],
                reason=(
                    f"Modeling Activity precedence: expected '{expected}', "
                    f"attempted '{args.get('subagent_type')}'"
                ),
            )
    return None


_TAIL_NEXT = "await_satisfaction"


def _chapter_walk_next(state: ConductionState) -> list[str]:
    expected = state.expected_activity
    if expected is None:
        return [_TAIL_NEXT]
    return [f"task: {ACTIVITY_SUBAGENT_TYPE[expected]}"]


def _attempted(tool_name: str, args: dict[str, Any]) -> str:
    if tool_name == TASK_TOOL and "subagent_type" in args:
        return f"task({args['subagent_type']})"
    return tool_name


def _redirect(
    state: ConductionState,
    tool_name: str,
    args: dict[str, Any],
    *,
    admissible_next: list[str],
    reason: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "conduction": {
            "state": state.label,
            "attempted": _attempted(tool_name, args),
            "admissible_next": list(admissible_next),
        },
        "redirect": reason,
    }


class ConductionMiddleware(AgentMiddleware):
    """Gates tool dispatch on the derived conduction state.

    Reads the Model's filesystem at dispatch time and short-circuits
    out-of-state calls with the redirect payload instead of executing them.
    In-state calls reach their handler untouched.
    """

    def __init__(self, backend: BackendProtocol) -> None:
        self._backend = backend

    def wrap_tool_call(
        self,
        request: "ToolCallRequest",
        handler: "Callable[[ToolCallRequest], ToolMessage | Any]",
    ) -> ToolMessage | Any:
        return self._gate(request) or handler(request)

    async def awrap_tool_call(
        self,
        request: "ToolCallRequest",
        handler: "Callable[[ToolCallRequest], Awaitable[ToolMessage | Any]]",
    ) -> ToolMessage | Any:
        return self._gate(request) or await handler(request)

    def _gate(self, request: "ToolCallRequest") -> ToolMessage | None:
        call = request.tool_call
        redirect = conduction_check(
            read_conduction_state(self._backend),
            call["name"],
            call.get("args") or {},
        )
        if redirect is None:
            return None
        return ToolMessage(
            content=json.dumps(redirect),
            tool_call_id=call.get("id") or "",
            name=call["name"],
        )
