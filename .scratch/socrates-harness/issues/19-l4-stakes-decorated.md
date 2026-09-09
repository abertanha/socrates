# 19 — L4 stakes decorated

**Specs:** `.scratch/central-proposition/spec.md` (L4 payload enrichment decisions)

**What to build:** The unavoidable-conflict Notification and the Iteration proposal carry the parties' centrality — dimension, dependents, weight — as stakes-at-a-glance decoration, so the user sees how much of the Model hangs on the contradiction when interrupted or when weighing a reopen. Decoration only, never gating: every L4 remains always unavoidable (non-deferrable, Notification outside Interview flow), the deliverable never ships an accepted×accepted contradiction, and the Supersede-cascade Notification stays ungated by centrality.

**Blocked by:** 16 — Centrality signal (the centrality computation and payload).

**Status:** done (2026-09-09) — delivered with ticket 16's centrality commit (the L4 stakes were payload decoration on the same centrality assessment; verified against the integrated suite)

- [x] The unavoidable-conflict Notification carries both parties' centrality (dimension, dependents, weight)
- [x] The Iteration proposal for an L4 carries the same stakes
- [x] L4 remains non-deferrable and always unavoidable — centrality buys no parking right
- [x] The Supersede cascade still always notifies, ungated

## Verification (2026-09-09)

Delivered by ticket 16's commit (scope fold ruled at integration: decoration rides the same centrality payload the signal computes — a separate slice would only re-drive the seam). Evidence in `tests/test_centrality.py`: `test_l4_stakes_decorated_but_never_gated` asserts the unavoidable Notification's `criticality.parties` stakes (dimension/dependents/weight) with `deferrable: false` / `blocks_progress: true` / `criticality.unavoidable: true`, and the Iteration interrupt's `parties` carrying the same stakes; the cascade tests assert notifications fire for BOTH a loaded cascade (`degraded_ids: ["p3"]`) and a peripheral one (`degraded_ids: []`) — ungated by centrality.
