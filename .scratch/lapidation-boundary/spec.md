---
Status: ready-for-agent
Feature: lapidation-boundary
---

# Spec: The boundary is honest about what it counts (lapidation-boundary)

## Problem Statement

The socrates-seam ticket 02 amendment changed what lapidation means: a
live Proposition counts as lapidated only with at least one recorded
Scenario AND a recorded assertion outcome. Sessions that ran under the
old ruling have the first and never the second — the old engine
recorded no outcomes at all (surviving outcomes were discarded by
design; breaking ones surfaced Conflicts, but no assertion record file
existed). The fifth specimen ran 36 Assertion Tests and left zero
records: that session's ground, read by the new engine, is entirely
unlapidated.

A mid-chapter session crossing the upgrade boundary therefore finds
its ground retroactively owing lapidation: the treadmill blocks the
next propose, the chapter door refuses to close. By the amended
definition this is correct — the debt is real because the record is
really absent. Two things are wrong:

- **The wording claims what the engine cannot know.** The refusals say
  the owed Propositions "have never been through a pass" — for
  pre-upgrade ground this is unobservable, and where passes ran it is
  simply false. The engine counts records; it has no knowledge of runs.
  "The record, not the run" is the amendment's principle, and the
  wording violates it in the one place the user meets it.
- **The break is behavior without a ruling on record.** The retroactive
  debt is currently an emergent consequence, not a decided thing — the
  next refactor could "fix" it (a grandfathering, a backfill) or regress
  it, and nothing in the suite would say which is intended.

The tail case is unblocked by construction and stays out of this spec:
treadmill and door-quiet apply while chapters stand open; a session
with every chapter completed crosses the boundary free to propose
(the tail's standing valve) — the break bites exactly the mid-chapter
resume.

## Solution

One ruling, two moves:

1. **The break stands, pinned.** Old-shape ground owes lapidation at
   the boundary; the gates refuse with the reason and the admissible
   next, and the repair is ordinary — the assertion records land
   conversationally, the gates proceed. A test crafts the old state
   shape and pins both halves, so the accepted break is designed
   behavior, not an accident a refactor may correct.
2. **The wording claims the record, never the run.** The three
   user-facing sites — the door's quiet debt (one definition, both
   surfaces) and the two treadmill refusals (session middleware and
   invocation surface) — stop saying "never been through a pass" and
   say **no pass on record**. True for new ground and boundary ground
   alike, no branching, no version sniffing: the engine's claim
   contracts to exactly what it counts.

## User Stories

1. As a session user resuming a mid-chapter session across an upgrade,
   I want the engine to hold my ground to the recorded pass rather than
   silently accept an unrecorded one, so that the Model's stretch stays
   auditable even across the boundary.
2. As a session user, I want the refusal to say what the engine
   actually counts — no pass on record — instead of what it cannot
   know — never ran — so that the boundary's honesty lives in its
   words, not only in its gates.
3. As an engine maintainer, I want the accepted break pinned by a test
   in the old state shape, so that the ruling survives refactors as
   behavior, never as memory.

## Implementation Decisions

- **Ruling recorded: the break is accepted.** The record never existed;
  synthesizing one would fabricate evidence — the exact rot the ticket
  02 amendment killed, rebuilt by mechanical means. No backfill, no
  grandfathered third state: the lapidation definition stays one
  (ticket 02's whole shape).
- **One wording family, three sites.** `quiet_debt_reason`'s lapidate
  leg and both treadmill strings move to "no pass on record". The
  wording scan must flatten source lines — two of the three sites carry
  the phrase wrapped across lines.
- **No state-format version marker.** Under an accepted break the
  engine's behavior is identical with or without one; a marker would
  exist only to serve a migration that does not exist.
- **Boundary test shape.** Old-ruling state: live Propositions with
  recorded Scenarios, no assertions file, chapter open. The gates
  refuse naming the owed ids; one assertion outcome set lands; the
  gates proceed. At the in-process invocation seam, through the
  definition every surface shares.

## Testing Decisions

- The boundary test asserts both halves at the invocation seam: the
  refusal (reason names the owed Propositions, admissible next names
  the lapidation path, the question stays pending where a question
  stands) and the repair (records land, the same gate proceeds).
- Wording pins: the three user-facing strings carry "no pass on
  record"; "never been through a pass" is pinned absent from `src/` —
  the claim the engine cannot make, made nowhere.

## Out of Scope

- Migration or backfill tooling, and any grandfathered lapidation
  state — rejected by ruling.
- The tail case — unblocked by construction (above); nothing to build.
- The lapidation definition itself — socrates-seam ticket 02, a decided
  amendment, untouched here.
- Skin text — the retired ordering prose means the phrase does not live
  there (verified this cycle); no conductor duty changes.

## Further Notes

- Ruling: user, 2026-09-23 — **break aceito**. "A dívida é real: o
  registro nunca existiu; retroalimentar registros seria fabricar
  evidência."
- Evidence: review cycle 4 finding #5 (confirmed behavior); the fifth
  specimen's 36 Assertion Tests with zero records (ticket 25, on
  record).
- Shortest form noted at drafting: with the ruling closed, this spec
  carries no new machinery at all — a wording contraction and a pin.
