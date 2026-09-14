"""Record Scenarios for a Proposition — several, Need-relevant, per edge."""

from __future__ import annotations

from typing import Any

from socrates.inference import InferenceEngine
from socrates.invocation import emit, invoke


def scenarios(backend: Any, data: Any) -> dict[str, Any]:
    data = data or {}
    engine = InferenceEngine(backend)
    recorded = engine.record_scenarios(data["proposition_id"], data["scenarios"])
    return {
        "ok": True,
        "scenarios": [scenario.__dict__ for scenario in recorded],
    }


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(scenarios, argv)


if __name__ == "__main__":
    emit(main)
