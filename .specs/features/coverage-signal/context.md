# Coverage Signal Context

**Gathered:** 2026-09-04
**Spec:** `.specs/features/coverage-signal/spec.md` (to be written via `/to-spec`)
**Status:** Ready for spec

---

## Feature Boundary

Re-operationalize the Coverage signal (ADR-0004) — how conflicts-per-pass are read into the Coverage gradient that drives the exploration budget. Today: `1 − last/peak` over productive passes only, peak = historical maximum. This delta replaces that reading with a trend measurement. Unchanged: the glossary's Coverage concept (gradient, never terminal), the inverse budget relation, the linear Coverage→recursion_limit mapping (40 lean ↔ 200 generous), and ADR-0004's guardrails (Relevance-anchored; allowance, never quality gate).

---

## Implementation Decisions

### Defects validated (and the one refused)

The interview first corrected the initial assessment's misreading: the `count ≤ 0` guard in the coverage store means **zero-conflict passes are never recorded** — silence is invisible, so the claimed "one silent pass collapses Coverage to 1.0" was wrong; the real failure modes are the opposite direction. Three defects were presented with session-level consequences; the user refused to accept two:

- **Defect 1 — peak-hostage (fix)**: an Opening flood (e.g. 30 conflicts) makes later steady production (6/pass) read as 80% covered → premature lean budget while the domain is still rich → **under-exploration**: the Model converges to Satisfaction looking done, with unexposed conflicts.
- **Defect 3 — single-point oscillation (fix)**: `last` is one pass; alternating series (8,1,8,1) swings the budget 200↔60 every pass — thrash.
- **Defect 2 — invisible silence (accepted as-is)**: zero passes don't register; Coverage freezes at the last productive reading; the session tail never winds down. **Refused as a defect**: per ADR-0004's own asymmetry — "a high limit buys nothing and a low one is harmless" — over-budgeting at maturity is costless (the agent terminates early anyway); only under-budgeting is expensive. The user's selection encodes exactly that asymmetry: fix the two under-budgeting failures, accept the tail generosity.
- Accepted consequence, stated explicitly: **all candidate designs read steady conflict production as sparse** (generous tail). This is the deliberate complement of refusing defect 2.

### The reading: moving-average crossover (design B)

- **Coverage = clamp(1 − EMA_short / EMA_long, 0, 1)** over the conflicts-per-pass series.
- No peak exists — defect 1 dissolves by absence of the immortal reference; defect 3 damps because both EMAs move slowly.
- Trend semantics: recent production small relative to the recent past → Coverage rises toward lean; production rising (Iteration rework reopening ground) → EMA_short crosses above EMA_long → ratio > 1 → clamped to 0 → **maximum generosity automatically during rework** — the Iteration/reopen interaction needs no special case and no reset.
- Rejected alternatives: (A) double smoothing (EMA signal + decaying peak — keeps the ratio shape but two mechanisms); (C) bounded peak window + two-pass direction confirmation (minimal change, but window-edge jump + one-pass lag). The user chose B.

### What stays untouched

- Zero passes remain unrecorded (the `count ≤ 0` guard stays) — silence neither raises nor lowers Coverage (refusal of defect 2).
- The linear Coverage→recursion_limit interpolation and its constants (LEAN 40, GENEROUS 200).
- The glossary Coverage term (concept level — unchanged) and ADR-0004 (the crossover **is** a faithful operationalization of "read pass-over-pass from declining signals"; no ADR amendment needed).
- Persistence: `conflicts_per_pass` continues to accumulate in the coverage file.

### Agent's Discretion

- EMA smoothing constants (short/long windows) — fixed and pinned by tests.
- EMAs recomputed deterministically from the persisted `conflicts_per_pass` history at measurement time — no new state fields required beyond the existing series; seed = first productive pass.
- Empty series (never any conflict) → Coverage 1.0 (mature by vacuity — same edge as today's `peak ≤ 0` guard).

---

## Specific References

- ADR-0004's asymmetry quote — "a well-mapped domain finds little new and terminates early regardless, so a high limit buys nothing and a low one is harmless" — is the principle behind refusing defect 2.
- Session-narrative framings that landed with the user: peak-hostage = "the harness loses its appetite too early"; oscillation = "bipolar rhythm"; invisible silence = "the tail never slows down."

---

## Deferred Ideas

- Registering silent passes (defect 2 fix) — revisit only if the first real-model session shows tail-drag actually costing interview fatigue.
- Non-linear budget mapping (tiers, hysteresis) — the linear interpolation survived this cycle untouched; revisit with real-session evidence.
- Per-activity Coverage (currently one global series) — not discussed; out of scope.
