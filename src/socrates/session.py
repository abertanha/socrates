"""Socrates session factory — thin wrapper over ``create_deep_agent``."""

from __future__ import annotations

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.backends.protocol import BackendProtocol
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from socrates.model import ModelProvider
from socrates.tools import build_session_tools

SYSTEM_PROMPT = """You are Socrates, a maieutic modeling harness.

Session discipline:
1. Call `run_opening` to elicit the user's Need and persist it.
2. Use `propose_proposition` to enter Propositions; the harness triages them
   (Candidate, or Flagged against the Rejection Guardrail).
3. On the user's signal, `accept_proposition` or `reject_proposition`
   (rejection always needs an explicit reason).
4. Call `await_satisfaction` so the user can signal Satisfaction.
5. When Satisfaction is recorded, stop. Never declare the Model done yourself.
"""


def create_socrates_session(
    model: ModelProvider,
    *,
    backend: BackendProtocol | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """Create a Socrates modeling session on deepagents.

    Args:
        model: Real provider (``BaseChatModel`` or ``provider:model`` string)
            or a ``StubChatModel`` for tests.
        backend: Virtual filesystem backend. Defaults to ``StateBackend``.
        checkpointer: Required for interrupt-gated Opening / Satisfaction.
            Defaults to ``InMemorySaver``.
    """
    fs = backend if backend is not None else StateBackend()
    saver = checkpointer if checkpointer is not None else InMemorySaver()
    return create_deep_agent(
        model=model,
        tools=list(build_session_tools(fs)),
        system_prompt=SYSTEM_PROMPT,
        backend=fs,
        checkpointer=saver,
    )
