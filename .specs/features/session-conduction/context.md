# Session Conduction Context

**Gathered:** 2026-09-08
**Spec:** to be written via `/to-spec` (slug: `session-conduction`)
**Status:** Interview complete — ready for spec

---

## Feature Boundary

Operationalize the session's **conduction** (working name) — who decides the next step at each point of a session. Today the method's order lives in the system prompt as a request (`session.py`, "Session discipline" items 1–7) and enforcement is reactive (PipelineStore `ValueError` after a wrong choice, [pipeline.py:42-81](src/socrates/pipeline.py#L42-L81)); the model chooses the next tool from the full surface at every step. Origin: a colleague's critique (2026-09-08, ML researcher) after an informal real-model run — long silence right after Opening, the session's widest decision point. Verified gaps feeding this feature: the main-orchestrator `propose_proposition` carries no pipeline gate; no Need gate exists before proposing; `await_satisfaction` is ungated in both directions (callable right after Opening, or never — the loop ends when the model stops calling tools, as `test_coverage_budget.py` literally does).

Unchanged: the method's concepts (CONTEXT.md) — Modeling Activity precedence, Opening, Probe recurrence, Satisfaction.

---

## Language Protocol (user's explicit request, 2026-09-08)

The project is meta-modeling — programming a thing that models — so three registers coexist here, and no term migrates between them without an explicit decision:

1. **The user's domain** — what the end user models (payments, orders, "capturing the client's phone"). Never an object of this interview; example content only, always marked as such.
2. **Socrates's domain** — modeling itself: the CONTEXT.md vocabulary. The only register that can receive new terms.
3. **The machine** — LangGraph, node, middleware, tool, JSON. Workshop vocabulary for choosing mechanisms; never promoted to the glossary (CONTEXT.md already practices this: Iteration avoids "loop (implementation)").

Consequences in force: "phase" is not a domain term — there are Modeling Activities (three) and there are passes/Probes (recurring); the name **conduction** is a placeholder, and naming is an open decision of this cycle.

---

## Decisions

### D1 — The session's shape: chapters with internal pulse (design A)

Opening contradiction, presented to the user: CONTEXT.md's Mapping ("spans the three Modeling Activities... Not a single pass — it is iterated... until Satisfaction"; "Precedence is linear; execution is not") reads as one continuous traversal; pipeline.py implements strict chapters (`begin`/`complete` in order; `reopen` drops downstream). The user chose **A — chapters with internal pulse**:

- The three Modeling Activities are **chapters in strict precedence** — the pipeline's door structure stands; the method's non-linearity is Iteration's L4 reopen.
- The **pass/Probe pulse lives inside each chapter**: propose, lapidate (Scenarios + Assertion Tests), resolve, interleaved — one regime per chapter. Rejected as consequence: C's produce-then-lapida split (two regimes, unowned seam — the seam where the colleague's model went silent; also an end-of-chapter flood generator, the "Opening flood" shape discussed in the Coverage cycle).
- A chapter declares completion **only when its Probes are quiet** (what "quiet" means exactly: next question).
- After the third chapter, **passes continue until Satisfaction** (the tail pulse).
- **Passes examine the whole Model** regardless of the open chapter — a conflict on requirements ground may surface during the structural chapter (L2 → Supersede); chapters govern where NEW propositions attach, not what passes examine.

---

### D2 — In-chapter rhythm: the treadmill with the maieutic valve (L3)

How far conduction reaches inside a chapter. All candidate levels were required to be mechanically checkable (counts and state — never requests). The user chose **L3**:

- **Invariant: at most one unlapidated proposition** at any moment (a proposition is lapidated once it has gone through ≥1 pass). Proposing the next one opens only after the previous is lapidated.
- **No new pass while a Batch awaits the user** — the glossary already states this ("the user clarifies every Conflict in it before the next pass runs").
- **The valve: proposing stays always available.** New ground revealed while resolving a Probe may be born immediately — it becomes the single unlapidated proposition. What queues is the next pass, never the proposition. Grounded in CONTEXT.md's Probe: "Resolving a Conflict can reveal new ground, so each Probe both de-conflicts and grows the Model."
- Rejected: L1 (doors+exit only — the model keeps the beat inside, so wide-decision silence and arbitrary unlapidated accumulation survive inside chapters); L2 (strict treadmill with no valve — new ground from a Probe queues behind the whole Batch; maieutic cost with no enforceability gain, since the valve is still just counting).

### D3 — The door close: model declares, user confirms

Plus two embedded rulings confirmed along with it:

- **Quiet is counting, not judgment**: a chapter is quiet when every proposition born in it has been through ≥1 pass and no Batch awaits the user (any ground — passes examine the whole Model, so a cross-chapter conflict surfaced in a Batch must be resolved or deferred before the door).
- **Deferred conflicts never block a door** — parking is deliberate; the conflict rides to the Satisfaction warning and re-raises on touch ("Deferring never blocks" extended from passes to doors).
- **The close itself**: when quiet, the model declares completion and the harness interrupts for the user's confirmation — the same propose/confirm pair as the glossary's Iteration term ("The harness proposes the phase; the user confirms"), and the house pattern (accept/reject/Satisfaction all interrupt-confirm). Division of labor per ADR-0002: quiet is bookkeeping; "good enough to close" is the user's judgment. A "not yet" keeps the chapter open, with the maieutic valve still available for ground the user reveals in refusing.

### D4 — Satisfaction: doors as the steering wheel + the tail; the only sink

- **Only-sink principle (confirmed)**: the session ends exclusively through a Satisfaction interrupt — never again by the model stopping (today's ADR-0002 gap: `test_coverage_budget.py` literally ends a session with no Satisfaction at all).
- **Reachability**: the door-close confirmation is the session's steering wheel — its answers are "yes, close" (next door opens), "not yet" (chapter stays open, valve available), and **Satisfaction** (terminate here; the non-blocking warning carries *chapters never visited* alongside the criticality-weighted deferred conflicts). After the third door (the tail), Satisfaction is always available and passes continue until it.
- Rejected: Satisfaction-from-anywhere (mechanically heavier — the question must live inside chapters — and a mid-Batch close strands pending conflicts, warned); tail-only (cheapest surface, but forces performative rides through unneeded chapters and denies legitimate early closure on small domains).

### D5 — Mechanism: the state-governed surface (machine register)

The user chose to stay in `deepagents` and govern the surface rather than rebuild the topology:

- **State-gated dispatch**: a middleware reads the persisted state (pipeline.json + Need/Batch facts) at tool-dispatch time and makes out-of-state tools unavailable — surface filtering or, fallback, a redirect result naming the current state and its admissible next steps (`{"ok": false, "conduction": {"state": ...}, "redirect": ...}` — assertable at the existing seam).
- **Passes migrate into the chapters**: the chapter subagent carries the pulse tools (shape A demands one regime per chapter — propose, lapidate, resolve under one roof). The main orchestrator keeps Opening, doors (`task`), and the tail.
- **Only-sink via a minimal outer loop-guard**: a thin wrapper around the compiled agent re-injects the session with a state redirect when the model stops without Satisfaction (D4's principle made mechanical).
- The system prompt's "Session discipline" (7 numbered requests) retires into an advisory persona/how-to-talk section; the order lives in the conduction.
- Rejected: the literal node graph (StateGraph of opening → chapter → tail with deepagents sub-agents inside nodes — the colleague's architecture done faithfully; recorded as the honest evolution path if real sessions still dither under the governed surface, but it re-cables BudgetAwareSubagent / FilesystemMiddleware / checkpointer and re-scripts all 24 orchestration tests before the first real session); full rebuild without deepagents (strictly dominated).

### D6 — The conduction matrix (confirmed as presented)

| State | Available | Redirected (out-of-state attempt → payload naming state + admissible next steps) |
|---|---|---|
| Pre-Opening | `run_opening` | everything else — the **Need gate** is born here: proposing without a Need redirects to the Opening |
| Chapter k open (specialist conducts) | `propose_proposition` (tag k — the valve), `accept`/`reject`, the pulse: `select_exploration_budget`, `reconcile` (pass ≥ 2), `record_scenarios`, `run_assertion_tests`, `probe_batch`, `defer`, `complete_modeling_activity` (declares → interrupt with the three answers: close / not yet / Satisfaction) | `task` for another chapter; `await_satisfaction`; `run_opening` (once — "run once at the start") |
| Tail (3 doors closed) | the full pulse; `propose_proposition` (the valve stays on in the tail — ground's tag; chapter stays closed; only L4 via `run_iteration` reopens); `await_satisfaction` | chapter `task`s (except an Iteration-proposed reopen) |
| L4 unavoidable (any state) | `run_iteration` proposes the door to reopen → user confirms (Iteration pattern); `reopen` drops downstream, as today | — |

Four embedded rules confirmed with it:

1. **The valve never closes** — proposing is available in every post-Opening state, the tail included; what the treadmill limits is the pass, never the proposition.
2. **The redirect always explains** — every out-of-state attempt returns the current state and admissible next steps; never a bare "no" (this is what kills post-decision silence: the surface always says where to go).
3. **The prompt retires the discipline** — the seven "Session discipline" items become advisory narrative (persona, how to talk); the order lives in the conduction.
4. **`run_iteration` remains the only reopen path** — conduction formalizes the glossary's existing way back; it does not invent a new one.

### D7 — Registration: ADR-0005, no new glossary term

No new glossary term: every concept involved (Modeling Activity precedence, Iteration, Satisfaction, Probe recurrence) already exists in CONTEXT.md — conduction is their operationalization, same pattern as Coverage's crossover (concept in the glossary, signal in the implementation). The architecture decision — *the harness conducts, the model asks; the method's order never lives in a prompt again* — becomes **ADR-0005**.

### D8 — Testing seam: the current seam + new assertions

The existing orchestration seam carries the delta (StubChatModel + `Command(resume=...)`); what changes is what gets asserted: out-of-state redirects (the `conduction` payload), the door-close interrupt with its three answers, the only-sink (loop-guard re-injection), and the treadmill invariant (≤1 unlapidated proposition). Plus direct tests of the pure state→availability function. Same seam as the two published specs — no double rewrite.

---

## Deferred Ideas

- **The literal node graph** (StateGraph of opening → chapter → tail, deepagents sub-agents inside nodes — the colleague's architecture done faithfully): the recorded evolution path if the first real sessions still dither under the governed surface.
- **Surface filtering vs. redirect fallback** (make out-of-state tools invisible vs. interceptable-with-redirect): agent's discretion at implementation; both are assertable at the seam.
- **Bilingual redirect messages** — redirects stay English-only for now, consistent with the deferred bilingual confirm/decline work.
- **Persona slimming beyond the discipline retirement** — how far the system prompt shrinks once the order leaves it; revisit with real-session evidence.

---

## Specific References (vocabulary)

- **"Chapter" (capítulo)** is interview jargon for a Modeling Activity acting as a door — recorded here, deliberately NOT promoted to the glossary (register discipline); likewise "treadmill" (esteira), "valve" (válvula maieutica), "tail" (rabo), and "steering wheel" (volante) — names for decisions, not domain terms.
- The maieutic valve's grounding, verbatim from CONTEXT.md's Probe: *"Resolving a Conflict can reveal new ground, so each Probe both de-conflicts and grows the Model."*
- The door-close pattern's grounding, verbatim from CONTEXT.md's Iteration: *"The harness proposes the phase; the user confirms."*
- The conduction matrix: tool availability per state (Opening-first / Need gate / main-orchestrator propose gate / task gating / Satisfaction placement).
- Satisfaction as the only sink — closing the ADR-0002 gap (today the loop can end by model silence) — and from when Satisfaction is reachable.
- Iteration/reopen edges under conduction.
- Mechanism (machine register): tool-surface gating driven by pipeline state vs. literal graph nodes; deepagents middleware viability (0.7.13 ships an AgentMiddleware surface, incl. a tool-exclusion middleware).
- Naming: does conduction receive a Socrates-domain term, or does it stay machine-level?
- Testing seam for the delta.

---

## Specific References

- The colleague's framing that stuck: *"No seu prompt a ordem é um pedido: o modelo escolhe a próxima tool... No grafo, cada fase é um nó e com isso o passo seguinte já está ligado... O LLM só pergunta e o harness conduz."*
- The post-Opening decision point is simultaneously the session's widest AND prompt-ambiguous: system-prompt items 2 and 3 compete (budget-per-pass vs. task-the-activities; is the requirements task itself a pass? the prompt never says).
- Diagnosis correction recorded during evaluation: "pular fase é permitido" is factually wrong at the activity layer (PipelineStore rejects out-of-order begins reactively); the true gaps are availability-before-choice, the ungated seams listed above, and the terminations.
