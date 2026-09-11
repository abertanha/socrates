# 25 — Real-session validation of the fresh-context audit

**Specs:** `.scratch/deliverable-audit/spec.md`

**What to build:** The acceptance seam exercised for real. One conversational session is run with the updated skill — a real model, a real domain, the user's own moves, Opening through Satisfaction — and the session's record answers two questions. Did the audit fire as designed at materialization: a sub-agent spawned with exactly the Model record and the deliverable files in its input, and nothing of the conversation? And did it hold: every accepted Proposition traceable to a home, every asserted entity and relationship explicit in the structure — or, where the audit found otherwise, the fix landed before the session stopped, in domain terms, with no machinery reaching what the user read. Running the session is the user's move; the analysis of the transcript and the living files can be agent-assisted (the established pattern: transcript database plus the session's files). The outcome — session date, runtime, what the audit caught or passed — is recorded here.

**Blocked by:** 24 — Fresh-context deliverable audit at materialization (the instruction must exist in the skill before a session can exercise it).

**Status:** ready-for-agent

- [ ] One full session with the updated skill runs Opening → chapters → tail → Satisfaction and materializes with the audit step executed
- [ ] The transcript shows the auditor received only the Model record and the deliverable files — no conversation content reached it
- [ ] Coverage held in the shipped deliverable: every accepted Proposition traceable, asserted entities and relationships explicit (or the audit's findings were fixed before stopping)
- [ ] Nothing of the audit's machinery appeared in what the user read
- [ ] Outcome recorded here: session date, runtime, what the audit caught or passed
