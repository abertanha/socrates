# 02 — Lapidation leaves a record

**Specs:** `.scratch/socrates-seam/spec.md`

**What to build:** The stretch stops being discardable. Assertion Test
outcomes persist — every outcome, survivals included, each citing the
scenario it exercised — so the specimen's rubber stamp (36 invocations,
all `survives: true`, zero trace, zero Conflicts ever) leaves a record
the door, the warning's successors, and any later reading can verify.
Breaking outcomes keep surfacing Conflicts exactly as today; surviving
outcomes stop being silently discarded. Lapidation's definition extends
on that record: a live Proposition counts as lapidated only with at
least one recorded Scenario AND a recorded assertion outcome set — the
ticket-17 ruling amended on specimen evidence that the record, not the
run, is what the engine can trust. One definition, every surface: the
treadmill gate, the door's quiet rule, and the propose-ordering gate all
see the extension. The minimum stays two Scenarios and is a floor,
never a ceiling. The skin pins the two conduct halves the engine cannot
hold: the Scenarios cross the user's eyes in conversation before the
Assertion Tests run, and the recorded count is never invoked against
the user's call for more stretch — asking for more is ordinary
lapidation.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] The assertion step records every outcome per Proposition —
      `survives` true and false, each citing its scenario id — persisted
      in the session state beside the Scenarios
- [ ] Breaking outcomes surface Conflicts exactly as today; surviving
      outcomes persist instead of being discarded
- [ ] Lapidation = ≥1 recorded Scenario AND a recorded assertion outcome
      set, as ONE definition shared by the treadmill gate, the door's
      quiet rule, and the propose-ordering gate
- [ ] A door refuses to close while any of its chapter's live
      Propositions lacks an assertion record, in the existing refusal
      grammar (reason + admissible next)
- [ ] Existing test seeds that lapidate by Scenarios alone are extended
      mechanically (~10 files); the suite stays green
- [ ] The Scenario minimum stays two — no quota, no edge-diversity law
- [ ] The skill pins: Scenarios are played out with the user before the
      Assertion Tests run; the recorded minimum is a floor the conductor
      never invokes against the user's judgment
- [ ] Full suite green

## Verification

Run the project gate. Demo the slice end-to-end: propose → record
Scenarios → door refuses (no assertion record) → record outcomes → door
proceeds; and an outcome set read back from state with survivals
present.
