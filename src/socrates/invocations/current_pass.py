"""The current pass — pass 1 is the Opening-seeded pass; each probe unlaps."""

from __future__ import annotations

from typing import Any

from socrates.inference import InferenceEngine
from socrates.invocation import emit, invoke


def current_pass(backend: Any, data: Any) -> dict[str, Any]:
    return {"ok": True, "pass": InferenceEngine(backend).current_pass()}


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(current_pass, argv)


if __name__ == "__main__":
    emit(main)
