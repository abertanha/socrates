# 13 — Conduction core: derived state → availability → redirect

**Specs:** `.scratch/session-conduction/spec.md` · decisions D1–D8 in `.specs/features/session-conduction/context.md`

**What to build:** The session stops being a full-surface free choice at every step. A conduction governor derives the session's state from persisted facts (Need registered, active/completed Modeling Activities, Batches awaiting the user, count of unlapidated Propositions) and a pure availability rule decides which tools exist. Out-of-state attempts on the session surface receive an explaining redirect — `ok:false`, the current conduction state, and the admissible next steps — never a bare "no". This ticket delivers the first three enforced seams: the Need gate (before the Opening, only the Opening exists), `run_opening` exactly once, and wrong-chapter `task` attempts redirected.

**Blocked by:** None — can start immediately.

**Status:** done — 2026-09-08 (see Verification)

- [x] A scripted session before the Opening shows any non-Opening tool call returning the redirect payload naming the pre-Opening state and the Opening as the next step (Need gate)
- [x] After the Need is registered, `run_opening` is no longer admissible and redirects (once, "run once at the start")
- [x] Attempting a `task` for a non-active Modeling Activity returns the redirect naming the active chapter and its admissible next steps
- [x] The availability rule is a pure function over persisted facts, tested directly (facts in → availability out), deterministic
- [x] In-state flows behave exactly as today — the full suite stays green with no behavior change where the state admits the call
- [x] No new persisted state: availability is derived at read time (ADR-0001)

## Verification (2026-09-08)

Implemented as the conduction module (derived `ConductionState` from NEED_PATH + pipeline snapshot; pure `conduction_check`; redirect payload `{ok, conduction: {state, attempted, admissible_next}, redirect}`) plus a `ConductionMiddleware` registered on the session — it reads the Model's filesystem at dispatch time inside `wrap_tool_call` and short-circuits out-of-state calls with the payload; in-state calls reach their handler untouched. The `task` gate makes precedence proactive (the pipeline store stays as the reactive authority inside chapter tools). TDD: 8 new tests written failing first (`tests/test_conduction.py` — 6 pure-rule, 2 orchestration at the declared seam). Gate: full suite **32 passed** (24 pre-existing + 8 new), confirming in-state flows unchanged. Kill-check: pre-implementation run failed on `ModuleNotFoundError`, as expected for the red phase.

