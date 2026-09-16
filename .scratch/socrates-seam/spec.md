---
Status: ready-for-agent
Feature: socrates-seam
---

# Spec: Hardening the conductor–engine seam (socrates-seam)

## Problem Statement

The first full session on the deployed hybrid (fifth specimen, on record in
ticket 25) proved the architecture: no resurrected ground, no fabricated
coverage, the deliverable engine-composed, every end routed through a
rendered question. It also proved where the rot lives now — every finding
was conductor-side, at the seam the engine cannot see:

- The conductor answered its own asks. ~22 compound commands ran an asking
  verb and its resume in one bash invocation — no render, no wait, no user.
  The `raw` provenance was sometimes real words from a different question
  (one "ok" became the raw of three accepts, 35 minutes apart from the
  answers' subjects). The engine recorded every one as a well-formed human
  decision.
- Lapidation degenerated into minimum-compliance filing. Exactly two
  Scenarios per Proposition, 33/33 — the gate minimum, mostly filed silently
  in the accept turn. The Assertion Tests ran (36 invocations, one per
  Proposition) but every outcome shipped `survives: true`, and the engine
  discards surviving outcomes by design: no record, nothing to audit, zero
  Conflicts ever surfaced from an Assertion Test.
- The deliverable audit never ran. No sub-agent, no `audit_charge`
  invocation, in a session whose skill text ends "only then stop".
- The session's root was invented. The conductor silently chose the user's
  home directory; the user was never asked where the session lives.
- The first question cost ~35k tokens and 13 tool calls — mostly the
  conductor spelunking engine source to discover an invocation recipe the
  skill is forbidden to teach by name, while 16 of 17 verb files already
  carry a `__main__` entry.
- `ask_door` accepted a fabricated activity (`"satisfaction"`) that chained
  into the real Satisfaction question — the end landed protocol-correct by
  accident.

An independent review (the writing-to-agents evaluation, dispositions on
record in ticket 25) confirmed further structural gaps: the bootstrap gate
verifies importability, not identity — any package named `socrates` passes;
an absolute path to this machine's repository rots everywhere else (the
skill has already circulated to a third-party machine); real engine errors
and absent session state have no taught path; the ask-never-guess loop has
no exit; the declared session language has no amendment path.

The seam's trust model — the conductor relays, the engine records — is now
the whole attack surface. This spec makes the seam honest: the engine
records what only it can record and surfaces the dishonesty signals it can
compute; the skin teaches the disciplines its conductor demonstrably
skipped; every degradation is declared, never silent.

## Solution

Four moves, all inside the two existing seams:

1. **The ask–answer binding becomes data.** The pending-question marker
   records when the ask persisted; the resume echoes when the answer
   arrived. The Satisfaction warning counts and names the answers that
   arrived faster than a human could have read the question — information
   the user weighs before ending the session. No latency enforcement: a
   refusal threshold would be a heuristic the conductor can sleep around;
   the recorded facts cannot be slept around. The skin pins the conduct
   rule the compound commands broke: never answer an ask in the same
   command that asked it — render, end the turn, wait.

2. **Lapidation leaves a record.** Assertion Test outcomes persist — every
   outcome, survivals included, each citing its scenario. A Proposition
   counts as lapidated only with scenarios AND an assertion record (the
   ticket-17 ruling extended on specimen evidence: the record, not the run,
   is what the engine can trust). The minimum-compliance path becomes two
   recorded steps, and the audit can verify the stretch. The Scenarios
   cross the user's eyes in conversation before the Assertion Tests run —
   pinned conduct, the half the engine cannot hold.

3. **The session is rooted, the audit is named, the gate knows who it
   imported.** The session's root is established with the user once,
   before the first verb; absent state at the expected root is a question
   (look elsewhere, or start fresh), never a silent re-greet. The
   materialization payload names the audit as the next step — the channel
   the conductor demonstrably obeys — and the fallback audit is declared
   to the user as the weaker thing it is. The engine exposes an identity
   marker; the gate asserts the imported package resolves inside this
   repository, and the document derives the repository root by resolving
   its own real location — the absolute path is gone.

4. **The skin teaches what it currently makes the conductor discover.**
   The invocation recipe without naming a runtime (verb files are
   programs), the error path for non-Refusal failures, the exit from re-ask
   loops, the language following the user, the re-read after compaction,
   the chapter orientation in domain terms. Door asks validate their
   activity against the engine's modeling activities — one gate, and the
   fabricated-door vector closes.

## User Stories

1. As a session user, I want every question the engine asks to reach me
   before any answer is recorded, so that the Model's ground reflects my
   judgments and not the conductor's momentum.
2. As a session user, I want each recorded answer to carry when it was
   given against when its question was asked, so that answers nobody had
   time to give are visible as what they are.
3. As a session user, I want the Satisfaction warning to tell me how many
   answers arrived faster than a human can read their question, so that I
   judge the session's honesty before ending it.
4. As a conductor, I want a pinned rule that I never answer an ask in the
   same command that asked it, so that render-and-wait is discipline, not
   assumption.
5. As a session user, I want every Assertion Test outcome persisted —
   survivals included, each citing its scenario — so that rubber-stamped
   lapidation leaves a record I can audit.
6. As a session user, I want a chapter door to refuse to close while any
   Proposition of the chapter lacks an assertion record, so that "quiet"
   means stretched, not filed.
7. As a session user, I want the Scenarios played out with me in
   conversation before the Assertion Tests run, so that the stretch is my
   elastic test and not paperwork.
8. As an engine, I want the treadmill gate to count assertion records
   alongside scenario records, so that the cheapest compliant path is two
   recorded steps, not one.
9. As a session user, I want to establish where the session's directory
   lives before the first verb runs, so that my Model never lands in my
   home directory by silent invention.
10. As a session user resuming a session, I want to be asked whether to
    look elsewhere for my state or start fresh when the expected root holds
    none, so that a changed working directory never silently re-greets me.
11. As a session user, I want the deliverable audit to run before the
    session stops, so that materialization is always checked by the fixed
    instrument.
12. As a session user, I want to be told when the fresh-reader audit is
    unavailable and the weaker fallback is about to run, so that
    degradation is declared, never silent.
13. As a conductor, I want the materialization payload itself to name the
    audit as the next step, so that "only then stop" rides the channel I
    demonstrably obey.
14. As a user running Socrates on a machine that has another `socrates`
   package installed, I want the bootstrap gate to refuse an import that
   does not resolve inside this repository, so that a stale or foreign
   engine cannot enforce a divergent method in Socrates' name.
15. As an engine maintainer, I want the package to expose an identity
    marker, so that the gate has something concrete to verify against.
16. As a user on any machine, I want the skill to derive the repository
    root and the glossary path by resolving its own real location, so that
    no absolute path in the document rots when the repo moves.
17. As an engine, I want door asks to refuse activity names that are not
    modeling activities, so that a fabricated door cannot chain into
    Satisfaction.
18. As a session user, I want the first question to arrive without the
    conductor spelunking the engine source, so that session start is fast
    and cheap.
19. As a conductor, I want the invocation recipe in the skill text — verb
    files are programs, run with the session root and the JSON payload —
    so that I execute verbs instead of discovering them.
20. As a session user, I want real engine errors to stop the conductor and
    reach me as plain language, so that corruption is faced and never
    improvised around.
21. As a session user stuck in a loop of refused answers, I want the
    conductor to reformulate as one open question after two failed
    renderings, so that the session never spins forever.
22. As a session user who switches language mid-session, I want the
    session's language to follow me, so that the interview stays in the
    language I am actually speaking.
23. As a conductor whose context was compacted, I want a pinned rule to
    re-run the reads before my next verb, so that resumption never runs on
    remembered state.
24. As a session user crossing a chapter boundary, I want a brief
    orientation in the domain's own terms about what this stretch of the
    conversation is for, so that I know what kind of thinking helps before
    I answer.

## Implementation Decisions

- **Ask/resume timestamps, recorded not enforced.** The persisted pending
  marker gains the moment the ask was recorded; every resume's answer echo
  gains the moment the resume was applied. Both are facts in state — no
  gate reads them during the session. Latency refusal was considered and
  rejected: a threshold is a heuristic (false positives on legitimately
  fast answers; sleepable around), and it would drag a clock dependency
  into a deterministic engine. The option stays on record for a future
  cycle with evidence from the recorded data.
- **The Satisfaction warning gains a self-answered count.** The warning
  builder computes, from the recorded timestamps, how many answers arrived
  within a small window of their ask (the compound-command signature) and
  words it as information in the payload — the same register as deferred
  Conflicts and amendment counts. Zero fast answers = the signal is
  absent, not zero-filled prose.
- **Assertion outcomes persist.** The assertion step records, per
  Proposition, every outcome with its scenario reference and survival
  verdict — `survives: true` included. Surviving outcomes stop being
  discarded; breaking outcomes keep surfacing Conflicts exactly as today.
  The record lives in the session state beside the Scenarios; its exact
  layout is a ticket-level decision. The deliverable audit's charge is
  unchanged (it audits the deliverable, not the process) — the record is
  for the door, the warning, and any later reading.
- **Lapidation extends (ticket-17 ruling amended on specimen evidence).**
  A live Proposition counts as lapidated only when it has at least one
  recorded Scenario AND a recorded assertion outcome set. The treadmill
  gate, the door's quiet rule, and the propose-ordering gate all see the
  same extension — one definition, every surface.
- **Door activity validation.** The door ask refuses activity names that
  are not the engine's modeling activities, with the admissible next
  verbs in the refusal — the same refusal grammar as every other gate.
- **Materialization names the audit.** The Satisfaction/materialization
  payload carries the audit as its named next step (admissible-next
  guidance, payload not prose). The audit instrument itself is unchanged:
  the charge stays byte-for-byte in the `audit_charge` verb; the fallback
  stays runtime-unnamed per the standing pin.
- **Audit degradation is declared.** The skill's audit process gains the
  honesty clause: when no fresh-reader mechanism exists and the fallback
  is about to run, the user is told the check is weaker before it runs.
  Naming a runtime-specific mechanism remains forbidden (the
  runtime-agnostic pin stands; the review's suggestion to name one is
  dispositioned rejected on record).
- **Engine identity marker.** The package exposes its version/identity.
  The bootstrap gate, after import, asserts the imported package resolves
  inside the repository the gate derived; a foreign or stale import is a
  failed gate with distinct wording (wrong engine, not missing engine).
- **The skill derives, never hardcodes.** The repository root comes from
  resolving the skill file's real location (through symlinks), the same
  root the gate imports from; the glossary path derives from that root.
  The absolute path to this machine's tree is removed (no test pins it).
- **Session root established at the Opening.** Before the first verb, the
  conductor establishes with the user where the session's directory lives
  (the working directory's `.socrates/` is the offered default, not a
  silent choice); every invocation passes that root — extending the
  standing same-root rule with its missing first half.
- **Missing state is a question.** When the expected root holds no session
  state, the conductor asks — resume elsewhere, or start fresh — instead
  of re-greeting. The never-re-greet rule gains the branch it lacked.
- **Invocation recipe in the skin, runtime-unnamed.** The skill teaches
  that each verb file is a program: execute it with the session root and
  the JSON payload as arguments. The transport decision (python3 +
  invocation files) is unchanged; what was discovery becomes instruction.
- **Non-Refusal error path.** A verb failure that is not a structured
  refusal stops the conductor: re-run the reads, tell the user in plain
  language, never improvise state surgery. Unreadable state is said to be
  unreadable.
- **Re-ask exit.** After two failed re-presentations of a question (refused
  classifications, ambiguous answers), the conductor reformulates as one
  open question in plain words — the ask-never-guess loop gains an exit
  that is still not a guess and still not a menu.
- **Language follows the user.** The language-boundary clause gains its
  amendment path: the session's language is the language the user is
  speaking; if they switch, the rendering switches with them from that
  point. No engine state is involved (language was never engine state).
- **Post-compaction re-read.** The skin pins: if the conductor's context
  was summarized, the reads re-run before the next verb — the third
  specimen's stale-charge precedent, made a standing rule.
- **Chapter orientation duty.** At each chapter boundary the conductor
  orients, briefly, in the domain's own terms: what this stretch is for
  and what kind of thinking helps. No machinery vocabulary, no method
  names — the user-facing half of "etapas não são claras".
- **Scenario minimums and edge quotas are untouched.** The specimen's
  edges were varied across the session; the rot was silent filing and
  rubber-stamped assertions, not edge shape. Diversity enforcement would
  add law without evidence.

## Testing Decisions

- A good test asserts external behavior at the surface the consumer uses,
  never internal helpers: engine behavior through the in-process
  invocation entry (verb + argv + JSON, assert the returned payload and
  the state it promised), conductor behavior through flattened-phrase
  pins and mechanism scans over the skill text. No new seams (user-ruled
  this cycle).
- Engine-side: timestamps are tested by invoking an ask and its resume
  back-to-back — in-process, that deterministically creates the fast
  answer the warning must count; a seeded slower pair (or the persistence
  format) covers the honest case. The extended treadmill is tested the
  way the current one is: propose → scenarios → door refuses → assertion
  record → door proceeds. Door validation gets its refusal-shape test
  (`"satisfaction"` as the activity, admissible next present). The
  materialization payload's audit hint is asserted on the payload, not
  the prose. The identity marker is asserted importable and stable.
- Skin-side: prior art is the v3 skin pin file and the deliverable-audit
  pin file — flattened-sentence pins for every new duty (compound-answer
  prohibition, session-root establishment, missing-state question, audit
  honesty, invocation recipe, error path, re-ask exit, language
  amendment, post-compaction re-read, chapter orientation), mechanism
  scans confirming no runtime got named and the absolute path is gone,
  and the gate's identity clause pinned against its section.
- Prior art for both surfaces: the invocation tests (ticket 29), the
  materialize/charge tests (ticket 31), the v3 skin tests (ticket 30),
  the audit charter tests (tickets 24–27).

## Out of Scope

- Latency enforcement (a minimum-time gate on resumes) — recorded as a
  future option; the data this spec records is its evidence base.
- Vocabulary leaks and the sampling-degeneration loop (DSML-style control
  tokens, the door question repeated twelve times) — model-side failure
  under protocol pressure; no mechanical fix identified. On record in
  ticket 25.
- Naming a runtime-specific sub-agent mechanism — the runtime-agnostic
  pin stands; the review's suggestion is dispositioned rejected.
- The go-back-a-step path (user-initiated replacement of accepted ground
  with no Conflict in the air) — watch-item since the fourth specimen,
  no new evidence.
- The one-question-per-turn ruling — flagged for ruling since the fourth
  specimen; unchanged.
- Scenario edge diversity or per-proposition quotas — rejected for lack
  of evidence (above).
- Tying `materialize` to Satisfaction — the verb stays callable for audit
  re-derivation by design; the door activity validation closes the
  observed end-run vector.
- Health-check or forensics-style machinery — the read verbs are the
  health check; the error path taught above is the recovery.
- Context budgets and compaction triggers — the host runtime owns
  compaction; the skill only re-anchors after it.
- The unglossed-term gate (phantom-attribute class from the fourth
  specimen) — the lapidation-duty sentence in this spec's conduct rules
  gestures at it; a mechanical gate awaits its own evidence.

## Further Notes

- Evidence base: the fifth-specimen record (first full session on the
  deployed hybrid — compound self-answers, stale raws, minimum-compliance
  lapidation, skipped audit, invented root, startup cost, door
  fabrication), the fourth-specimen record (pre-patch rot the hybrid
  demonstrably killed, plus the still-open carryovers), and the
  writing-to-agents evaluation with per-point dispositions (P0 identity,
  P1 audit degradation, P2 rooting, P3 error path, P4 re-ask loop, P5
  absolute path, P6 language, P7 context — accepted as scoped above; P8
  menu tension and runtime-naming rejected). All three live in ticket
  25's comment thread.
- User rulings this cycle: the two existing seams (invocation surface +
  skill-text pins), no new ones; record-and-expose over latency
  enforcement for the ask–answer binding; the treadmill extends to
  assertion records.
- The D6 residual (propose tag gate on the invocation surface mid-walk)
  is unchanged by this spec and stays a ticket-25 watch-item.
- Acceptance remains ticket 25's: the next real hybrid session, judged
  against the watch-list this spec's deltas compile into.
