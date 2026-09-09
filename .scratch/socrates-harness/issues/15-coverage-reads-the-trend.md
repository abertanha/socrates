# 15 — Coverage reads the trend, not two points

**Specs:** `.scratch/coverage-signal/spec.md` · interview decisions in `.specs/features/coverage-signal/context.md`

**What to build:** The Coverage reading is replaced: instead of the single point against an immortal peak (`1 − last/peak`), Coverage becomes the moving-average crossover `clamp(1 − EMA_short / EMA_long)` recomputed deterministically from the persisted conflicts-per-pass series at measurement time (seed = first productive pass; empty series → 1.0). Named scenarios pin the reading. Everything downstream is untouched: the linear mapping (lean 40 ↔ generous 200), per-pass budget selection, subagent propagation, allowance-never-quality-gate, and the zeros guard (silent passes stay unrecorded — the refused defect, per ADR-0004's asymmetry).

**Blocked by:** 14 — The pulse moves into the chapters (the budget-selection flow this ticket re-tests lives in the chapters afterwards).

**Status:** done (2026-09-09)

- [x] Flood-decay scenario: an Opening burst's influence fades as passes accumulate — no immortal peak exists
- [x] Oscillation scenario: an alternating series (8, 1, 8, 1) yields a stable budget, not a thrash
- [x] Decline scenario: Coverage rises smoothly as the Model accounts for more of the domain
- [x] Rework-rise scenario: rising conflict production (Iteration rework) clamps Coverage to 0 — maximum generosity falls out of the formula, no special case
- [x] Vacuity edge: a session that never surfaced a conflict reads 1.0
- [x] Zero passes remain unrecorded; silence neither raises nor lowers the signal
- [x] Budget mapping bounds and subagent-propagation assertions carry over unchanged
- [x] Smoothing constants fixed and pinned by tests; recomputation needs no new persisted fields

## Verification

Gate: `pytest -q` via the repo venv — **46 passed** (38 pre-existing outside
the rewritten file + 8 in `tests/test_coverage_budget.py`). TDD followed:
the rewritten suite first failed against the old reading (it imports the
new constants, and every scenario pin mismatches `1 − last/peak`).

### Rulings and chosen values

- **Smoothing constants** (the context file left them to discretion):
  `EMA_SHORT_SPAN = 3`, `EMA_LONG_SPAN = 9`, converted with the canonical
  `alpha = 2 / (span + 1)` → `EMA_SHORT_ALPHA = 0.5`, `EMA_LONG_ALPHA = 0.2`.
  A 1:3 short:long ratio of a 3-pass and a 9-pass average; round alpha
  values make hand verification easy. Pinned by
  `test_smoothing_constants_are_pinned`.
- **Seed and recomputation**: both EMAs seeded at the first productive
  pass, recomputed from the persisted series on every call. `measure()`
  only reads — the store test asserts persisted keys stay within
  `{conflicts_per_pass, subagent_propagations}` (no reading, no smoothing
  state persisted).
- **Zeros**: filtered in the pure function before the averages run, on top
  of the unchanged `count <= 0` store guard. Numbering gaps left by silent
  passes (`{"1": 8, "3": 1}`) read identically to the gap-free series.
- **Scenario values pinned** (spans 3/9):
  - flood-decay `[30] + [6]×20`: 0.4382 after `[30, 6, 6]` → 0.0441 at the
    end (< 0.1); strictly declining after its peak. Old reading: 0.8
    forever (limit ~72).
  - oscillation `[8, 1]×8`: readings ≤ 0.3645 (old: 0.875); limits in
    [142, 200] — never below the 120 midpoint; max per-pass swing 54
    (old: 140 every pass).
  - decline `[10, 8, 6, 4, 2]`: 0 → 0.4236 strictly rising, per-pass steps
    < 0.2; limits `[200, 190, 175, 156, 132]`.
  - rework-rise `[2, 4, 8, 16]`: every prefix exactly 0.0; reopened
    `[6, 6, 4, 2, 6, 10]` had risen to 0.2828 then clamps to exactly 0.0 —
    Iteration needs no reset.
  - vacuity: `[]`, `{}`, `[0, 0, 0]` → 1.0.
- **Orchestration saga** (`tests/test_coverage_budget.py`, rewritten
  treadmill-shaped for ticket 17: propose → record → test per Candidate,
  chapter-close stubs in one helper, no ticket-17 interrupts scripted):
  `{"1": 3, "2": 1}` → Coverage 3/13 ≈ 0.2308, limit 163 (old reading:
  2/3 → 93). Last propagation = behavioral-specification @ 163; first
  propagation = requirements @ LEAN 40 — the vacuity edge at the live seam
  (the Requirements chapter runs before any conflict exists).
- **Deviation from the file rule, recorded**: one edit outside
  `tests/test_coverage_budget.py` — `tests/test_conduction.py::
  test_full_pass_runs_inside_a_chapter` asserted the carried limit was
  GENEROUS, but its script selects the budget *before* any conflict is
  recorded, and under this ticket's vacuity edge an empty series reads 1.0
  (lean), so the expectation moves GENEROUS → LEAN (assertions and import,
  with a comment). The spec's note that empty → 1.0 was "the same edge as
  the current `peak ≤ 0` guard" was inaccurate: the retired code returned
  0.0 on the empty branch, so vacuity is a real behavior change — the AC
  ("a session that never surfaced a conflict reads 1.0") was applied as
  written. The test's intent (explicit propagation, never silent 25) is
  unchanged. `test_conduction.py::test_redirect_*` and all other
  pre-existing tests were untouched and stay green.

### Integration addendum (2026-09-09, two-axis review + user ruling)

The empty→1.0 flip means every session's FIRST budget selection (before any
Conflict exists) is LEAN 40, was GENEROUS 200. **The user reviewed this
against ADR-0004's asymmetry and ruled: keep LEAN 40** — faithful to the
AC's letter and the no-special-case rule; pass 2+ self-corrects to generous
as soon as any Conflict exists. Recorded so the first real-model session
knows the first pass digs lean by design.
