# 29 — Invocation files and the JSON contract

**Specs:** `.scratch/socrates-hybrid/spec.md`

**What to build:** The transport that lets a skill call the engine: one thin Python invocation file per engine verb, living in the skill's clone beside the engine, run by the conductor with whatever code execution its runtime offers. Each file parses its JSON input (argument or stdin), makes exactly one engine call, and prints its JSON output — no policy, no orchestration, no state of its own. The verb surface mirrors the engine's mutations — the Opening and the Need with its amendments, proposing, accepting, rejecting, reconciliation, scenarios, assertion tests, the probe batch and its resume, iteration, deferral, the door, satisfaction — plus the read verbs: the pipeline's status, the current pass, and any pending question with its resume contract. Wrong order is refused with the reason and the admissible next verbs, as structured JSON. The tracer bullet: a full pass — Need, propositions accepted, reconciliation, scenarios, assertion tests, a probe that returns its pending question and resumes with a canonical answer, a door closed — driven end to end by calling nothing but the files' entry functions against a temporary working directory.

**Blocked by:** 28 — The AskHuman protocol in the engine (the files can only return questions as data once the engine asks that way).

**Status:** done

- [x] One invocation file per engine mutation, plus read verbs (pipeline status, current pass, pending question) — each thin: parse, one engine call, serialize
- [x] JSON in (argument or stdin), JSON out (stdout), errors as structured JSON — never stack traces
- [x] Order violations refused with reason and admissible next verbs, as JSON
- [x] A pending question is returned as data; the resume verb carries `{canonical, raw}`
- [x] Entry functions tested in-process with argv and a temporary working directory, asserting on the JSON (the approved seam)
- [x] The tracer-bullet pass runs end to end through the files alone (Need → propositions → reconcile → scenarios → tests → probe pending → probe resume → door)
- [x] Full suite green

## Verification

TDD: `tests/test_invocation_files.py` written first against the seam —
11 tests, confirmed red (collection error, no `socrates.invocations`),
then green. `INVOCATIONS` matches both the files on disk and the verb
surface (14 mutations + 3 reads); thinness pinned by source scan (no
`import json` / `import sys` / `print(` / `sys.argv` / `os.` in any
invocation file); the JSON contract pinned per shape (ask payload,
`{canonical, raw}` resume writing `<root>/model/need.md` on real disk,
stdin input, structured errors for unknown Proposition / mis-shaped
input / non-JSON argv); order refusals carry `admissible_next` exactly
(reconcile at pass 1 → `["scenarios", "assertion_tests", "door"]`;
scenarios pre-reconcile at pass 2 → `["reconcile"]`); one-pending gates
a second ask through the files; the tracer runs Need → propose → accept
→ reconcile-refused → scenarios → assertion tests (L1 conflict) → probe
pending → probe resume → reconcile (pass 2) → door → close → pipeline
completed, calling nothing but the files' entry functions against a
temporary root.

Full suite: **157 passed** (was 146; +11 new, zero legacy pins changed).

## Rulings

- **`Refusal` IS-A `ValueError`** (`src/socrates/refusal.py`): every
  engine gate converted by adding the `admissible` field, keeping the
  same messages — all legacy `pytest.raises(ValueError)` pins stay
  green. The runner catches `Refusal` before the generic
  `ValueError` arm and emits `{refused, reason, admissible_next}`.
- **One resume file, not one per kind**: the pending payload carries
  its `kind`, so `resume` dispatches on it (`verbs.resume_pending`) —
  the conductor answers the question it was shown and never picks a
  resume verb. The invocation surface resumes orchestrator-style:
  accept/reject/propose pass `touch=True` (deferred Conflicts
  re-raised, `re_raised_conflict_ids` in the payload — ticket 17's
  one-regime ruling, now stated in the verb, not the caller).
- **Apply-failure results are NOT order refusals**: the door close
  failing (`still active`) and a lifecycle apply failing return
  `{ok: false, error}` with the question kept pending — the ticket-28
  pin stands unchanged; `Refusal` is for wrong-order gates only.
- **`invoke` never mutates payloads** (no `setdefault("ok")` at the
  boundary): the persisted pending payload must equal the returned one
  (`pending_question` reads back exactly what the ask returned). Files
  that wrap bare engine results (`defer`, `reconcile`, `scenarios`,
  `assertion_tests`) state `ok: true` themselves;
  `verbs.resume_pending` normalizes the Probe's and Iteration's bare
  apply results.
- **One-pending law negotiates before validation**: `ask_accept` /
  `ask_reject` call `guard_pending` before `store.get`, so a question
  already standing is named by the refusal even when the new ask is
  itself mis-addressed (unknown id).
- **Single home for the touch postlude**: `tools.py`'s
  propose/accept/reject tools dropped their inline
  `touch_propositions` postludes and now call the `verbs` helpers with
  `touch=True` — the session and invocation surfaces share one
  implementation of the orchestrator regime.
- **`--root` default is the process cwd**; `virtual_mode=True`
  resolves the engine's virtual `/model/...` paths under the session
  directory on real disk (user story 10: a closed terminal never ends
  the session). Stdin carries the JSON when no argument is given; an
  unreadable stdin (no TTY, captured) degrades to no input rather than
  crashing a read verb.

## Review (fixed point `dbe414d..HEAD` — tickets 28+29, user-invoked)

Ten findings, all confirmed by execution against the working tree and
all fixed. Root fusion: the session adapter (`tools.py`) and the
contract its payloads advertise (`asking.py`'s `{canonical, raw}` +
token menus) were two grammars never tested against each other. Gate
after the cycle: **188 passed** (157 + 31 grammar/rollback/refresh
pins; three legacy pins adapted in place — two door `answers` lists to
canonical spelling, one compound decline `resume="no, hold on"` →
`"hold on"` exact word).

1. **Hedged compounds silently declined** — `_classify_confirmation`'s
   `startswith("no")` turned "No problem, go ahead" and "not sure" into
   declines, and "accept" answering an amendment declined it
   (cross-polarity leaked to non-lifecycle actions). Fixed: declines
   are exact words only (single-token no/n/nope + the
   `_DECLINE_WORDS` set); cross-polarity applies solely to
   accept/reject; everything else refuses (ask-never-guess).
2. **Iteration re-presented a foreign conflict's question** —
   `run_iteration` had no subject fingerprint, so `run_iteration("c999")
   with c1 pending re-presented c1. Fixed: `"subject": conflict.id` on
   the payload + `guard_pending(kind, conflict_id)` — a foreign or
   unknown id refuses naming the standing question. Sibling fixed:
   re-asking Satisfaction refreshed nothing — `ask_satisfaction` now
   recomputes the derived `deferred_warning` and re-persists it
   (`asking.refresh_pending`), so the user never confirms on a stale
   picture.
3. **The door refused its own advertised token** — `_parse_door_answer`
   could not produce "not_yet" (underscore), livelocking the session
   adapter on the exact token the menu lists, and the payload's legacy
   display list spelled "not yet" (refused by the engine). Fixed: the
   underscore token recognized; `DOOR_ANSWERS` display list now spells
   the canonical tokens.
4. **Session surface refused the contract's own envelope** — tools
   classified the whole resumed value, so `{canonical, raw}` resumed as
   advertised mapped to None and refused, while the invocation surface
   accepted it. Fixed (with 5 and 10): `_session_resume` — one block
   that crosses `parse_envelope` FIRST, classifies the canonical alone,
   and rebuilds the envelope with raw as provenance; all 12 resume
   sites (orchestrator + chapter surfaces) go through it.
5. **`run_iteration` double-wrapped** — `_envelope(answer, answer)`
   turned an advertised envelope into canonical-as-dict, refusing the
   one shape the contract names (probe_batch passed bare — the copies
   had drifted). Subsumed by `_session_resume` (identity classify for
   engine-parsed grammars).
6. **Probe rollback missed non-ValueErrors** — `_apply_resolutions`
   could raise TypeError (unhashable conflict_id) and escape without
   `_restore_state`, half-applying the Batch. Fixed: rollback on any
   `Exception`, re-raised — the transaction no longer depends on the
   error's class.
7. **Door and Satisfaction vocabularies out of step** — "enough"/"stop
   here"/"terminate" routed at the door but refused at the question
   (infinite loop on a word the system accepted); the "satisf"
   substring routed "dissatisfied" to Satisfaction. Fixed: the
   substring rule is dead; "dissatisfied" is a not_yet negation; every
   word that routes classifies "satisfied" at the question — one
   vocabulary, two speech acts.
8. **Refusals flattened on the session surface** — `_ask`/`_conduct`
   caught `Refusal` (a ValueError subclass) in the generic arm, dropping
   refused/admissible_next the invocation files emit. Fixed: explicit
   `Refusal` arm via `refusal_payload` (`refusal.py` — one writer both
   surfaces share; `invocation.py` now uses it too).
9. **Truncated-but-valid marker crashed resumes** — `{"kind":
   "iteration"}` passed read_pending's checks and the resume verbs'
   subscripts raised raw KeyError. Fixed: `_PENDING_REQUIRED_FIELDS`
   per kind in `asking.py`; a marker missing its resume's required
   fields is corruption — self-heals to none, refused as data, fresh
   asks work.
10. **The boundary was hand-copied** — `_conduct`/`_ask` byte-identical
    except-bodies, the ask→interrupt→resume block pasted 10×, four
    envelope writers. Fixed: `_session_resume` collapses the block
    (envelope stays single-writer via `_envelope`), the Refusal arms
    share one shape, and `tools.py`'s dead `store` local is gone. The
    review's refuted candidates recorded: `OPENING_QUESTION`/
    `SATISFACTION_QUESTION` imports are live re-exports consumed by
    five test files.
