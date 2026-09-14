"""The pipeline — which Modeling Activities completed, which is active."""

from __future__ import annotations

from typing import Any

from socrates.invocation import emit, invoke
from socrates.pipeline import PipelineStore


def pipeline_status(backend: Any, data: Any) -> dict[str, Any]:
    return {"ok": True, "pipeline": PipelineStore(backend).snapshot()}


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(pipeline_status, argv)


if __name__ == "__main__":
    emit(main)
