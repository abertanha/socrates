"""Ask to Accept a Proposition into the Model."""

from __future__ import annotations

from typing import Any

from socrates.invocation import emit, invoke
from socrates.verbs import ask_accept


def accept(backend: Any, data: Any) -> dict[str, Any]:
    data = data or {}
    return ask_accept(
        backend, data["proposition_id"], data.get("via_proposition_id", "")
    )


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(accept, argv)


if __name__ == "__main__":
    emit(main)
