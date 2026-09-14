# 31 — Materialization from ground and the audit charge payload

**Specs:** `.scratch/socrates-hybrid/spec.md`

**What to build:** The end of the session, composed by the engine instead of authored by the model. The materialization verb derives the deliverable from the recorded ground — the Need, the accepted Propositions, the relationships and cardinalities the ground asserts — writing the canonical files verbatim from the record, every shipped line traceable to its ground entry by identifier. The audit stops depending on the conductor reading anything: an audit-charge invocation returns the fixed charge — the v2 charter semantics verbatim, self-standing, hardening included — and the skill's audit section becomes pure process around that payload: hand the charge to a fresh-context sub-agent spawned by whatever mechanism the host offers, with exactly the Model record and the deliverable; re-derive affected files through the engine; then exactly one bounded re-audit of the touched entries; the report is information, never a block, and never persisted. The pins extend: the charge payload matches its source of truth verbatim, and the deliverable's rows cite their ground identifiers.

**Blocked by:** 29 — Invocation files and the JSON contract (the materialization and the charge ride the invocation surface).

**Status:** done

- [x] The materialization verb composes the deliverable from the recorded ground (verbatim derivation — the dropped-relationship class dies by construction)
- [x] Every shipped row cites the ground entry it derives from, by identifier
- [x] The audit-charge invocation returns the fixed charge verbatim — self-standing, hardening and report format included
- [x] The skill's audit section is process over the payload: fresh-context auditor via the host's mechanism, exactly the two artifact sets, one bounded re-audit, report never persisted
- [x] Pins: the charge payload verbatim against its source; identifier citations in composed rows
- [x] Full suite green

## Verification

TDD: `tests/test_materialize_and_charge.py` written first against the
invocation seam — 8 tests, confirmed red (no `socrates.audit`, no
verbs), then green. Materialize through the files alone: opening →
Need → five propositions accepted across the three parts →
`materialize` → the three canonical files on disk under
`<root>/model/deliverable/`, each accepted statement verbatim (the
asserted relationship and its "exactly one" cardinality ride inside
it), each row suffixed `_(ground: pN)_` with the citation set exactly
the accepted-and-admitted ids (the II-excluded clause — "via push
within 120 minutes" — ships nowhere and cites nothing), the Need
shipping as the live body. Pre-Need materialize refuses with
`admissible_next == ["opening"]`. Re-derivation: idempotent over
unchanged ground; new accepted ground enters on the next composition
with earlier rows intact. Empty parts render `_(none)_`. The charge:
`audit_charge` returns `{ok, charge}` where `charge == AUDIT_CHARGE`
byte-for-byte and delivery mutates no session state.

`tests/test_skill_deliverable_audit.py` migrated in place: the
charter pins (~40 phrases) now hold against the PAYLOAD through a
module fixture invoking `audit_charge`; the skill keeps the process
(fresh-context auditor, two artifacts, payload handoff verbatim, one
bounded re-audit, never-persisted report, domain-terms-only) and a new
one-home pin — no fenced block in the audit section and nine charge
markers absent from the whole skill file. `EXPECTED_MUTATIONS` /
`EXPECTED_READS` extended (`materialize` mutation, `audit_charge`
read); the file-set and thinness pins cover the new files
automatically. The skin suite held green throughout and its
every-verb-taught pin forced the skill to teach both new verbs.

Full suite: **210 passed** (was 203; +8 materialize/charge, the audit
suite re-seated on the payload, zero charter phrases lost).

## Rulings

- **Two new verbs, one charge, one composer**: `materialize` is the
  mutation (the engine's work) and `audit_charge` is a read (static
  payload, mutates nothing — pinned). `resume_satisfaction` keeps its
  materialization; both surfaces call the same `DeliverableComposer`.
- **Citations ride on every row, not only re-derived ones**:
  `_cited_row` suffixes each shipped statement with
  `_(ground: {id})_` — the statement itself is never reworded (pinned
  verbatim-minus-citation). The Need section cites nothing: it IS the
  ground entry.
- **The relationships/cardinalities need no parser**: shipping every
  accepted, II-admitted statement verbatim means whatever the ground
  asserted — linkage, cardinality, function — ships inside it. The
  dropped-relationship class dies by construction, which is why the
  composer stays statement-granular.
- **The mission line moved INTO the charge**: "carries the accepted
  ground whole" was v2's intro sentence in the skill, outside the
  fenced block; with one home for the instrument, the charge now opens
  with its own one-charge statement — more self-standing than v2, and
  the pin survived the move verbatim.
- **The citation duty is stated in the skill, performed by the
  engine**: "citing the ground entry it comes from, by its identifier"
  stays a skill-process pin (it teaches the conductor what
  re-derivation must produce); the charge carries the finding-side
  rule ("the Proposition it bears on by its identifier"). The two
  phrases were never the same sentence — the first test draft conflated
  them.
- **The skill may not paraphrase the charge**: one-home pins (no
  fenced block, nine markers absent) close the improvisation door
  from the other side — not only must the conductor hand the payload
  verbatim, the file has no charge-shaped text left to improvise
  from.

