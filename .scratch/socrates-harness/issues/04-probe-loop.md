# 04 — The Probe loop: Scenarios, Assertion Tests, Batch, Probe

**What to build:** The Inference Engine generates Scenarios (Relevance-Filter-anchored, several per Proposition), runs Assertion Tests stretching each Proposition toward its Elasticity limit, collects the surfaced Conflicts into a Batch, and the user resolves them via an interrupt-gated Probe. Resolving a Conflict can reveal new ground and grow the Model for the next pass.

**Blocked by:** 03 — modeling activity pipeline.

**Status:** ready-for-agent

- [ ] Scenarios are generated from the current Model and kept Need-relevant by the Relevance Filter; several per Proposition.
- [ ] Assertion Tests stretch Propositions toward their Elasticity limit and surface Conflicts.
- [ ] Surfaced Conflicts are gathered into a Batch and presented together, not one at a time.
- [ ] The user resolves Conflicts via an interrupt-gated Probe, and resolution updates the Model.
