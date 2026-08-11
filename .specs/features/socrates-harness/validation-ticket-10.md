# Ticket 10 — Notification policy (quiet by default) Validation

**Date**: 2026-08-11
**Spec**: `.scratch/socrates-harness/spec.md` (story 36, Notification policy, Testing Decisions, Out of Scope — delivery channels), `CONTEXT.md` (Notifications), `.scratch/socrates-harness/issues/10-notification-policy.md`
**Diff range**: `b054ed3^..b054ed3` (`feat(harness): add quiet-by-default Notification policy`)
**Verifier**: independent sub-agent (author ≠ verifier)
**Verdict**: **PASS ✅**

---

## Scope of diff

| File | Change |
| ---- | ------ |
| `src/socrates/notifications.py` | New: `ALLOWED_KINDS`, stub channels (`in_app`/`push`/`email`), `is_unavoidable`, `NotificationService.emit` / persist |
| `src/socrates/inference.py` | Criticality exposes `deferrable`/`unavoidable`; L4 notify on Assertion-Test surface; L4 defer refused (tool + Probe action) |
| `src/socrates/proposition.py` | `supersede` emits `supersede_cascade` via `NotificationService` |
| `src/socrates/session.py` | Prompt: quiet by default; L4 unavoidable (not deferrable) |
| `tests/test_notification_policy.py` | Orchestration test (quiet Probe/Interview, L4 notify, cascade notify, stubbed channels) |
| `tests/test_deferral.py` | Ticket-08 L4-can-defer test refined: L4 defer refused |
| `.scratch/.../issues/10-...md` | Ticket marked done |

---

## Spec-Anchored Acceptance Criteria (Done-when)

| Criterion (Done-when) | Spec-defined outcome | `file:line` + assertion | Result |
| --------------------- | -------------------- | ----------------------- | ------ |
| **AC1** — Routine Probes and Interviews produce no Notification | Quiet by default: routine Probes and Interviews are not Notifications (story 36 / CONTEXT / spec Notification policy) | `tests/test_notification_policy.py:207` — Opening interrupt (`kind == "opening"`), then Accept resumes (`:211-213`); after L4 surface + L1 Probe, `:221-223` persisted kinds `== {"unavoidable_conflict"}` only. `:232` — `"probe" not in` kinds. `:249-255` — after L2 Probe (still Interview/Probe flow) kinds remain `== {"unavoidable_conflict"}`. Probe lists existing notes but does not emit (`inference.py:375-416`). `emit` rejects non-policy kinds (`notifications.py:73-79`, `ALLOWED_KINDS` at `:17`) | ✅ PASS |
| **AC2** — An unavoidable conflict (non-deferrable, blocks progress) triggers a Notification | Only an unavoidable Conflict — cannot be Deferred and blocks progress — interrupts outside Interview flow (CONTEXT: two triggers; ticket 08 refined: L4 is that case) | `:223-228` — one note `kind == "unavoidable_conflict"`, `level == "L4"`, `deferrable is False`, `blocks_progress is True`, `conflict_id == "c1"`. Selector `notifications.py:48-54` (`critical and level == "L4"`); emit from `inference.py:370-371` / `:751-765`. Defer refused: `inference.py:490-495`; `tests/test_deferral.py:337` L4 stays `"open"`; `:339-347` ToolMessage `ok:false` and `"unavoidable"` | ✅ PASS |
| **AC3** — A Supersede cascade removing interdependent Propositions triggers a Notification | User is notified of the cascade (not asked) when Supersede Degrades interdependent Propositions (CONTEXT Supersede / story 36) | `:274-282` — final kinds `== {"unavoidable_conflict", "supersede_cascade"}`; cascade `superseded_id == "p1"`, `new_proposition_id == "p6"`, `"p2" in degraded_ids` (p2 was Accepted via p1). Emit at `proposition.py:206-212` | ✅ PASS |
| **AC4** — Delivery channels are stubbed behind the Notification boundary | Push, email, in-app are implementation details, not modeled — stubbed behind the boundary (spec Out of Scope / CONTEXT) | `:229-231` — unavoidable `deliveries` channels `== set(CHANNEL_NAMES)` and `all(status == "stubbed")`. `:283-284` — same for cascade. Boundary: `CHANNEL_NAMES = ("in_app", "push", "email")` (`notifications.py:18`); `StubDeliveryChannel.deliver` writes `status: "stubbed"` (`:37-45`); `emit` fans out through injected channels (`:86-89`) | ✅ PASS |

**Status**: ✅ All 4 Done-when criteria covered with `file:line` + assertion, matching spec-defined outcomes.

---

## Discrimination Sensor

Run in isolated `git worktree` at `b054ed3` (`/tmp/socrates-sensor-t10`, removed after). Real tree never mutated; confirmed clean afterward (`git status` empty; worktree gone; gate re-run green). Worktree tests via `PYTHONPATH=src` + repo `.venv`.

| # | File:line | Mutation | Killed? |
| - | --------- | -------- | ------- |
| 1 | `src/socrates/notifications.py:54` | `is_unavoidable` always returns `False` (L4 treated as deferrable; no notify) | ✅ Killed — `test_notification_policy.py:221` via `_load_json` `:41` (`KeyError: /model/notifications.json` — no emit); also `test_deferral.py:337` (`status == "deferred"` ≠ `"open"`) |
| 2 | `src/socrates/proposition.py:206-212` | `supersede` skips `NotificationService.emit` (cascade not persisted) | ✅ Killed — `test_notification_policy.py:275` (kinds `{"unavoidable_conflict"}` ≠ `{unavoidable_conflict, supersede_cascade}`) |
| 3 | `src/socrates/notifications.py:40` | `StubDeliveryChannel.deliver` reports `status: "sent"` instead of `"stubbed"` | ✅ Killed — `test_notification_policy.py:231` (`all(status == "stubbed")` is False) |

**Sensor depth**: lightweight (3 targeted behavior-level mutations)
**Result**: 3/3 killed — **PASS ✅**

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code / no scope creep | ✅ Notification boundary + two emit sites + L4 defer refusal; no real push/email wiring |
| Surgical changes | ✅ New module + thin wiring (inference, proposition, session prompt); one new test; ticket-08 L4-defer test refined (not deleted) |
| Matches existing patterns | ✅ Same FS JSON / interrupt / stubbed orchestration seam as tickets 01–09 |
| Spec-anchored outcome check | ✅ Quiet kind-set; L4 payload flags; cascade degraded_ids; stubbed channel receipts |
| Every test maps to a Done-when / story | ✅ Orchestration test covers AC1–AC4; refined deferral test covers AC2 non-deferrable |
| Documented guidelines followed | ✅ spec "Testing Decisions" (one seam, stubbed model, observable FS); CONTEXT two-trigger policy; channels out of scope |

**Observations (non-blocking):**
- Quiet-on-Interview is inferred from the post-Opening/Accept/L1-Probe snapshot (only `unavoidable_conflict` present), not a dedicated empty-store assert immediately after Opening. A spurious same-kind emit during Interview would not be distinguished; a different kind would fail `:223`.
- Ticket 08's `test_any_level_including_l4_can_be_deferred` was renamed and **strengthened** (L4 must stay open and the tool must refuse). No assertion was weakened.
- `probe_batch` returns `list_notifications()` (`inference.py:415`) for the agent to see prior notes; it does not emit. Matches quiet-by-default.

---

## Gate Check

- **Gate command**: `/home/agx/agx/Socrates/.venv/bin/pytest -q`
- **Result**: **13 passed, 0 failed, 0 skipped** (~2.9s)
- **Tickets 01–09 kept green**: `test_walking_skeleton`, `test_proposition_lifecycle`, `test_modeling_activity_pipeline`, `test_probe_loop`, `test_reconciliation_conflict_levels`, `test_supersede_routing`, `test_iteration_l4`, `test_deferral` (incl. refined L4), `test_coverage_budget` all pass alongside the ticket-10 test.
- **Test count before feature**: 12
- **Test count after feature**: 13
- **Delta**: +1 (`tests/test_notification_policy.py`). No tests deleted or weakened.

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 4/4 Done-when criteria matched spec-defined outcomes
**Sensor**: 3/3 mutations killed
**Gate**: 13 passed, 0 failed

**What works**: Routine Opening/Accept/Probe flow leaves no Probe Notification; an L4 Accepted×Accepted Conflict persists as `unavoidable_conflict` (`deferrable: false`, `blocks_progress: true`) and cannot be parked; Supersede of a foundation notifies `supersede_cascade` with degraded dependents; `in_app`/`push`/`email` receipts are `stubbed` behind `NotificationService`.

**Issues found**: None blocking.

**Next steps**: None. Ticket 10 verified.
