"""Interview tools for the walking-skeleton session."""

from __future__ import annotations

from collections.abc import Sequence

from deepagents.backends.protocol import BackendProtocol
from langchain_core.tools import BaseTool
from langchain.tools import tool
from langgraph.types import interrupt

from socrates.paths import NEED_PATH

OPENING_QUESTION = "What Need should this Model serve?"
SATISFACTION_QUESTION = (
    "Do you signal Satisfaction with the Model as it stands?"
)


def build_session_tools(backend: BackendProtocol) -> Sequence[BaseTool]:
    """Build interrupt-gated Opening and Satisfaction tools bound to ``backend``."""

    @tool
    def run_opening() -> str:
        """Opening: elicit the Need from the user and persist it as the Model's first content."""
        need = str(
            interrupt(
                {
                    "kind": "opening",
                    "question": OPENING_QUESTION,
                }
            )
        )
        backend.write(NEED_PATH, need)
        return f"Need persisted to {NEED_PATH}."

    @tool
    def await_satisfaction() -> str:
        """Ask whether the user signals Satisfaction; blocks until they answer."""
        answer = str(
            interrupt(
                {
                    "kind": "satisfaction",
                    "question": SATISFACTION_QUESTION,
                }
            )
        )
        return f"Satisfaction signal received: {answer}"

    return [run_opening, await_satisfaction]
