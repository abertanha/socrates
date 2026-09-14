"""Hand an L4 Conflict to Iteration — propose reopening a Modeling Activity."""

from __future__ import annotations

from typing import Any

from socrates.inference import InferenceEngine
from socrates.invocation import emit, invoke


def iteration(backend: Any, data: Any) -> dict[str, Any]:
    data = data or {}
    payload = InferenceEngine(backend).run_iteration(data["conflict_id"])
    return payload


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(iteration, argv)


if __name__ == "__main__":
    emit(main)
