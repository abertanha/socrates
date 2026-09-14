"""Ask to Reject a Proposition, with its reason."""

from __future__ import annotations

from typing import Any

from socrates.invocation import emit, invoke
from socrates.verbs import ask_reject


def reject(backend: Any, data: Any) -> dict[str, Any]:
    data = data or {}
    return ask_reject(backend, data["proposition_id"], data["reason"])


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(reject, argv)


if __name__ == "__main__":
    emit(main)
