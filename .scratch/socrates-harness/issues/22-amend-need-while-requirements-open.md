# 22 — Amend the Need while Requirements is open

**Specs:** `.scratch/need-refinement/spec.md`

**What to build:** The Need stops being frozen at the Opening's first raw answer. While the Requirements chapter is open — its first pass, or a reopening through Iteration — the orchestrator can propose amending the Relevance Filter. The model declares the reshaped Need and the reason; the user confirms at an interrupt presenting the current Need and the proposed one side by side with the reason, as one comparison question in the session's plain conversational terms. On confirmation the Need is rewritten with the amendment recorded beneath it — superseded shape plus reason, newest last, no separate store (reasons always survive). A declined amendment leaves the Need exactly as it was and returns to the model as a normal declined action. Attempted anywhere else the amendment is redirected with the established payload: pre-Opening names the Opening (the Need does not exist yet); any other chapter and the tail name the Iteration path — a Need-level shift outside Requirements is an L4-grade event that travels through Iteration, which reopens Requirements and re-admits the amendment. Amendments govern future filtering only: recorded Scenarios and Acceptances are the user's decisions and never cascade, and relevance already judges at record time, so anything recorded after an amendment falls under the new filter. The state × availability matrix extends by one column; admissibility stays a deterministic, pure rule over persisted facts — counting, never judgment (ADR-0002).

**Blocked by:** None — can start immediately.

**Status:** done (2026-09-10)

- [x] The amendment is admitted exactly while Requirements is open — its first pass or an Iteration reopening — and nowhere else (pure rule, tested on its own: same facts, same availability)
- [x] Pre-Opening attempts redirect naming the Opening; any other chapter and the tail redirect naming the Iteration path
- [x] After an L4 reopen of Requirements, the amendment is admissible again
- [x] The interrupt carries the current Need, the proposed Need, and the reason as one comparison question, in plain conversational terms — no machinery leaks
- [x] Confirmation rewrites the Need with the amendment recorded beneath it — superseded shape plus reason, newest last
- [x] A declined amendment leaves the Need untouched and returns to the model as a normal declined action
- [x] Scenarios recorded after an amendment are judged under the new Need; previously recorded Scenarios and Acceptances stand untouched
- [x] The redirect payload keeps the established shape — `ok:false`, current conduction state, attempted tool, admissible next steps
- [x] Full suite green; zero new test seams (orchestration seam + the pure rule, per the spec's testing decisions)

## Verification

Gate: `.venv/bin/pytest -q` — **89 passed** (80 pre-existing + 9 in
`tests/test_amend_need.py`).
TDD followed: the suite first failed against the old behavior (no gate —
`amend_need` fell through to admission everywhere; no tool; frozen Need),
then went green on the implementation.

Implementation: `src/socrates/need.py` (new — the Need file's single
home: the body is the live filter, amendments append beneath the
`## Amendment record` separator, superseded shape + reason, newest last),
`src/socrates/conduction.py` (the `amend_need` column: admitted iff
Requirements is active or next-in-precedence with nothing completed —
which is also the exact facts shape an Iteration reopen re-enters;
elsewhere the redirect names the Iteration path), `src/socrates/tools.py`
(`amend_need` on the orchestrator surface — the comparison interrupt
`current_need`/`proposed_need`/`reason` with one plain question, confirm
rewrites, decline returns a declined action), `src/socrates/inference.py`
+ `src/socrates/deliverable.py` (`_require_need`/`_read_need` now read
the live body via `read_need` — the record never leaks into the filter or
the grounding; both were previously duplicated raw reads, now one home).

### Rulings

- **"Requirements open" covers the pre-begin moment**: post-Opening,
  before any proposition exists, the state is between-chapters with
  Requirements next in precedence — amending exactly there is the
  spec's founding scenario (US1: sharpen the Need after the raw first
  answer, which in the harness's single-shot Opening lands before the
  chapter begins). The rule admits `active == requirements OR
  (active is None AND expected == requirements)`; the Iteration reopen
  (`PipelineStore.reopen`) produces the identical facts shape, so one
  rule serves both arms — pinned against the real `reopen` in the pure
  suite rather than a scripted L4 walk (the orchestration cost of the
  full L4 machinery buys no new facts).
- **The Need file is body + separator + record**: the body alone is the
  filter every consumer reads (relevance's `need` requirement, the
  deliverable's grounding); the record beneath `## Amendment record` is
  audit — reasons always survive, but never judge. This keeps
  relevance-live by construction: recording Scenarios after an amendment
  runs `_require_need` → the new body, with zero new wiring (the spec's
  "no retroactive cascade" reads the same).
- **The confirm vocabulary is the generic set**: `_is_confirmed(answer,
  "amend")` — yes/confirm/ok/true (+ `yes…` prefix). No polarity word
  exists for an amendment, so no action-specific set was added;
  English-only per the deferred bilingual ruling.

### Review (two-axis, post-commit)

Fixed from the review:

- **A blank confirmed amendment corrupted the Need** (spec axis,
  CONFIRMED): `amend_need` validated neither argument — an empty
  `proposed_need` confirmed would rewrite the file to an empty body,
  `read_need` → `None`, and Scenario recording would die on the Need
  requirement. US4 read strictly: a mis-shaped proposal never reaches
  the user. Guard added (both the shape and the reason must be
  non-blank), pinned by
  `test_blank_amendment_is_refused_and_never_interrupts`.
- **US8 unpinned** (spec axis): "recorded Scenarios and Acceptances
  stand untouched" held by construction but had no test.
  `test_amendment_never_touches_recorded_ground` pins it — Scenarios'
  descriptions and the Proposition's status byte-stable across a
  mid-chapter amendment (which also pins begun-chapter admission at the
  orchestration seam).
- **Standards axis**: `write_amendment` returned a string no caller
  read (`-> None`); the next-amendment `index` renamed `number`; the
  admissibility predicate extracted as `_requirements_open` (the ruling
  now lives in code, not comments); the tool docstring says "the
  Relevance Filter" (CONTEXT.md's avoid-word is a bare "filter").

Recorded rulings (both axes flagged; kept deliberately):

- **The pre-begin admission arm stays** (spec axis: scope creep): the
  spec's written line is "the Requirements chapter is open — its first
  pass, or a reopening through Iteration", and between-chapters
  post-Opening is strictly neither. US1 is the founding scenario ("sharpen
  the Need after the Opening's first raw answer") and the harness's
  single-shot Opening lands exactly there; the Iteration reopen re-enters
  the identical facts shape. Adjudicated here, in the ticket.
- **Test duplication suppressed** (standards axis): the Opening preamble,
  the guard comment, and the on-disk separator literal repeat across the
  suite — matching the house style of every existing orchestration suite
  (the repo overrides the baseline), and the literal
  `"\n## Amendment record\n"` in tests deliberately pins the file format
  against accidental drift.
- **Shared FS-read helper deferred** (standards axis):
  `need._read_content` re-creates the `result.error /
  file_data["content"]` unpack that `conduction._read_json` already has —
  a cross-module `fs` helper wants to be born; noted for a cleanup pass,
  not worth churning beyond this ticket's blast radius.
