"""The Need file — the Relevance Filter's artifact and its amendment record.

Ticket 22 / spec `need-refinement`: the Need is amendable while the
Requirements chapter is open. The file's body is the CURRENT Need — the
filter every consumer reads (relevance enforcement, deliverable
grounding); amendments accumulate beneath a fixed separator, each keeping
the shape it superseded and the reason (reasons always survive), newest
last. One artifact, no separate store — everything else derives at read
time (ADR-0001).
"""

from __future__ import annotations

import re

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import NEED_PATH

# The separator between the live Need and its history. The body above it
# is what consumers read; the record below it is audit, never filter.
AMENDMENT_RECORD_HEADER = "## Amendment record"

_AMENDMENT_SECTION = re.compile(r"^### Amendment (\d+) — ", re.MULTILINE)


def _read_content(backend: BackendProtocol) -> str:
    result = backend.read(NEED_PATH)
    if result.error or result.file_data is None:
        return ""
    return result.file_data["content"]


def _split(content: str) -> tuple[str, str]:
    """The file's body and its amendment record (empty when never amended)."""
    body, separator, record = content.partition(f"\n{AMENDMENT_RECORD_HEADER}\n")
    if not separator:
        return content, ""
    return body, record


def read_need(backend: BackendProtocol) -> str | None:
    """The current Need — the file's body, before the amendment record."""
    body, _ = _split(_read_content(backend))
    body = body.strip()
    return body or None


def write_amendment(
    backend: BackendProtocol,
    new_need: str,
    reason: str,
) -> None:
    """Rewrite the Need, recording the amendment beneath it (newest last).

    The superseded shape and the reason join any earlier amendments — the
    record grows append-only; the body becomes the new Need alone.
    """
    content = _read_content(backend)
    body, record = _split(content)
    superseded = body.strip()
    numbers = [int(n) for n in _AMENDMENT_SECTION.findall(record)]
    number = max(numbers) + 1 if numbers else 1

    sections = record.strip()
    section = (
        f"### Amendment {number} — {reason}\n\n"
        f"Superseded Need:\n\n{superseded}\n"
    )
    record_body = f"{sections}\n\n{section}" if sections else section
    backend.write(
        NEED_PATH,
        f"{new_need.strip()}\n\n"
        f"{AMENDMENT_RECORD_HEADER}\n\n"
        f"{record_body}",
    )
