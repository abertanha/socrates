---
Status: ready-for-agent
Feature: coverage-signal
---

# Spec: Coverage signal — read the trend, not two points

## Problem Statement

How deep each Inference pass digs — the exploration budget — is driven by a Coverage signal that misreads the domain in two ways, and both fail in the expensive direction. First, an **Opening flood anchors the peak forever**: a first pass that surfaces 30 conflicts makes later steady production (6 per pass) read as 80% covered, so the harness gives itself near-lean budget while the domain is still rich in conflict — the Model can converge to Satisfaction *looking* done, with conflicts never exposed. Second, the reading is a **single point against that immortal peak**: an alternating stretch (8, 1, 8, 1) swings the budget between generous and lean every pass — an erratic session rhythm, truncating digging exactly when a seam reopens. The user experiences a harness that loses its appetite too early, and whose appetite is unpredictable.

## Solution

Read **trend, not points**: Coverage becomes a moving-average crossover — `clamp(1 − EMA_short / EMA_long)` over the conflicts-per-pass series. No peak exists, so the flood cannot hold the signal hostage; both averages move slowly, so oscillation damps; and when conflict production *rises* — the rework an Iteration reopens — the short average crosses above the long one and the clamp pins Coverage to 0, granting maximum generosity automatically during rework, with no special case. Silence stays invisible, by explicit decision: over-budgeting a mature domain is harmless (the agent terminates early anyway — ADR-0004's own asymmetry), only under-budgeting is expensive, so this delta fixes exactly the two under-budgeting failures and accepts the generous tail. The budget mapping (lean 40 ↔ generous 200, linear), the per-pass selection flow, subagent propagation, and both ADR-0004 guardrails (Relevance-anchored; allowance, never quality gate) are unchanged.

## User Stories

1. As a user, I want Coverage to read the trend of my conflict series rather than its last point, so that the budget reflects where the domain is heading, not one pass.
2. As a user, I want the Opening flood's influence to fade as passes accumulate, so that an early burst of conflicts stops masquerading as maturity.
3. As a user, I want a domain that still produces conflicts steadily to read as sparse, so that digging stays generous while there is still ground to find.
4. As a user, I want an alternating conflict series (8, 1, 8, 1) to produce a stable budget, so that the session rhythm does not thrash between generous and lean.
5. As a user, I want a declining conflict series to raise Coverage smoothly, so that the budget leans out as the Model accounts for more of the domain.
6. As a user, I want rising conflict production — the rework an Iteration reopens — to grant maximum exploration generosity automatically, so that rework digs deep without a special case.
7. As a user, I want passes with zero conflicts to leave the signal unchanged, so that the accepted generous tail costs nothing (I refused to fix silence; per the ADR's asymmetry, over-budget is harmless).
8. As a user, I want a session that never surfaced any conflict to read as fully mature, so that an empty domain leans out immediately.
9. As a user, I want the budget selected at the start of each pass exactly as today, so that the flow I know does not change.
10. As a user, I want the Coverage-to-budget mapping to stay linear between the same bounds, so that this delta changes the reading, not the dial.
11. As a user, I want the chosen limit stamped onto subagent invokes, so that exploration depth propagates without the silent fallback (deepagents #1698).
12. As a user, I want the budget to remain an exploration allowance and never a quality gate, so that termination stays loop-ending plus my Satisfaction (ADR-0002).
13. As a user, I want Coverage recomputed from the persisted pass history at measurement time, so that no derived signal is stored beside the Model's state.
14. As a user, I want the smoothing constants fixed and pinned by tests, so that the reading is deterministic and reproducible.
15. As a user, I want Scenarios still anchored by the Relevance Filter, so that a generous budget explores Need-relevant ground, never wanders.
16. As a user, I want the persisted conflict history to remain the only state this signal needs, so that the Model's filesystem stays the source of truth.
17. As a user, I want the signal's behavior on flood-decay, oscillation, decline, and rework-rise each pinned by a named scenario, so that future changes cannot silently regress the reading.

## Implementation Decisions

- **The reading**: `Coverage = clamp(1 − EMA_short / EMA_long, 0, 1)` computed over the conflicts-per-pass series (productive passes only). This replaces the point reading `1 − last/peak` and its historical-maximum peak — no peak exists in the new reading.
- **Both averages recomputed deterministically from the persisted pass history** at measurement time; seed = the first productive pass. No new persisted fields beyond the existing series.
- **Zero passes remain unrecorded** (the non-positive count guard stays): silence neither raises nor lowers Coverage — the deliberate complement of fixing only the under-budgeting failures, grounded in ADR-0004's asymmetry ("a high limit buys nothing and a low one is harmless").
- **Empty series → Coverage 1.0** (mature by vacuity — same edge as the current `peak ≤ 0` guard).
- **Iteration/reopen needs no reset**: rising production crosses the averages and clamps Coverage to 0 — generosity during rework falls out of the formula.
- **Unchanged**: the linear Coverage→recursion_limit mapping and its bounds (lean 40, generous 200); per-pass budget selection; subagent limit propagation; both ADR-0004 guardrails.
- **Docs**: the glossary Coverage term (concept level) and ADR-0004 stand unchanged — the crossover is the faithful operationalization of "read pass-over-pass from declining signals"; no amendment needed.
- **Rejected alternatives** (recorded with rationale in the feature's context file): double smoothing (EMA signal + decaying peak — two mechanisms for one effect); bounded peak window + two-pass direction confirmation (window-edge jump and one-pass lag).
- Modules touched: the Coverage measurement/store module and its budget-selection entry point. The session system prompt and tool surface are untouched.

## Testing Decisions

- **Good tests assert external behavior**: for the reading, its contract as a pure function over the persisted series (series in → Coverage out); for the session wiring, interrupt payloads, tool-result JSON, and virtual-filesystem state.
- **Mixed seam, as decided with the user**: series dynamics (flood decay, oscillation damping, decline, rework-rise clamp, vacuity edge) asserted directly against the reading; interaction semantics (per-pass budget selection, subagent propagation, allowance-never-gate) via the orchestration seam with the stubbed model provider.
- **Prior art**: the existing coverage-budget tests — which already combine the declared orchestration seam with direct imports of the reading functions — are the rewrite ground; their propagation and allowance-not-gate assertions carry over.
- **Gate**: the project pytest suite via the repo virtualenv, all green.

## Out of Scope

- **Registering silent passes** (the refused third defect) — revisit only if the first real-model session shows tail-drag costing real interview fatigue.
- **Non-linear budget mapping** (tiers, hysteresis) — the linear dial survived this cycle untouched.
- **Per-activity Coverage** (one global series today) — not discussed, out of scope.
- **Glossary or ADR text changes** — concept and architecture stand; only the operationalization changes.
- **The Central Proposition delta** — separate spec, already published.
- **First real-model session work** — remains the gate for deliverable-composition and filter work.

## Further Notes

- Origin: the initial assessment (2026-09-04) flagged the Coverage formula — with a correction recorded during the interview: the assessment's claim that "one silent pass collapses Coverage to 1.0" was wrong (zero passes are never recorded); the real defects were the two under-budgeting failures specified here.
- Interview decisions, the refused defect with its grounding, and rejected formula designs live in the feature's context file; tickets should reference both.
- The principle the user's choices encode: **fix under-budgeting, accept over-budgeting** — worth carrying into any future signal work.
