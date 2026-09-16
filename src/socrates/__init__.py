"""Socrates — maieutic agent harness on deepagents."""

__version__ = "0.1.0"

from socrates.model import StubChatModel
from socrates.session import create_socrates_session
from socrates.coverage import exploration_invoke_config

__all__ = [
    "__version__",
    "StubChatModel",
    "create_socrates_session",
    "exploration_invoke_config",
]

