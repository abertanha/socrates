# 05 — Reconciliation before the batch + Conflict Levels (L1–L4)

**What to build:** From pass 2, before Assertion Tests run, Reconciliation cross-checks the user's latest answers against the existing Model and surfaces latent conflicts (L2 new×Accepted, L3 new×Rejection-Guardrail) so Scenario generation is not spent on already-contradicted material. Every conflict is classified by level from the parties' lifecycle states. L4 is reachable only from the Assertion-Test arm (intersection Scenarios exercising two Accepted Propositions).

**Blocked by:** 04 — Probe loop.

**Status:** done

- [x] From pass 2, Reconciliation surfaces latent conflicts between the latest answers and the existing Model before Assertion Tests run.
- [x] Every conflict is classified L1–L4 by the lifecycle state of its parties.
- [x] Reconciliation yields only L2/L3 (one party is always new); L4 arises only from Assertion Tests exercising two Accepted Propositions together.
- [x] Scenario generation is skipped on material Reconciliation has already contradicted.

## Comments

- `reconcile` tool + `classify_conflict_level`. Pass 2+ requires Reconciliation before Scenarios/Assertion Tests. L2/L3 block Scenario generation for the new Proposition; L4 only via intersection Assertion Tests on two Accepted parties. Orchestration coverage: `tests/test_reconciliation_conflict_levels.py`.
