---
status: accepted
---

# The harness conducts, the model asks

The method's order — the Opening first, the three Modeling Activities in precedence, the pass/Probe pulse inside each, Satisfaction as the only end — used to live in the system prompt as seven numbered requests, with the full tool surface available at every step. A first real-model run showed what that costs: silence at the session's widest decision point, propositions without a Need to filter them, Satisfaction askable right after the Opening or never — the loop ended whenever the model went quiet, behind the user's back. Requested order is one distracted turn away from wrong order.

**The decision: the harness conducts, the model asks; the method's order never lives in a prompt again.**

The mechanism is a **state-governed tool surface**, not a graph rewrite. A dispatch-time governor derives the session's conduction state from the Model's own filesystem facts — Need, pipeline progress, lapidation, pending Batches — and admits only the tools that state allows; out-of-state calls receive an explaining redirect naming the current state and the admissible next steps, never a bare "no". Chapters close at doors — model declaration, user confirmation with three answers (close / not yet / Satisfaction) — and an outer loop-guard re-injects the session with a state redirect when the model stops without an affirmative Satisfaction: the session's only sink. Every rule the prompt used to request — the Need gate, precedence, the pulse's placement, the treadmill, quiet, the doors, the only-sink — is enforced mechanically, and the prompt retired into an advisory persona (how to talk, what a redirect is, never the order).

**Two guardrails:**

1. **Counting, never judgment (per ADR-0002).** Every conduction rule is bookkeeping over persisted facts — quiet counts passes and pending Batches; it never grades the domain. "Good enough to close" stays the user's answer at the door.
2. **Derived at read time (per ADR-0001).** No new persisted state: availability is a pure function of the Model's filesystem, recomputed at every dispatch.

**Rejected alternative — the literal node graph** (a StateGraph of Opening → chapters → tail with deepagents subagents inside the nodes): faithful to the architecture critique, but it re-cables the budget propagation, the filesystem middleware, and the checkpointer, and re-scripts the whole orchestration suite before the first real session. **Recorded as the evolution path:** if real sessions still dither under the governed surface, the node graph is the honest next step.

**Consequence:** the system prompt carries no ordered discipline — persona and how-to-talk only, pinned by `tests/test_prompt_retirement.py`; the conduction's conduct terms (chapter, door, quiet, lapidate, treadmill, valve) are glossary terms at concept level; ADR-0001..0004 stand unchanged.
