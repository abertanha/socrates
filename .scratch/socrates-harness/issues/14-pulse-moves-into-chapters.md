# 14 — The pulse moves into the chapters

**Specs:** `.scratch/session-conduction/spec.md` (D1 — chapters with internal pulse; D5 — mechanism)

**What to build:** The pass/Probe pulse — budget selection, Reconciliation (from pass 2), Scenarios, Assertion Tests, Probe — migrates from the orchestrator's surface into the chapter specialists' toolsets, making each Modeling Activity one regime: propose, lapidate, resolve under one roof. The orchestrator keeps the Opening, the doors, and the tail. The Coverage-selected exploration budget must keep riding the passes wherever they run, with explicit subagent propagation (never the silent fallback — issue #1698).

**Blocked by:** 13 — Conduction core (the derived-state reader and redirect contract exist to migrate onto).

**Status:** done — 2026-09-08 (see Verification)

- [x] A chapter specialist runs a full pass inside its chapter (propose → budget → Scenarios → Assertion Tests → Probe) in a scripted session
- [x] Subagent invokes still carry the Coverage-selected recursion limit explicitly; propagation assertions carry over
- [x] The orchestrator surface admits the pulse tools only in the tail (composed in, conduction-gated — D6's tail row); out-of-state attempts redirect into the chapters
- [x] Existing orchestration tests re-scripted to the in-chapter flow (per-activity stubbed models are the prior art), all green
- [x] Reconciliation-from-pass-2 and Probe interrupt payloads unchanged in shape

## Verification (2026-09-08)

The pulse is now a shared toolset composed into both surfaces: unconditionally into each chapter specialist (`build_pulse_tools` — reconcile, record_scenarios, run_assertion_tests, probe_batch, defer_conflict, select_exploration_budget), and into the orchestrator, where the conduction governor admits it **only in the tail** — out-of-state attempts redirect into the open/next chapter with the standard payload (state + admissible next steps). `run_iteration` stays orchestrator-level in any state (a door move, D6 row 4). The chapter Acceptance and Probe interrupts surface to the user from inside the subagent with unchanged payload shapes (verified: the deepagents task path propagates the parent checkpointer/thread into the nested graph, so `interrupt()` inside a specialist pauses the whole session and `Command(resume=...)` returns to it).

Re-scripting split (AC 4, interpreted per D6's tail row): `test_coverage_budget` runs its whole saga inside the Domain Modeling specialist (the flagship in-chapter shape; the budget selected inside the chapter propagates to the following Behavioral spawn); the six files whose sagas are post-chapter behavior (`deferral` ×2, `notification_policy`, `probe_loop`, `reconciliation_conflict_levels`, `supersede_routing` ×2, `iteration_l4` test 2) walk the three chapters first via close-only specialist stubs so their pulse runs in the tail — no Proposition IDs shifted; `iteration_l4` test 1 was already the target shape and is untouched.

Two implementation rulings discovered en route, both recorded in the conduction module:
1. A chapter's door opens on its specialist's first act — `propose` (as before) or `complete_modeling_activity`, which now declares completion and opens-and-closes the door in one step (a chapter with no Propositions is vacuously quiet, D3). A middleware-side begin-on-entry was tried and rejected: its write lands in the parent's state channel, but the subagent is seeded from the pre-write snapshot, so the specialist never saw the open door.
2. Mid-chapter, the parent's filesystem view lags the subgraph's (files merge on task completion) — tests assert chapter-written state after the task returns; at interrupt time only the interrupt payload itself is asserted.

TDD: 7 new tests written failing first (`tests/test_conduction.py` — 4 pure-rule, 3 orchestration, including the bubbling experiment). Gate: full suite **39 passed** (24 pre-existing re-scripted where needed + 15 conduction), confirming in-state flows and payload shapes unchanged.
