# 02 — Proposition lifecycle: Candidate triage, Accept / Reject, Rejection Guardrail

**What to build:** The user proposes Propositions; each is triaged by an immediate-conflict check and becomes a Candidate; the user Accepts a Proposition (direct signal) into the Model or Rejects it with an explicit reason that lands in the Rejection Guardrail; a future Proposition resembling a guardrail entry is flagged.

**Blocked by:** 01 — walking skeleton.

**Status:** ready-for-agent

- [ ] A newly proposed Proposition with no immediate conflict becomes a Candidate.
- [ ] The user can Accept a Candidate (direct signal) into the Model, or Reject it with an explicit reason.
- [ ] Rejected Propositions and their reasons are recorded in the Rejection Guardrail.
- [ ] A later Proposition that resembles a Rejection Guardrail entry is flagged.
- [ ] Lifecycle transitions are asserted through the stubbed-provider seam.
