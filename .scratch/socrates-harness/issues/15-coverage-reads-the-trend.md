# 15 — Coverage reads the trend, not two points

**Specs:** `.scratch/coverage-signal/spec.md` · interview decisions in `.specs/features/coverage-signal/context.md`

**What to build:** The Coverage reading is replaced: instead of the single point against an immortal peak (`1 − last/peak`), Coverage becomes the moving-average crossover `clamp(1 − EMA_short / EMA_long)` recomputed deterministically from the persisted conflicts-per-pass series at measurement time (seed = first productive pass; empty series → 1.0). Named scenarios pin the reading. Everything downstream is untouched: the linear mapping (lean 40 ↔ generous 200), per-pass budget selection, subagent propagation, allowance-never-quality-gate, and the zeros guard (silent passes stay unrecorded — the refused defect, per ADR-0004's asymmetry).

**Blocked by:** 14 — The pulse moves into the chapters (the budget-selection flow this ticket re-tests lives in the chapters afterwards).

**Status:** ready-for-agent

- [ ] Flood-decay scenario: an Opening burst's influence fades as passes accumulate — no immortal peak exists
- [ ] Oscillation scenario: an alternating series (8, 1, 8, 1) yields a stable budget, not a thrash
- [ ] Decline scenario: Coverage rises smoothly as the Model accounts for more of the domain
- [ ] Rework-rise scenario: rising conflict production (Iteration rework) clamps Coverage to 0 — maximum generosity falls out of the formula, no special case
- [ ] Vacuity edge: a session that never surfaced a conflict reads 1.0
- [ ] Zero passes remain unrecorded; silence neither raises nor lowers the signal
- [ ] Budget mapping bounds and subagent-propagation assertions carry over unchanged
- [ ] Smoothing constants fixed and pinned by tests; recomputation needs no new persisted fields
