---
Status: ready-for-agent
Feature: session-conduction
---

# Spec: Session conduction — the harness conducts, the model asks

## Problem Statement

In a real session, the method's order exists only as a request: the system prompt lists seven disciplines ("call run_opening first… do not skip or reorder them…"), and at every step the model chooses the next tool from the full surface. Nothing operational owns the handoffs. A first real-model run made this concrete — after the Opening, long silence at the session's widest and most ambiguous decision point, where two of the prompt's own disciplines compete for the next call. And the unguarded seams are worse than dithering: proposing works without a Need ever being registered; the main orchestrator can propose outside any Modeling Activity, bypassing the precedence that activity specialists are held to; Satisfaction can be asked right after the Opening — or never, because the loop ends whenever the model stops calling tools, without the user ever being asked. The user experiences a harness that can wander out of method, lose its place, or end the session behind their back.

## Solution

The harness conducts; the model asks. The session's order becomes enforced state rather than requested behavior: a conduction (machine-level working name — no glossary term) reads the persisted facts at every step and governs which tools exist — the Opening first (nothing else before the Need exists), the three Modeling Activities as chapters in strict precedence with the pass/Probe pulse living inside each (one regime per chapter: propose, lapidate, resolve interleaved), a treadmill rhythm with a maieutic valve (at most one unlapidated Proposition; no new pass while a Batch awaits the user; proposing never waits), chapter doors closed by model declaration with user confirmation whose interrupt carries three answers — close, not yet, or Satisfaction — and, after the third door, a tail of passes until a Satisfaction that is the session's only sink: the loop never again ends by model silence. Every out-of-state attempt receives an explaining redirect naming the current state and the admissible next steps, so the surface always says where to go — the silence killer. The system prompt's ordered discipline retires into advisory narrative. The architecture decision is recorded as ADR-0005; the glossary stands unchanged.

## User Stories

1. As a user, I want the Opening to be the only thing the session can do before the Need is registered, so that no Proposition can exist without the Relevance Filter that judges it.
2. As a user, I want the run_opening question to happen exactly once, so that the session never re-greets me mid-work.
3. As a user, I want the three Modeling Activities to run in precedence because the harness makes the wrong door unavailable — not because the model was told nicely, so that the method's order survives any model, any day.
4. As a user, I want out-of-order attempts to be redirected with the current state and the admissible next steps, so that a wrong move costs one turn and teaches the way back — never a bare "no" that invites silence.
5. As a user, I want the pass/Probe pulse to live inside each chapter — propose, lapidate, resolve interleaved by one conductor, so that what a chapter produces is audited before the door closes, and no produce-then-lapida seam ever splits my session into two regimes.
6. As a user, I want at most one unlapidated Proposition at any moment (the treadmill), so that Conflicts surface while the ground is fresh, not in an end-of-chapter flood.
7. As a user, I want no new pass while a Batch awaits my resolution, so that the harness never piles new conflicts on top of ones I already owe an answer to.
8. As a user, I want proposing to stay available at every moment after the Opening (the maieutic valve), so that new ground revealed while resolving a Probe is born immediately — resolving a Conflict grows the Model, on the spot.
9. As a user, I want a chapter to close only when it is quiet by counting — every Proposition born in it has been through at least one pass, and no Batch awaits me on any ground, so that "complete" means lapidated and silent, never merely produced.
10. As a user, I want deferred Conflicts never to block a chapter door, so that parking stays what it promises — deliberate deferral that rides to the Satisfaction warning and re-raises on touch.
11. As a user, I want passes to keep examining the whole Model regardless of the open chapter, so that a Conflict on requirements ground can still surface during the structural chapter (L2 → Supersede), exactly as the method describes.
12. As a user, I want the model to declare a chapter complete and myself to confirm it, so that quiet is bookkeeping but "good enough to close" is my judgment — the same propose/confirm pair Iteration already uses.
13. As a user, I want the door-close interrupt to carry three answers — close and proceed, not yet, or Satisfaction — so that every door is a steering wheel where I decide whether the session keeps going.
14. As a user, I want the Satisfaction warning to tell me which chapters were never visited alongside the deferred Conflicts it already weighs, so that an early close is informed, never surprised.
15. As a user, I want Satisfaction to remain non-blocking in that warning, so that closing the Model with doors open is still my call (ADR-0002).
16. As a user, I want the session after the third door (the tail) to keep offering passes and Satisfaction, so that the Model tightens until I say it is enough.
17. As a user, I want the tail's valve to keep working — Propositions born in the tail tagged with their ground's activity, the chapter staying closed, so that late ground enters the Model without ceremony.
18. As a user, I want the session to end exclusively through my Satisfaction, so that the loop never again terminates because the model went quiet on its own.
19. As a user, I want an L4 Conflict to keep proposing Iteration — the harness proposing the door to reopen, me confirming — as the only reopen path, so that conduction formalizes the method's way back rather than inventing a new one.
20. As a user, I want a reopen to keep dropping the downstream chapters' completion, so that invalidated ground is re-earned, as today.
21. As a user, I want the exploration budget to keep riding the passes wherever they run — including inside chapters — with the same explicit subagent propagation, so that the Coverage allowance never silently regresses.
22. As a user, I want availability derived from persisted facts at every step (pipeline progress, Need existence, pending Batches, lapidation counts) and never stored as its own state, so that the Model's filesystem remains the single source of truth (ADR-0001).
23. As a user, I want quiet, the treadmill, and door admissibility to be counting, never judgment of my domain, so that no automated grader sneaks in through the conduction (ADR-0002).
24. As a user, I want the system prompt's ordered discipline retired into an advisory persona, so that the order lives in one enforced place, not two disagreeing ones.
25. As a user, I want the conduction deterministic and pure — same persisted facts, same availability — so that sessions are reproducible and the availability rule is testable on its own.
26. As a user, I want every redirect, door interrupt, and Satisfaction question in the session's plain conversational terms, so that the machinery never leaks into my interview.

## Implementation Decisions

- **The conduction is a state-governed tool surface, not a graph rewrite.** The deepagents agent loop remains the session; a dispatch-time governor reads persisted facts and makes out-of-state tools unavailable (surface filtering, or an intercepting redirect — implementer's discretion, both observable). The state machine never becomes node topology. The literal node graph is recorded as the evolution path if real sessions still dither.
- **The matrix (state × availability)**: Pre-Opening — only the Opening tool, everything else redirected (this is where the Need gate lives). Chapter open — its specialist carries: proposing (the valve), accept/reject, the full pulse (budget selection, Reconciliation from pass 2, Scenarios, Assertion Tests, Probe, Deferral), and chapter completion; other chapters' tasks, Satisfaction, and a second Opening are redirected. Tail — the full pulse, proposing (ground's tag), and Satisfaction; chapter tasks redirected unless an Iteration-proposed reopen. L4 unavoidable, any state — Iteration proposes, user confirms.
- **Treadmill invariant**: at most one Proposition that has never been through a pass; no new pass while a Batch awaits the user; proposing available in every post-Opening state. All three are counting over persisted facts.
- **Quiet**: every Proposition born in the chapter has ≥1 pass, and no Batch pending on any ground; deferred Conflicts do not block. Completion becomes a declaration that interrupts for user confirmation with three answers (close / not yet / Satisfaction); a "not yet" keeps the chapter open with the valve live.
- **Only-sink**: a minimal outer guard re-injects the session with a state redirect when the model stops without Satisfaction.
- **Passes migrate into the chapters**: the budget-selection and inference tools move from the session surface into the chapter specialists' toolsets (one regime per chapter); the orchestrator keeps the Opening, the doors, and the tail. Budget-aware subagent propagation must survive the migration unchanged.
- **Registration**: ADR-0005 — *the harness conducts, the model asks; the method's order never lives in a prompt again.* No glossary term is added and no existing term's text changes: precedence, Iteration, Satisfaction, and Probe recurrence already say the concepts; this delta is their operationalization.
- **No new persisted state**: availability is derived at read time from the existing filesystem facts (pipeline progress, Need, Batches, lapidation).
- **Redirect payload**: an explicit `ok:false` result naming the current conduction state and the admissible next steps — the model's map back, and the tests' assertion point.
- **Rejected alternatives** (rationale in the feature context file): literal node graph and rebuild-without-deepagents (cost before the first real session, seam rewrite of the whole suite); doors-only internal rhythm (silence survives inside chapters); strict treadmill without the valve (new ground queues behind a Batch — maieutic cost, no enforceability gain); model-closes-alone (door shuts behind the user's back, against the house confirm pattern); user-only closes (nobody propels the close); Satisfaction-from-anywhere (heavier mechanism, strands pending Batches); tail-only Satisfaction (performative rides through unneeded chapters).

## Testing Decisions

- **Good tests assert external behavior only**: tool-result JSON (redirect payloads and their named state), interrupt payloads (the three-answer door close, the Satisfaction warning's unvisited-chapters line), virtual-filesystem state, and the loop-guard's re-injection — never internal helpers.
- **Seam — the existing orchestration seam, as decided with the user**: a Socrates session driven with the stubbed model provider, scripting tool calls and resolving interrupts, exactly as the suite does today; the delta adds assertions, not a new seam. Alongside it, direct tests of the pure state→availability rule (facts in → availability out), matching the mixed-seam prior art.
- **Prior art**: the coverage-budget orchestration (session scripting with budget propagation), the deferral tests (criticality and warning payloads), the iteration-L4 tests (reopen proposals), the proposition-lifecycle tests (interrupt confirm/decline patterns — the door close reuses that shape).
- **Gate**: the project pytest suite via the repo virtualenv, all green.

## Out of Scope

- **The literal node graph** — evolution path, not v1; revisit with first-real-session evidence.
- **Glossary changes and amendments to ADR-0001..0004** — ADR-0005 is added; everything conceptual stands.
- **The Central Proposition and Coverage signal deltas** — separate published specs; the sequencing against this one (shared test seam) is decided at ticket breakdown.
- **Bilingual redirect and interrupt text** — English-only for now, consistent with the deferred bilingual confirm/decline work.
- **Reopen semantics changes** — drop-downstream behavior stays as is.
- **Persona slimming beyond the discipline retirement** — how far the prompt shrinks is revisited with real-session evidence.
- **Deliverable composition and Implementation-Independence filter work** — still gated on the first real-model session.
- **Registering silent passes / Coverage reading changes** — owned by the Coverage signal spec.

## Further Notes

- Origin: a colleague's critique (2026-09-08, after an informal real-model run — silence post-Opening), evaluated against the code before this cycle. Corrections recorded during evaluation: "skipping phases is permitted" was wrong at the activity layer (precedence was already enforced reactively — a ValueError after the wrong choice); the true gaps are availability-before-choice, the unguarded seams (no Need gate, orchestrator proposing outside precedence, Satisfaction early-or-never, loop-end-by-silence — the ADR-0002 conformance gap this spec closes).
- The interview's language protocol (three registers; no term migrates without decision) and the full decision record D1–D8 live in the feature's context file; tickets should reference both.
- Glossary groundings the decisions lean on, verbatim: Probe — "Resolving a Conflict can reveal new ground, so each Probe both de-conflicts and grows the Model." Iteration — "The harness proposes the phase; the user confirms." Batch — "the user clarifies every Conflict in it before the next pass runs."
- Interview jargon deliberately not promoted: chapter, treadmill, valve, tail, steering wheel — names for decisions, not domain terms.
