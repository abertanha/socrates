---
Status: ready-for-agent
Feature: deliverable-audit
---

# Spec: Deliverable audit — a fresh-context auditor at materialization (socrates skill)

## Problem Statement

When the session reaches the user's affirmative Satisfaction, the conversational skill materializes the Conceptual Domain Model by hand: the conductor, holding the whole interview in context, authors the three deliverable files from the recorded Model. That authorship is lossy — and the session proved it. The recorded ground was perfect (the identity-by-parties Proposition family, accepted and refined); the glossary carried it faithfully; yet the structure file dropped the action→party relationship entirely, rendering the party concept as a textual attribute of the action instead of an explicit relationship with its cardinality. The omission surfaced only when the user, hours later, manually audited a diagram derived from the deliverable. Nothing stood between the recorded ground and the shipped files to check that everything agreed actually made it in: the conductor's memory of the discussion masks the page's silence, because author and artifact share one context.

## Solution

At materialization — after the three deliverable files are written, before the session stops — the skill opens a sub-agent with no access to the conversation and hands it exactly two things: the session's living Model record and the deliverable files. The auditor is charged with one coverage check, nothing else: everything the accepted ground asserts is explicitly rendered in the deliverable. Each accepted Proposition must be traceable to a home; every entity and relationship the accepted ground asserts must be explicit in the structure — an asserted relationship never ships only as an attribute inside another concept's description, and cardinality appears where the ground states it. The check respects the Implementation-Independence filter (what it excludes is not missing) and covers accepted ground only — rejected candidates and the Rejection Guardrail are the Model's negative space, not omissions; deferred Conflicts remain the Satisfaction warning's business.

The auditor reports findings as facts with citations; it never grades quality, never proposes anything, never reopens the Model. The report is information, never a block — Satisfaction was already the user's verdict. Where ground is homeless or implicit, the conductor re-derives the affected deliverable file (the ground stands; the artifact is fixed) and states the fix in the domain's own terms. A clean audit closes silently, ending the session exactly as before. Where the runtime offers no sub-agent, the conductor runs the same charter as a dedicated pass reading only those files — a weaker, same-context fallback, but the checklist still forces the sweep.

## User Stories

1. As a user, I want everything we agreed in the interview to actually reach the deliverable, so that what ships is what I accepted — not what the conductor remembered of it.
2. As a user, I want the deliverable checked by a reader with no memory of the conversation, so that nothing hides behind the conductor's familiarity with what was discussed.
3. As a user, I want relationships asserted by accepted ground explicit in the structure with their cardinality, so that a concept never ships as a textual attribute where a relationship belongs.
4. As a user, I want entities asserted by accepted ground present as entities in the structure, so that no concept the Model agreed on arrives undefined or orphaned.
5. As a user, I want the audit to respect the Implementation-Independence filter, so that deliberately excluded material — delivery technologies, concrete parameter values — is not flagged as missing.
6. As a user, I want the audit to cover accepted ground only, so that rejected ideas and the session's negative space are not reported as gaps.
7. As a user, I want deferred Conflicts left to the Satisfaction warning, so that the audit does not duplicate what the warning already carries.
8. As a user, I want the audit to be information and never a block, so that my Satisfaction remains the session's only verdict.
9. As a user, I want gaps found by the audit fixed in the deliverable without reopening the Model, so that my accepted ground and past decisions are never re-made by a check.
10. As a user, I want the findings and their fixes told to me in my domain's terms, so that the audit's machinery never leaks into what I read.
11. As a user, I want a clean audit to close silently, so that a complete session ends exactly as it ends today, with no new noise.
12. As the conductor, I want the auditor spawned with only the files and a fixed charter, so that the conversation's context never reaches it and its reading stays reproducible.
13. As the conductor, I want the auditor's output mapped to Proposition identifiers, so that each finding traces precisely back to the recorded ground it cites.
14. As the conductor, I want a fallback pass when no sub-agent tool exists, so that the audit still runs, weaker, instead of silently disappearing.
15. As the auditor, I want a charter of coverage only, so that I never drift into grading quality, proposing improvements, or interviewing the user.
16. As the auditor, I want the check answerable from the files alone, so that my report is reproducible by anyone reading the same two artifacts.
17. As the maintainer of the skill, I want the audit instruction pinned by a test, so that future edits cannot silently drop or blunt it.
18. As the maintainer of the skill, I want the skill to stay one self-contained file, so that the symlink deployment to other runtimes keeps working unchanged.
19. As the maintainer of the skill, I want the instruction runtime-agnostic, so that the same skill file works wherever it is loaded, whichever sub-agent mechanism that runtime offers.

## Implementation Decisions

- Only the conversational skill document changes — the materialization step inside its Satisfaction section (and, where placement demands, the files section that describes what the session keeps). No runtime code, no harness module, no runner surface: the user's explicit scope ruling. (Confirmed with the user.)
- Timing: once per session, after the three deliverable files are written and before the session stops. No re-audit loop — the conductor fixes what the report names and stops; a re-run happens only if the user asks.
- Spawn, runtime-agnostic: open a sub-agent by whatever task/agent mechanism the runtime offers; the instruction names no specific tool as mandatory. The sub-agent receives exactly the path to the living Model record and the path to the deliverable directory — never the conversation, never the session's context.
- Charter — coverage of accepted ground, modulo the Implementation-Independence filter, in two checks: (1) presence — every accepted Proposition traceable to a home in the glossary, structure, or rules; (2) structural explicitness — every entity the accepted ground asserts present as an entity, and every relationship it asserts explicit in the structure's relationship inventory with cardinality where the ground states it; an asserted relationship never ships only as an attribute inside another concept's description.
- Not in the charter: quality judgment of any kind; proposing new Propositions or edits; reopening chapters or the Model; rejected/candidate propositions; the Rejection Guardrail; deferred Conflicts; anything the Implementation-Independence filter excludes by design.
- Output: a findings list — each accepted Proposition's identifier with its home or a homeless flag, plus asserted-but-implicit structure findings, each citing the ground that asserts it. Facts with citations, never verdicts.
- On findings: the conductor re-derives the affected deliverable file — the Model and its recorded ground stand untouched — then states the fix in the domain's terms and stops. The user-facing surface follows the skill's talking rules: findings phrased in the user's domain language; the audit's own vocabulary never appears.
- The audit report is not persisted to the session's files — it is a derived check, not ground; the conversation record keeps what the user saw.
- Clean audit: no new message; the session ends exactly as the skill ends today.
- Fallback, where the runtime offers no sub-agent: the conductor performs the same charter as a dedicated pass reading only the two artifacts — weaker (the author's context is still present), and the instruction says so. (Confirmed with the user.)

## Testing Decisions

- Good tests assert external behavior only. For an instruction artifact, the external behavior is the text the runtime consumes: the pin test reads the skill file and asserts it carries the audit instruction with each binding limit — the two-check coverage charter (presence and structural explicitness), the Implementation-Independence modulo, accepted-ground-only scope, never grades and never reopens, information never a block, the files-only context-free spawn, the fallback pass, the silent clean ending, and the no-machinery-leak phrasing — and that the instruction sits where the session order puts it, between writing the files and stopping.
- Prior art for the pin: the prompt-retirement tests — a pytest pinning instruction text against drift, one file read, many small assertions. Same family; no new seam beyond it.
- The acceptance seam is the real conversational session: run one session with the updated skill; from the session transcript verify a sub-agent was spawned at materialization with only the two artifacts in its input; from the session's files verify the deliverable's coverage holds against the recorded Model. Prior art: the two conversational session analyses already performed (transcript database plus the session's living files). (Seams confirmed with the user: pin test plus real session.)

## Out of Scope

- The runtime entirely — the runner, the Python harness, its conduction governor, its deliverable composer: there, construction already guarantees what this spec audits (verbatim derivation from the recorded store); the user ruled this spec to the conversational skill alone.
- Relationship-row synthesis or cardinality derivation in the harness deliverable — the deferred deliverable-composition work, its own cycle.
- Auditing artifacts derived after the session ends (diagrams, renderings built post-Satisfaction at the user's request) — they live outside the session's conduction.
- Persisting audit reports, an audit record in the session files, audit-on-resume, and re-audit loops.
- Bilingual answer vocabularies — the standing ruling.

## Further Notes

- Evidence lineage: the second conversational session (2026-09-10, OpenCode, run with the skill) — the recorded Model held the identity-by-parties family perfectly and the glossary carried it; the structure file dropped the action→party relationship (the party concept shipped as a textual attribute), surfaced only by the user's manual audit of a post-session derived diagram, fixed outside the session. The conductor's own admission at the time: "the explicit relationship was dropped in materialization."
- Design rationale: fresh context is the only reader without the author's anchoring mask — the same reason the two-axis review runs its axes in fresh sub-agents. Construction beats audit where construction is possible; this spec exists because the skill's authorship is free-form by nature, and the harness needs no auditor precisely because its composer derives.
- Input brief and open-decision record: the feature's directory in `.scratch/`, alongside this spec.
