# Central Proposition Context

**Gathered:** 2026-09-04
**Spec:** `.specs/features/central-proposition/spec.md` (to be written — spec delta on `socrates-harness`)
**Status:** Ready for spec

---

## Feature Boundary

Define **Central Proposition** operationally and rebuild Deferral criticality on it. Today "central" is the proxy "any party is Accepted" (`assess_deferral_criticality` in `src/socrates/inference.py`), which makes criticality ≈ binary (everything ≥ L2 is critical). This delta: a glossary term for the concept, a computable signal, graded weighting in the Satisfaction warning, and enriched L4 payloads. No changes to: deferrability boundaries (L1–L3 deferrable, L4 unavoidable), Supersede-cascade notification gating, or Iteration routing.

---

## Implementation Decisions

### Concept (the definition)

- **Central Proposition = a structuring synthesis**: a Proposition from which other Propositions unfold — by derivation from the Need, and consequently into the structure and behaviors of the Model. Displacing or conflicting with it propagates beyond itself.
- One derivational concept, **not** two orthogonal dimensions: requirements-anchoring and structural load are the two faces of measurement, not two separate centralities.
- Periphery = a leaf: nothing derived via it, and it does not shape the Relevance Filter.
- The Need itself is **not** a Proposition (no lifecycle, no Scenarios) — it stands above the graph as the filter. Requirements-activity Propositions are how the Need's derivation lives in the graph.

### Signal v1 (operationalization — deliberately coarse, revisable)

- Central ⇔ **(out-degree > 0 in the `accepted_via` graph) OR (activity = requirements)**.
- Rejected: pure graph alone — the top Need-synthesis Proposition is Accepted directly (never *via* anything), so the most structuring Proposition of all would read peripheral until derivations land; that failure is silent. The shortcut's failure mode is conservative (over-warning), which is the safe direction for an operational blocking-ness heuristic (ADR-0002).
- Rejected for v1: `need_derived` flag (precise, but new state + new tool contract + localized discipline). Promotion path if v1 proves too coarse: recorded in Deferred Ideas.

### Consumers

- Centrality feeds **only**: (a) Deferral criticality (`recommend_against` and reasons), (b) the Satisfaction warning's weighting. The Deferral recommendation itself stays boolean (critical / not).
- **Supersede-cascade Notification stays ungated** — every cascade notifies, regardless of centrality. Rationale: removing Accepted state is always visible; whoever supersedes is present in the Probe, so the Notification is a record of a destructive act, not an interruption.
- L4 payloads (unavoidable-conflict Notification, Iteration proposal) carry centrality info (dimension + dependents + weight) as stakes-at-a-glance — decoration, never gating.

### Dynamics

- Centrality is **always derived from the current graph at assessment time, never stored**. A Proposition becomes central when its first dependent lands via it; a cascade that guts its dependents makes it peripheral again.

### Graduation (Satisfaction warning ordering)

- Graded from the start (user's choice over staged boolean).
- **Weight = dependents + (1 if requirements); ties resolve to scope (requirements first).** The count dominates — blast radius is the honest signal — and the +1 dilutes the known coarseness of the v1 proxy (every requirements Proposition counts as central). No cross-dimension arithmetic beyond this single bonus.

### L4 × periphery

- **L4 remains always unavoidable — no centrality carve-out.** Foundation: the Conflict kinds are named for the relations of the **square of oppositions** (contradiction, contrariety, …); the Model's admission test is non-contradiction. A deferred L4 parks a contradiction *inside* the Accepted set, and at Satisfaction the DeliverableComposer would ship both contradictory Accepted Propositions in the deliverable — no other deferral can do this (L2/L3 park the new/candidate side; L1 parks unconsolidated breaks). The Model never ships internally contradictory.

### Criticality structure (downstream of the above)

- The criticality reason `central_proposition` now means the defined concept (v1 signal), replacing "party is Accepted". Level-based criticality (`high_conflict_level` for L2–L4) is unchanged; `unavoidable` remains `critical ∧ L4` — hence still exactly L4.

---

## Agent's Discretion

None — all forks were decided by the user during the interview.

---

## Specific References

- **Square of oppositions** as the conceptual foundation of Conflict kinds and of the never-ship-contradictory rule (user, this session — not yet recorded in CONTEXT.md; this delta should reflect it in the Central Proposition term).
- The phone-capture example: the user says "precisamos pegar o celular do cliente"; the Need exists so the harness can judge whether that datum belongs in the Model at all — the Need as validator (Relevance Filter in action).
- User's phrasing of the concept: "uma síntese estruturante dos demais requisitos, entendimentos sobre a necessidade que a aplicação visa suprir e, por consequência, comportamentos que os relacionamentos das entidades do modelo terão."

---

## Deferred Ideas

- **`need_derived` flag** (interview option 3): promote if the first real session shows the requirements shortcut crying wolf too often.
- **Richer requirements Opening flow** — Need → max/min scope → target audience → interface → critical end-user properties — is deeper than the current `requirements` specialist prompt elicits. Belongs to the first-real-model-session work, not this delta.
- **Scale refinement** of the graduation formula (weight/tie-break) with evidence from real warnings.
- Square-of-oppositions as an explicit foundational note in CONTEXT.md beyond the Central Proposition term (potential glossary enrichment, separate discussion).
