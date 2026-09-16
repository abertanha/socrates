"""Ask at the chapter door — close, not yet, or route to Satisfaction."""

from __future__ import annotations

from typing import Any

from socrates.invocation import emit, invoke
from socrates.verbs import ask_door


def door(backend: Any, data: Any) -> dict[str, Any]:
    data = data or {}
    return ask_door(backend, data.get("activity"))


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(door, argv)


if __name__ == "__main__":
    emit(main)
