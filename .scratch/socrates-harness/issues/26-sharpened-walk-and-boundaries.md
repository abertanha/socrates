# 26 — The sharpened walk and its boundaries (charter v2)

**Specs:** `.scratch/deliverable-audit/spec.md` (v2 — the sharpened charter)

**What to build:** The audit's two checks, rewritten in the skill's instruction at the granularity where content is actually lost. Presence becomes an exhaustive walk by assertion: each accepted Proposition is decomposed into the assertions it makes, and each assertion traces to a home individually — a proposition whose substance survives while one of its clauses does not is a finding, named by the assertion, not the proposition. Structural explicitness gains the inference rule: wherever the accepted ground says one concept conditions, gates, meters, defines, produces, contains, or derives from another — any functional grammar between two concepts, not only relationship-shaped words — that asserts a relationship, and the structure's inventory must carry it with the cardinality the ground states. The boundaries sharpen with it: anything in the deliverable directory that is not one of the three canonical files is a derived rendering — checked in both directions (nothing may live only in a rendering; the rendering must reflect the inventory) while never counting as a home; and the Implementation-Independence filter gains its clause-level boundary test — obligations and constraints of the product in the domain's own terms stay (conformity to a named legal regime, the product's language, what is billable), the mechanisms implementing them go (authentication flows, storage forms, delivery channels) — with the no-silence rule: an auditor unsure between gap and exclusion ships the finding as a QUESTION, never a silent pass. The v1 limits re-pin beside the sharpening: never judges, never proposes, never reopens, information never a block, the report never persisted, the audit's vocabulary never reaching the user. The pin extends in place with assertions holding each new binding phrase.

**Blocked by:** None — can start immediately.

**Status:** done (2026-09-11)

- [x] Presence in the skill's charter walks by assertion — each accepted Proposition decomposed into its assertions, each traced individually; a finding names the assertion
- [x] The "in substance" per-proposition bar is retired from the instruction (and its retirement pinned)
- [x] Structural explicitness carries the inference rule with its grammar list (conditions, gates, meters, defines, produces, contains, derives)
- [x] Derived renderings are consistency-checked in both directions and pinned as never a home
- [x] The filter's clause-level boundary test is stated in the instruction (domain-termed obligations in; implementing mechanisms out)
- [x] The QUESTION category exists with the no-silence rule — unsure is never a silent pass
- [x] The v1 carried limits are re-pinned (never judges/proposes/reopens, never blocks, never persisted, vocabulary never leaks)
- [x] Full suite green

## Verification

Implemented in 159fa9c: the four charter bullets (Presence at
assertion granularity; Structural explicitness with the inference
rule; Derived renderings both ways never a home; The filter's boundary
with QUESTION/no-silence), all 11 v1 pins kept green through the
rewrite, 5 new pins. Suite 112 → 118 across 26+27.

## Rulings

- **All four checks now live in the auditor's charge, not as
  conductor-facing bullets** — ticket 27 folded them into the fixed
  charge block, since the sub-agent reads only the charge. The charter
  has one home; the prose intro keeps only the handoff and the
  one-charge sentence.
- **Retirement pinned by omission + scope**: "in substance" is absent
  from the audit section (it never literally existed in v1 — the pin
  guards reintroduction of the named bar), scoped to the audit section
  so legitimate figures of speech elsewhere in the skill don't break
  the suite (review fix, daca0d3).
- **Register**: "assertion" (the audit's sub-propositional unit) is
  disambiguated in CONTEXT.md beside **Assertion Test** (the stress
  operation) — the two senses collided (review fix, daca0d3); the
  entry carries the functional-grammar rule.
