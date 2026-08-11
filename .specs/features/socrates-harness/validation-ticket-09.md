# Ticket 09 — Coverage-driven exploration budget Validation

**Date**: 2026-08-11
**Spec**: `.scratch/socrates-harness/spec.md` (Coverage-driven exploration budget, Testing Decisions, #1698 landmine), `CONTEXT.md` (Coverage), `docs/adr/0004-exploration-budget-scales-with-coverage.md`, `docs/adr/0002-no-automated-grader.md`, `.scratch/socrates-harness/issues/09-coverage-budget.md`
**Diff range**: `3d73f95^..3d73f95` (`feat(harness): add Coverage-driven exploration budget with subagent propagation`)
**Verifier**: independent sub-agent (author ≠ verifier)
**Verdict**: **PASS ✅**

---

## Scope of diff

| File | Change |
| ---- | ------ |
| `src/socrates/coverage.py` | New: `measure_coverage`, `recursion_limit_for`, `CoverageStore`, `BudgetAwareSubagent` (#1698 stamp + persist), `exploration_invoke_config` |
| `src/socrates/paths.py` | `COVERAGE_PATH = "/model/coverage.json"` |
| `src/socrates/inference.py` | `CoverageStore.add_conflicts` after Reconciliation and Assertion-Test surfacing |
| `src/socrates/tools.py` | `select_exploration_budget` tool |
| `src/socrates/session.py` | Prompt: select budget per pass; wrap activity CompiledSubAgents in `BudgetAwareSubagent`; start parent at generous limit |
| `src/socrates/__init__.py` | Export `exploration_invoke_config` |
| `tests/test_coverage_budget.py` | Orchestration test (pass-over-pass Coverage, inverse limit, subagent propagation, allowance flags) |
| `.scratch/.../issues/09-...md` | Ticket marked done |

---

## Spec-Anchored Acceptance Criteria (Done-when)

| Criterion (Done-when) | Spec-defined outcome | `file:line` + assertion | Result |
| --------------------- | -------------------- | ----------------------- | ------ |
| **AC1** — Coverage is read pass-over-pass from declining signals (e.g., Conflicts surfaced per pass) | Coverage is a gradient from Conflict counts across passes: latest/peak; sparse when latest == peak; rises as Conflicts-per-pass decline (CONTEXT / ADR-0004) | `tests/test_coverage_budget.py:238-244` — after pass-1 Probe, `conflicts_per_pass["1"] == 3` and `coverage == 0.0` (latest == peak). `:269-274` — after pass 2, `conflicts_per_pass["1"] == 3` and `["2"] == 1`; `coverage == 1.0 - (1 / 3)`. Engine records per-pass counts at `inference.py:228` (Reconciliation) and `:364` (Assertion Tests) via `CoverageStore.add_conflicts`; formula at `coverage.py:28-41` | ✅ PASS |
| **AC2** — The per-pass recursion limit scales inversely with Coverage | Generous when Coverage is low (sparse/early), lean when high (mature) — ADR-0004; not a static limit | `:245-247` — sparse `recursion_limit == RECURSION_LIMIT_GENEROUS` (200) and `== recursion_limit_for(0.0)`. `:275-278` — mature limit `== recursion_limit_for(2/3)` and `mature_limit < sparse_limit`. Selector at `coverage.py:44-52` interpolates LEAN(40)↔GENEROUS(200) by `(1 - coverage)`; persisted by `select_budget` (`coverage.py:73-87`) via tool `tools.py:250-261` | ✅ PASS |
| **AC3** — The chosen limit is propagated to spawned subagents (no silent fallback to 25 — #1698) | Activity subagents receive the Coverage-selected `recursion_limit`; must not silently fall back to 25 | `:298-306` — after `task` → `requirements`, `subagent_propagations` is non-empty; last record `subagent == "requirements"`, `recursion_limit == mature_limit`, `silent_fallback_avoided is True`, `last_subagent_recursion_limit == mature_limit`. Sparse/mature limits also `!= SILENT_SUBAGENT_FALLBACK` (`:248`, `:279`). Wrapper stamps invoke config at `coverage.py:168-178`; activity runnables wrapped at `session.py:109-114`. Subagent actually ran: `:308-313` (`"req activity complete"` in ToolMessages) | ✅ PASS |
| **AC4** — The budget is an exploration allowance, not a quality gate | Allowance only — never a quality signal / automated done (ADR-0002 / ADR-0004); termination stays loop-ending + Satisfaction | `:249-251` — persisted `quality_gate is False`, `role == "exploration_allowance"`, `relevance_anchored is True`. `:280` — mature snapshot still `quality_gate is False`. Session continues after both budget selections (second Probe, then subagent) and ends by stubbed-loop termination (`:295-296` — no interrupt, `next == ()`), not by Coverage scoring. Flags written in `coverage.py:78-84` | ✅ PASS |

**Status**: ✅ All 4 Done-when criteria covered with `file:line` + assertion, matching spec-defined outcomes.

---

## Discrimination Sensor

Run in isolated `git worktree` at `3d73f95` (`/tmp/socrates-sensor-t09`, removed after). Real tree never mutated; confirmed clean afterward (`git status` empty; worktree gone; gate re-run green). Worktree tests via `PYTHONPATH=src` + repo `.venv`.

| # | File:line | Mutation | Killed? |
| - | --------- | -------- | ------- |
| 1 | `src/socrates/coverage.py:41` | `measure_coverage` ignores declining-signal formula (always `0.0`) | ✅ Killed — `test_coverage_budget.py:274` (`expected_coverage` 0.0 ≠ `1.0 - 1/3`) |
| 2 | `src/socrates/coverage.py:44-46` | `recursion_limit_for` always returns silent fallback `25` | ✅ Killed — `:247` (`sparse_limit` 25 ≠ `RECURSION_LIMIT_GENEROUS` 200) |
| 3 | `src/socrates/coverage.py:168-178` | `BudgetAwareSubagent.invoke` pass-through (no stamp, no propagation record) | ✅ Killed — `:301` (`subagent_propagations` empty) |

**Sensor depth**: lightweight (3 targeted behavior-level mutations)
**Result**: 3/3 killed — **PASS ✅**

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code / no scope creep | ✅ Coverage store + inverse selector + subagent wrapper + one tool; Notification left to later tickets |
| Surgical changes | ✅ New module + thin wiring (paths, inference counts, session wrap, tools); one new test module; issue md marked done |
| Matches existing patterns | ✅ Same FS JSON / interrupt / stubbed orchestration seam as tickets 01–08 |
| Spec-anchored outcome check | ✅ Pass-over-pass Conflict counts; inverse limit; #1698 record ≠ 25; allowance flags / no quality close |
| Every test maps to a Done-when / story | ✅ Single orchestration test covers AC1–AC4 |
| Documented guidelines followed | ✅ spec "Testing Decisions" (one seam, stubbed model, observable FS + selected recursion_limit); ADR-0002/0004 (allowance ≠ grader) |

**Observations (non-blocking):**
- Parent session is created with a static generous `recursion_limit` (`session.py:149-151`). The *selected* per-pass limit is persisted and stamped onto activity subagents (`BudgetAwareSubagent`); callers can also pass it via `exploration_invoke_config`. Matches the #1698 landmine (Modeling Activities are the long-reasoning subagents) and the ticket comment.
- AC4 is asserted as persisted metadata (`quality_gate` / `role`) plus continued orchestration — there is no separate Satisfaction-at-high-Coverage path in this ticket's test. Consistent with ADR-0002: Coverage never closes the Mapping.
- `relevance_anchored` is a stored flag; Need-relevant Scenario filtering remains the existing Relevance Filter, not new Coverage logic.

---

## Gate Check

- **Gate command**: `/home/agx/agx/Socrates/.venv/bin/pytest -q`
- **Result**: **12 passed, 0 failed, 0 skipped** (~2.7s)
- **Tickets 01–08 kept green**: `test_walking_skeleton`, `test_proposition_lifecycle`, `test_modeling_activity_pipeline`, `test_probe_loop`, `test_reconciliation_conflict_levels`, `test_supersede_routing`, `test_iteration_l4`, `test_deferral` all pass alongside the ticket-09 test.
- **Test count before feature**: 11
- **Test count after feature**: 12
- **Delta**: +1 (`tests/test_coverage_budget.py`). No tests deleted or weakened.

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 4/4 Done-when criteria matched spec-defined outcomes
**Sensor**: 3/3 mutations killed
**Gate**: 12 passed, 0 failed

**What works**: Conflict counts accumulate per pass and Coverage rises as they decline; the selected `recursion_limit` is generous at Coverage 0.0 and leaner after 3→1 Conflicts; activity subagents receive that limit (recorded, not silent 25); the budget is persisted as an exploration allowance (`quality_gate: false`) and does not terminate the session — asserted through the orchestration seam.

**Issues found**: None blocking.

**Next steps**: None. Ticket 09 verified.
