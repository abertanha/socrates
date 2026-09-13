---
Status: ready-for-agent
Feature: socrates-hybrid
---

# Spec: The skill that invokes the engine (socrates-hybrid)

## Problem Statement

The conversational skill conducts real sessions, and its audit catches real
losses — but every guarantee it carries is requested of the model, never
imposed. The evidence is on record: a conductor re-ran the deliverable audit
from stale memory and reused an improvised charge while the fixed one sat on
disk (third specimen); free-form file editing churned and corrupted session
artifacts before self-repairing (second session); door and Satisfaction
answers route through fuzzy wording. Meanwhile the repo carries a complete
deterministic engine — reconciliation gates, conflict levels, batches, doors,
treadmill, satisfaction warning — pinned by the whole test suite, that has
never driven a real session. The user runs Socrates inside agent harnesses
(Claude Code, OpenCode, Cursor, and the like) and wants both worlds as one
thing: the skill as conductor and voice, the engine as the always-present
enforcer of the method — invoked through the harness's own code execution —
with no CLI product and no separate runtime to operate.

## Solution

The skill becomes the caller of the engine. Every state mutation in a
session — the Need and its amendments, propositions and their lifecycle,
reconciliation, scenarios, assertion tests, batches and probes, iteration,
doors, satisfaction, materialization, the audit — goes through small Python
invocation files that live beside the engine inside the skill's own clone,
run by the conductor with whatever code-execution mechanism its runtime
offers (none named in the skill). Invocation files take JSON in and return
JSON out. When the engine needs a human decision it does not block: it
returns a pending-question payload — the question, the accepted canonical
answers, their meanings — and records the marker in the session state; the
conductor renders the question in the session's language, classifies the
user's reply into a canonical token (the raw words preserved), and resumes on
the next invocation. Wrong order is refused by the engine, and a refusal is
information the conductor repairs. Materialization is composed from the
recorded ground; the fixed audit charge is delivered by the engine as a
payload; the auditor is spawned through the host's sub-agent mechanism. Where
the engine is not importable, the skill is a bootstrap — installation
instructions, not a session. Socrates stays language-agnostic with pt-BR as
its first availability: canonical English enums inside, the conductor as the
only language boundary.

## User Stories

1. As a user, I want the method's rules enforced by the engine rather than
   remembered by the model, so that a session cannot drift out of the
   Socrates method even when the model improvises.
2. As a user, I want every session artifact written atomically by the
   engine, so that a model's clumsy edit can never churn or corrupt the
   record.
3. As a user, I want the deliverable composed from the recorded ground by
   the engine, so that nothing accepted can silently vanish from the shipped
   files — the dropped-relationship class dies by construction.
4. As a user, I want the audit instrument identical in every session and
   runtime, so that what the audit catches does not depend on the conductor's
   memory of it.
5. As a user, I want exactly one bounded re-audit after fixes, so that the
   cure is held to the test of the disease without spiraling.
6. As a user, I want the skill to refuse conducting when the engine is
   absent, so that "Socrates" always means the engine-backed session.
7. As a user, I want to run my session in my language (pt-BR first), so that
   I model my domain without translating myself.
8. As a user, I want the door question, the Satisfaction warning, and every
   harness question rendered in my language, so that my decisions are made
   on meaning, not on translation guessing.
9. As a user, I want my exact words preserved beside every canonical answer
   the state machine recorded, so that nothing I said is lost to routing.
10. As a user, I want the session resumable from the state files alone, so
    that a closed terminal or a crashed runtime never ends a modeling
    session.
11. As a user, I want chapter precedence, doors, and the treadmill enforced
    by refusals I can see answered, so that the session's shape is the
    method's shape.
12. As a user, I want deferred Conflicts to ride to the honest Satisfaction
    warning exactly as before, so that the hybrid strengthens the method
    without changing its promises.
13. As the conductor, I want each invocation to return a structured payload
    telling me what happened and what may come next, so that I always know
    what to say and what to call.
14. As the conductor, I want the pending-question payload to list the
    accepted canonical answers with their meanings, so that I can render
    them faithfully and classify the reply without inventing options.
15. As the conductor, I want a structured rule for door ambiguity — between
    closing and satisfaction, ask, never guess — so that a consequential
    misroute is impossible.
16. As the conductor, I want refusals as structured information with the
    reason and the admissible next verbs, so that I repair my conduct
    instead of improvising around it.
17. As the conductor, I want the invocation files runnable by whatever code
    execution my runtime offers, so that Socrates works in Claude Code,
    OpenCode, Cursor, and the rest alike, none named in the skill.
18. As the conductor, I want the ordering prose retired from the skill, so
    that the skill shrinks to the persona, the talking rules, and when to
    invoke which verb — the order itself lives in the engine's refusals.
19. As the auditor, I want the charge as a self-contained payload from the
    engine — checks, filter boundary, hardening, report format — so that I
    audit with the exact instrument every time.
20. As the maintainer, I want the engine's semantics unchanged, so that the
    hybrid adds an invocation surface without rewriting the method its tests
    already pin.
21. As the maintainer, I want the invocation files thin — parse, call the
    engine, serialize — so that no policy lives outside the engine.
22. As the maintainer, I want the AskHuman contract pinned end-to-end at the
    invocation seam, so that pending markers, payloads, resumes, and
    refusals cannot silently regress.
23. As the maintainer, I want pins on the skill's text — the bootstrap gate,
    the runtime-agnostic invocation phrasing, the translation and ambiguity
    rules, the retired ordering prose — in the established tradition.
24. As the maintainer, I want pins on the engine-delivered charge, so that
    the v2 charter survives its migration from file to payload whole.
25. As the maintainer, I want the deployment story to stay a clone or
    symlink of one directory, so that installing the skill installs the
    engine with it.

## Implementation Decisions

- **No CLI, no MCP** (user ruling): invocation files are run by the host's
  code execution as `python3` plus a file — no console-script packaging, no
  server transport. The skill's phrasing stays runtime-agnostic, in the
  pinned tradition of naming no mechanism.
- **The engine lives in the skill's clone** (user ruling): the deployed
  skill directory contains the skill text, the engine, and the invocation
  files together; deployment is a clone or symlink of that directory. The
  bootstrap gate verifies the harness's `python3` can import the engine from
  there and, failing that, the skill prints installation steps and refuses
  to conduct.
- **The AskHuman protocol** replaces the engine's mid-method interrupts: an
  asking verb returns a pending-question payload (`question`,
  `accepted_answers` with `meanings`, and the resume contract) and persists
  a pending marker in the session state; exactly one question is pending at
  a time (the one-question-per-turn ruling); the resume arrives on the next
  invocation as `{canonical, raw}` — the canonical token drives the machine,
  the raw words ride as provenance; an invalid or non-canonical token is a
  structured refusal the conductor repairs.
- **The language boundary** (user ruling, language-agnostic with pt-BR
  first): canonical English enums stay closed inside the engine; the session
  language is declared once at the Opening and recorded in the session meta;
  the conductor renders payload questions in the session language and
  classifies free replies into canonical tokens; free-text fields
  (statements, summaries, the Need) carry the user's language as data, never
  as control.
- **Verb surface**: one invocation file per engine mutation plus read verbs
  (status of the pipeline, the pass, the pending question), mirroring the
  session-tool surface the engine already exposes — opening, Need and
  amendments, propose/accept/reject, reconcile, scenarios, assertion tests,
  probe batch and resume, iteration, defer, door, satisfaction,
  materialization, audit charge. Granularity stays one-to-one with engine
  mutations; no orchestration lives in the files.
- **Ordering by refusal**: the ordering prose retires from the skill; the
  verbs refuse wrong order (Reconciliation before scenarios from pass 2, the
  door before the next chapter, guardrail blocks, treadmill), and each
  refusal names the reason and the admissible next verbs.
- **Materialization and the audit**: the deliverable is composed by the
  engine from the recorded ground (verbatim derivation, identifier
  citations); the fixed charge — the v2 charter semantics verbatim — is
  returned by the audit-charge invocation; the auditor is spawned through
  the host's sub-agent mechanism; the one bounded re-audit and the
  never-persisted report ride as the skill's process rules, exactly as v2
  settled them.
- **The skill text rewrites** as the conductor's skin: bootstrap gate,
  when-to-invoke-which-verb, the talking rules, the translation boundary,
  the ask-never-guess rule. The one-self-contained-file constraint of v1/v2
  is superseded: the unit of deployment is now the directory.
- **An ADR records the identity ruling** — skill-conducted, engine-enforced,
  host loop, no CLI — so the architecture's why outlives this conversation.
- The standalone deepagents session layer (its own system-prompt loop and
  guard) is superseded as the product surface; its removal is a separate
  cleanup, out of scope here. deepagents remains the machinery inside the
  package (state backend, protocol).
- Carried unchanged: ADR-0001 (state in files, derived never persisted —
  the pending marker included), ADR-0002 (information never blocks; the
  audit and every warning included), ADR-0005's spirit inverted to its
  purest form — the harness conducts through the engine, the model asks.

## Testing Decisions

- Good tests are external: they call the invocation files' entry functions
  in-process with argv and a temporary working directory, and assert on the
  JSON returned — never on engine internals. This is the highest seam that
  stays fast (user ruling).
- The AskHuman contract is tested end-to-end at that seam: pending marker
  and payload shape; resume with `{canonical, raw}`; invalid token refused;
  one pending question at a time; door ambiguity surfaced as
  ask-never-guess.
- The engine's existing suite stays green — semantics unchanged except the
  interrupt plumbing.
- The pin tradition extends: a pin file holds the skill's v3 text (bootstrap
  gate present, no runtime mechanism named, translation and ambiguity rules,
  ordering prose retired by omission) and the engine-delivered charge
  (flattened-whitespace phrase assertions, as the v1/v2 pins did against the
  file).
- Prior art: the deliverable-audit pin suite, the prompt-retirement pins,
  and the engine's fake-backend unit tradition.
- The acceptance seam is one real conversational session through the hybrid
  in a host harness — transcript and artifacts analyzed against the
  criteria the validation ticket carries (re-pointed to this spec).

## Out of Scope

- CLI console-scripts, MCP servers, and package-distribution surfaces — the
  invocation files are the only transport (user ruling).
- The standalone session loop as a product surface (REPL dead); deleting
  the superseded layer is a follow-up cleanup ticket.
- Automated grading of any kind — the audit's information never blocks;
  copy-defect detection stays out, as v2 ruled.
- Persisting audit reports; audit-on-resume.
- Languages beyond the mechanism plus pt-BR availability (the mechanism is
  language-agnostic; each availability is content, not code).
- The runtime harness itself (BYOK models, hosting, billing).

## Further Notes

- Evidence lineage: the three recorded specimens — the dropped relationship
  (lossy free-form materialization), the exhaustive sweep (clause-level
  gaps under a per-proposition bar), and the improvised charge with the
  fixed one on disk (conductor memory beats file when the file isn't read).
- Migration map: the v2 charter and fixed charge move from the skill file to
  the engine payload whole; the talking rules stay as the skill's skin; the
  pins move with them.
- The validation ticket (real-session audit validation) is re-pointed to
  this spec's acceptance seam; its criteria carry over, plus the hybrid's
  own: the conductor invoked the engine for every mutation, the pending
  question cycle ran through the payload contract, and the audit charge
  handed over matches the engine's verbatim.
- Until the hybrid lands, the soft skill remains the live Socrates; the v2
  work is not wasted — it is the instrument this spec installs behind the
  engine.
