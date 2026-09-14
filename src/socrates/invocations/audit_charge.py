"""Deliver the auditor's fixed charge — the engine's verbatim instrument."""

from __future__ import annotations

from typing import Any

from socrates.audit import AUDIT_CHARGE
from socrates.invocation import emit, invoke


def audit_charge(backend: Any, data: Any) -> dict[str, Any]:
    return {"ok": True, "charge": AUDIT_CHARGE}


def main(argv: list[str]) -> dict[str, Any]:
    return invoke(audit_charge, argv)


if __name__ == "__main__":
    emit(main)
