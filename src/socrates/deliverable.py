"""Materialize the Conceptual Domain Model deliverable at Satisfaction.

Settled layout (ticket 11):
  /model/deliverable/glossary.md
  /model/deliverable/structure.md
  /model/deliverable/rules.md

Composition draws Accepted Propositions only, filtered by
Implementation-Independence (structure in; technologies and concrete
parameter values out). Part assignment:
  - Glossary  ← requirements + definitional domain_modeling
  - Structure ← remaining domain_modeling
  - Rules     ← behavioral_specification
"""

from __future__ import annotations

import re
from typing import Iterable

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import (
    DELIVERABLE_GLOSSARY_PATH,
    DELIVERABLE_RULES_PATH,
    DELIVERABLE_STRUCTURE_PATH,
)
from socrates.need import read_need
from socrates.proposition import Proposition, PropositionStore

# Technologies / delivery channels / implementation artifacts (CONTEXT
# Implementation-Independence — "via push", junction tables, etc.).
_TECHNOLOGY = re.compile(
    r"\b("
    r"via\s+push|via\s+email|via\s+sms|via\s+webhook|"
    r"junction\s+table|postgres|postgresql|mysql|mongodb|redis|"
    r"rest\s+api|graphql|http|https|websocket|"
    r"kafka|rabbitmq|sqlite|dynamodb|s3\b"
    r")\b",
    re.IGNORECASE,
)

# Concrete parameter values (Platform Parameter value is out; nature is in).
_CONCRETE_VALUE = re.compile(
    r"\b\d+(\.\d+)?\s*"
    r"(minutes?|hours?|seconds?|days?|weeks?|ms|milliseconds?)\b"
    r"|"
    r"\b\d{2,}\s*%",
    re.IGNORECASE,
)

_FUNCTIONAL = re.compile(r"\bthe system shall\b", re.IGNORECASE)

# Definitional Domain Modeling → Glossary (ubiquitous-language terms).
_DEFINITIONAL = re.compile(
    r"\b(is|are|means|denotes|refers to|defined as|is defined as)\b",
    re.IGNORECASE,
)

_AFFIRMATIVE = frozenset(
    {
        "yes",
        "y",
        "true",
        "satisfied",
        "satisfaction",
        "i am satisfied",
        "i'm satisfied",
        "im satisfied",
    }
)


def is_affirmative_satisfaction(answer: str) -> bool:
    """Whether the resume answer signals Satisfaction (not a deferral/no)."""
    normalized = " ".join(answer.strip().casefold().split())
    return normalized in _AFFIRMATIVE or normalized.startswith("yes")


def is_implementation_independent(statement: str) -> bool:
    """Admission test: structure/parameterized rules in; specifics out."""
    if _FUNCTIONAL.search(statement):
        return False
    if _TECHNOLOGY.search(statement):
        return False
    if _CONCRETE_VALUE.search(statement):
        return False
    return True


def _part_for(prop: Proposition) -> str | None:
    if prop.activity == "behavioral_specification":
        return "rules"
    if prop.activity == "requirements":
        return "glossary"
    if prop.activity == "domain_modeling":
        if _DEFINITIONAL.search(prop.statement):
            return "glossary"
        return "structure"
    return None


def _bullet_block(title: str, need: str | None, statements: Iterable[str]) -> str:
    lines = [f"# {title}", ""]
    if need:
        lines.extend(["## Need", "", need.strip(), ""])
    lines.append("## Propositions")
    lines.append("")
    items = list(statements)
    if not items:
        lines.append("_(none)_")
    else:
        for statement in items:
            lines.append(f"- {statement}")
    lines.append("")
    return "\n".join(lines)


class DeliverableComposer:
    """Compose Glossary / Structure / Rules into the virtual filesystem."""

    def __init__(self, backend: BackendProtocol) -> None:
        self._backend = backend
        self._propositions = PropositionStore(backend)

    def materialize(self) -> dict[str, str]:
        """Write the three deliverable parts; return path → content."""
        need = self._read_need()
        glossary: list[str] = []
        structure: list[str] = []
        rules: list[str] = []

        for prop in self._propositions.list_propositions():
            if prop.status != "accepted":
                continue
            if not is_implementation_independent(prop.statement):
                continue
            part = _part_for(prop)
            if part == "glossary":
                glossary.append(prop.statement)
            elif part == "structure":
                structure.append(prop.statement)
            elif part == "rules":
                rules.append(prop.statement)

        contents = {
            DELIVERABLE_GLOSSARY_PATH: _bullet_block("Glossary", need, glossary),
            DELIVERABLE_STRUCTURE_PATH: _bullet_block("Structure", None, structure),
            DELIVERABLE_RULES_PATH: _bullet_block("Rules", None, rules),
        }
        for path, content in contents.items():
            self._backend.write(path, content)
        return contents

    def _read_need(self) -> str | None:
        # The live Need — the file's body, never its amendment record
        # (ticket 22: what ships reflects the last thing agreed).
        return read_need(self._backend)
