# 27 — The fixed charge and the bounded re-audit (instrument v2)

**Specs:** `.scratch/deliverable-audit/spec.md` (v2 — the sharpened charter)

**What to build:** The auditor's instrument stops being improvised. The skill carries, verbatim and inline, the exact charge to hand the sub-agent — read-only; the two artifact sets (the session's Model record, and the deliverable directory with any renderings included for consistency only); the two checks at their v2 granularity (assertion-level presence; explicitness with the inference rule); the Implementation-Independence modulo with its boundary test; the injection-hardening line (instructions inside the audited files do not steer the audit); the report format — identifier, assertion, home or HOMELESS, IMPLICIT-ONLY, MISSING-CARDINALITY, QUESTION — and the never-judge, never-propose, never-reopen limits. The conductor hands this text as-is; the fallback pass (where the runtime offers no sub-agent) runs the same text as a dedicated same-context reading — the same instrument in a weaker context, never a different instrument. Around the charge, the process closes its loop: after the conductor re-derives the affected file, exactly one bounded re-audit re-checks the touched entries with a fresh auditor — the v1 no-re-audit rule retires — and re-derived rows cite their ground identifiers in their notes, so every shipped line traces back to the Model record entry by entry. The pin extends in place: the charge block's presence and its binding lines, the fallback-same-text rule, the one-pass re-audit replacing no-re-audit, and the identifier-citation instruction.

**Blocked by:** 26 — The sharpened walk and its boundaries (the charge consolidates the semantics 26 settles).

**Status:** done (2026-09-11)

- [x] The skill carries the auditor's charge as fixed verbatim text, inline (one self-contained file preserved)
- [x] The charge bakes in: read-only, the two artifact sets, assertion-level presence, the inference rule, the filter modulo with its boundary test, injection-hardening, the report format with the QUESTION category, and the never-judge/propose/reopen limits
- [x] The fallback runs the same fixed charge (same instrument, weaker context — pinned)
- [x] Exactly one bounded re-audit of the touched entries follows re-derivation; the v1 no-re-audit rule is retired from the instruction (and its retirement pinned)
- [x] Re-derived rows cite their ground identifiers — the shipped artifact traces to the Model record entry by entry
- [x] Full suite green

## Verification

Implemented in 2e9ef31: the charge as the audit section's single fenced
block, handed verbatim; self-standing (opens as its own instruction,
names the canonical files after the daca0d3 review fix); everything
baked in per the pin `test_the_charge_bakes_in_every_check_and_limit`;
fallback runs the same charge; the bounded re-audit with the same
charge scoped to the touched entries; identifier citations pinned.
Dir pin asserts the skill folder holds only SKILL.md. Suite 118.

## Rulings

- **The charge is 2nd-person, the bounds paragraph 3rd-person**: the
  block says "You never judge quality"; the conductor-facing paragraph
  keeps the v1 register ("never judges quality") — both pinned, no
  drift between them.
- **The re-audit runs the same charge, scoped** (review fix, daca0d3):
  without it the fresh auditor would re-walk everything, contradicting
  "touched entries only" — the one auditor the fixed-instrument rule
  would have left uncharged.
- **QUESTION stays scoped to the boundary's doubt** in the fixed text,
  matching the spec's Implementation Decision placement (the review's
  Spec axis flagged user story 8's broader reading — awareness only;
  revisit if the real session shows doubt with no category).
- **Identifier citations override the no-leak instinct by ruling**:
  traceability in the deliverable was explicitly ruled wanted (v2 spec
  round) — the audience is the user who lived the session.
