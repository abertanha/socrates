# 16 — Centrality signal + honest criticality reason

**Specs:** `.scratch/central-proposition/spec.md` · interview decisions in `.specs/features/central-proposition/context.md`

**What to build:** "Central Proposition" is defined in the domain glossary — a structuring synthesis, the Proposition other Propositions unfold from — and operationalized with a computable signal: a Proposition is central when others were Accepted via it (its transitive derivation subtree in the `accepted_via` graph — the same closure Supersede cascades degrade) or when it belongs to the Requirements activity. Centrality is derived at assessment time, never stored. The criticality reason `central_proposition` reflects the defined concept instead of "any party Accepted"; the payload exposes how a party is central (dimension, dependents count, weight). Level-based reasons (L2–L4) unchanged.

**Blocked by:** 14 — The pulse moves into the chapters (criticality payloads flow through the in-chapter passes afterwards; via-chain fixtures are scripted per the new surfaces).

**Status:** done (2026-09-09)

- [x] The glossary term lands with the Conflict/Deferral cluster, stating the concept and noting the v1 proxy's deliberate coarseness (failure direction: over-caution)
- [x] A conflict touching a Proposition with transitive dependents reads central, with the dependents count in the payload
- [x] A Requirements Proposition reads central from its first moment, before any derivation is recorded via it
- [x] A leaf Proposition (no dependents, not Requirements) reads non-central — its conflicts are not flagged risky
- [x] The Need itself is never a Proposition; centrality stays a property of the Model's graph
- [x] Centrality recomputes from the current graph: a Proposition that lost its dependents to a Supersede cascade stops reading central
- [x] No new persisted state; via-chain fixtures follow the Supersede-cascade tests' pattern

## Verification

Gate (repo venv): `44 passed` — the 39 pre-existing tests plus 5 new ones in `tests/test_centrality.py`, all at the existing orchestration seam (StubChatModel session, scripted tool calls, resolved interrupts; via-chains built with orchestrator-level `accept_proposition` + `via_proposition_id`, the `test_supersede_routing.py` pattern; the three-chapter walk isolated in `_three_chapter_walk()` / `_close_stubs()` for ticket 17's door-interrupt adaptation).

Rulings:

- **Signal**: `assess_centrality(proposition, dependents)` in `src/socrates/inference.py` — central ⇔ (transitive dependents > 0) ∨ (activity == requirements), computed at assessment time only. The store exposes the closure via `PropositionStore.transitive_dependents()`, which wraps the existing `_indirect_dependents` traversal that Supersede cascades already Degrade — reused, not duplicated.
- **Payload field names**: criticality gains `"parties": [{"id", "centrality": {central, dimension, dependents, weight}}]`. `dimension` ∈ `"derivation" | "requirements" | "derivation+requirements"` (both faces firing) | `null` (peripheral); `weight = dependents + (1 if requirements)`. The `run_iteration` interrupt's party dicts each gain the same nested `"centrality"`; the unavoidable-conflict Notification carries the stakes via its existing `criticality.parties`. Warning entries gain `dependents`, `weight`, `requirements` beside `criticality`.
- **Ordering proof**: a conflict's weight is the **max** over its parties' weights — a parked conflict is as heavy as its heaviest party; summing would double-count the collision as if the subtrees stacked. Sort key `(-weight, not requirements, id)`: weight descending (blast radius read first), ties to whichever conflict touches a Requirements party, conflict id as the deterministic last resort. `test_warning_ties_resolve_to_requirements_side` pins the tie (weight-1 requirements vs weight-1 derivation → requirements first, leaf last); `test_derivation_subtree_reads_central_and_leaf_reads_peripheral` pins weight 2 > 0.
- **Reasons**: `central_proposition` fires iff a party's centrality reads central (an L1 with a Requirements party now carries it — proof the reason no longer proxies "Accepted", since L1 has no Accepted party). `high_conflict_level` (L2–L4) untouched; `unavoidable` remains `critical ∧ L4`, hence still exactly L4 — decoration never gates (deferring an L4 still errors, every Supersede cascade still notifies, warning stays non-blocking, recommendation stays boolean).
- **Glossary placement**: `CONTEXT.md`, maieutic-method section, between **Conflict Level** and **Deferral** — the Conflict/Deferral cluster; Deferral's own text already said "touching central Propositions", so the term now precedes its first use. Register matched (dense paragraph + `_Avoid_` line): the concept, the v1 signal's coarseness with failure direction over-caution, the Need standing above the graph, and the square-of-oppositions grounding (non-contradiction as the Model's admission test — no periphery makes an L4 deferrable).
- **Deviation (flagged)**: one stale assertion in `tests/test_deferral.py` updated (its L2's accepted party is a leaf: `reasons == ["high_conflict_level"]`, no centrality reason). It encoded exactly the old "any party Accepted" proxy this ticket replaces; no parallel ticket touches it (17 = conduction, 18 = warning entries, 19 = L4 stakes), and the gate must stay green. Two-line diff, comment included.
- **Scope fold**: the ticket-18 warning weighting and ticket-19 L4 stakes decoration landed here per task instructions (both are blocked-by-16 payload extensions over the same computation) — 18/19's ACs are covered by `test_derivation_subtree…`, `test_warning_ties…`, and `test_l4_stakes_decorated_but_never_gated`.
