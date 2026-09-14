"""Record Assertion-Test outcomes — the broken ones surface L1/L4 Conflicts."""

from __future__ import annotations

from typing import Any

from socrates.inference import InferenceEngine
from socrates.invocation import emit, invoke


def assertion_tests(backend: Any, data: Any) -> dict[str, Any]:
    data = data or {}
    engine = InferenceEngine(backend)
    surfaced = engine.run_assertion_tests(data["proposition_id"], data["outcomes"])
    return {
        "ok": True,
        "conflicts": [conflict.__dict__ for conflict in surfaced],
    }


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(assertion_tests, argv)


if __name__ == "__main__":
    emit(main)
