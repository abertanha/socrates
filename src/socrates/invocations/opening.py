"""Ask the Opening question — the Need, in the user's own words."""

from __future__ import annotations

from typing import Any

from socrates.invocation import emit, invoke
from socrates.verbs import ask_opening


def opening(backend: Any, data: Any) -> dict[str, Any]:
    return ask_opening(backend)


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(opening, argv)


if __name__ == "__main__":
    emit(main)
