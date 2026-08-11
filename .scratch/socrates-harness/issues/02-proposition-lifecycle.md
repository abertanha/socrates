# 02 — Proposition lifecycle: Candidate triage, Accept / Reject, Rejection Guardrail

**What to build:** The user proposes Propositions; each is triaged by an immediate-conflict check and becomes a Candidate; the user Accepts a Proposition (direct signal) into the Model or Rejects it with an explicit reason that lands in the Rejection Guardrail; a future Proposition resembling a Rejection Guardrail entry is flagged.

**Blocked by:** 01 — walking skeleton.

**Status:** done

- [x] A newly proposed Proposition with no immediate conflict becomes a Candidate.
- [x] The user can Accept a Candidate (direct signal) into the Model, or Reject it with an explicit reason.
- [x] Rejected Propositions and their reasons are recorded in the Rejection Guardrail.
- [x] A later Proposition that resembles a Rejection Guardrail entry is flagged.
- [x] Lifecycle transitions are asserted through the stubbed-provider seam.

## Comments

- `PropositionStore` persists `/model/propositions.json` and `/model/rejection_guardrail.json`. Triage: no conflict → Candidate; normalized resemblance to Guardrail → Flagged; equality with Accepted → immediate conflict. `accept_proposition` / `reject_proposition` are interrupt-gated user signals. Orchestration coverage: `tests/test_proposition_lifecycle.py`.
