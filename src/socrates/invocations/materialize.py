"""Compose the deliverable from the recorded ground."""

from __future__ import annotations

from typing import Any

from socrates.invocation import emit, invoke
from socrates.verbs import materialize_deliverable


def materialize(backend: Any, data: Any) -> dict[str, Any]:
    return materialize_deliverable(backend)


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(materialize, argv)


if __name__ == "__main__":
    emit(main)
