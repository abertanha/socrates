# 23 — Amendments ride to the Satisfaction warning and ground the deliverable

**Specs:** `.scratch/need-refinement/spec.md`

**What to build:** Closing the Model early stays the user's call (ADR-0002), but the honest warning gets fuller: alongside the criticality-weighted deferred Conflicts and the chapters never visited, it now lists the session's Need amendments with their reasons — an early close is informed about the Relevance Filter's history, not just its conflicts. Never a block; if the warning changes the user's mind, the session simply continues. And what ships reflects the last thing agreed: a deliverable materialized after amendments is grounded in the final Need (the composer already reads the Need live at composition — this ticket pins it). Amendments surviving inside the Need file are the source; the warning derives from them at read time (ADR-0001 — nothing new is persisted).

**Blocked by:** 22 — Amend the Need while Requirements is open (amendments must exist in the Need file before anything can derive from them).

**Status:** done (2026-09-10)

- [x] The Satisfaction warning lists the session's amendments with their reasons, alongside the weighted deferred Conflicts and the chapters never visited
- [x] The warning stays non-blocking — closing with amendments on record remains the user's call
- [x] A deliverable materialized after amendments is grounded in the final Need
- [x] The warning payload follows the deferral-warning prior art — same shape family, no new consumer contract
- [x] Full suite green

## Verification

Gate: `.venv/bin/pytest -q` — **95 passed** (91 pre-existing + 4 in
`tests/test_amend_warning.py`).
TDD followed: the amendments-ride and emptiness-flip tests first failed
against the old warning (no `amendments` key; amendments did not count in
the emptiness rule), then went green on the implementation. The two
deliverable-grounding tests were green on arrival — they pin the
behavior ticket 22 already guaranteed by routing the composer through
`read_need`.

Implementation: `src/socrates/need.py` (`read_amendments` — the record
parser deferred from ticket 22: `### Amendment N — reason` headings split
the record; each entry keeps `number`, `reason`, `superseded`, file
order, oldest first), `src/socrates/inference.py`
(`satisfaction_warning` reads the amendments at read time; the emptiness
rule counts them — with amendments on record there is something to say
even with nothing deferred; the payload gains `amendments` beside
`conflicts` and `chapters_never_visited`).

### Rulings

- **`amendments` rides the existing payload** (ticket 20 precedent): the
  warning's `kind` stays `"deferred_conflicts"` and no new payload type
  is introduced — `chapters_never_visited` rode the same way. Consumers
  that read the warning keep one shape family; the real-session runner
  renders it all at once.
- **Amendments count in the emptiness rule**: US10's point is that an
  early close is informed about the filter's history even when no
  Conflict was parked — so amendments alone make the warning worth
  showing (pinned with the pipeline completed, isolating the flip).
- **File order, oldest first**: the warning reports the history as the
  record reads — newest last, matching the file's own rule.
- **Deliverable grounding needed no new wiring**: the composer already
  read the live body through `read_need` (ticket 22); the tests pin it
  at both seams (orchestration + direct composer) so a future regression
  cannot ship the superseded shapes or leak the record into the
  deliverable.
