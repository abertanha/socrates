# Ticket 07 — Iteration (L4) Validation

**Date**: 2026-08-11
**Spec**: `.scratch/socrates-harness/spec.md` (stories 31–33, Conflict-Level routing, Iteration), `CONTEXT.md` (Iteration), `.scratch/socrates-harness/issues/07-iteration-l4.md`
**Diff range**: `493485f^..493485f` (`feat(harness): route L4 Conflicts to Iteration with phase confirm`)
**Verifier**: independent sub-agent (author ≠ verifier)
**Verdict**: **PASS ✅**

---

## Scope of diff

| File | Change |
| ---- | ------ |
| `src/socrates/inference.py` | `propose_iteration_activity`; `run_iteration` + `interrupt_iteration` + confirm parse; `probe_batch` excludes L4; Probe apply rejects L4; `_probe_routing` → `"iteration"` for L4 |
| `src/socrates/pipeline.py` | `PipelineStore.reopen` (drop activity + downstream; set active) |
| `src/socrates/tools.py` | `run_iteration` tool; `probe_batch` docstring notes L4 → Iteration |
| `src/socrates/session.py` | Prompt: L4 → `run_iteration` (propose / confirm / reopen) |
| `tests/test_iteration_l4.py` | Orchestration tests (L4→Iteration, upstream proposal, confirm, re-run) |
| `tests/test_reconciliation_conflict_levels.py` | L4 left out of Probe batch; Iteration interrupt + resolve |
| `.scratch/.../issues/07-...md` | Ticket marked done |

---

## Spec-Anchored Acceptance Criteria (Done-when)

| Criterion (Done-when) | Spec-defined outcome | `file:line` + assertion | Result |
| --------------------- | -------------------- | ----------------------- | ------ |
| **AC1** — An L4 conflict is routed to Iteration, not resolved by a Probe | L4 (Accepted×Accepted) handed to Iteration; not Probe-batched/resolved | `tests/test_iteration_l4.py:217-226` — `probe_batch` with only L4 yields ToolMessage `"ok":false` containing `"Iteration"` (`assert probe_err`); `:234-235` — interrupt `kind == "iteration"`. Sibling: `tests/test_reconciliation_conflict_levels.py:267-269` — Probe2 `by_level` is only `{"L2","L3"}` (no L4); `:291-298` — L4 stays `open` until Iteration; `:311-318` — Iteration interrupt then `resume="yes"`. Enforced at `inference.py:334-347` (`level != "L4"` filter + error text), `:479-483` (Probe apply rejects L4), `:706-713` (`_probe_routing` → `"iteration"`), `tools.py:212-218` (`run_iteration`) | ✅ PASS |
| **AC2** — Iteration proposes the most-upstream Modeling Activity whose output the L4 invalidates, based on the conflicting Propositions' nature | Most-upstream of parties' activities (Need → Requirements; entity → Domain Modeling; behavior → Behavioral) | `:238` — requirements × domain_modeling → `proposed_activity == "requirements"`; `:239-242` — parties carry both activities; `test_l4_iteration_proposes_domain_for_entity_vs_behavior` `:360` — domain × behavioral → `proposed_activity == "domain_modeling"`. Sibling `:314` — mixed L4 proposes `"domain_modeling"`. Logic at `inference.py:94-103` (`min` of `ACTIVITIES_IN_ORDER` indices) + `:405` | ✅ PASS |
| **AC3** — The user confirms which phase reopens | Harness proposes; user confirms (accept proposal or name activity) | `:244` — `Command(resume="yes")` after Iteration interrupt; `:261-264` — conflict `resolution.action == "iterate"`, `activity`/`proposed_activity == "requirements"`. Second test `:362-364` — `resume={"activity": "domain_modeling"}` confirms explicit phase; `:368-369` — pipeline `active == "domain_modeling"`, `completed == ["requirements"]`. Confirm path: `inference.py:407-433` (`kind: "iteration"` interrupt) + `_parse_iteration_confirm` `:716-743` | ✅ PASS |
| **AC4** — The reopened activity re-runs against the current Model | Reopen sets pipeline active; activity re-executes; prior Model (Need + propositions) retained | `:249` — Need unchanged after Iteration; `:254-258` — original propositions still present and `revised_req` added with `activity == "requirements"`; `:266-269` — after re-run, `pipeline.completed == ["requirements"]`, `active is None`; `:276` — tool text contains `"req activity re-run complete"`. Reopen at `pipeline.py:73-81`; applied in `run_iteration` `:434` | ✅ PASS |

**Status**: ✅ All 4 Done-when criteria covered with `file:line` + assertion, matching spec-defined outcomes.

---

## Discrimination Sensor

Run in isolated `git worktree` at `493485f` (`/tmp/socrates-sensor-t07`, removed after). Real tree never mutated; confirmed clean afterward (`git status` empty; gate re-run green). Worktree tests via `PYTHONPATH=src` + repo `.venv`.

| # | File:line | Mutation | Killed? |
| - | --------- | -------- | ------- |
| 1 | `src/socrates/inference.py:340` | Drop `and c.level != "L4"` so L4 enters Probe batch | ✅ Killed — `test_iteration_l4.py:226` (`probe_err` empty; Probe no longer errors for L4-only) |
| 2 | `src/socrates/inference.py:99` | `min` → `max` (propose most-downstream, not upstream) | ✅ Killed — `:238` (`domain_modeling` ≠ `requirements`); `:360` (`behavioral_specification` ≠ `domain_modeling`) |
| 3 | `src/socrates/pipeline.py:73-81` | `reopen` no-op: return `_load()` without rewriting pipeline | ✅ Killed — `:257` (`revised_req` missing — Requirements did not re-run); second test KeyError `/model/pipeline.json` at load after failed reopen write (`:367-369` path) |

**Sensor depth**: lightweight (3 targeted behavior-level mutations)
**Result**: 3/3 killed — **PASS ✅**

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code / no scope creep | ✅ Iteration path for L4 only; Probe remains L1–L3; Notification/Deferral left to later tickets |
| Surgical changes | ✅ Engine + pipeline reopen + one tool + session prompt; one new test module; sibling test updated for L4 exclusion |
| Matches existing patterns | ✅ Same FS JSON / interrupt confirm / stubbed orchestration seam as tickets 04–06 |
| Spec-anchored outcome check | ✅ L4→Iteration not Probe; most-upstream proposal; user confirm; reopen + re-run against current Model |
| Every test maps to a Done-when / story | ✅ Two orchestration tests cover AC1–AC4; reconciliation sibling asserts Probe/Iteration split |
| Documented guidelines followed | ✅ spec "Testing Decisions" (one seam, stubbed model, observable harness behavior) |

**Observations (non-blocking):**
- “Nature” of parties is carried by Proposition `activity` tags (min upstream index), matching the issue comment and CONTEXT phase mapping; tests do not NLP-classify statement text.
- Override confirm (`resume={"activity": ...}`) is covered; rejecting/aborting Iteration without reopen is out of ticket Done-when scope.

---

## Gate Check

- **Gate command**: `/home/agx/agx/Socrates/.venv/bin/pytest -q`
- **Result**: **9 passed, 0 failed, 0 skipped** (~2.4s)
- **Tickets 01–06 kept green**: `test_walking_skeleton`, `test_proposition_lifecycle`, `test_modeling_activity_pipeline`, `test_probe_loop`, `test_reconciliation_conflict_levels`, `test_supersede_routing` all pass alongside both ticket-07 tests.
- **Test count before feature**: 7
- **Test count after feature**: 9
- **Delta**: +2 (`tests/test_iteration_l4.py`). No tests deleted or weakened; reconciliation test updated to assert L4→Iteration instead of Probe-dismiss.

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 4/4 Done-when criteria matched spec-defined outcomes
**Sensor**: 3/3 mutations killed
**Gate**: 9 passed, 0 failed

**What works**: L4 Conflicts are excluded from Probe and handed to Iteration; the harness proposes the most-upstream Modeling Activity from party activity tags; the user confirms (yes or explicit activity); `PipelineStore.reopen` reopens that phase and the activity re-runs against the retained Model — asserted through the orchestration seam.

**Issues found**: None blocking.

**Next steps**: None. Ticket 07 verified.
