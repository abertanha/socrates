# 01 — The ask–answer binding becomes data

**Specs:** `.scratch/socrates-seam/spec.md`

**What to build:** The session's asks stop being answerable by the
conductor's own momentum — not by a gate, but by light. Every pending
question's persisted marker records the moment the ask was recorded, and
every resume's answer echo records the moment the resume was applied: raw
facts in state, read by nothing during the session. The Satisfaction
warning joins them to what it already carries — deferred Conflicts,
unvisited chapters, amendments — and counts the answers that arrived
faster than a human could have read their question, worded as information
the user weighs before ending the session. The specimen's compound
self-answers (`ask && resume` in one command, stale raws, one "ok"
becoming three accepts) become visible at the one moment the user can
still act on them. The skin pins the conduct rule the compounds broke:
never answer an ask in the same command that asked it — render, end the
turn, wait. Latency enforcement is explicitly NOT built: no resume is
ever refused for arriving fast; the recorded facts cannot be slept
around, a threshold could be.

**Blocked by:** None — can start immediately.

**Status:** done (2026-09-24)

- [ ] The persisted pending-question marker carries when the ask was
      recorded; every resume's answer echo carries when the resume was
      applied — both as plain data in the state files and returned
      payloads
- [ ] No engine gate reads the timestamps to refuse or route anything —
      a resume is never refused for arriving fast (data, never
      enforcement)
- [ ] The Satisfaction warning counts and names the answers that arrived
      faster than a human can read their question, in the same
      information register as its existing entries; zero fast answers =
      the signal is absent, not zero-filled prose
- [ ] The warning's emptiness rule weighs the new signal alongside the
      existing ones
- [ ] Deterministic tests: a back-to-back ask+resume through the
      invocation surface creates the fast answer; the honest case (a
      slow pair, or the persisted format read back) is covered without a
      clock seam
- [ ] The skill text pins: an ask is never answered in the same command
      that asked it — render, end the turn, wait for the user's words
- [ ] Full suite green

## Verification

Run the project gate. Demo the slice end-to-end: seed a session, resume
an ask immediately after asking it, and read the Satisfaction warning
naming it.
