---
Status: ready-for-agent
Feature: deliverable-audit
---

# Spec: Deliverable audit v2 — the sharpened charter (socrates skill)

> **Amendments (v2, 2026-09-11):** v1 of this spec shipped the audit
> (tickets 24–25) and its first two real exercises validated the design —
> and exposed the audit's own limits. This revision rewrites the charter
> on six axes and closes one open ruling; everything else carries
> forward. v1 is preserved in git history.

## Problem Statement

The deliverable audit works: its first real exercise caught the known failure plus two unnoticed relationships of the same class. But the second, exhaustive exercise — an independent fresh-context sweep of the same artifacts — exposed limits in the instrument itself. A relationship of exactly the failure class the audit exists for survived it, because the ground words it as function ("consumes for access and metering", "the billable unit") rather than as linkage, and the auditor only looked for linkage. The charter's presence bar — "traceable in substance" per proposition — let eight clauses vanish silently: every accepted entry was "homed" while individual assertions inside them (a product language, a demand-back guarantee, a hierarchy's member enumerations) were simply gone. A lifecycle existed only inside a derived diagram, and nothing checked it, because the charter says a rendering is never a home but says nothing about looking there. The conductor's fixes landed unaudited — yet re-derivation is the same lossy authorship the audit exists to catch. The charge itself was improvised per run: good, but different every time. And the Implementation-Independence filter, clear at artifact level, goes ambiguous at clause level — is "users authenticate" a gap or an exclusion? — and every ambiguity resolved itself in silence.

## Solution

The charter sharpens on six axes, and one ruling closes. Presence becomes an exhaustive walk at assertion granularity: each accepted Proposition decomposes into the assertions it makes, and each assertion traces to a home individually — a proposition whose substance survives but whose clause does not is a finding. Structural explicitness gains the inference rule: wherever the ground says one concept conditions, gates, meters, defines, produces, contains, or derives from another — any functional grammar between two concepts — that is a relationship demanding an inventory row with its cardinality; the audit no longer waits for relationship-shaped words. Derived renderings living in the deliverable (diagrams and the like) are consistency-checked in both directions: nothing may live only in a rendering, and the rendering must reflect the structure's inventory — while never being a home. After the conductor re-derives, exactly one bounded re-audit checks the touched entries — the cure is held to the same test as the disease, without a loop. The auditor's charge becomes fixed text carried inside the skill — the same instrument in every runtime, with the injection-hardening baked in — and the fallback pass runs the same text. The filter gains its clause-level boundary test: obligations and constraints of the product in the domain's own terms stay (conformity to a data-protection regime, the product's language, the billable unit); the mechanisms implementing them go (authentication flows, storage, delivery); and when the auditor is unsure, the finding ships as a question — never a silent pass. And by ruling, re-derived rows cite their ground identifiers: every shipped line traces back to the Model record, entry by entry.

## User Stories

1. As a user, I want every clause of everything I accepted to reach the deliverable, so that a proposition cannot "arrive" while half its content silently does not.
2. As a user, I want relationships found even when the ground words them as function rather than linkage, so that a gating or metering link cannot hide the way the party link once did.
3. As a user, I want nothing living only in a derived rendering, so that a diagram cannot quietly become the sole home of something we agreed.
4. As a user, I want the rendering to reflect the structure's inventory, so that the two never diverge silently.
5. As a user, I want the conductor's fixes re-checked before the session stops, so that the cure is held to the same test as the disease.
6. As a user, I want the same audit instrument in every runtime, so that where I run the session does not change what the audit catches.
7. As a user, I want the filter's exclusions decided by a stated boundary rather than per-case judgment, so that a clause like an authentication duty or a data-protection obligation is neither silently dropped nor silently kept.
8. As a user, I want the auditor's uncertainty surfaced as a question, never passed in silence, so that ambiguity costs one exchange rather than a lost clause.
9. As a user, I want every re-derived line to cite the ground it comes from, so that the shipped artifact traces back to what we agreed, entry by entry.
10. As a user, I want the re-audit bounded to one pass over what changed, so that closing the session does not spiral.
11. As the conductor, I want the charge as fixed text I hand to the sub-agent verbatim, so that I cannot blunt the instrument while improvising it.
12. As the conductor, I want the injection-hardening inside the fixed charge, so that instructions inside the audited files cannot steer the audit.
13. As the conductor, I want the report to carry a question category, so that the auditor's doubt reaches me as a finding rather than a feeling.
14. As the conductor, I want the fallback pass to run the same fixed charge, so that a runtime without sub-agents gets the same text in a weaker context, not a different instrument.
15. As the auditor, I want the walk defined at assertion granularity, so that my report's unit matches the granularity at which content is actually lost.
16. As the auditor, I want the pair-grammar rule named in my charge, so that inferring a relationship is a duty, not a liberty I might decline.
17. As the auditor, I want the rendering's status stated — never a home, always consistency-checked — so that I treat derived files correctly without guessing.
18. As the maintainer, I want the sharpened charter pinned beside the v1 pins, so that the sharpening cannot silently regress.
19. As the maintainer, I want the skill to remain one self-contained file, so that deployment stays a symlink.
20. As the maintainer, I want the carried limits — never judges, never proposes, never reopens, never blocks, never persisted — re-pinned, so that v2's sharpening does not erode v1's boundaries.

## Implementation Decisions

- The artifact is unchanged from v1: the conversational skill file alone — its audit subsection rewrites. No runtime code, no harness surface. (Standing scope ruling.)
- **Presence at assertion granularity:** the walk decomposes each accepted Proposition into the assertions it makes and traces each one; a finding names the assertion, not just the proposition. "Traceable in substance" at proposition level is retired as the bar.
- **The inference rule for explicitness:** any functional grammar between two concepts in the accepted ground — one conditions, gates, meters, defines, produces, contains, or derives from the other — asserts a relationship; the inventory must carry it with the cardinality the ground states.
- **Renderings, both directions:** anything in the deliverable directory that is not one of the three canonical files is a derived rendering — checked for content found only there (a finding) and for divergence from the structure's inventory (a finding); never counted as a home.
- **One bounded re-audit:** after re-derivation, a fresh auditor re-checks exactly the touched entries, once; the skill's text replaces v1's "no re-audit" with this single bounded pass.
- **The fixed charge, inline:** the skill carries verbatim the text to hand the auditor — read-only; the two artifact sets (the Model record; the deliverable directory, renderings included for consistency only); the two checks at their sharpened granularity; the filter with its boundary test; the report format (identifier, assertion, home or HOMELESS, IMPLICIT-ONLY, MISSING-CARDINALITY, QUESTION); the injection-hardening line; the never-judge, never-propose, never-reopen limits. The skill stays one self-contained file — the charge lives inside it. (User ruling.)
- **The filter's clause-level boundary:** obligations and constraints of the product, stated in the domain's own terms, belong (conformity to a named legal regime, the product's language, what is billable); the mechanisms and technologies implementing them do not (authentication flows, storage forms, delivery channels). Unsure is never silent: it ships as a QUESTION finding.
- **Identifier traceability in the artifact** (user ruling, previously open): re-derived rows cite the ground identifiers in their notes — the deliverable's audience is the user who lived the session, and every shipped line traces to the Model record.
- Carried from v1 unchanged: the audit gates the stop; findings re-derive the artifact while the ground stands; the report is information, never a block; the audit's vocabulary never reaches the user; rejected ground and deferred Conflicts are not the audit's business; the report is never persisted; the spawn is runtime-agnostic; a clean audit ends the session exactly as before; the same-context fallback runs where no sub-agent exists.

## Testing Decisions

- The pin extends in place — same file, same tradition as the prompt-retirement pins and the v1 audit pins. New assertions hold: the assertion-granular presence language; the inference rule's grammar list; both-direction rendering consistency with the never-a-home status; the one bounded re-audit replacing no-re-audit; the fixed charge's presence as a block, with its injection-hardening line and the QUESTION category; the filter's boundary test and the no-silence rule; the identifier-citation instruction; and the carried v1 limits, re-pinned so the rewrite cannot erode them.
- Good tests stay external: they read the skill artifact and assert the binding phrases and their placement, never implementation detail beneath.
- The acceptance seam stays the real conversational session (the validation ticket) — one full walk exercising the sharpened charter end to end.

## Out of Scope

- The runtime — runner, harness, conduction, composer: standing ruling; construction already guarantees there what this spec audits.
- Copy-defect detection (misspellings, formatting): the audit covers ground, not prose quality.
- Multi-auditor or cross-model double audits: the evidence supports one bounded re-audit instead; revisit only if the real session shows the re-audit still leaking.
- Auditing artifacts outside the deliverable directory (working notes, session scratch).
- Persisting audit reports; audit-on-resume; bilingual vocabulary.

## Further Notes

- Evidence lineage: two specimens, both recorded in the validation ticket's comments — (1) the controlled retro-exercise (the conductor undid its manual fix and re-ran under the updated skill: the audit fired faithfully and caught three implicit-only relationships); (2) the exhaustive independent sweep (fresh context, different runtime, assertion-granular walk: 61 entries traced, zero fully homeless, zero missing cardinality — but one implicit-only relationship surviving the first audit, eight clause-level gaps under the "in substance" bar, and a lifecycle living only in a rendering).
- Sequencing: implement this revision before the validation session runs, so the real session exercises the final instrument; the validation ticket's criteria carry over unchanged.
- The v1-to-v2 deltas in one line each: presence by assertion; inference rule; rendering consistency both ways; one bounded re-audit; the fixed charge inline; the filter's clause boundary with no silence; identifier citations ruled in.
