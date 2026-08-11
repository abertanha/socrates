# 09 — Coverage-driven exploration budget (ADR-0004) + subagent propagation

**What to build:** Coverage is measured pass-over-pass from declining signals (e.g., Conflicts surfaced per pass). The per-pass recursion limit is selected ∝ 1/Coverage — generous when Coverage is low (sparse, early), lean when high (mature) — anchored by the Relevance Filter so a generous early budget explores Need-relevant ground, not drift. The chosen limit is explicitly propagated to subagents (#1698 — they otherwise silently fall back to 25). The budget is an exploration allowance, never a quality signal (ADR-0002).

**Blocked by:** 04 — Probe loop (needs passes running to measure Coverage).

**Status:** done

- [x] Coverage is read pass-over-pass from declining signals (e.g., Conflicts surfaced per pass).
- [x] The per-pass recursion limit scales inversely with Coverage.
- [x] The chosen limit is propagated to spawned subagents (no silent fallback to 25 — issue #1698).
- [x] The budget is an exploration allowance, not a quality gate.

## Comments

- `CoverageStore` + `select_exploration_budget`; `BudgetAwareSubagent` stamps `recursion_limit` on activity CompiledSubAgents and records propagation in `/model/coverage.json`. Orchestration coverage: `tests/test_coverage_budget.py`.
