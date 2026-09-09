# 20 — Only-sink: Satisfaction as the only end

**Specs:** `.scratch/session-conduction/spec.md` (D4 — doors as steering wheel + only-sink)

**What to build:** The session can no longer end behind the user's back. An outer loop-guard re-injects the session with a state redirect when the model stops without Satisfaction; termination happens exclusively through an affirmative Satisfaction answer (closing the ADR-0002 conformance gap — today the loop ends whenever the model goes quiet). The tail keeps the full pulse plus Satisfaction always available. The Satisfaction warning gains a chapters-never-visited line alongside the criticality-weighted deferred conflicts — informed early closure, never blocked. Also the D6 Chapter-k-open redirect of `await_satisfaction` (routed here from the 15/16/17 review — the matrix row lists it under Redirected, but no rule admits it only in the tail today; D4 rejected Satisfaction-from-anywhere).

**Blocked by:** 17 — Treadmill, quiet, and the three-answer door (the door interrupt's Satisfaction answer and the final surface shape).

**Status:** done (2026-09-09)

- [x] A session whose model stops calling tools is re-injected with a redirect naming the state — not terminated
- [x] Termination happens only via an affirmative Satisfaction answer through the interrupt
- [x] Door-close interrupts offer Satisfaction as the third answer (the steering wheel)
- [x] An early Satisfaction warns with the chapters never visited, alongside the weighted deferred conflicts
- [x] The warning stays non-blocking — closing with doors open remains the user's call
- [x] `await_satisfaction` on the orchestrator surface redirects outside the tail (D6: Satisfaction lives in the tail and in the door's third answer, nowhere else)

## Verification

Gate: `.venv/bin/pytest -q` — **73 passed** (67 pre-existing + 6 in `tests/test_only_sink.py`).
TDD followed: the new suite first failed against the old behavior (no gate, no
re-injection, no unvisited-chapters line; 6 red), then went green on the
implementation.

Implementation: `src/socrates/conduction.py` (the `await_satisfaction`
tail-gate in `conduction_check`; `silence_redirect(state)` — the re-injection
payload, same shape as every redirect), `src/socrates/inference.py`
(`satisfaction_warning` gains `chapters_never_visited`, derived from pipeline
facts), `src/socrates/tools.py` (`_ask_satisfaction` passes the door's own
activity as `visiting`), `src/socrates/session.py` (`OnlySinkSession` — the
outer loop-guard wrapping the compiled graph; `create_socrates_session`
returns it).

### Rulings

- **Deliverable existence is the derived terminated-by-Satisfaction fact
  (ADR-0001):** no ended-flag is persisted. The guard reads the last
  result's `files` channel — the Model's filesystem — through a small
  read-only snapshot adapter (`_SnapshotBackend`), because the guard runs
  BETWEEN graph runs, where a live `StateBackend` has no graph context.
- **`reinjection_limit` (constructor param, default `None`):** `None` is
  the invariant itself — the loop never ends by silence. An int caps
  consecutive silent re-injections per invoke (an operational cost bound
  for environments that want one). The legacy suites pin `reinjection_limit=0`:
  their orchestrator scripts end in scripted silence (stub exhaustion) and
  they test other tickets' properties; the guard's own behavior is pinned
  unbounded in `tests/test_only_sink.py`. This is the blast-radius ruling —
  the alternative (re-scripting ~38 test endings to reach Satisfaction)
  would churn suites that gain nothing from it.
- **Two legacy scripts re-scripted for the D6 gate** (they called
  `await_satisfaction` mid-walk, now out-of-state by design):
  `tests/test_walking_skeleton.py` (ticket 01's skeleton — its minimum
  legal path is now the conducted one: Opening, three vacuous doors, the
  tail's Satisfaction; the guard stays ON there, proving a legitimate
  Satisfaction end passes through it) and
  `tests/test_conduction.py::test_deferred_conflict_never_blocks_the_door_and_rides_to_the_warning`
  (the warning is now reached through the NEXT door's third answer — which
  also pinned the unvisited-chapters line alongside the deferred Conflict).
- **The vacuous door counts as visited:** `satisfaction_warning(visiting=...)`
  receives the door's own activity on the door path — the chapter whose
  door carries the question was self-evidently visited, but `pipeline.begin`
  only persists at close, so the pipeline facts alone would misreport a
  vacuous chapter as never visited. Derived at the call site, never
  persisted (ADR-0001).
- **Guard scope:** only the orchestrator's END triggers re-injection. A
  chapter specialist going silent just returns control to the orchestrator
  (the conduction state still names the open chapter; `task` re-enters it).

### Integration addendum (2026-09-09, two-axis review)

Fixed from the review:

- **Pre-Opening silence misdirected** (spec axis, CONFIRMED): the
  silence redirect's non-tail branch used the chapter-walk pointer, which
  degenerates to `await_satisfaction` exactly when the Need is not
  registered — pointing the model at the one tool the Need gate blocks.
  `silence_redirect` now has its own pre-Opening branch naming
  `run_opening` (D6 row 1: the only admissible tool). Pinned by
  `test_pre_opening_silence_is_reinjected_toward_the_opening`; the spec's
  originating scenario (silence right after the Opening) pinned by
  `test_post_opening_silence_is_reinjected_toward_the_chapter_walk`.
- `_SnapshotRead` (bool-error re-creation of the read shape) replaced by
  the protocol's real `ReadResult` (duplication + type fidelity).

Recorded rulings (both axes flagged; kept deliberately):

- **`reinjection_limit` stays** (standards: speculative generality; spec:
  scope creep — an opt-out of the headline invariant). It is the
  blast-radius compromise: the default `None` IS the invariant; the int
  form is an operational cost bound, and the legacy suites' `0` pins are
  the honest alternative to re-scripting ~38 endings that test other
  tickets. The standards axis's conftest factory idea is noted as future
  test-suite cleanup, not worth re-churning 12 files today.
- **L4-reopen overwarning kept** (spec axis): after a reopen drops
  downstream completions, the warning lists chapters the user did visit
  as never visited — the begin-facts are gone (single `active` slot), and
  distinguishing them needs persisted visit-state (ADR-0001 violation).
  The overstatement is conservative and directionally right per US 20:
  the invalidated chapters genuinely need re-walking. Watch in the first
  real-model session.
- **Guard surface is `invoke` only**: no `ainvoke`/`stream` — no caller
  exists for either; a stream-based runner would fail loudly
  (AttributeError) rather than silently bypass the guard. Add when the
  real-session runner picks its driving mode.
- **Warning `kind` stays `"deferred_conflicts"`** (standards: mysterious
  name when `conflicts == []`): the warning's provenance and graded
  entries are the deferred Conflicts; the chapters line rides along.
  Renaming would churn consumers for a cosmetic gain — revisit when the
  real-session runner renders the payload.
