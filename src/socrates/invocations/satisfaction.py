"""Ask the Satisfaction question — warning first, never blocking."""

from __future__ import annotations

from typing import Any

from socrates.invocation import emit, invoke
from socrates.verbs import ask_satisfaction


def satisfaction(backend: Any, data: Any) -> dict[str, Any]:
    return ask_satisfaction(backend)


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(satisfaction, argv)


if __name__ == "__main__":
    emit(main)
