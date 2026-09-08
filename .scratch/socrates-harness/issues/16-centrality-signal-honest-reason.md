# 16 — Centrality signal + honest criticality reason

**Specs:** `.scratch/central-proposition/spec.md` · interview decisions in `.specs/features/central-proposition/context.md`

**What to build:** "Central Proposition" is defined in the domain glossary — a structuring synthesis, the Proposition other Propositions unfold from — and operationalized with a computable signal: a Proposition is central when others were Accepted via it (its transitive derivation subtree in the `accepted_via` graph — the same closure Supersede cascades degrade) or when it belongs to the Requirements activity. Centrality is derived at assessment time, never stored. The criticality reason `central_proposition` reflects the defined concept instead of "any party Accepted"; the payload exposes how a party is central (dimension, dependents count, weight). Level-based reasons (L2–L4) unchanged.

**Blocked by:** 14 — The pulse moves into the chapters (criticality payloads flow through the in-chapter passes afterwards; via-chain fixtures are scripted per the new surfaces).

**Status:** ready-for-agent

- [ ] The glossary term lands with the Conflict/Deferral cluster, stating the concept and noting the v1 proxy's deliberate coarseness (failure direction: over-caution)
- [ ] A conflict touching a Proposition with transitive dependents reads central, with the dependents count in the payload
- [ ] A Requirements Proposition reads central from its first moment, before any derivation is recorded via it
- [ ] A leaf Proposition (no dependents, not Requirements) reads non-central — its conflicts are not flagged risky
- [ ] The Need itself is never a Proposition; centrality stays a property of the Model's graph
- [ ] Centrality recomputes from the current graph: a Proposition that lost its dependents to a Supersede cascade stops reading central
- [ ] No new persisted state; via-chain fixtures follow the Supersede-cascade tests' pattern
