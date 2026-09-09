# 18 — Graded Satisfaction warning

**Specs:** `.scratch/central-proposition/spec.md` (weight and ordering decisions)

**What to build:** The Satisfaction warning weighs each deferred Conflict by structural load and scope: weight = transitive dependents + (1 if Requirements activity), entries ordered by weight descending, ties resolved to the Requirements side — so the conflicts that would cascade read heavier than leaf skirmishes, and the heaviest structural risk is read first. The Deferral recommendation stays boolean; the warning stays non-blocking.

**Blocked by:** 16 — Centrality signal (the weight computation and payload).

**Status:** done (2026-09-09) — delivered with ticket 16's centrality commit (the warning weighting and ordering were one payload-lump with the signal itself; verified against the integrated suite)

- [x] Warning entries carry the weight and dependents count; ordering puts the heaviest structural risk first
- [x] Ties resolve toward Requirements
- [x] The boolean deferral recommendation is unchanged ("resolve now?" stays simple)
- [x] The warning remains non-blocking — the user may still close the Model with conflicts open (ADR-0002)

## Verification (2026-09-09)

Delivered by ticket 16's commit (scope fold ruled at integration: the warning is assembled by the same centrality assessment that computes the payload — slicing it apart would have tested the same seam twice). Evidence in `tests/test_centrality.py` (orchestration seam): weight in warning entries asserted (heavy 2 before light 0; post-cascade zero-weights fall to id order); the tie test pins weight-1 Requirements ahead of weight-1 derivation with the leaf last; `recommend_against` stays boolean throughout (True/True/False in the tie test, False for leaves); every warning test finishes via a "not yet" Satisfaction answer with no materialization — non-blocking (ADR-0002).
