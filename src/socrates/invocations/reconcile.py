"""Surface latent L2/L3 Conflicts from the latest ingest (pass 2+ only)."""

from __future__ import annotations

from typing import Any

from socrates.inference import InferenceEngine
from socrates.invocation import emit, invoke


def reconcile(backend: Any, data: Any) -> dict[str, Any]:
    data = data or {}
    engine = InferenceEngine(backend)
    surfaced = engine.reconcile(data["findings"])
    return {
        "ok": True,
        "pass": engine.current_pass(),
        "conflicts": [conflict.__dict__ for conflict in surfaced],
    }


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(reconcile, argv)


if __name__ == "__main__":
    emit(main)
