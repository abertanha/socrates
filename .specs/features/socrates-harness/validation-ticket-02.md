# Socrates Harness — Ticket 02 Proposition Lifecycle Validation

**Date**: 2026-08-11
**Spec**: `.scratch/socrates-harness/issues/02-proposition-lifecycle.md` (Done-when ACs); broader context `.scratch/socrates-harness/spec.md` (stories 9–10, 24–25; Proposition lifecycle implementation decision; Testing Decisions — single orchestration seam); `CONTEXT.md` Proposition lifecycle terms; ADR-0001
**Diff range**: `ee383e0^..ee383e0` (commit `ee383e0c64e405715d390263406a36da0636db32`)
**Verifier**: independent sub-agent (author ≠ verifier)

---

## Task Completion

No formal `tasks.md` for this feature (tracer-bullet ticket). Ticket Done-when checklist:

| Criterion | Status | Notes |
| --------- | ------ | ----- |
| DW1 No-conflict propose → Candidate | ✅ Done | Orchestration asserts `status == "candidate"` after propose |
| DW2 Accept Candidate / Reject with explicit reason | ✅ Done | Interrupt-gated Accept → `accepted`; Reject with reason → `rejected` |
| DW3 Rejected + reason recorded in Rejection Guardrail | ✅ Done | `/model/rejection_guardrail.json` entry asserted |
| DW4 Resembling Guardrail entry → Flagged | ✅ Done | Normalized-equality resemblance → `flagged` + `flagged_against_id` |
| DW5 Stubbed-provider orchestration seam | ✅ Done | `StubChatModel` + session invoke/resume |

---

## Spec-Anchored Acceptance Criteria

Source of truth: ticket 02 Done-when (5 criteria). Broader stories 9–10, 24–25 and CONTEXT lifecycle terms supply outcome vocabulary. **MVP resemblance precision** (documented): normalized string equality (`casefold` + whitespace collapse) — not fuzzy semantic similarity.

| Criterion (WHEN X THEN Y) | Spec-defined outcome | `file:line` + assertion | Result |
| ------------------------- | -------------------- | ----------------------- | ------ |
| WHEN a Proposition is proposed with no immediate conflict THEN it becomes a Candidate | Persisted proposition `status == "candidate"` with the proposed statement | `tests/test_proposition_lifecycle.py:103` — `assert _by_id(...)["p1"]["status"] == "candidate"`; `:104` — statement equality; `:112` — p2 also Candidate before reject | ✅ PASS |
| WHEN the user Accepts a Candidate (direct signal) OR Rejects with an explicit reason THEN Accept lands in Model / Reject carries reason | Accept interrupt then resume → `status == "accepted"`; Reject interrupt carries reason; after reject resume → `status == "rejected"` and `reason` set | `:101-102` — `kind == "accept"`, `proposition_id == "p1"`; `:108` — `p1` `accepted`; `:109-111` — `kind == "reject"`, id/reason; `:122-123` — p2 `rejected` + reason | ✅ PASS |
| WHEN a Proposition is Rejected THEN it and its reason are recorded in the Rejection Guardrail | Guardrail FS entry `{proposition_id, statement, reason}` for the rejected prop (ADR-0001 persistence) | `:128-135` — `assert guardrail == [{"proposition_id": "p2", "statement": rejected_statement, "reason": rejection_reason}]` via `REJECTION_GUARDRAIL_PATH` | ✅ PASS |
| WHEN a later Proposition resembles a Rejection Guardrail entry THEN it is Flagged | Status `flagged`; `flagged_against_id` points at rejected prop; resemblance = normalized equality (MVP documented precision) | `:56` — resembling statement differs only by case; `:125-126` — `status == "flagged"`; `flagged_against_id == "p2"` | ✅ PASS |
| WHEN lifecycle is tested THEN transitions are asserted through the stubbed-provider seam | Single orchestration test drives tools via `StubChatModel` / `create_socrates_session` (spec Testing Decisions) | `:58-89` — `StubChatModel(responses=[...])` + `create_socrates_session(model=model)`; flow asserts Candidate/Accept/Reject/Guardrail/Flagged end-to-end | ✅ PASS |

**Status**: ✅ All ACs covered (5/5 matched spec-defined outcomes; resemblance precision documented as normalized equality — not a gap)

**Out of Done-when scope (noted, not scored):** ticket comment mentions equality with Accepted → immediate conflict; no Done-when criterion requires that negative path. Not treated as a coverage gap against this ticket's ACs.

---

## Discrimination Sensor

Scratch state: detached git worktree at `/tmp/socrates-verify-02-*` on `ee383e0`; mutations only in worktree `src/socrates/proposition.py`; ran via main `.venv` + `PYTHONPATH=src`. Worktree removed after sensor; main tree verified clean (`git status` empty; `.venv/bin/pytest -q` → 2 passed).

| Mutation | File:line | Description | Killed? |
| -------- | --------- | ----------- | ------- |
| 1 | `src/socrates/proposition.py` Candidate branch (`propose` after append) | Skip Candidate write (`_save_propositions` removed) | ✅ Killed — `KeyError: '/model/propositions.json'` at `tests/test_proposition_lifecycle.py:103` via `_by_id` |
| 2 | `src/socrates/proposition.py` Guardrail triage loop | Always Candidate instead of Flagged (`if False and …`) | ✅ Killed — `assert … == "flagged"` fail at `:125` (`candidate` observed) |
| 3 | `src/socrates/proposition.py` `reject` after status update | Skip Guardrail append/save on reject | ✅ Killed — resembling propose no longer Flagged; fail at `:125` (`candidate` vs `flagged`); Guardrail list assert at `:129-135` would also fail |

**Sensor depth**: lightweight (3 targeted behavior-level mutations)
**Result**: 3/3 killed — PASS ✅

---

## Interactive UAT Results

Not performed — backend/harness infrastructure; automated orchestration checks sufficient per validate.md.

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code | ✅ |
| Surgical changes | ✅ Diff adds `proposition.py`, tools, paths, session prompt, one orchestration test |
| No scope creep | ✅ No Reconciliation / Assertion Tests / Conflict-Level router / Supersede |
| Matches patterns | ✅ Interrupt-gated tools + FS persistence + stubbed seam (ticket 01 pattern) |
| Spec-anchored outcome check | ✅ Asserted statuses/paths/reasons match ticket + CONTEXT + ADR-0001 |
| Per-layer Coverage Expectation | ✅ Domain lifecycle ACs 1:1 with Done-when via orchestration seam |
| Every test maps to a spec requirement — no unclaimed tests | ✅ Single new test maps to all five Done-when criteria; ticket 01 test unchanged |
| Documented guidelines followed | ✅ Spec Testing Decisions (single stubbed-provider seam); ADR-0001 FS paths `/model/propositions.json`, `/model/rejection_guardrail.json` |

---

## Edge Cases

Ticket 02 lists no separate edge-case section. Covered within ACs:

- [x] Case/whitespace-normalized Guardrail resemblance (MVP equality after `normalize_statement`)
- [ ] Accepted-equality immediate conflict (mentioned in ticket comment only; not a Done-when AC — deferred / not required for this verdict)

---

## Gate Check

- **Gate command**: `.venv/bin/pytest -q` (from `/home/agx/agx/Socrates`)
- **Result**: 2 passed, 0 failed, 0 skipped
- **Test count before feature** (parent `9b5ea98`): 1 (`tests/test_walking_skeleton.py`)
- **Test count after feature** (`ee383e0`): 2 (+ `tests/test_proposition_lifecycle.py`)
- **Delta**: +1 new orchestration test
- **Skipped tests**: none
- **Failures**: none
- **Ticket 01 still green**: yes (`test_walking_skeleton_opening_need_satisfaction_persists_need`)

---

## Fix Plans

None — no gaps.

---

## Requirement Traceability Update

| Requirement | Previous Status | New Status |
| ----------- | --------------- | ---------- |
| Ticket 02 DW1–DW5 | done (implementer) | ✅ Verified |
| Spec stories 9–10, 24–25 (MVP slice: Candidate / Accept·Reject / Guardrail / Flag) | Implementing | ✅ Verified (orchestration seam) |

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 5/5 ACs matched spec outcome (MVP resemblance = normalized equality, documented)
**Sensor**: 3/3 mutations killed
**Gate**: 2 passed (tickets 01 + 02)

**What works**: Candidate triage, interrupt-gated Accept/Reject, Guardrail persistence, Flagged resemblance, stubbed orchestration seam.

**Issues found**: none

**Next steps**: none for ticket 02; proceed to next harness ticket.
