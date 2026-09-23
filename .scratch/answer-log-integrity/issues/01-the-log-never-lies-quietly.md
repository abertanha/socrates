# 01 — The log never lies quietly

**Specs:** `.scratch/answer-log-integrity/spec.md`

**What to build:** The ask–answer binding's storage stops being the one
state file whose corruption is silent. Today a `model/answers.json`
that exists but does not parse reads as empty (`read_answer_log`
swallows the failure into `[]`), the next recorded answer then
overwrites whatever the corrupt bytes held, and a failed write goes
unnoticed (`record_answered` never checks the `WriteResult` — the
backend's write is `O_TRUNC` with no temp-and-rename, so a partial
write is exactly how the file comes to be corrupt). Three moves, all
engine-side, no skin: the reader reports (the Satisfaction warning
carries the unreadable condition, present-or-absent like `self_answered`),
the writer preserves then rewrites (corrupt bytes move to a
`.corrupt` sidecar beside the log; the fresh log opens with a marker
entry the warning also reads, so the condition outlives the repair),
and a failed write rides the resume's result — never silent, never
fatal (the answer applied; the log is data, never enforcement). The
writer becomes lossless on the way: it appends to what the file holds
and never filters — the skip of unjudgeable entries stays where it
already lives, in the warning's reader.

**Blocked by:** None — can start immediately (no file overlap with
lapidation-boundary's ticket; the two run parallel cleanly).

**Status:** ready-for-agent

- [ ] A log that exists but does not parse as a JSON list is a visible
      condition: the Satisfaction warning carries
      `answer_log_unreadable` — present only when it holds, never
      zero-filled prose (same convention as `self_answered`) — and read
      verbs stay side-effect-free (the corrupt file is left exactly
      where it is)
- [ ] The writer preserves before it rewrites: the next
      `record_answered` against an unparseable log moves the corrupt
      bytes to a sidecar beside the log (`answers.json.corrupt`,
      numbered suffixes when one already stands) and the fresh log
      opens with a marker entry recording the preservation (kind + the
      moment; no answer payload — it is not a decision)
- [ ] The marker outlives the repair: a later Satisfaction warning
      still names the condition — one definition covering both states
      (presently unreadable, or repaired-by-marker), one wording
- [ ] `record_answered` checks the `WriteResult`: a failed write never
      fails the resume (the answer applied — data, never enforcement)
      and the resume's result carries the recording failure alongside
      the answer echo
- [ ] The writer is lossless: it appends to what the file actually
      holds, never filters — non-dict elements inside a parseable list
      survive the rewrite; skipping stays in the warning's reader
- [ ] Deterministic tests at the in-process invocation seam: a crafted
      corrupt file → the warning's signal; the corrupt file plus one
      resume → sidecar beside the log, fresh log headed by the marker;
      a later Satisfaction ask still names the condition; the log path
      occupied by a directory fails the backend's write deterministically
      → the resume still applies the answer and declares the recording
      failure
- [ ] The existing pins hold untouched: fast answers counted, clock
      skew skipped, malformed entries skipped, declines logged — this
      ticket adds conditions around the log, never changes what a
      well-formed log records
- [ ] Full suite green

## Verification

Run the project gate. Demo the slice end-to-end: seed a session, craft
a corrupt `answers.json`, ask Satisfaction and read the warning's
signal; resume one answer and show the sidecar beside the log with the
fresh log headed by the marker; ask Satisfaction again and read the
condition still named.
