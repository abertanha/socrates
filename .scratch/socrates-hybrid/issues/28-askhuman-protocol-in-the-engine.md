# 28 — The AskHuman protocol in the engine

**Specs:** `.scratch/socrates-hybrid/spec.md`

**What to build:** The engine's asking points stop interrupting mid-method and start returning questions as data. Today every human decision — the Opening's Need confirmation, Need amendments, the Probe's Batch resolutions, Iteration's confirm, the doors' three answers, Satisfaction — rides a graph interrupt that folds asking and applying into one call. This ticket splits them: a verb that needs a decision persists a pending-question marker in the session state and returns the payload — the question, the accepted canonical answers with their meanings, and the resume contract — and the resume arrives on a later call carrying the canonical token plus the user's raw words (the token drives the machine, the raw rides as provenance). Exactly one question is pending at a time; another asking verb while one is pending is a refusal naming the pending question; a non-canonical token is a structured refusal the conductor repairs; the door's close-versus-satisfaction ambiguity is surfaced as ask-never-guess. The boundary itself is pluggable so the engine asks without knowing who answers. The method's semantics are unchanged — the same elenchus through different plumbing — and the engine's suite adapts with them, staying green. The superseded standalone session layer keeps working by wiring its interrupts to the new boundary.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Every asking point in the engine returns a pending-question payload (`question`, `accepted_answers` with `meanings`, resume contract) instead of interrupting inline
- [ ] The pending marker persists in the session state; exactly one pending question at a time (a second asking verb refuses, naming the pending one)
- [ ] Resume carries `{canonical, raw}` — canonical token drives, raw preserved as provenance
- [ ] A non-canonical or invalid token is a structured refusal, never a crash, never a silent default
- [ ] Door ambiguity between close and satisfaction surfaces as ask-never-guess
- [ ] The engine's suite stays green with the new plumbing, semantics unchanged
- [ ] The standalone session layer keeps working (its interrupts wired to the new boundary)
- [ ] Full suite green
