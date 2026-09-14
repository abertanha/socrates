"""Ask confirmation of a Need amendment — the Relevance Filter reshaped."""

from __future__ import annotations

from typing import Any

from socrates.invocation import emit, invoke
from socrates.verbs import ask_amend_need


def amend_need(backend: Any, data: Any) -> dict[str, Any]:
    data = data or {}
    return ask_amend_need(backend, data["proposed_need"], data["reason"])


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(amend_need, argv)


if __name__ == "__main__":
    emit(main)
