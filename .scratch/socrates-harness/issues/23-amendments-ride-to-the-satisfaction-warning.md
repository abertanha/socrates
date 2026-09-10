# 23 — Amendments ride to the Satisfaction warning and ground the deliverable

**Specs:** `.scratch/need-refinement/spec.md`

**What to build:** Closing the Model early stays the user's call (ADR-0002), but the honest warning gets fuller: alongside the criticality-weighted deferred Conflicts and the chapters never visited, it now lists the session's Need amendments with their reasons — an early close is informed about the Relevance Filter's history, not just its conflicts. Never a block; if the warning changes the user's mind, the session simply continues. And what ships reflects the last thing agreed: a deliverable materialized after amendments is grounded in the final Need (the composer already reads the Need live at composition — this ticket pins it). Amendments surviving inside the Need file are the source; the warning derives from them at read time (ADR-0001 — nothing new is persisted).

**Blocked by:** 22 — Amend the Need while Requirements is open (amendments must exist in the Need file before anything can derive from them).

**Status:** ready-for-agent

- [ ] The Satisfaction warning lists the session's amendments with their reasons, alongside the weighted deferred Conflicts and the chapters never visited
- [ ] The warning stays non-blocking — closing with amendments on record remains the user's call
- [ ] A deliverable materialized after amendments is grounded in the final Need
- [ ] The warning payload follows the deferral-warning prior art — same shape family, no new consumer contract
- [ ] Full suite green
