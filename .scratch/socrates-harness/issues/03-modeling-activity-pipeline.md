# 03 — Modeling Activity pipeline: Requirements → Domain Modeling → Behavioral Specification

**What to build:** The three Modeling Activities run in logical precedence, each as a specialist subagent with its own harness profile (system prompt / tool subset). Every Proposition is tagged with the activity that produced it, so Iteration can later reopen the right phase. Behavioral Specification produces conceptual rules only — no "the system shall…" functional requirements.

**Blocked by:** 02 — proposition lifecycle.

**Status:** done

- [x] The session progresses through Requirements, then Domain Modeling, then Behavioral Specification, in that precedence.
- [x] Each activity runs as a distinct subagent with its own harness profile.
- [x] Every Proposition records which Modeling Activity produced it.
- [x] Behavioral Specification produces conceptual rules only — functional requirements stay out.

## Comments

- Three `SubAgent`s (`requirements`, `domain-modeling`, `behavioral-specification`) with distinct `system_prompt` + tool subsets; `PipelineStore` enforces precedence in `/model/pipeline.json`. Propositions carry `activity`. Behavioral `propose` rejects `the system shall…`. Orchestration coverage: `tests/test_modeling_activity_pipeline.py`.
