# 04 — The Probe loop: Scenarios, Assertion Tests, Batch, Probe

**What to build:** The Inference Engine generates Scenarios (Relevance-Filter-anchored, several per Proposition), runs Assertion Tests stretching each Proposition toward its Elasticity limit, collects the surfaced Conflicts into a Batch, and the user resolves them via an interrupt-gated Probe. Resolving a Conflict can reveal new ground and grow the Model for the next pass.

**Blocked by:** 03 — modeling activity pipeline.

**Status:** done

- [x] Scenarios are generated from the current Model and kept Need-relevant by the Relevance Filter; several per Proposition.
- [x] Assertion Tests stretch Propositions toward their Elasticity limit and surface Conflicts.
- [x] Surfaced Conflicts are gathered into a Batch and presented together, not one at a time.
- [x] The user resolves Conflicts via an interrupt-gated Probe, and resolution updates the Model.

## Comments

- `InferenceEngine` + tools `record_scenarios` / `run_assertion_tests` / `probe_batch`. Relevance Filter requires `need_relevant=true`; ≥2 Scenarios per Proposition; Probe interrupt presents the full Batch; resolutions revise (Degrade if Accepted), add new ground, or dismiss. Orchestration coverage: `tests/test_probe_loop.py`.
