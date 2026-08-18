# Socrates

An agent harness, built on the `deepagents` library, specialized for the logical-conceptual, long-reasoning front-end of software development. Its deliverable is a Conceptual Domain Model — entities, relationships, and conceptual rules, well-defined. Functional and non-functional requirements specification is downstream and out of scope. Named for Socratic maieutics — the model is elicited through questioning, not authored top-down.

This glossary describes **modeling itself** — Socrates's own domain. It never describes any one Subject Domain being modeled (that belongs in *that* domain's context). Keeping the two apart is the first discipline of this model.

## Language

### Foundational

**Harness**:
The layer Socrates adds on top of the `deepagents` agent harness — specialized for long-reasoning modeling work, where `deepagents` alone is generic.
_Avoid_: Framework, app, "the deep agents harness" (that is the underlying library)

**Deliberative Task**:
A software-development task whose value lies in sustained reasoning across many inputs — reconciling objectives, needs, and the specificities of a domain — rather than in a mechanical transformation. Defining Socrates's scope: requirements, domain modeling, specification.
_Avoid_: "long task" (long in what?), "hard task" (subjective), "complex task"

**Subject Domain**:
The real-world area the software-under-development addresses. The thing **being** modeled — never modeled in full, only in the relevant cuts.
_Avoid_: "the domain" alone (ambiguous — may mean Socrates's own domain), business

**Model**:
A purpose-bound, selective representation of a slice of the Subject Domain — never the whole truth, only the cut relevant to the software's objective. The primary product of Socrates (a glossary, a requirements spec, a behavioral spec, an ADR).
_Avoid_: "the data", schema (implementation), documentation (passive — a Model is *built*, not merely written)

**Conceptual Domain Model**:
The deliverable of Socrates: a Model at the conceptual abstraction level, stated in the ubiquitous language. Composed of three parts — a **Glossary** (the terms and their definitions), a **Structure** (entities, their characteristics, relationships, and cardinality), and **conceptual Rules** (the behavioral rules governing how entities relate). Well-defined enough that functional and non-functional requirements specification can proceed downstream, outside Socrates. Defines the hard edge of Socrates's scope. The concrete file layout holding these parts is implementation, discovered when Socrates is built and produces its first real Model.
_Avoid_: "the ER", data model (implementation), logical/physical model (lower abstraction than Socrates delivers)

**Implementation-Independence**:
The admission test for the Conceptual Domain Model: a Proposition belongs only if it is true independent of any technology choice and logically verifiable by reasoning — never by presupposing or running an implementation. It admits **structure** — entities and their characteristics, relationships between entities including cardinality (e.g. "one Payment yields at least one Notification"), and parameterized rules — but excludes **specifics**: delivery/implementation technologies ("via push", "an n×n relation needs a junction table") and concrete parameter values (see Platform Parameter).
_Avoid_: "abstract" (too vague), "high-level"

**Platform Parameter**:
An admin-configurable value governing a business rule. Its existence and nature — that the rule is parameterized and admin-tunable — belong in the Conceptual Domain Model; its specific value does not. The value is config, not concept. E.g. "the Payment Window is an admin-configurable duration" is in; "120 minutes" is out.
_Avoid_: Constant, setting (implementation)

**Coverage**:
How much of the Need-relevant domain the Model currently accounts for — sparse early (many omissions, ambiguities, open Candidates), denser as Propositions settle and Conflicts resolve. A gradient, never a terminal "complete." The inverse driver of how much exploration a pass warrants: low Coverage → a generous exploration budget; high Coverage → a lean one (see ADR-0004). Read pass-over-pass from declining signals, e.g. Conflicts surfaced per pass.
_Avoid_: Completeness (implies an end state), progress %, done-ness

**Mapping**:
The operation that produces a Model by crossing the Need, the structure, and the behavior of a Subject Domain. Spans the three Modeling Activities. Not a single pass — it is iterated, the Model tightening toward Assertiveness and Ubiquitous Language until the user signals Satisfaction. Its completed result is the Model.
_Avoid_: "the documentation process", analysis (too passive)

**Satisfaction**:
The user's signal that the Model is complete enough — the termination condition for Iteration. Until Satisfaction, Mapping keeps exposing and resolving Conflicts; the loop has no other built-in end.
_Avoid_: "done" (vague), approval, sign-off (bureaucratic)

### The modeling pipeline

**Modeling Activity**:
One of three deliberative activities, in logical order — Requirements → Domain Modeling → Behavioral Specification. Each produces a Model of a different nature: the need, the structure, the behavior. Precedence is linear; execution is not (see Iteration).
_Avoid_: "project phase", step

**Requirements**:
The first Modeling Activity: define the Need the application exists to satisfy, and from it derive what every later Model must include and exclude.
_Avoid_: "what the client wants", features (those are solutions, not the need)

**Need**:
The underlying problem the application exists to solve. Defined first because it is the Relevance Filter for every later Model — it decides which slice of reality belongs in the model and what is out of scope.
_Avoid_: Feature, requirement (a requirement *serves* the Need; not the same), wish

**Relevance Filter**:
The principle, anchored in the Need, that a Model contains only the slice of reality relevant to the software's objective — and nothing beyond. Established in Requirements, applied in every later Model.
_Avoid_: Scope (UI/managerial), filter

**Domain Modeling**:
The second Modeling Activity: bound the Subject Domain and establish its ubiquitous language and entities — *what the domain is*, within the limits fixed by the Need.
_Avoid_: "data modeling", ER (that is behavior/implementation-leaning)

**Behavioral Specification**:
The third Modeling Activity: infer the *conceptual* behavior and relationships between domain entities such that, together, they satisfy the Need — *what the domain does*, stated as domain rules, not as functional requirements. Bounded to the conceptual level: "the system shall..." functional and non-functional requirements are downstream and out of scope.
_Avoid_: "the logic", business rules (too vague), algorithm, functional requirements ("the system shall...")

### The maieutic method

**Maieutics**:
The method that governs Socrates: the Model is *given birth to* through questioning that exposes contradictions and forces sharper definition, not authored top-down. Practiced through Interviews.
_Avoid_: "conversational AI" (generic), chatbot

**Inference Engine**:
The agent that drives each pass. It first Reconciles the latest ingest against the current Model, then performs Assertion Tests over Scenarios, collecting the Conflicts both yield. Runs to exhaust its inference capacity before gathering results; the Assertion Tests' output forms one Batch of Conflicts. Feeds the Probe.
_Avoid_: "the AI", validator (too narrow), linter

**Reconciliation**:
The first operation of an Inference pass (meaningful once the Model has grown past the Opening): cross-reference the ingest the user just provided to resolve the prior Batch's Conflicts against the existing Model, to surface **latent** Conflicts — contradictions, contrarieties, or ambiguities that the new information exposes in what was already Accepted. Presented to the user and resolved before Assertion Tests run, so scenario generation is not spent on material already directly contradicted. The longer the Mapping runs, the more it matters: accumulating ingests increasingly risk contradicting earlier ones.
_Avoid_: Consistency check (too QA-flavored), cross-validation (statistics), merge

**Batch**:
The set of Conflicts one Inference Engine pass yields, presented to the user together to resolve. The unit of a single Probe engagement: the agent exhausts its pass, collects the Batch, and the user clarifies every Conflict in it before the next pass runs — not one conflict at a time.
_Avoid_: Queue, list (too passive)

**Interview**:
A short, agent-initiated, targeted exchange with the user, run to drive Propositions toward assertiveness and ubiquitous language. Opens with broad questions, then recurs in Probes driven by the Batches of Conflicts the Inference Engine surfaces.
_Avoid_: Dialogue (too free-form), FAQ, "system questions"

**Opening**:
The initial phase of an Interview: broad questions that establish context — the Need, the session's objective, and what the user seeks to model. Run once at the start; not conflict-driven, it seeds the first Inference Engine pass.
_Avoid_: Onboarding, questionnaire

**Probe**:
The recurring phase of an Interview: the user resolves Conflicts the Inference Engine has surfaced — whether the latent ones from Reconciliation or the ones in an Assertion-Test Batch. Resolving a Conflict can reveal new ground, so each Probe both de-conflicts and grows the Model, and that grown Model is what the next Inference pass works on. The elenchus that refutes and reshapes loose Propositions. Repeats until Satisfaction.
_Avoid_: Follow-up (too generic), interrogation

**Proposition**:
A candidate statement in a Model — a term definition, a boundary, a behavior rule — that is plastic, not final: reshaped under Assertion Tests and Probes toward Assertiveness.
_Avoid_: "the text", note

**Elasticity**:
How far a Proposition's explanatory scope stretches across Need-relevant Scenarios before it breaks into a Conflict. Every Proposition eventually breaks on some scenario — the project only requires it survive the Need-relevant ones. What an Assertion Test measures.
_Avoid_: Flexibility (vague), robustness (implies unbreakable)

**Plasticity**:
A Proposition's capacity to be reshaped — its statement reformed so its Elasticity changes — when an Assertion Test shows it breaks before covering a Need. The remedy: measure with Elasticity, fix with Plasticity. The goal is to mold each Proposition until its Elasticity covers every explicit Need (Assertiveness); bursting beyond the Needs is expected.
_Avoid_: Malleability (near-synonym), flexibility (vague)

**Scenario**:
A concrete situation, generated from the current Model and kept relevant by the Relevance Filter, constructed to stretch a Proposition toward its Elasticity limit. The agent plays it out and asks whether the Proposition survives; if not, the Scenario has surfaced a Conflict. A Proposition is stressed by several Scenarios together — their set evidences its Plasticity. Valuable Scenarios probe Need-relevant edges (zero, one, many, none, intersections), not comfortable middles.
_Avoid_: Fixture (the outcome is unknown — that's the point), use case (edges toward functional requirements, out of scope), example (too passive)

**Assertion Test**:
The act the Inference Engine performs: stress a Proposition for soundness — across several Scenarios, against other Propositions, or (post-MVP) against the codebase — to find where its Elasticity runs out. Its output is a Conflict, or none.
_Avoid_: "validation" (vague), unit test (implementation)

**Assertiveness**:
The target quality of a Proposition: its Elasticity covers every explicit Need (it survives all Need-relevant Scenarios), it is de-conflicted, and stated precisely. A target an Accepted Proposition approaches — not a precondition for Acceptance.
_Avoid_: "being right" (absolutist)

**Ubiquitous Language**:
The target quality of the Model's vocabulary: one unambiguous term per concept, shared by all parties.
_Avoid_: Glossary (that is the *medium*, not the quality), nomenclature

**Conflict**:
A flaw surfaced by Reconciliation or an Assertion Test, that a Probe then works to resolve. Four kinds: a **contradiction** — two Propositions cannot both hold; an **omission** — the Model is silent where a Scenario demands it speak; a **contrariety** — a Proposition holds but yields an undesired or counter-intuitive outcome under a Scenario; an **ambiguity** — a Proposition is unclear or multi-meaning relative to the rest of the Model, under-specified rather than broken (surfaced especially by Reconciliation). Encompasses limits.
_Avoid_: Bug, error

**Conflict Level**:
The severity of a Conflict, set by what is conflicting with what — chiefly the lifecycle state of the parties (Candidate vs Accepted vs Rejection Guardrail). Determines handling: conflicts among unconsolidated Propositions resolve in-line through a Probe; conflicts that touch an Accepted Proposition escalate and may Supersede it; conflicts between two Accepted Propositions are handed to Iteration rather than resolved by a Probe. The deeper the parties are consolidated, the higher the level and the heavier the handling.
Detection tracks the Inference-pass arm: **Reconciliation** (new × Model) can only surface conflicts the ingest introduces — a new Proposition vs an Accepted one (L2) or vs the Rejection Guardrail (L3) — never two Accepted Propositions, since one side is always new. **Assertion Tests** surface conflicts *latent within* the consolidated Model — including two Accepted Propositions a Scenario exercising both reveals to be incompatible (L4). An L4 is therefore never introduced by a single ingest; it is exposed when both established Propositions are stressed together.
_Avoid_: Priority, severity (too generic)

**Deferral**:
Parking a surfaced Conflict to resolve later rather than now — the user's choice when a conflict need not block the current pass. Orthogonal to how a conflict is resolved (Probe vs. Iteration): any conflict, any level, may be deferred. Deferring never blocks the current pass: a deferred Reconciliation Conflict releases the new Proposition it had quarantined, so Scenario generation may proceed on that ground while the Conflict stays parked. Deferred conflicts are tracked and **re-raised when new information touches their Propositions** (an ingest, Scenario, or Proposition that interacts with them — event-driven, not every pass), and surfaced as a **criticality-weighted warning at Satisfaction** rather than a hard block, so the user may still close the Model with conflicts open (per ADR-0002/0003). The harness recommends against deferring when a conflict is **critical** — high Conflict Level or touching central Propositions — judging operational blocking-ness for progress, never correctness.
_Avoid_: Ignore, skip (a deferred conflict is not dropped — it returns)

**Iteration**:
The process that removes strict linearity from the pipeline: an L4 conflict (Accepted × Accepted) reopens a prior Modeling Activity. Which phase: the most upstream whose output the conflict invalidates — entity contradictions point to Domain Modeling, behavioral ones to Behavioral Specification, a conflict that invalidates a Need assumption goes all the way to Requirements. The harness proposes the phase; the user confirms. Triggered only by L4 — L1/L2 are Probe-resolved, not Iteration. Driven by the agent loop; surfaced to the user through Interviews.
_Avoid_: Rework (carries a penalty connotation the model rejects), loop (implementation)

### Proposition lifecycle

**Candidate**:
A Proposition past the immediate-conflict triage — it contradicts, contraries, or ambiguifies nothing already in the Model on first pass — now queued for Scenario evaluation and the user's Acceptance. The default state of a freshly proposed Proposition that survives triage; ambiguity sends it to clarification, not rejection.
_Avoid_: Draft, pending (too generic)

**Accepted**:
A Proposition the user has accepted into the Model — directly (express satisfaction with it) or indirectly (entailed by another Accepted Proposition). Scenario survival is **evidence the user weighs, not a gate**: the user may accept a Proposition that Scenarios have not yet exhausted. An Accepted Proposition should approach Assertiveness but may Degrade. Indirectly accepted Propositions are marked as such and remain eligible for Scenarios.
_Avoid_: Approved, final (implies frozen), "asserted" (collides with Assertiveness)

**Rejected**:
A Proposition removed from consideration, with an explicit reason that is always kept. Feeds the Rejection Guardrail.
_Avoid_: Deleted, discarded (the reason must survive)

**Rejection Guardrail**:
The accumulated set of Rejected Propositions with their reasons, used to stop the same rejected idea re-entering and to keep future Propositions consistent with past decisions — the Model's negative space.
_Avoid_: Blacklist, rules

**Degradation**:
The reverse of Acceptance: an Accepted Proposition returns to Candidate when a later Scenario (often from ground a prior Probe revealed) breaks it. Reversible by design, on plausible justification — so the Model never freezes and Satisfaction is always provisional.
_Avoid_: Rollback, demotion (carries a penalty connotation)

**Supersede**:
To displace an Accepted Proposition with newer information that conflicts with it — the user's resolution when new info contradicts something consolidated. The displaced Proposition leaves the Model, recorded with the reason it was overtaken (distinct from a Rejected Candidate, which never entered); the new information enters the Candidate queue for validation. The displacement **cascades automatically via Degradation**: every Proposition Accepted indirectly via the superseded one loses its foundation and is Degraded back to Candidate for re-evaluation. The user is notified of the cascade, not asked.
_Avoid_: Replace (too generic), overwrite, swap

### Notifications

**Notification**:
The mechanism that interrupts the user for events demanding attention outside the normal Interview flow. Socrates is quiet by default — routine Probes and Interviews are not Notifications. Two triggers only: an **unavoidable Conflict** (one that cannot be Deferred and blocks all progress until resolved), and a supersede-cascade about to remove interdependent Propositions (destructive — the user must see it, though not approve it). Delivery channels (push, email, in-app) are implementation, not part of the term.
_Avoid_: Push, email, alert, toast (delivery channels — implementation)
