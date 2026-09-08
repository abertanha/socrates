# 18 — Graded Satisfaction warning

**Specs:** `.scratch/central-proposition/spec.md` (weight and ordering decisions)

**What to build:** The Satisfaction warning weighs each deferred Conflict by structural load and scope: weight = transitive dependents + (1 if Requirements activity), entries ordered by weight descending, ties resolved to the Requirements side — so the conflicts that would cascade read heavier than leaf skirmishes, and the heaviest structural risk is read first. The Deferral recommendation stays boolean; the warning stays non-blocking.

**Blocked by:** 16 — Centrality signal (the weight computation and payload).

**Status:** ready-for-agent

- [ ] Warning entries carry the weight and dependents count; ordering puts the heaviest structural risk first
- [ ] Ties resolve toward Requirements
- [ ] The boolean deferral recommendation is unchanged ("resolve now?" stays simple)
- [ ] The warning remains non-blocking — the user may still close the Model with conflicts open (ADR-0002)
