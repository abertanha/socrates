"""Socrates — maieutic agent harness on deepagents."""

from socrates.model import StubChatModel
from socrates.session import create_socrates_session
from socrates.coverage import exploration_invoke_config

__all__ = [
    "StubChatModel",
    "create_socrates_session",
    "exploration_invoke_config",
]

