<p align="center">
  <img src="assets/socrates-banner.png" alt="Socrates" width="600">
</p>

# Socrates

A maieutic agent harness for conceptual domain modeling, built on the LangChain [`deepagents`](https://github.com/langchain-ai/deepagents) library.

Socrates elicits a **Conceptual Domain Model** — a glossary, an entity structure, and conceptual rules — through questioning rather than top-down authoring. Named for Socratic maieutics: the model is *given birth to* through questions that expose contradictions and force sharper definition.

Its scope is the logical-conceptual, long-reasoning front-end of software development — requirements, domain modeling, behavioral specification. Functional and non-functional requirements ("the system shall…") are downstream and out of scope.

## How a session works

A Socrates session is a conducted interview with a fixed shape:

1. **Opening** — the agent elicits the **Need**: the underlying problem the
   software exists to solve. The Need is the relevance filter for everything
   that follows.
2. **Three chapters**, walked in precedence — **Requirements** (bound the
   Need), **Domain Modeling** (the ubiquitous language and entities — what
   the domain *is*), **Behavioral Specification** (conceptual rules — what
   the domain *does*). Each chapter closes at a **door** the user answers:
   close, not yet, or route to Satisfaction.
3. Inside a chapter the rhythm is: **propose** a candidate statement
   (a Proposition), **lapidate** it — stretch it with Scenarios and record
   where it breaks as Assertion Tests — and **resolve** the Conflicts that
   surface, gathered into Batches the user answers together (Probes).
4. After the third door, passes continue over the whole Model until the
   user's affirmative **Satisfaction** — the session's only end. The engine
   then **materializes** the deliverable and a memory-less auditor re-checks
   it against the recorded ground.

The method is deliberately reversible: acceptance can degrade, displaced
Propositions cascade their dependents back to candidates, deferred Conflicts
re-raise when touched. Nothing freezes before Satisfaction, and Satisfaction
itself stays provisional.

## The architecture: the skill conducts, the engine enforces

Two parties, one seam (`docs/adr/0006-skill-conducts-engine-enforces.md`):

- **The engine** (this repository, `src/socrates/`) is the session's memory
  and its law. Every fact — the Need, Propositions, Scenarios, Conflicts,
  doors, the deliverable — lives under `.socrates/` in the working
  directory, written atomically by the engine and by no one else. The
  method's order lives there too: a verb invoked out of its moment is
  **refused with a structured payload** naming the reason and the admissible
  next verbs. The order is enforced by the machine, never merely requested
  of the model.
- **The conductor** (the agent skill) is the session's voice. It renders
  every question in the user's language, classifies free replies into the
  engine's canonical tokens with the raw words preserved as provenance, and
  never lets the machinery leak into the conversation. Sessions run in
  whatever language the user is already speaking.

Before a session's first question, a **bootstrap gate** verifies through
code execution that the engine imports — and that it is *this* repository's
engine (identity marker, resolved path, and version, not just a package
name). No engine, no Socrates: the gate refuses to conduct rather than
improvise a session in Socrates' name.

## The deliverable

Satisfaction composes the Conceptual Domain Model under
`.socrates/model/deliverable/`:

| File | Content |
| --- | --- |
| `glossary.md` | The Need and its accepted Propositions (Requirements ground) |
| `structure.md` | Entities, characteristics, relationships, cardinality (Domain Modeling ground) |
| `rules.md` | Conceptual behavioral rules (Behavioral Specification ground) |

Every row ships the accepted statement verbatim, citing the ground entry it
derives from, filtered by implementation-independence: structure and
parameterized rules in; delivery technologies and concrete parameter values
out ("admin-configurable duration" is in; "120 minutes" is out). A fixed
audit charge — the same in every runtime — hands the deliverable and the
Model record to a fresh, memory-less reader; its report is information,
never a block.

## Installation

Requires Python ≥ 3.12.

```bash
git clone https://github.com/abertanha/socrates.git
cd socrates
pip install -e .          # or: pip install -e '.[dev]' for the test suite
```

Alternatively, point your import path at the repository's `src/` directory.

## Running a session

Socrates runs as an **agent skill** — the conductor half. The skill lives at
`.claude/skills/socrates/` and deploys to any runtime that executes code and
follows a skill file (Claude Code natively; other runtimes via a symlink or
copy of `SKILL.md`).

1. Install the skill in your runtime and open a session with your agent:
   *"run a Socrates session"* or *"model this domain with Socrates"*.
2. Agree with the agent where the session's record lands — the working
   directory's `.socrates/` is the default it will offer.
3. Answer in your own words. The agent asks one question at a time; every
   answer is classified into the engine's record with your raw words
   preserved beside it.
4. The session ends only when you say it does — and even then the engine
   shows you an honest warning (deferred conflicts, self-answered
   questions, unreadable-log markers) before accepting your Satisfaction.

## The engine's verbs

The verbs are programs in `src/socrates/invocations/` — executed with the
session's `--root` and a JSON payload, answering as JSON data. The skill
never reads engine source to learn them; each file is the whole recipe.

| Verb | Moment |
| --- | --- |
| `opening` | Once, before anything — elicits the Need |
| `propose` | An answer has distilled into a candidate worth testing |
| `scenarios` / `assertion_tests` | Lapidating a candidate toward its edges |
| `reconcile` | New ground crossed against the accepted Model |
| `probe` | Open Conflicts gathered into one Batch for the user |
| `accept` / `reject` | The user's explicit signal about a candidate |
| `defer` | The user parks a Conflict — parked, not dropped |
| `iteration` | An Accepted × Accepted Conflict reopens a chapter |
| `amend_need` | The conversation reshapes what they are building |
| `door` | A chapter looks quiet — the user closes it or not |
| `satisfaction` | The session's only end, with its honest warning |
| `materialize` | Compose (or re-derive) the deliverable from recorded ground |
| `audit_charge` | The auditor's fixed charge, verbatim |
| `resume` | Answer to whatever question is pending |
| `pipeline_status` / `current_pass` / `pending_question` | Reads, for orientation |

## Development

```bash
python -m pytest tests/ -q
```

Layout: `src/socrates/` (the engine — state, conduction, inference), 
`src/socrates/invocations/` (the verb programs), `tests/` (the suite,
including an adversarial layer that keeps the fifth review's destruction
conditions strung), `CONTEXT.md` (the domain glossary — Socrates's own
domain), `docs/adr/` (architectural decisions).

State is a filesystem model (`docs/adr/0001-models-as-filesystem-state.md`):
the session's `.socrates/` tree is the single source of truth, and derived
conclusions are the engine's recomputation, never stored entries.

## Status

v0.1.0 — pre-1.0. The engine's verb surface and the session file layout may
still shift. The full glossary of the method (Proposition, Elasticity,
Treadmill, Door, Quiet, Conflict levels, and the rest) is `CONTEXT.md`.
