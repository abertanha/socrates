"""Resume the pending question — one entry for every kind.

The pending payload carries its kind; the conductor answers the question
it was shown with ``{canonical, raw}`` and never picks a resume verb.
"""

from __future__ import annotations

from typing import Any

from socrates.invocation import emit, invoke
from socrates.verbs import resume_pending


def resume(backend: Any, data: Any) -> dict[str, Any]:
    return resume_pending(backend, data)


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(resume, argv)


if __name__ == "__main__":
    emit(main)
