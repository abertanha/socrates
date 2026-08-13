# LESSONS — auto-maintained by scripts/lessons.py

> Machine-owned. Do NOT hand-edit. Changes are overwritten on the next `lessons.py` write.
> Canonical state lives in `.specs/lessons.json`. Edit lessons only via the script.
> promote_threshold=2 distinct features · window_days=45 · quarantine_threshold=2

## Confirmed (load these at Specify/Design)

Corroborated across multiple features. Safe to apply as guidance.

_none_

## Candidates (under observation — do NOT load as guidance yet)

Seen once or not yet corroborated. Tracked, not trusted.

### L-001 — When a side effect is gated on an affirmative user answer, assert the negative resume path leaves the side effect absent
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `harness/orchestration` · harmful: 0
- features: socrates-harness
- evidence: validation-ticket-11.md sensor#4 deliverable.py:73-76 / test_deliverable_composition.py:148 (harness/orchestration)
- last seen: 2026-08-13T12:53:31Z

### L-002 — Do not treat constant-equality asserts as evidence that a discovered layout was validated against produced content
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `harness/tests` · harmful: 0
- features: socrates-harness
- evidence: validation-ticket-11.md AC3 test_deliverable_composition.py:158-160 (harness/tests)
- last seen: 2026-08-13T12:53:31Z

### L-003 — When composition draws only Accepted records, include a non-Accepted fixture that would otherwise qualify and assert it stays out
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `harness/orchestration` · harmful: 0
- features: socrates-harness
- evidence: validation-ticket-11.md extra-probe deliverable.py:133-134 (harness/orchestration)
- last seen: 2026-08-13T12:53:53Z

## Quarantined (failed when applied — ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
