"""The pending question, if one stands — the conductor's cue to resume."""

from __future__ import annotations

from typing import Any

from socrates.asking import read_pending
from socrates.invocation import emit, invoke


def pending_question(backend: Any, data: Any) -> dict[str, Any]:
    return {"ok": True, "pending": read_pending(backend)}


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(pending_question, argv)


if __name__ == "__main__":
    emit(main)
