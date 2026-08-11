# 03 — Modeling Activity pipeline: Requirements → Domain Modeling → Behavioral Specification

**What to build:** The three Modeling Activities run in logical precedence, each as a specialist subagent with its own harness profile (system prompt / tool subset). Every Proposition is tagged with the activity that produced it, so Iteration can later reopen the right phase. Behavioral Specification produces conceptual rules only — no "the system shall…" functional requirements.

**Blocked by:** 02 — proposition lifecycle.

**Status:** ready-for-agent

- [ ] The session progresses through Requirements, then Domain Modeling, then Behavioral Specification, in that precedence.
- [ ] Each activity runs as a distinct subagent with its own harness profile.
- [ ] Every Proposition records which Modeling Activity produced it.
- [ ] Behavioral Specification produces conceptual rules only — functional requirements stay out.
