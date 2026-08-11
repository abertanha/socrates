# Ticket 05 — Reconciliation + Conflict Levels Validation

**Date**: 2026-08-11
**Spec**: `.scratch/socrates-harness/spec.md` (stories 18–19, 30–31; Conflict-Level routing; Testing Decisions), `CONTEXT.md` (Reconciliation + Conflict Level), `.scratch/socrates-harness/issues/05-reconciliation-conflict-levels.md`
**Diff range**: `c5f3271^..c5f3271` (`feat(harness): add Reconciliation and Conflict Levels L1–L4`)
**Verifier**: independent sub-agent (author ≠ verifier)
**Verdict**: **PASS ✅**

---

## Scope of diff

| File | Change |
| ---- | ------ |
| `src/socrates/inference.py` | `classify_conflict_level`; `InferenceEngine.reconcile`; L2/L3-only reconcile; blocked props; L4 intersection guard on Assertion Tests; pass-2+ reconcile-before-scenarios |
| `src/socrates/tools.py` | New `reconcile` tool |
| `src/socrates/paths.py` | `INFERENCE_STATE_PATH` |
| `src/socrates/session.py` | Prompt: pass-2+ `reconcile` first; skip contradicted Scenarios |
| `tests/test_reconciliation_conflict_levels.py` | Orchestration test (single seam, stubbed model) |
| `.scratch/.../issues/05-...md` | Ticket marked done |

---

## Spec-Anchored Acceptance Criteria (Done-when)

| Criterion (Done-when) | Spec-defined outcome | `file:line` + assertion | Result |
| --------------------- | -------------------- | ----------------------- | ------ |
| **AC1** — From pass 2, Reconciliation surfaces latent conflicts between the latest answers and the existing Model before Assertion Tests run | Pass ≥2: `reconcile` surfaces new×Accepted / new×Guardrail conflicts with `source=="reconciliation"` before Scenarios/Assertion Tests; pass-2+ requires reconcile first | `tests/test_reconciliation_conflict_levels.py:269-270` — `by_level["L2"]["source"] == "reconciliation"`; `by_level["L3"]["source"] == "reconciliation"`; `:273-274` — L2/L3 party ids `p6`/`p7`. Ordering guard at `src/socrates/inference.py:460-469` (`_require_reconciliation_before_scenarios`); reconcile entry `inference.py:103-108` (pass &lt; 2 rejected); tool `tools.py:135-150` | ✅ PASS |
| **AC2** — Every conflict is classified L1–L4 by the lifecycle state of its parties | Levels from party lifecycle: Candidate×Candidate→L1; new×Accepted→L2; new×Guardrail→L3; Accepted×Accepted→L4 | `:251` — probe1 conflict `level == "L1"`; `:268` — `set(by_level) == {"L2","L3","L4"}`; `:309-312` — persisted conflicts include all of L1–L4. Classifier at `inference.py:73-88` | ✅ PASS |
| **AC3** — Reconciliation yields only L2/L3 (one party always new); L4 arises only from Assertion Tests exercising two Accepted Propositions together | Reconcile source only for L2/L3; L1/L4 source `assertion_test`; L4 via intersection Scenario on two Accepted | `:269-271` — L2/L3 `source=="reconciliation"`, L4 `source=="assertion_test"`; `:272` — `other_proposition_id == "p2"`; `:313-318` — all L2/L3 reconciliation-sourced; all L1/L4 assertion-sourced. Enforced at `inference.py:152-161` (reconcile L2/L3 only), `:288-300` (Assertion Tests reject L2/L3; L4 requires `edge=="intersection"`) | ✅ PASS |
| **AC4** — Scenario generation is skipped on material Reconciliation has already contradicted | Blocked new Proposition cannot record Scenarios; skip is observable | `:277-285` — ToolMessage contains `"Scenario generation skipped"` and `"p6"`; `:288-290` — scenarios exist for `p1`, none for `p6`. Guard at `inference.py:193-197` (`blocked_proposition_ids`) | ✅ PASS |

**Status**: ✅ All 4 Done-when criteria covered with `file:line` + assertion, matching spec-defined outcomes.

---

## Discrimination Sensor

Run in isolated `git worktree` at `c5f3271` (`/tmp/socrates-sensor-t05`, removed after). Real tree never mutated; confirmed clean afterward (`git status` empty; gate re-run green).

| # | File:line | Mutation | Killed? |
| - | --------- | -------- | ------- |
| 1 | `src/socrates/inference.py:193` | Allow Scenarios on blocked props: `if proposition_id in self._blocked_proposition_ids():` → `if False:` | ✅ Killed — `test_reconciliation_conflict_levels.py:268` (L4 missing; blocked p6 absorbed scenario ids) |
| 2 | `src/socrates/inference.py:151-156` | Let Reconciliation emit L4: force `level = "L4"` for against-accepted findings; bypass L2 check | ✅ Killed — `:268` (set missing `L2`) |
| 3 | `src/socrates/inference.py:73-88` | Skip level classification: `classify_conflict_level` always returns `"L1"` | ✅ Killed — `:265` (reconcile/assertion path breaks; no probe2 interrupt) |

**Sensor depth**: lightweight (3 targeted behavior-level mutations)
**Result**: 3/3 killed — **PASS ✅**

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code / no scope creep | ✅ Deterministic reconcile + classify + block; no Iteration/Supersede (tickets 06–07) |
| Surgical changes | ✅ Extends `inference.py` + one tool + path + prompt; no unrelated churn |
| Matches existing patterns | ✅ Same dataclass/FS/tool JSON style as ticket 04 |
| Spec-anchored outcome check | ✅ Asserted levels, sources, skip message, persisted artifacts match CONTEXT/ticket |
| Every test maps to a Done-when / story | ✅ Single orchestration test per Testing Decisions |
| Documented guidelines followed | ✅ spec "Testing Decisions" (one seam, stubbed model, observable harness behavior) |

**Observations (non-blocking):**
- Pass-1 reject of `reconcile` and the explicit “must run before Scenarios” ValueError are enforced in code (`inference.py:106-108`, `:460-469`) but only exercised positively via the pass-2 happy path, not via dedicated negative orchestration asserts. Acceptable for this ticket’s Done-when set.
- L4 Iteration routing is out of scope (ticket 07); this ticket only requires L4 classification + Assertion-Test origin.

---

## Gate Check

- **Gate command**: `/home/agx/agx/Socrates/.venv/bin/pytest -q`
- **Result**: **5 passed, 0 failed, 0 skipped** (~1.8s)
- **Tickets 01–04 kept green**: `test_walking_skeleton`, `test_proposition_lifecycle`, `test_modeling_activity_pipeline`, `test_probe_loop` all pass alongside `test_reconciliation_levels_and_scenario_skip`.
- **Test count before feature**: 4
- **Test count after feature**: 5
- **Delta**: +1 (`tests/test_reconciliation_conflict_levels.py`). No tests deleted or weakened.

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 4/4 Done-when criteria matched spec-defined outcomes
**Sensor**: 3/3 mutations killed
**Gate**: 5 passed, 0 failed

**What works**: Pass-2+ Reconciliation surfaces L2/L3 before Scenarios/Assertion Tests; all Conflicts classified L1–L4 from lifecycle state; L4 only from intersection Assertion Tests on two Accepted Propositions; Scenario generation skipped for Reconciliation-blocked material — asserted through the single orchestration seam.

**Issues found**: None blocking.

**Next steps**: None. Ticket 05 verified.
