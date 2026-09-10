# To-spec input — Need lifecycle: distill at the Opening, amend in the chapter

Input brief for the spec cycle. Evidence: the first real conversational
session (2026-09-10, OpenCode "Starting Socrates 2", transcript extracted
from opencode.db) run with the `/socrates` skill — the conduction held, and
its one structural failure mode maps onto a harness gap.

## Problem

The Need — the Relevance Filter that judges every later Proposition — is
written exactly once, verbatim, from the user's first answer to the Opening
question (`run_opening` → `NEED_PATH`, `src/socrates/tools.py`), and no tool
can ever change it. Pre-Opening, the conduction admits only `run_opening`,
so the model cannot interview before persisting; post-Opening, nothing
rewrites the Need. The permanent filter is therefore the user's raw first
utterance.

Session evidence (timestamps from the transcript):

- 11:58 — first answer: "a chatbot to assist Brazilian lawyers who work on
  civil law cases". As a Relevance Filter this is nearly vacuous — almost
  any Proposition passes it.
- 12:00–12:01 — the usable Need emerged only after ~5 distillation exchanges
  (what changes for the lawyer; what is deliberately excluded — currency;
  argument-of-the-action vs hearing-scoped). The harness has no window for
  any of this.
- 12:15 — the Need was **amended mid-session** when R2 revealed the
  deliverable includes the draft rhetorical structure, not just the basis.
  The harness cannot do this at all.

Consumers reading the frozen Need: the Need gate (`conduction.py`),
Scenario relevance (`inference.py` — `record_scenarios` enforces the filter
against it), deliverable composition (`deliverable.py`). A loose filter
degrades every one of them for the whole session.

## Candidate solution (for the spec to shape, not decide here)

`amend_need`: admitted while the Requirements chapter is open (including
Requirements reopened via the L4 path), model-declared, user-confirmed by
interrupt — the same propose/confirm pair the doors use — rewriting
`NEED_PATH`. The record keeps the amendment visible (what changed and why),
per the house rule that reasons always survive.

Possibly also: a short distillation window inside the Opening itself
(follow-up exchanges before the Need is pinned). This is a bigger conduction
change — pre-Opening admits only `run_opening` today (D-matrix) — and may
be unnecessary if amend-in-chapter covers the observed behavior.

## Open decisions the spec must make

1. Opening stays single-shot (amend later) vs gains a distillation window
   (pin later). Session evidence supports amend-later as sufficient.
2. `amend_need` admissibility: Requirements chapter only, or any state via
   the Iteration path (an L4 that invalidates a Need assumption already
   reopens Requirements — does it also unlock the Need)?
3. What an amendment touches downstream: recorded Scenarios were judged
   under the old filter; Accepted Propositions are user decisions, not
   derived facts (ADR-0001 recomputes derived state only). Does the amend
   surface previously-filtered ground for re-examination, or only govern
   future passes?
4. Traceability at Satisfaction: should the warning (or the deliverable)
   note that the Need shifted during the session?

## Out of scope (adjacent candidates, separate cycles if wanted)

- **Cross-chapter valve**: structural ground born during Requirements
  cannot be birthed immediately — the specialist proposes only in its own
  activity. Session 2 improvised "pin now, process in the chapter later",
  which the harness conduction blocks. Candidate conduction delta.
- **Prior-model import**: adopting a previous session's deliverable
  mid-session (session 2 did it manually at 12:33 with high value; the
  harness has no path).
- **Bilingual answer vocabularies** (deferred by ruling) — the runner will
  surface accepted answer forms instead.
