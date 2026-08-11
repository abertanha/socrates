---
Status: ready-for-agent
Feature: socrates-harness
---

# Spec: Socrates harness (MVP — forward flow)

## Problem Statement

The long-reasoning, logical-conceptual front-end of software development — eliciting the **Need**, bounding the **Subject Domain**, and defining the **behavior** of its entities — is done poorly today. A developer (the **user**) facing a new domain has no tool that helps them *give birth to* a sound **Conceptual Domain Model** through disciplined questioning. Generic LLM chat produces plausible-but-shallow documents: it does not stress-test its own assertions, does not surface latent contradictions between what the user said earlier and what they just said, and declares its output "done" with no real basis. The result is models that look complete but collapse on the first edge case — entities undefined, relationships ambiguous, terms overloaded. The user is left to manually cross-check, with no memory of what was rejected or why.

## Solution

**Socrates** — a maieutic agent harness, built on the LangChain `deepagents` v0.7 library, that elicits a Conceptual Domain Model from the user through Socratic questioning rather than top-down authoring. It runs the user through three **Modeling Activities** in logical precedence (**Requirements → Domain Modeling → Behavioral Specification**), and within each, it generates **Scenarios** that stretch the user's **Propositions** to their **Elasticity** limit, surfacing **Conflicts** (contradictions, omissions, contrarieties, ambiguities) it presents back to the user in **Batches** for resolution via **Probes**. The user's explicit **Satisfaction** — never an automated grader — terminates the work. Every model-changing step is persisted to a virtual filesystem, so the Model survives across phases and sessions. The deliverable is a Conceptual Domain Model composed of a **Glossary**, a **Structure**, and conceptual **Rules**.

## User Stories

1. As a user, I want to start a modeling session, so that Socrates begins eliciting my domain.
2. As a user, I want an **Opening** that asks me broad questions (the **Need**, the session's objective, what I seek to model), so that the session is seeded with my intent before any deep probing.
3. As a user, I want Socrates to derive a **Relevance Filter** from my Need, so that only the slice of reality relevant to my objective enters the Model.
4. As a user, I want Socrates to run the **Requirements** activity first, so that what must be inside and outside the Model is settled before structure or behavior.
5. As a user, I want Socrates to run **Domain Modeling** after Requirements, so that the Subject Domain is bounded and its ubiquitous language and entities are established.
6. As a user, I want Socrates to run **Behavioral Specification** last, so that the conceptual behavior and relationships between entities are inferred only after the domain is bounded.
7. As a user, I want Socrates to treat **Behavioral Specification** as conceptual domain rules only, so that "the system shall..." functional requirements stay out of scope.
8. As a user, I want each Modeling Activity to run as a specialist agent with its own focus, so that Requirements-elicitation differs in posture from Domain Modeling and Behavioral Specification.
9. As a user, I want my freshly proposed **Proposition** to be triaged for immediate conflict, so that anything that plainly contradicts the existing Model is caught on entry.
10. As a user, I want a non-conflicting Proposition to become a **Candidate**, so that it enters the queue for Scenario evaluation and my acceptance.
11. As a user, I want Socrates to generate **Scenarios** grounded in the current Model, so that my Propositions are probed against concrete situations rather than assessed in the abstract.
12. As a user, I want several Scenarios generated per Proposition, so that the **Plasticity** of each Proposition is evidenced across varied situations.
13. As a user, I want Scenarios kept relevant by the Relevance Filter, so that effort is spent on Need-relevant edges (zero, one, many, none, intersections), not wandering.
14. As a user, I want Socrates to run **Assertion Tests** that stretch each Proposition toward its Elasticity limit, so that I learn where my assertions break before I build on them.
15. As a user, I want the conflicts surfaced in a pass gathered into a **Batch** and presented together, so that I resolve a whole set of issues at once rather than one at a time.
16. As a user, I want a **Probe** to let me resolve conflicts the Inference Engine surfaces, so that each Proposition is driven toward assertiveness and a ubiquitous language.
17. As a user, I want resolving a conflict to be able to reveal new ground, so that each Probe both de-conflicts and grows the Model for the next pass.
18. As a user, I want **Reconciliation** to cross-check my new answers against the existing Model before the next Scenario batch, so that latent contradictions I just introduced are caught before expensive testing.
19. As a user, I want Reconciliation to run *before* Assertion Tests, so that Scenarios are not wasted on material that directly contradicts what I already said.
20. As a user, I want a conflict between my new information and an Accepted Proposition surfaced to me, so that I decide how to resolve it.
21. As a user, to resolve such a conflict, I want to **Supersede** the Accepted Proposition, so that the new information takes its place and the displaced one is recorded with its reason.
22. As a user, I want a Supersede to cascade automatically, so that any Proposition accepted only indirectly via the displaced one is sent back to Candidate for re-evaluation.
23. As a user, I want to be notified (but not asked) when a Supersede cascade removes interdependent Propositions, so that I am never surprised by model churn.
24. As a user, I want a Candidate that cannot be salvaged to be **Rejected** with an explicit reason, so that the Rejection Guardrail remembers what we decided not to model and why.
25. As a user, I want future Propositions that resemble a Rejection Guardrail entry to be flagged, so that rejected ideas do not silently re-enter.
26. As a user, I want to decide whether to resolve a surfaced conflict now or **Defer** it, so that I can keep momentum when a conflict need not block the current pass.
27. As a user, I want Socrates to recommend against deferring a critical conflict, so that I am nudged to resolve the conflicts that block modeling progress.
28. As a user, I want a deferred conflict to re-surface when new information touches its Propositions, so that parked issues are not forgotten.
29. As a user, I want deferred conflicts surfaced as a warning at Satisfaction (not a hard block), so that I can knowingly close the Model with issues open.
30. As a user, I want conflicts classified by **Conflict Level** (Candidate×Candidate, new×Accepted, new×Rejection-Guardrail, Accepted×Accepted), so that handling matches the stakes.
31. As a user, I want an L4 conflict (Accepted × Accepted) to trigger **Iteration** rather than a local Probe fix, so that a contradiction between two established beliefs reopens the right phase.
32. As a user, I want Iteration to reopen the most upstream Modeling Activity whose output the L4 invalidates, so that the root is re-examined, not just the symptom.
33. As a user, I want Socrates to propose which phase Iteration reopens and let me confirm, so that I retain control over phase-level rework.
34. As a user, I want an Accepted Proposition to **Degrade** back to Candidate when a later Scenario breaks it, so that the Model never freezes on a belief that turned out wrong.
35. As a user, I want my explicit **Satisfaction** to terminate the work, so that I — not an automated judgment — decide when the Model is complete enough.
36. As a user, I want Socrates to be quiet by default and only notify me on unavoidable conflicts and Supersede cascades, so that I am interrupted only when it matters.
37. As a user, I want every model-changing step written to a persistent store, so that my Model survives across phases, subagents, and sessions without depending on conversation memory.
38. As a user, I want the exploration depth to scale with how under-mapped my domain is, so that sparse early domains get generous exploration and mature ones run lean.
39. As a user, I want the final deliverable to be a Conceptual Domain Model — a Glossary, a Structure, and conceptual Rules — so that I can hand it to downstream requirements work.
40. As a user, I want Socrates to use one consistent ubiquitous language throughout, so that terms are never overloaded across the session.
41. As a user, I want to be able to resume a paused session later, so that long modeling efforts span multiple sittings.

## Implementation Decisions

- **Built on `deepagents` v0.7.** The harness wraps the library's factory (`create_deep_agent`), using its core agent loop, virtual filesystem, subagent spawning, interrupts, and harness-profile registration as primitives. Socrates adds the maieutic discipline; it does not re-implement the agent runtime.
- **One subagent per Modeling Activity** (Requirements, Domain Modeling, Behavioral Specification), each with its own harness profile — a tailored system prompt and tool subset reflecting that activity's posture (elicitor / bounder / behavior-specifier). Spawned via the library's subagent middleware.
- **Models live in the virtual filesystem, not in conversation** (ADR-0001). The Model is the shared state of the pipeline: every model-changing step ends by writing it; every phase begins by loading the relevant parts. This is the only seam through which isolated subagents share state. Conversation is ephemeral transport.
- **The maieutic loop.** Within a pass: `Reconciliation` → `Assertion Tests` → collect `Conflicts` into a `Batch` → `Probe`. Passes repeat until `Satisfaction`. An `Opening` seeds the first pass.
- **Reconciliation precedes Assertion Tests** (from the second pass on). It cross-references the user's latest answers against the existing Model and surfaces latent conflicts (L2/L3) before any Scenario is generated — so scenario generation is never spent on already-contradicted material.
- **Assertion Tests generate Scenarios** — several per Proposition, Need-relevant (Relevance Filter), probing edges and intersections. They surface Elasticity limits and, via intersection Scenarios, the only source of L4 (Accepted × Accepted) conflicts.
- **Probes are interrupt-gated** (human-in-the-loop), using the library's interrupt mechanism. Every Proposition-resolution and phase-level decision is a human checkpoint. (ADR-0002)
- **No automated grader.** The harness never scores the Model's correctness and never auto-declares it done. A single Inference pass ends by the agent loop's natural termination (which delimits a Batch); the overall Mapping ends at the user's Satisfaction. (ADR-0002)
- **Proposition lifecycle is a state machine.** States: `Candidate` → `Accepted`; plus `Rejected` (feeding the Rejection Guardrail). Transitions: `Accept` (user signal, direct or indirect), `Degrade` (Accepted → Candidate, reversible), `Supersede` (displace an Accepted Proposition; cascades via Degrade to indirectly-accepted dependents, user notified not asked). Acceptance is the user's signal, not a guarantee of Scenario survival.
- **Conflict-Level routing.** L1 (Candidate×Candidate) resolves in-line via Probe. L2 (new×Accepted) escalates and may Supersede. L3 (new×Rejection-Guardrail) is blocked/flagged. L4 (Accepted×Accepted) is handed to Iteration, not Probe-resolved. The level is determined by the lifecycle state of the parties.
- **Iteration reopens the most upstream Modeling Activity** whose output an L4 invalidates (entity contradiction → Domain Modeling; behavior → Behavioral Specification; Need-assumption → Requirements). The harness proposes the phase; the user confirms.
- **Deferral.** Any surfaced conflict may be deferred. Re-raise is event-driven (new information touching the deferred conflict's Propositions), plus a criticality-weighted, non-blocking warning at Satisfaction.
- **Coverage-driven exploration budget** (ADR-0004). The per-pass recursion limit is a function of Coverage — generous when Coverage is low (sparse, early), lean when high (mature). Anchored by the Relevance Filter so generous early budgets explore Need-relevant ground, not drift. It is an exploration allowance, never a quality signal (consistent with ADR-0002). The chosen limit must be explicitly propagated to subagents (deepagents issue #1698 — subagents otherwise silently fall back to a recursion limit of 25).
- **Notification policy: quiet by default.** The harness interrupts the user only for unavoidable conflicts (cannot be deferred, block progress) and Supersede cascades removing interdependent Propositions. Routine Probes and Interviews are not notifications. Delivery channels (push, email, in-app) are an implementation detail.
- **MVP is forward-only.** Assertion Tests run against Scenarios and other Propositions; reverse-engineering from a codebase (via ast-grep, rg, fd, LSP) is explicitly deferred past the MVP.
- **Deliverable composition.** The Conceptual Domain Model is composed of a Glossary (terms and definitions), a Structure (entities, characteristics, relationships, cardinality), and conceptual Rules (behavior governing how entities relate). The concrete file layout that holds these is discovered when the harness produces its first real Model.

## Testing Decisions

- **One seam: the session orchestration, with the model provider stubbed.** The model provider (LLM) is treated as an external dependency on the boundary. Tests drive the harness through Opening → Reconciliation → Assertion Tests → Probe using scripted model outputs and assert the harness's *external behavior* — never the LLM's internals and never the Model's "quality" (which ADR-0002 reserves for human judgment).
- **What makes a good test here.** A good test asserts observable state and persisted artifacts given scripted inputs: which lifecycle state a Proposition reached, how a conflict was routed by level, what was written to the virtual filesystem, which recursion limit Coverage selected. It does not peek into how a Scenario was generated or how the LLM phrased a question.
- **Behaviors covered through this seam.** Lifecycle transitions (Candidate→Accepted, Rejected→Guardrail, Supersede cascade via Degrade with notification); Conflict-Level routing (L1 in-line, L2 escalate+Supersede, L4→Iteration); Reconciliation-before-batch ordering and that L4 only emerges from the Assertion-Test arm; FS persistence on every model-changing step and re-load on phase entry; Coverage-driven recursion-limit selection and subagent propagation; Deferral re-raise on touch and the non-blocking Satisfaction warning.
- **Modules tested.** The orchestration layer and its deterministic components — the Proposition lifecycle state machine, the Conflict-Level router, the Supersede cascade, the Reconciliation ordering, the Coverage→budget selector, the FS persistence adapter, the Deferral tracker. All exercised through the single orchestration seam, not in separate test harnesses.
- **Prior art.** None in-repo (greenfield). The stubbed-model-provider approach mirrors how agent libraries test orchestration: fix the model's responses, assert the surrounding logic.
- **Out of this seam (eval, not tests).** Real-LLM runs that judge reasoning quality, Scenario usefulness, or Interview clarity are evaluation, not deterministic tests. They are observed through the actual Models produced and adjudicated by humans, per ADR-0002.

## Out of Scope

- **Reverse / codebase Assertion Testing.** Stressing Propositions against an existing codebase (ast-grep, rg, fd, LSP) is deferred past the MVP — forward flow only.
- **Functional and non-functional requirements specification.** Downstream of the Conceptual Domain Model; Socrates stops at the conceptual level. "The system shall..." requirements are out.
- **Automated grading / eval loop for Model quality.** Deliberately excluded (ADR-0002) — ground truth lives with the user.
- **Specific Notification delivery channels.** Push, email, in-app are implementation details, not modeled.
- **Concrete file layout of the produced Model.** Discovered when the harness produces its first real Model; not prescribed upfront.
- **Multi-context (CONTEXT-MAP) support.** Single-context MVP; one Model per session.
- **Matt Pocock triage/agent execution flow beyond publishing this spec.** Triage and agent pickup of the resulting issues are separate workflows.

## Further Notes

- **Authoritative sources.** `CONTEXT.md` (the domain glossary, ~41 terms) and `docs/adr/0001–0004` are the source of truth this spec operationalizes. Where this spec and the glossary disagree, the glossary wins; raise the conflict via `/domain-modeling`.
- **Feedback loop.** Building the harness and producing the first real Conceptual Domain Model will refine the domain model itself — especially the deliverable's file layout and any fine behavior the practice reveals. Treat the first real Model as a test of the model.
- **Two-level discipline.** While building, keep Socrates's *own* design (this repo's `CONTEXT.md` + ADRs) separate from the *Subject Domain Model* Socrates produces at runtime. Conflating them is the classic mistake.
- **Known landmine.** deepagents issue #1698: subagents silently fall back to a recursion limit of 25 when a custom limit is not propagated. Because each Modeling Activity runs as a subagent doing long-reasoning work, the Coverage-driven per-pass limit must be explicitly propagated, or passes will truncate silently.
- **deepagents version pin.** Target `deepagents` v0.7, which is described as a leaner, more configurable, more token-efficient base harness — aligning with the maieutic, interrupt-driven design.
