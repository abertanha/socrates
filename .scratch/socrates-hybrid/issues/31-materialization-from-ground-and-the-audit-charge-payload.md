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


## Review (fixed point `9b4301e..a1d6ffe` — ticket 31, user-invoked)

Ten findings; nine confirmed by execution against the working tree and
fixed, one (F2) partially stale with its residual fixed. Root fusion:
ticket 30's skin retired the ordering prose on the premise that "the
engine refuses what is not admissible" — but the engine only refused on
the session surface (ConductionMiddleware wraps the deepagents tool
surface alone); the invocation seam the skill actually drives had no
gates, so the premise was false exactly where the skill lives. The fix
moves the ordering into the shared engine layer, beneath both surfaces.
Gate after the cycle: **215 passed** (210 + 5 new pins: four ordering
pins on the invocation files, one admissible-next pin on the AskRefusal
families; collateral: the materialize seed lapidates between proposes,
and the three lifecycle stubs now walk the chapters to the tail — where
the treadmill is legitimately off — mirroring test_centrality).

1. **F1 (confirmed, fixed)** — propose passed at the invocation seam
   with no Need, with the Opening question pending, and on the
   treadmill (unlapidated ground); the pass verbs ran under a presented
   Batch. Fixed engine-side, once for every surface:
   `verbs._gate_propose` (Need → `resume`/`opening`; treadmill →
   `scenarios`+`assertion_tests`, scoped `label != TAIL` because
   chapters are implicit on this surface — `pipeline.begin` only fires
   at door-close, so the middleware's `active` marker never exists
   here) and `inference._require_no_pending_batch` at the top of
   reconcile / record_scenarios / run_assertion_tests.
2. **F2 (partially stale; residual fixed)** — "no invocation verb
   implements re-derivation" was already false at `a1d6ffe`
   (`materialize` is the cure path). The residual was real: the skill's
   parentheticals promised glossary "one unambiguous term per concept"
   and structure "entities, characteristics, relationships,
   cardinality" while the composer ships flat verbatim statements —
   spec-settled, so the parentheticals now say what each part holds
   (the chapter's accepted ground, rows verbatim, cited) instead of
   promising a shape the derivation does not perform.
3. **F3 (confirmed, fixed)** — the skill said the deliverable lands at
   `.socrates/deliverable/`; it lands at `.socrates/model/deliverable/`
   (paths are `/model/deliverable/*` under the session root).
4. **F4 (confirmed, fixed)** — language circularity: the greeting was to
   be rendered "in the session's language", but the language was
   defined as "the language the user speaks in their first answer" —
   nonexistent at greeting time. Now: declared at the Opening as "the
   language the user is already speaking with you when they arrive";
   the opening bullet renders in that language.
5. **F5 (confirmed, fixed)** — neither AskRefusal family
   (`token_refusal`, `_one_pending_payload`) carried `admissible_next`,
   breaking the skin's promise that every refusal names the admissible
   next verbs. Both now say `["resume"]`; the absent-question refusal
   says `["pending_question"]`. Pinned.
6. **F6 (confirmed, fixed)** — the skill hardcoded enumerations that
   duplicate payload data: the door menu ("close, not yet, or
   Satisfaction") and the Satisfaction warning's contents (deferred
   Conflicts + unvisited chapters — stale since ticket 23 added
   amendments). Both now defer to the payload ("its payload
   advertising the answers it accepts"; "everything it names, nothing
   it does not").
7. **F7 (confirmed, fixed)** — the bootstrap gate passed once but each
   invocation file is a fresh process importing `socrates` at module
   top, and the skill never located the repo root relative to itself.
   The gate now states where the file lives
   (`<repository>/.claude/skills/socrates/SKILL.md`, root three up),
   says to install "the repository this skill ships in", and teaches
   that the import must hold at every invocation (installed package,
   or the import path set in every execution).
8. **F8 (confirmed, fixed)** — v2's Opening distillation duty ("until
   it is a Need, not a feature list") was deleted in the v3 rewrite
   while `resume_opening` accepts any non-empty text. Restated on the
   `opening` verb: distill in conversation before the resume — the
   engine persists what is resumed, so the distillation cannot happen
   after.
9. **F9 (confirmed, fixed)** — `--root` (the invocation surface's one
   flag, default the working directory) was never named in the skill.
   The verbs paragraph now names it and pins the convention: every
   invocation of the session passes that same root.
10. **F10 (confirmed, fixed)** — the probe resume carries
    `notifications` (supersede cascade, degraded ground) but no prose
    instructed relaying them. The `probe` bullet now teaches the relay
    in the domain's own terms.

**Known residual, unflagged by the review, recorded**: the D6 propose
TAG gate (a Proposition born tagged to a chapter other than the walk's
current one) is enforced by the middleware on the session surface only;
`_gate_propose` does not reproduce it. Deliberate for this cycle — the
invocation surface's chapter marker does not exist mid-walk (same
`active` absence as the treadmill scoping), and the spec's valve
question (which chapter a Probe-born Proposition belongs to) is still
open. To be settled with the ticket-25 real session's evidence.
