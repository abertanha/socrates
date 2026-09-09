# 17 — Treadmill, quiet, and the three-answer door

**Specs:** `.scratch/session-conduction/spec.md` (D2 — treadmill with valve; D3 — door close; matrix in D6)

**What to build:** In-chapter conduction. The treadmill: at most one unlapidated Proposition at any moment (lapidated = has been through ≥1 pass) — proposing the next opens only after the previous is lapidated; no new pass while a Batch awaits the user; proposing itself stays always available (the maieutic valve: ground revealed during Probe resolution is born immediately as the single unlapidated). Quiet is counting: every Proposition born in the chapter has ≥1 pass and no Batch is pending on any ground; deferred Conflicts never block. `complete_modeling_activity` becomes a declaration that interrupts the user with three answers: close / not yet / Satisfaction. Also the propose tag-gate from D6's Chapter-k-open row (routed here from ticket 14's review): while a chapter is open, a `propose` on the orchestrator surface is admitted only tagged with that chapter's Activity — other tags redirect.

**Blocked by:** 13 — Conduction core; 14 — The pulse moves into the chapters.

**Status:** done (2026-09-09)

- [x] Proposing while another Proposition is unlapidated redirects (treadmill), except the valve: ground born from Probe resolution enters immediately as the single unlapidated
- [x] A pass attempt while a Batch awaits the user redirects
- [x] Declaring completion with unlapidated Propositions or a pending Batch redirects — quiet is counting
- [x] The door-close interrupt carries the three answers; "not yet" keeps the chapter open with the valve live
- [x] A deferred Conflict does not block the door — it rides to the Satisfaction warning
- [x] While a chapter is open, an orchestrator `propose` tagged with another Activity redirects (D6: "propose tag k")
- [x] Nothing in quiet is a quality judgment: bookkeeping only (ADR-0002)

## Verification

Gate: `cd .claude/worktrees/ticket-17 && /home/shenmue/socrates/.venv/bin/pytest -q` — **54 passed**.

Implementation: `src/socrates/conduction.py` (pure rules: `conduction_check`, derived `ConductionState`, `ConductionMiddleware` side-effect-free), `src/socrates/tools.py` (the door inside `complete_modeling_activity`), `src/socrates/session.py` (chapter specialists get `ConductionMiddleware(surface=CHAPTER, activity=...)`).

Rulings:

- **Lapidation is derived, not persisted (ADR-0001):** a Proposition counts as lapidated iff at least one Scenario is recorded for it (`SCENARIOS_PATH` at read time). Only live ground counts — statuses candidate/flagged/accepted; rejected/superseded ground is dead (it can never be lapidated, and counting it would deadlock the treadmill). Redirects for an unlapidated Proposition point at `["record_scenarios", "run_assertion_tests"]`; a pending Batch points at resolving it.
- **Pass attempts while a Batch awaits:** `PASS_TOOLS = {select_exploration_budget, reconcile, record_scenarios, run_assertion_tests, probe_batch}` redirect. `defer_conflict` is deliberately excluded — deferring is a resolution move (it can park a batched Conflict from the tool surface), not a pass, so a pending Batch never redirects it.
- **Door interrupt:** kind `"door"`, payload `{kind, activity, question: "Confirm closing Modeling Activity '{activity}'?", answers: ["close", "not yet", "satisfaction"]}`. It fires inside the chapter specialist (like the pass/Probe interrupts from ticket 14) and bubbles to the session's `__interrupt__`. A vacuous chapter (no Propositions born) is vacuously quiet (D3): the declaration opens and closes the door in one step — `pipeline.begin` + `pipeline.complete` on "close".
- **Answer parsing** is contextual English-only, reusing the `_is_confirmed` polarity pattern: `bool` → True=close / False=not_yet; a Satisfaction word (satisfaction, satisfied, enough, …) or any "satisf" substring → satisfaction; generic confirms plus close/closed/done/proceed/move on → close; no/n/later/wait/not now/keep open/continue/keep going → not_yet; startswith("yes") → close; unrecognized → **not_yet** — the door never closes (and never routes to Satisfaction) on a mumble.
- **Door outcomes:** close → chapter completes (`{ok, completed, door: "close"}`); not yet → `{ok, door: "not_yet", chapter_open: true}` with the valve live (the next propose enters as the single unlapidated); satisfaction → routes to the existing Satisfaction flow via `_ask_satisfaction` WITHOUT closing (`chapter_open: true` in the payload). A deferred Conflict never blocks the door — it rides to the Satisfaction warning as before.
- **Treadmill + valve:** the next `propose_proposition` while a live Proposition is unlapidated redirects; ground born from Probe resolution via `add_proposition` enters structurally (the resolution path writes the store directly, never through the gated tool dispatch) and the treadmill then counts it as the single unlapidated. In-chapter proposing is never tag-gated (the chapter's own tag is implied); the D6 tag-gate applies to the orchestrator surface while a chapter is open/expected, and in the tail any tag is admitted.
- **Test seam discovery (recorded for future tickets):** chapter specialists run as tool-invoked subagents, so their ToolMessages never merge into the session messages. The conduction tests read a specialist's own history from the checkpointer: enumerate `agent.checkpointer.list(config)` for non-empty `checkpoint_ns` values, then read each namespace's newest checkpoint `channel_values["messages"]` (helper `_subagent_messages` in `tests/test_conduction.py`).
- **Re-script list (blast radius):** `tests/test_conduction.py`, `tests/test_modeling_activity_pipeline.py`, `tests/test_deliverable_composition.py`, `tests/test_deferral.py`, `tests/test_notification_policy.py`, `tests/test_probe_loop.py`, `tests/test_reconciliation_conflict_levels.py`, `tests/test_supersede_routing.py`, `tests/test_iteration_l4.py`, `tests/test_coverage_budget.py`. `test_deliverable_composition.py` was beyond the ticket's predicted list — its chapters must now close through the door before the tail runs. Two scripting rules discovered: pass-2+ `record_scenarios`/`run_assertion_tests` require `reconcile` for the current pass (an empty `findings_json: "[]"` run is valid and satisfies the gate), and Reconciliation-contradicted ground cannot lapidate until its Conflict resolves in a Probe (the resolution also unblocks it).

Integration addendum (2026-09-09, two-axis review): the answer parser gained contextual polarity — declines (`_DOOR_NOT_YET_WORDS` or any `not `-prefix) are checked BEFORE the Satisfaction substring, so "not satisfied"/"unsatisfied" decline the action instead of routing to the Satisfaction flow; the shared `_normalize_answer` replaced the triplicated casefold/collapse idiom. Pinned by `test_door_unrecognized_and_negated_answers_keep_the_chapter_open` (a mumble and a negation both keep the chapter open; only an explicit Satisfaction word routes).
