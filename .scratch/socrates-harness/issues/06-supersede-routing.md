# 06 — Conflict routing: Supersede (L2) + cascade via Degrade; L1 in-line, L3 block

**What to build:** An L2 conflict lets the user Supersede the Accepted Proposition — the displaced one leaves the Model recorded with its reason, the new information enters Candidate. The displacement cascades automatically via Degradation: every Proposition accepted indirectly via the superseded one is Degraded back to Candidate, and the user is notified (not asked). L1 conflicts resolve in-line via Probe; L3 conflicts are blocked by the Rejection Guardrail.

**Blocked by:** 05 — Reconciliation + Conflict Levels.

**Status:** done

- [x] An L2 conflict can be resolved by Superseding the Accepted Proposition (displaced recorded with reason; new info → Candidate).
- [x] Supersede cascades: every Proposition accepted indirectly via the superseded one is Degraded back to Candidate, automatically.
- [x] The user is notified of the cascade, not asked for permission.
- [x] L1 conflicts resolve in-line via Probe; L3 conflicts are blocked by the Rejection Guardrail.

## Comments

- Probe action `supersede` (L2 only); `accepted_via` tracks indirect Acceptance; cascade Degrades dependents and appends `supersede_cascade` to `/model/notifications.json` (no permission interrupt). Probe `routing`: L1 `inline`, L2 `supersede`, L3 `blocked` (dismiss only). Orchestration coverage: `tests/test_supersede_routing.py`.
