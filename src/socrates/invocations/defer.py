"""Park an open Conflict for later — refused when unavoidable."""

from __future__ import annotations

from typing import Any

from socrates.inference import InferenceEngine
from socrates.invocation import emit, invoke


def defer(backend: Any, data: Any) -> dict[str, Any]:
    data = data or {}
    payload = InferenceEngine(backend).defer_conflict(data["conflict_id"])
    payload.setdefault("ok", True)
    return payload


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(defer, argv)


if __name__ == "__main__":
    emit(main)
