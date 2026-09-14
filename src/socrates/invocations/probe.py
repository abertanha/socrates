"""Gather open L1–L3 Conflicts into a Batch — the Probe's pending question."""

from __future__ import annotations

from typing import Any

from socrates.inference import InferenceEngine
from socrates.invocation import emit, invoke


def probe(backend: Any, data: Any) -> dict[str, Any]:
    return InferenceEngine(backend).probe_batch()


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(probe, argv)


if __name__ == "__main__":
    emit(main)
