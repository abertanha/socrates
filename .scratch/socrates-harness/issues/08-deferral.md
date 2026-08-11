# 08 — Deferral: now/later, criticality recommendation, re-raise, Satisfaction warning

**What to build:** Any surfaced conflict can be deferred. The harness recommends against deferring critical conflicts (high Conflict Level or central Propositions) — judging operational blocking-ness for progress, never correctness (ADR-0002). A deferred conflict re-raises when new information touches its Propositions. Satisfaction shows a non-blocking, criticality-weighted warning for open deferred conflicts.

**Blocked by:** 05 — Reconciliation + Conflict Levels.

**Status:** done

- [x] Any surfaced conflict can be deferred to resolve later.
- [x] The harness recommends against deferring critical conflicts (operational blocking-ness, not correctness — ADR-0002).
- [x] A deferred conflict re-raises when new information touches its Propositions (event-driven, not every pass).
- [x] Satisfaction surfaces a non-blocking, criticality-weighted warning for open deferred conflicts.

## Comments

- Probe action `defer` (L1–L3) + `defer_conflict` tool (any level including L4). Criticality: L2–L4 and/or Accepted parties → `recommend_against`. `touch_propositions` re-opens deferred Conflicts; Satisfaction interrupt carries `deferred_warning` with `blocking: false`. Orchestration coverage: `tests/test_deferral.py`.
