"""Propose a Proposition — the orchestrator surface re-raises deferred Conflicts."""

from __future__ import annotations

from typing import Any

from socrates.invocation import emit, invoke
from socrates import verbs


def propose(backend: Any, data: Any) -> dict[str, Any]:
    data = data or {}
    return verbs.propose(backend, data["statement"], data["activity"], touch=True)


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(propose, argv)


if __name__ == "__main__":
    emit(main)
