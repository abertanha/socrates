---
Status: ready-for-agent
Feature: central-proposition
---

# Spec: Central Proposition — definition, signal, and graded criticality

## Problem Statement

When Socrates recommends against deferring a conflict, or warns about deferred conflicts at Satisfaction, the signal it uses for "this matters" is broken: a conflict is "critical" whenever any party is Accepted — and since every L2+ conflict touches an Accepted party by definition, **everything is critical**. The user parking conflicts gets a "recommend against deferring" on the trivial and the structural alike, and a Satisfaction warning where every entry shouts equally. The warnings have stopped meaning anything: the harness cannot tell the user *which* parked conflict actually carries the Model's weight, because "central Proposition" was never defined — it was proxied by lifecycle state.

## Solution

Define **Central Proposition** as a concept of the harness's own domain — *a structuring synthesis: a Proposition from which other Propositions unfold* — and operationalize it with a computable signal: a Proposition is central when others were Accepted via it (its derivation subtree in the `accepted_via` graph) or when it belongs to the Requirements activity (shaping the Relevance Filter). Centrality is always derived from the current graph, never stored, and it is **graded**: the Satisfaction warning weighs each deferred conflict by structural load and scope (dependents count, with a bonus for Requirements), ordered so the heaviest structural risk is read first. Deferral recommendation stays boolean. An L4 conflict remains **always unavoidable** — centrality never buys the right to park an accepted×accepted contradiction, because the Model never ships internally contradictory (the Conflict kinds are named for the square of oppositions; non-contradiction is the Model's admission test).

## User Stories

1. As a user, I want "Central Proposition" defined in the domain glossary as a structuring synthesis — the Proposition other Propositions unfold from — so that centrality means structural role, not lifecycle state.
2. As a user, I want a Proposition counted central when other Propositions were Accepted via it, so that the derivation graph — the same one that feeds Supersede cascades — is what criticality reads.
3. As a user, I want a Proposition counted central when it belongs to the Requirements activity, so that the Propositions shaping the Relevance Filter are central from their first moment, before any derivation is recorded via them.
4. As a user, I want the Need itself never treated as a Proposition, so that centrality stays a property of the Model's graph — the Need stands above it as the filter.
5. As a user, I want a peripheral Proposition (a leaf: nothing derived via it, not Requirements) treated as non-central, so that deferring its conflicts is not flagged as risky.
6. As a user, I want centrality recomputed from the current graph at every assessment, so that a Proposition that gained (or lost, via cascade) its dependents is (no longer) central — the signal never goes stale.
7. As a user, I want no new persisted state for centrality, so that the Model's filesystem stays the source of truth and derived facts are never stored beside it.
8. As a user, I want the criticality reason `central_proposition` to reflect the defined concept, so that "Accepted party" alone no longer marks a conflict critical.
9. As a user, I want level-based criticality unchanged (L2–L4 remain high-level reasons), so that this delta sharpens centrality without loosening the stakes of consolidated parties.
10. As a user, I want the Deferral recommendation to stay boolean (critical or not), so that the Probe question remains a simple "resolve now?" — while the *evidence* behind it becomes honest.
11. As a user, I want the criticality payload to expose how a party is central (dimension, dependents count, weight), so that the recommendation is auditable against the graph.
12. As a user, I want the Satisfaction warning to weigh deferred conflicts by structural load and scope, so that the conflicts that would cascade read heavier than leaf skirmishes.
13. As a user, I want warning ordering to let the dependents count dominate, so that blast radius — the honest signal — decides what I read first.
14. As a user, I want ties in weight resolved toward Requirements, so that filter-shaping Propositions edge out equally-loaded structural ones.
15. As a user, I want the Satisfaction warning to remain non-blocking, so that I can still knowingly close the Model with conflicts open (ADR-0002).
16. As a user, I want every Supersede cascade to keep notifying regardless of centrality, so that removal of Accepted state is always visible — the Notification is a record of a destructive act, not an interruption.
17. As a user, I want an L4 conflict to remain always unavoidable — non-deferrable, with its Notification outside Interview flow — so that a contradiction inside the Accepted set is never parked.
18. As a user, I want it to be impossible for the deliverable to ship an accepted×accepted contradiction, so that the Conceptual Domain Model never contains two Accepted Propositions that cannot both hold.
19. As a user, I want the unavoidable-conflict Notification to carry the parties' centrality (dimension, dependents, weight), so that I see the stakes at a glance when interrupted.
20. As a user, I want the Iteration proposal for an L4 to carry the parties' centrality, so that reopening a Modeling Activity is informed by how much of the Model hangs on the contradiction.
21. As a user, I want the top Need-synthesis Proposition (Accepted directly, nothing via it yet) to be central via the Requirements activity, so that the most structuring Proposition of all is never mis-read as peripheral.
22. As a user, I want the requirements-shortcut's known coarseness (every Requirements Proposition counts as central) accepted deliberately for v1, so that the failure mode is over-caution — the safe direction for an operational blocking-ness heuristic.

## Implementation Decisions

- **Modules touched**: the Inference Engine (criticality assessment and Satisfaction-warning assembly), the Proposition store (expose the derivation closure — reuse the existing transitive-dependents computation that Supersede cascades already use), and the tool layer only as payload pass-through. The domain glossary gains the **Central Proposition** term (placed with the Conflict/Deferral cluster).
- **Concept vs. signal separation**: the glossary term states the concept (structuring synthesis); the operational signal — derivation out-degree ∨ Requirements activity — is recorded as a deliberately coarse v1 proxy, revisable with evidence from the first real-model session (same pattern as Coverage: concept in the glossary, signal in the implementation).
- **Dependents are transitive**: the weight counts the full derivation subtree (what a Supersede of this Proposition would actually Degrade), not just direct via-edges.
- **Weight and ordering**: weight = transitive dependents + (1 if Requirements); the Satisfaction warning orders by weight descending, ties resolve to the Requirements side. The formula applies to warning ordering and payload only — never to blocking or to the boolean recommendation.
- **Derived, never stored**: centrality is computed at assessment time from the graph; no new filesystem state, no new tool contracts.
- **L4 unchanged in boundary, enriched in payload**: unavoidability remains level-based (all L4s); the unavoidable-conflict Notification and the Iteration proposal carry centrality as stakes-at-a-glance decoration, never as gating.
- **Supersede-cascade Notification stays ungated** by centrality — every cascade notifies (quiet-by-default already permits exactly two triggers; this does not become one-and-a-half).
- **Criticality structure**: reasons remain `high_conflict_level` (L2–L4) and `central_proposition` — the latter now meaning the defined concept. `unavoidable` remains `critical ∧ L4`, hence still exactly L4.
- **Foundational note**: the Conflict kinds are named for the relations of the **square of oppositions**; the never-ship-contradictory rule for L4 follows from it. The glossary term should carry this grounding.
- Interview decisions, rationale, and rejected alternatives (pure-graph signal; `need_derived` flag; lexicographic ordering; periphery-gated L4) are recorded in `.specs/features/central-proposition/context.md`.

## Testing Decisions

- **Good tests assert external behavior only**: interrupt payloads, tool-result JSON, and virtual-filesystem state — never internal functions or private helpers.
- **Single seam — the existing orchestration seam**: a Socrates session driven with the stubbed model provider, scripting tool calls and resolving interrupts, asserting on what the user would see. This is the declared seam of all existing orchestration tests; no new seam is introduced.
- **Prior art**: the deferral tests (criticality payload, Satisfaction warning), the notification-policy tests (unavoidable trigger, Supersede cascade), the iteration-L4 tests (proposal payload), and the proposition-lifecycle tests (the `via`-chain fixtures needed to build derivation subtrees are the same pattern the Supersede-cascade tests use).
- **Gate**: project pytest suite via the repo virtualenv, all green.

## Out of Scope

- **`need_derived` flag** — the precise-but-costlier signal; promoted only if the first real-model session shows the Requirements shortcut crying wolf.
- **Richer Requirements Opening flow** (Need → max/min scope → target audience → interface → critical end-user properties) — belongs to the first-real-session work.
- **Scale refinement** beyond the agreed formula (weight curves, dimension multipliers) — revisit with evidence from real warnings.
- **Coverage signal changes** (the other delta from the same assessment) — separate spec.
- **Deliverable composition changes** and Implementation-Independence filter work — gated on the first real-model session by prior decision.
- **Gating the Supersede-cascade Notification** — explicitly decided against.
- **Bilingual confirm/decline parsing** — still deferred until after the first real-model testing pass.

## Further Notes

- Origin: the initial conceptual/logical/technical assessment (2026-09-04) flagged criticality as ≈ binary ("central ≡ Accepted"); this spec is the elicited fix, decided through a specification interview the same day.
- The concept the user supplied, verbatim: *"uma síntese estruturante dos demais requisitos, entendimentos sobre a necessidade que a aplicação visa suprir e, por consequência, comportamentos que os relacionamentos das entidades do modelo terão."*
- Revisit triggers and deferred ideas live in the context file; the tickets that follow should reference both this spec and the context file's decision record.
