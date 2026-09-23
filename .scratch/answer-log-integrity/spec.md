---
Status: ready-for-agent
Feature: answer-log-integrity
---

# Spec: The answer log never lies quietly (answer-log-integrity)

## Problem Statement

Review cycle 4 (dfd3aba..c9f24eb) confirmed a three-part defect in the
ask–answer binding's storage (socrates-seam ticket 01), all pointing the
same direction: a corrupt answer log is indistinguishable from an empty
one, and the engine destroys the evidence while pretending nothing
happened.

- **Corrupt read is silent.** `read_answer_log` swallows a JSON decode
  failure into `[]`. The Satisfaction warning — whose self-answered
  signal is the user's instrument for judging the session's honesty —
  then weighs a picture that says "nothing fast here" when the truth is
  "the record could not be read". For an honesty instrument, the
  unreadable and the empty must never look alike.
- **The next write destroys the evidence.** `record_answered` reads the
  swallowed `[]`, appends one entry, and rewrites the file — whatever
  the corrupt log held is overwritten with no trace anything was lost.
  The backend's write is non-atomic (`O_TRUNC` then write, no
  temp-and-rename), so a partial write is exactly how the file comes to
  be corrupt; the engine's own append then finishes the job.
- **A failed write is a silent loss.** `record_answered` ignores the
  backend's `WriteResult`. The answer applied, the Model moved, and the
  binding event simply never landed — nothing in any payload says so.

The asymmetry frames the scope: every other state file already fails
loudly on corruption (the parsers raise, the transport returns
`{ok: false, error}`, and the conductor's taught error path faces it).
The answer log is the one file whose corruption is silent on both
sides — and the one file whose whole purpose is honesty about what
happened.

## Solution

Three moves, all engine-side, all inside the existing invocation seam.
No skin changes: the conductor's error path (socrates-seam ticket 06)
already covers what it must cover, and the repair here is engine
business, not conductor duty.

1. **The reader reports, never repairs.** Reading a log that exists but
   does not parse is a condition the caller can see — the Satisfaction
   warning says the log was unreadable, in the same register as its
   other signals (present-or-absent key, never zero-filled prose). Read
   verbs stay side-effect-free: the corrupt file is left exactly where
   it is.
2. **The writer preserves, then rewrites.** When `record_answered`
   finds a log that exists but does not parse as a list, the corrupt
   bytes are moved aside — a sidecar beside the log
   (`answers.json.corrupt`, numbered suffixes if one already stands) —
   and the fresh log opens with a marker entry recording that this
   happened. The warning reads that marker too, so the condition
   outlives the repair: a session that lost a stretch of its record
   never gets to forget it.
3. **A failed write is a declared fact.** `record_answered` checks the
   `WriteResult`; on failure the resume still succeeds (the answer
   applied — the binding is data, never enforcement), and the resume's
   result carries the recording failure alongside the echo. Never
   silent, never fatal.

## User Stories

1. As a session user, I want a corrupt answer log preserved rather than
   overwritten, so that whatever evidence it holds survives whatever
   corrupted it.
2. As a session user weighing Satisfaction, I want the warning to tell
   me when the answer log could not be read — now or at any repaired
   point in the session — so that I never judge a session's honesty on
   a record that silently lost its past.
3. As a session user, I want a failed recording of an answer surfaced
   in the resume's result, so that the binding's absence is a declared
   fact, never a silent loss.
4. As an engine, I want the log's writer to append to what the file
   actually holds and its readers to skip what they cannot judge, so
   that filtering happens where data is weighed, never where it is
   rewritten.

## Implementation Decisions

- **Unreadable ≠ empty.** `read_answer_log` keeps returning entries for
  its consumers, but the file-level condition (exists, does not parse
  as a JSON list) becomes a fact the Satisfaction warning reports —
  `answer_log_unreadable: true`, present only when it holds, same
  convention as `self_answered`.
- **Preserve-then-rewrite is the writer's move alone.** The sidecar
  lands when the next `record_answered` runs against an unparseable
  log; a session that ends without one leaves the corrupt file in
  place, which is also preservation. The warning's signal makes either
  state visible either way.
- **The marker entry outlives the repair.** The fresh log's first entry
  records the preservation (kind + the moment; no answer payload — it
  is not a decision). The warning treats the marker's presence as the
  same signal as a presently unreadable log: one definition, both
  states, one wording.
- **Write failures ride the result, not a refusal.** The ticket-01
  ruling stands — the log is data, nothing refuses or routes on it. A
  failed write is noted on the resume's payload (the answer applied,
  its binding was not recorded); the session continues.
- **The writer is lossless.** `record_answered` parses what the file
  holds and appends; it never filters. Non-dict elements already inside
  a parseable list stay in the file on rewrite — the skip happens in
  the warning's reader (socrates-seam review fix #8), which is where
  unjudgeable entries are weighed.
- **Scope is the answer log alone.** The other state files' loud
  failure is the already-designed behavior: the parsers raise, the
  transport converts, the conductor's taught error path faces it with
  the user. Nothing here touches them.

## Testing Decisions

- Engine-side, at the in-process invocation seam, asserting payloads
  and state: a crafted corrupt log under the session root, the
  Satisfaction ask returns the warning with the unreadable signal; a
  corrupt log plus one resume lands the sidecar beside the log and a
  fresh log headed by the marker; a later Satisfaction ask still names
  the condition (the marker, post-repair); the failed write is
  simulated deterministically (the log path occupied by a directory —
  the backend's `O_TRUNC` open fails) and the resume still applies the
  answer while carrying the recording failure.
- The existing pins hold untouched: fast answers counted, clock skew
  skipped, malformed entries skipped, declines logged — this spec adds
  conditions around the log, never changes what a well-formed log
  records.

## Out of Scope

- Atomic writes inside the backend — the `O_TRUNC` shape belongs to
  deepagents; the sidecar makes the engine honest about the
  consequence, not the mechanism's owner.
- Repair of any other state file, or a general corruption framework —
  they fail loudly today, by design.
- Recovering entries from the sidecar back into the log — a human or
  audit decision, never an engine one.
- Latency enforcement or any gate over the log — the ticket-01 ruling
  stands.
- Skin-text changes — no conductor duty is added or amended.

## Further Notes

- Evidence: review cycle 4 finding #3 (confirmed), plus the backend's
  own write shape read at `deepagents/backends/filesystem.py`
  (`O_WRONLY | O_CREAT | O_TRUNC`, `WriteResult` unchecked at the
  call site).
- No new user rulings were required: every decision follows standing
  ones — data-never-enforcement (ticket 01), present-or-absent signals
  (ticket 01), declared degradation (socrates-seam move 3), and the
  loud-failure design of every other state file.
