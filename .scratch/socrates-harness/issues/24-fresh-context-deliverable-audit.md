# 24 — Fresh-context deliverable audit at materialization (skill + pin)

**Specs:** `.scratch/deliverable-audit/spec.md`

**What to build:** When a conversational session reaches the user's affirmative Satisfaction, the materialized deliverable gets a second, independent reading. A sub-agent with no access to the conversation receives exactly two things — the session's living Model record and the deliverable files — and checks coverage and nothing else: every accepted Proposition traceable to a home in the glossary, structure, or rules; every entity and relationship the accepted ground asserts explicit in the structure (cardinality where the ground states it), never only a textual attribute inside another concept's description. The Implementation-Independence filter's exclusions are not missing; rejected candidates and the Rejection Guardrail are the Model's negative space, not gaps; deferred Conflicts stay the Satisfaction warning's business. Findings come back as cited facts mapped to Proposition identifiers. Where ground is homeless or implicit, the conductor re-derives the affected deliverable file — the ground stands, the Model is never reopened — states the fix in the domain's own terms, and stops. A clean audit changes nothing: the session ends exactly as it ends today. Where the runtime offers no sub-agent, the conductor runs the same charter as a dedicated pass reading only the two artifacts (the weaker fallback, marked as such). The report is never written to the session's files, and the audit's machinery never leaks into what the user reads. The instruction stays runtime-agnostic and the skill stays one self-contained file. A pytest pin holds the instruction in the skill file with every binding limit, in the prompt-retirement pin tradition.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] The skill's materialization step runs the audit between writing the files and stopping: a sub-agent without conversation context receiving exactly the Model record and the deliverable files
- [ ] The charter is coverage only — presence (each accepted Proposition has a home) plus structural explicitness (asserted entities and relationships explicit, cardinality where the ground states it), modulo the Implementation-Independence filter; nothing else is flagged
- [ ] The auditor never grades, never proposes, never reopens the Model; the report is information, never a block (Satisfaction stays the session's only verdict)
- [ ] Findings lead to re-derivation of the affected deliverable file, stated to the user in domain terms with no machinery vocabulary; a clean audit ends the session silently as today
- [ ] Fallback in place: where the runtime offers no sub-agent, the same charter runs as a dedicated same-context pass over the two artifacts, marked as the weaker path
- [ ] The audit report is never persisted to the session's files
- [ ] A pytest pin holds the instruction and every binding limit above in the skill file, placed at the materialization step (prompt-retirement precedent)
- [ ] Full suite green
