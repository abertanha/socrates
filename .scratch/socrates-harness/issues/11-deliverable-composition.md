# 11 — Deliverable: Conceptual Domain Model as Glossary + Structure + Rules

**What to build:** At Satisfaction, the persisted Model is materialized in its composed form as the user-facing Conceptual Domain Model — a Glossary (terms and definitions), a Structure (entities, characteristics, relationships, cardinality), and conceptual Rules (behavior governing how entities relate). The deliverable respects Implementation-Independence (structure in, specifics out). The concrete file layout is discovered here from the first real Model produced.

**Blocked by:** 08 — Deferral (capstone, once the core maieutic machinery is complete).

**Status:** done

- [x] At Satisfaction, the persisted Model is presented as three composed parts: Glossary, Structure, and conceptual Rules.
- [x] The deliverable respects Implementation-Independence (structure in; technologies and concrete parameter values out).
- [x] The concrete file layout is settled against the first real Model produced.

## Comments

- Settled layout: `/model/deliverable/glossary.md`, `structure.md`, `rules.md`. `DeliverableComposer` materializes on affirmative Satisfaction from Accepted Propositions (requirements + definitional domain_modeling → Glossary; remaining domain_modeling → Structure; behavioral_specification → Rules), filtering technology specifics and concrete parameter values. Orchestration coverage: `tests/test_deliverable_composition.py`.
