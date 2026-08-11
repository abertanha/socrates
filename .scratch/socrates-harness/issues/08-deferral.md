# 08 — Deferral: now/later, criticality recommendation, re-raise, Satisfaction warning

**What to build:** Any surfaced conflict can be deferred. The harness recommends against deferring critical conflicts (high Conflict Level or central Propositions) — judging operational blocking-ness for progress, never correctness (ADR-0002). A deferred conflict re-raises when new information touches its Propositions. Satisfaction shows a non-blocking, criticality-weighted warning for open deferred conflicts.

**Blocked by:** 05 — Reconciliation + Conflict Levels.

**Status:** ready-for-agent

- [ ] Any surfaced conflict can be deferred to resolve later.
- [ ] The harness recommends against deferring critical conflicts (operational blocking-ness, not correctness — ADR-0002).
- [ ] A deferred conflict re-raises when new information touches its Propositions (event-driven, not every pass).
- [ ] Satisfaction surfaces a non-blocking, criticality-weighted warning for open deferred conflicts.
