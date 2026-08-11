# 07 — Iteration (L4): reopen the most-upstream invalidated activity

**What to build:** An L4 conflict (Accepted × Accepted) is handed to Iteration, not resolved by a Probe. Iteration reopens the most-upstream Modeling Activity whose output the conflict invalidates — entity contradiction → Domain Modeling, behavior → Behavioral Specification, a conflict invalidating a Need-assumption → Requirements. The harness proposes the phase; the user confirms. The reopened activity re-runs against the current Model.

**Blocked by:** 05 — Reconciliation + Conflict Levels (sibling to 06; independent handler).

**Status:** done

- [x] An L4 conflict is routed to Iteration, not resolved by a Probe.
- [x] Iteration proposes the most-upstream Modeling Activity whose output the L4 invalidates, based on the conflicting Propositions' nature.
- [x] The user confirms which phase reopens.
- [x] The reopened activity re-runs against the current Model.

## Comments

- `run_iteration` tool + `PipelineStore.reopen`; most-upstream from party `activity` tags; confirm via interrupt (`kind: iteration`). `probe_batch` gathers only L1–L3. Orchestration coverage: `tests/test_iteration_l4.py`.
