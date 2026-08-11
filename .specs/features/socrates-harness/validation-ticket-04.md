# Ticket 04 — Probe loop Validation

**Date**: 2026-08-11
**Spec**: `.scratch/socrates-harness/spec.md` (stories 11–17), `.scratch/socrates-harness/issues/04-probe-loop.md`, `CONTEXT.md` (Scenario/Assertion Test/Batch/Probe/Elasticity/Relevance Filter)
**Diff range**: `baf6158^..baf6158` (`feat(harness): add Probe loop with Scenarios, Assertion Tests, and Batch`)
**Verifier**: independent sub-agent (author ≠ verifier)
**Verdict**: **PASS ✅**

---

## Scope of diff

| File | Change |
| ---- | ------ |
| `src/socrates/inference.py` | New `InferenceEngine`: `record_scenarios`, `run_assertion_tests`, `probe_batch` + FS adapters + `interrupt_probe` |
| `src/socrates/tools.py` | New session tools `record_scenarios` / `run_assertion_tests` / `probe_batch`; `pipeline.begin` moved to activity tool |
| `src/socrates/proposition.py` | New `revise` (Degrade-on-Accepted) + `get`; removed `PipelineStore` coupling from `propose`; `_get` now raises `ValueError` |
| `src/socrates/paths.py` | `SCENARIOS_PATH`, `BATCHES_PATH`, `CONFLICTS_PATH` |
| `src/socrates/session.py` | Prompt updated with Inference-pass step |
| `tests/test_probe_loop.py` | Orchestration test (single seam, stubbed model) |

---

## Spec-Anchored Acceptance Criteria (Done-when)

| Criterion (Done-when) | Spec-defined outcome | `file:line` + assertion | Result |
| --------------------- | -------------------- | ----------------------- | ------ |
| **AC1** — Scenarios generated from current Model, kept Need-relevant by Relevance Filter, several per Proposition | Scenarios require an existing Proposition + persisted Need; `need_relevant=true` enforced (ticket: Relevance Filter requires `need_relevant=true`); ≥2 per Proposition (ticket: "≥2 Scenarios per Proposition") | `tests/test_probe_loop.py:208` — `assert scenario["need_relevant"] is True`; `:209-210` — `assert len(by_prop["p1"]) >= MIN_SCENARIOS_PER_PROPOSITION` (and p2); `:211` — `{s["edge"] ...} >= {"zero","one","many"}`; `:214-222` — irrelevant (`need_relevant=false`) batch rejected with `"Relevance Filter"` + `"ok":false`. Enforced at `src/socrates/inference.py:98` (`need_relevant is not True`), `:80` (MIN), `:78-79` (require proposition + Need) | ✅ PASS |
| **AC2** — Assertion Tests stretch Propositions to Elasticity limit and surface Conflicts | Non-surviving Scenario (`survives=False`) with a valid `kind` surfaces a Conflict | `tests/test_probe_loop.py:201` — `assert {c["id"] for c in probe["conflicts"]} == {"c1","c2"}`; `:202` — `len(...) == 2`; `:252-254` — conflicts `{c1,c2}` persisted. Logic at `src/socrates/inference.py:142-167` | ✅ PASS |
| **AC3** — Surfaced Conflicts gathered into a Batch, presented together (not one at a time) | All open conflicts collected into one Batch, presented in a single Probe payload | `tests/test_probe_loop.py:200` — `probe["batch_id"] == "b1"`; `:201-202` — both `c1,c2` in one payload; `:247-250` — `batches == [{"id":"b1","conflict_ids":["c1","c2"],"status":"probed"}]`. Logic at `src/socrates/inference.py:171-201` | ✅ PASS |
| **AC4** — User resolves Conflicts via interrupt-gated Probe; resolution updates the Model | Probe is an interrupt (human-in-the-loop); resolutions revise (Degrade if Accepted) + add new ground; conflicts marked resolved | `tests/test_probe_loop.py:197-199` — interrupt `kind == "probe"`; `:224-243` — `Command(resume={resolutions:[revise_proposition, add_proposition]})`; `:244-245` — interrupt cleared, `state.next == ()`; `:253` — all conflicts `resolved`; `:260` — `props["p1"]["statement"] == revised_p1`; `:261` — `status == "candidate"` (Degrade); `:262` — new_ground present. Logic at `src/socrates/inference.py:188-291`, `proposition.py:112-126` | ✅ PASS |

**Status**: ✅ All 4 Done-when criteria covered with `file:line` + assertion, matching spec-defined outcomes.

---

## Discrimination Sensor

Run in an isolated `git worktree` at `baf6158` (`/tmp/socrates-sensor`, since removed). Real tree never mutated; confirmed clean afterward.

| # | File:line | Mutation | Killed? |
| - | --------- | -------- | ------- |
| 1 | `src/socrates/inference.py:98` | Relevance Filter bypass: `if need_relevant is not True:` → `if False:` (allow `need_relevant=false`) | ✅ Killed — `test_probe_loop.py:201` (extra `c2`; irrelevant scenarios landed, shifting ids) |
| 2 | `src/socrates/inference.py:172` | Batch gathers only first conflict: `[...]` → `[...][:1]` (one at a time) | ✅ Killed — `test_probe_loop.py:201` (Batch missing `c2`) |
| 3 | `src/socrates/proposition.py:123-124` | Skip Model update on revise: `if status=="accepted": status="candidate"` → `pass` (no Degrade) | ✅ Killed — `test_probe_loop.py:261` (`accepted` != `candidate`) |

**Sensor depth**: lightweight (standard feature, 3 mutations across the two highest-risk modules)
**Result**: 3/3 killed — **PASS ✅**

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code / no scope creep | ✅ Deterministic harness logic only; LLM phrasing left to provider |
| Surgical changes | ✅ New module + 3 tools; `pipeline.begin` relocation is a justified decoupling (activity tool owns pipeline begin) |
| Matches existing patterns | ✅ Dataclass + JSON FS-adapter style mirrors `proposition.py`/`pipeline.py`; interrupt indirection mirrors `tools.py` |
| Spec-anchored outcome check | ✅ Asserted values match spec (batch id, statuses, revised statement, Degrade) |
| Every test maps to a Done-when / story | ✅ Single orchestration test per Testing Decisions (one seam, stubbed model) |
| Documented guidelines followed | ✅ spec "Testing Decisions" (assert observable state + persisted artifacts through the orchestration seam) |

**Observations (non-blocking):**
- **Spec-precision (minor):** spec story 12 / `CONTEXT.md` say "several" Scenarios (vague); ticket 04 pins the threshold to **≥2**, which the impl (`MIN_SCENARIOS_PER_PROPOSITION = 2`) and test honor. Aligned to the authoritative ticket; noted only because "several" colloquially implies ≥3.
- **Coverage (minor):** the `dismiss` Probe action (`inference.py:268-269`, listed in the ticket comment) and the `add_proposition activity` requirement are implemented but not exercised by a test. `revise` + `add_proposition` (the model-update behaviors named in AC4) are covered. Not a Done-when gap.
- "Generated from current Model" is enforced via `_require_proposition`/`_require_need` guards but has no dedicated negative test; the guards are exercised indirectly. Acceptable.

---

## Gate Check

- **Gate command**: `/home/agx/agx/Socrates/.venv/bin/pytest -q`
- **Result**: **4 passed, 0 failed, 0 skipped** (1.61s)
- **Tickets 01–03 kept green**: `test_walking_skeleton`, `test_proposition_lifecycle`, `test_modeling_activity_pipeline` all pass alongside `test_probe_loop`.
- **Test count delta**: +1 (`tests/test_probe_loop.py`, 1 orchestration test). No test deleted or weakened.

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 4/4 Done-when criteria matched spec-defined outcomes (2 minor spec-precision/coverage notes, non-blocking)
**Sensor**: 3/3 mutations killed
**Gate**: 4 passed, 0 failed

**What works**: Relevance-Filter-gated Scenarios (≥2/Proposition), Assertion Tests surfacing typed Conflicts, single-Batch presentation, interrupt-gated Probe whose resolutions revise (with Degrade) and grow the Model — all persisted to the virtual filesystem and asserted through the single orchestration seam.

**Issues found**: None blocking.

**Next steps**: None. Ticket 04 verified.
