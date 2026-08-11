# Ticket 08 — Deferral Validation

**Date**: 2026-08-11
**Spec**: `.scratch/socrates-harness/spec.md` (stories 26–29, Deferral), `CONTEXT.md` (Deferral), `docs/adr/0002-no-automated-grader.md` (Satisfaction is human), `.scratch/socrates-harness/issues/08-deferral.md`
**Diff range**: `ab847f8^..ab847f8` (`feat(harness): add Deferral with criticality, re-raise, and Satisfaction warning`)
**Verifier**: independent sub-agent (author ≠ verifier)
**Verdict**: **PASS ✅**

---

## Scope of diff

| File | Change |
| ---- | ------ |
| `src/socrates/inference.py` | `assess_deferral_criticality`; Probe action `defer`; `defer_conflict`; `touch_propositions`; `satisfaction_warning`; Conflict `deferred` / `re_raised`; Probe payload carries `deferral` + `re_raised`; touch after scenarios / assertion tests |
| `src/socrates/tools.py` | `defer_conflict` tool; Satisfaction interrupt includes `deferred_warning`; touch on propose / accept / reject |
| `src/socrates/session.py` | Prompt: defer any Conflict; criticality nudge; re-raise on touch; non-blocking Satisfaction warning |
| `tests/test_deferral.py` | Orchestration tests (Probe defer, criticality, re-raise, Satisfaction warning; L4 via `defer_conflict`) |
| `.scratch/.../issues/08-...md` | Ticket marked done |

---

## Spec-Anchored Acceptance Criteria (Done-when)

| Criterion (Done-when) | Spec-defined outcome | `file:line` + assertion | Result |
| --------------------- | -------------------- | ----------------------- | ------ |
| **AC1** — Any surfaced conflict can be deferred to resolve later | Orthogonal to Probe/Iteration: any Conflict, any level, may be parked | `tests/test_deferral.py:173-185` — Probe resume `action: "defer"` → Conflict `status == "deferred"`, `resolution.action == "defer"`. Second test `:317` — `defer_conflict` on L4; `:335-337` — L4 remains `status == "deferred"` with ToolMessage confirming defer (`:339-347`). Enforced at `inference.py:641-655` (Probe `defer`), `:470-488` (`defer_conflict` any open level), `tools.py:239-245` | ✅ PASS |
| **AC2** — Harness recommends against deferring critical conflicts (operational blocking-ness, not correctness — ADR-0002) | Critical = high Conflict Level and/or central (Accepted) Propositions → `recommend_against`; still allowed | `:170-171` — L1 Candidate×Candidate: `deferral.critical` / `recommend_against` are False. `:216-219` — L2 + Accepted party: both True; reasons include `high_conflict_level` and `central_proposition`. L4 path `:337` — `resolution.criticality.recommend_against is True`. Logic at `inference.py:111-131` (`assess_deferral_criticality`); exposed on Probe payload via `_probe_conflict_payload` / `_criticality_for` | ✅ PASS |
| **AC3** — Deferred conflict re-raises when new information touches its Propositions (event-driven, not every pass) | Touch of a party re-opens deferred Conflict with `re_raised` | `:187-197` — after `reject_proposition` on deferred party `p3` and confirm, next Probe resurfaces same `l1["id"]` with `re_raised is True`. Engine: `inference.py:490-512` (`touch_propositions`); wired from lifecycle tools (`tools.py:102`, `:134`, `:157`) and scenario/assertion paths (`inference.py:275`, `:361`) | ✅ PASS |
| **AC4** — Satisfaction surfaces a non-blocking, criticality-weighted warning for open deferred conflicts | Warning present; `blocking: false`; per-conflict criticality; session may still close | `:232-244` — Satisfaction interrupt has `deferred_warning` with `blocking is False`, `kind == "deferred_conflicts"`, both deferred Conflicts listed; L1 `recommend_against` False / L2 True. `:246-254` — resume `"yes"` ends session (`next == ()`); both Conflicts remain `deferred` (not hard-blocked). `inference.py:514-533` (`satisfaction_warning`); `tools.py:83-89` | ✅ PASS |

**Status**: ✅ All 4 Done-when criteria covered with `file:line` + assertion, matching spec-defined outcomes.

---

## Discrimination Sensor

Run in isolated `git worktree` at `ab847f8` (`/tmp/socrates-sensor-t08`, removed after). Real tree never mutated; confirmed clean afterward (`git status` empty; worktree gone; gate re-run green). Worktree tests via `PYTHONPATH=src` + repo `.venv`.

| # | File:line | Mutation | Killed? |
| - | --------- | -------- | ------- |
| 1 | `src/socrates/inference.py:117-131` | `assess_deferral_criticality` always returns non-critical (`recommend_against=False`) | ✅ Killed — `test_deferral.py:216` (`critical`/`recommend_against` False≠True for L2); `:337` (L4 `recommend_against` False≠True) |
| 2 | `src/socrates/inference.py:490-512` | `touch_propositions` no-op (`return []`) | ✅ Killed — `:196` (expected re-raised `c1`; next Probe was later L2 `c2` because deferred L1 never re-opened) |
| 3 | `src/socrates/inference.py:514-533` | `satisfaction_warning` always `None` | ✅ Killed — `:236` (`warning is not None` fails) |

**Sensor depth**: lightweight (3 targeted behavior-level mutations)
**Result**: 3/3 killed — **PASS ✅**

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code / no scope creep | ✅ Deferral tracker + Probe action + tool + Satisfaction warning; Notification / Coverage left to later tickets |
| Surgical changes | ✅ Engine + tools wiring + session prompt; one new test module; issue md marked done |
| Matches existing patterns | ✅ Same FS JSON / interrupt confirm / stubbed orchestration seam as tickets 04–07 |
| Spec-anchored outcome check | ✅ Any-level defer; criticality recommend-against; event-driven re-raise; non-blocking Satisfaction warning |
| Every test maps to a Done-when / story | ✅ Main orchestration test covers AC1–AC4; second test covers AC1 for L4 + AC2 criticality |
| Documented guidelines followed | ✅ spec "Testing Decisions" (one seam, stubbed model, observable harness behavior); ADR-0002 (warning ≠ grader / hard block) |

**Observations (non-blocking):**
- Criticality is operational (Conflict Level L2–L4 and/or Accepted parties), not Model-correctness scoring — matches CONTEXT Deferral and ADR-0002.
- Re-raise is tied to explicit touch sites (propose/accept/reject + scenario/assertion ingest), not a every-pass sweep — matches “event-driven, not every pass.”

---

## Gate Check

- **Gate command**: `/home/agx/agx/Socrates/.venv/bin/pytest -q`
- **Result**: **11 passed, 0 failed, 0 skipped** (~2.8s)
- **Tickets 01–07 kept green**: `test_walking_skeleton`, `test_proposition_lifecycle`, `test_modeling_activity_pipeline`, `test_probe_loop`, `test_reconciliation_conflict_levels`, `test_supersede_routing`, `test_iteration_l4` all pass alongside both ticket-08 tests.
- **Test count before feature**: 9
- **Test count after feature**: 11
- **Delta**: +2 (`tests/test_deferral.py`). No tests deleted or weakened.

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 4/4 Done-when criteria matched spec-defined outcomes
**Sensor**: 3/3 mutations killed
**Gate**: 11 passed, 0 failed

**What works**: Any open Conflict (including L4 via `defer_conflict`) can be deferred; Probe payloads carry criticality that recommends against deferring high-level / central Conflicts without blocking deferral; touching a deferred party re-opens the Conflict with `re_raised`; Satisfaction presents a non-blocking, criticality-weighted `deferred_warning` and still allows close — asserted through the orchestration seam.

**Issues found**: None blocking.

**Next steps**: None. Ticket 08 verified.
