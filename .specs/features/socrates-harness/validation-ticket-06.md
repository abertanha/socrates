# Ticket 06 — Supersede routing + L1/L3 Probe Validation

**Date**: 2026-08-11
**Spec**: `.scratch/socrates-harness/spec.md` (stories 21–23, Conflict-Level routing; Testing Decisions), `CONTEXT.md` (Supersede, Degradation cascade, Notification), `.scratch/socrates-harness/issues/06-supersede-routing.md`
**Diff range**: `687d40a^..687d40a` (`feat(harness): add L2 Supersede cascade and L1/L3 Probe routing`)
**Verifier**: independent sub-agent (author ≠ verifier)
**Verdict**: **PASS ✅**

---

## Scope of diff

| File | Change |
| ---- | ------ |
| `src/socrates/proposition.py` | `accepted_via`; `degrade`; `supersede` (+ cascade Degrade + `supersede_cascade` notification); status `superseded` |
| `src/socrates/inference.py` | Probe action `supersede` (L2 only); L3 dismiss-only guard; Probe `routing` via `_probe_routing` |
| `src/socrates/tools.py` | `accept_proposition(..., via_proposition_id)` for indirect Acceptance |
| `src/socrates/session.py` | Prompt: L1/L2/L3 Probe routing + cascade notify-not-ask |
| `src/socrates/paths.py` | `NOTIFICATIONS_PATH` |
| `tests/test_supersede_routing.py` | Orchestration tests (single seam, stubbed model) |
| `.scratch/.../issues/06-...md` | Ticket marked done |

---

## Spec-Anchored Acceptance Criteria (Done-when)

| Criterion (Done-when) | Spec-defined outcome | `file:line` + assertion | Result |
| --------------------- | -------------------- | ----------------------- | ------ |
| **AC1** — An L2 conflict can be resolved by Superseding the Accepted Proposition (displaced recorded with reason; new info → Candidate) | L2 Probe action `supersede` marks Accepted party `superseded` with reason; new party stays/enters `candidate` | `tests/test_supersede_routing.py:219` — `by_level["L2"]["routing"] == "supersede"`; `:247-249` — `props["p1"]["status"] == "superseded"`, `props["p1"]["reason"] == "Multi-Order payments are in scope."`, `props["p6"]["status"] == "candidate"`. Enforced at `src/socrates/inference.py:439-455` (L2-only supersede + reason); `proposition.py:190-195` | ✅ PASS |
| **AC2** — Supersede cascades: every Proposition accepted indirectly via the superseded one is Degraded back to Candidate, automatically | Indirect dependents (`accepted_via`) Degrade to Candidate; link cleared | `:250-251` — `props["p2"]["status"] == "candidate"`, `props["p2"]["accepted_via"] is None`; cascade payload `:260` — `"p2" in cascade[0]["degraded_ids"]`. Indirect Accept seeded via `via_proposition_id` (`:83-85`). Cascade at `proposition.py:197-201` + `_indirect_dependents` `:265-282` | ✅ PASS |
| **AC3** — The user is notified of the cascade, not asked for permission | Cascade recorded as Notification (`supersede_cascade`); no permission interrupt | `:255-260` — one `kind == "supersede_cascade"` notification with `superseded_id`/`new_proposition_id`/`degraded_ids`; `:240` — `finished.get("__interrupt__") is None` after supersede (no ask). Persist at `proposition.py:205-212` (`_append_notification` → `/model/notifications.json`) | ✅ PASS |
| **AC4** — L1 conflicts resolve in-line via Probe; L3 conflicts are blocked by the Rejection Guardrail | Probe `routing`: L1 `inline`, L3 `blocked` (dismiss only); L3 `supersede` rejected | `:197-198` — L1 conflict `level == "L1"`, `routing == "inline"`; `:220` — L3 `routing == "blocked"`; `:252` — dismissed L3 party `props["p7"]["status"] == "flagged"`; `test_l3_supersede_rejected_by_guardrail_routing` `:367-392` — L3 `routing == "blocked"`, ToolMessage error contains `"Rejection Guardrail"` and `"ok":false`. Guards at `inference.py:398-402`, `:440-444`; routing map `_probe_routing` `:613-619` | ✅ PASS |

**Status**: ✅ All 4 Done-when criteria covered with `file:line` + assertion, matching spec-defined outcomes.

---

## Discrimination Sensor

Run in isolated `git worktree` at `687d40a` (`/tmp/socrates-sensor-t06`, removed after). Real tree never mutated; confirmed clean afterward (`git status` empty; gate re-run green).

| # | File:line | Mutation | Killed? |
| - | --------- | -------- | ------- |
| 1 | `src/socrates/proposition.py:197-201` | Skip cascade Degrade: leave indirect dependents Accepted (`pass` in degrade loop) | ✅ Killed — `test_supersede_routing.py:250` (`p2` remained `accepted`, expected `candidate`) |
| 2 | `src/socrates/proposition.py:212` | Skip `_append_notification` (cascade notify not persisted) | ✅ Killed — `:255` path via `_load_json` KeyError `/model/notifications.json` (no notification file) |
| 3 | `src/socrates/inference.py:614-615` | L1 routing returns `"blocked"` instead of `"inline"` | ✅ Killed — `:198` (`routing` expected `inline`) |

**Sensor depth**: lightweight (3 targeted behavior-level mutations)
**Result**: 3/3 killed — **PASS ✅**

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code / no scope creep | ✅ Supersede + cascade + L1/L3 routing; L4 Iteration left to ticket 07; full Notification policy to ticket 10 |
| Surgical changes | ✅ Extends proposition store + Probe apply path + accept `via_`; one new test module |
| Matches existing patterns | ✅ Same FS JSON / interrupt Probe / stubbed orchestration seam as tickets 04–05 |
| Spec-anchored outcome check | ✅ Displaced reason, Candidate new info, cascade Degrade, notify-not-ask, L1/L3 routing asserted |
| Every test maps to a Done-when / story | ✅ Two orchestration tests covering AC1–AC4 (happy path + L3 supersede reject) |
| Documented guidelines followed | ✅ spec "Testing Decisions" (one seam, stubbed model, observable harness behavior) |

**Observations (non-blocking):**
- `tests/test_supersede_routing.py:261-264` is a vacuous `assert not any(... for m in [])` — does not strengthen “not asked.” Real evidence for notify-not-ask is the persisted `supersede_cascade` notification plus `:240` (no post-supersede interrupt). Acceptable; optional tighten later.
- Ticket 10 will own quiet-by-default Notification policy beyond cascade recording.

---

## Gate Check

- **Gate command**: `/home/agx/agx/Socrates/.venv/bin/pytest -q`
- **Result**: **7 passed, 0 failed, 0 skipped** (~2.0s)
- **Tickets 01–05 kept green**: `test_walking_skeleton`, `test_proposition_lifecycle`, `test_modeling_activity_pipeline`, `test_probe_loop`, `test_reconciliation_conflict_levels` all pass alongside both ticket-06 tests.
- **Test count before feature**: 5
- **Test count after feature**: 7
- **Delta**: +2 (`tests/test_supersede_routing.py`). No tests deleted or weakened.

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 4/4 Done-when criteria matched spec-defined outcomes
**Sensor**: 3/3 mutations killed
**Gate**: 7 passed, 0 failed

**What works**: L2 Supersede displaces Accepted with reason and leaves new info Candidate; indirect dependents cascade-Degrade automatically; cascade is recorded as Notification without a permission interrupt; L1 Probe routing is in-line and L3 is Guardrail-blocked (dismiss only; supersede rejected) — asserted through the orchestration seam.

**Issues found**: None blocking.

**Next steps**: None. Ticket 06 verified.
