# to-spec brief — deliverable-audit

## Input (what produced this spec)

The 2026-09-10 analysis of the second conversational session (OpenCode
"Starting Socrates 2", run with the `/socrates` skill), requested by the user
after they caught the deliverable gap themselves:

- Recorded ground was faithful — the identity-by-parties Proposition family
  accepted and refined in the session's living Model; the glossary carried it.
- The structure file dropped the action→party relationship: the party concept
  shipped as a textual attribute of the action, no relationship row, no
  cardinality — despite the skill demanding "relationships, cardinality" in
  the structure deliverable.
- The gap surfaced only at the user's manual audit of a Mermaid diagram
  derived post-session; the fix landed outside the session.
- Responsibility ruling from the analysis: the skill-as-harness — it prescribes
  the artifact's shape but leaves materialization as free-form one-shot
  authorship, with no derivation discipline and no verification. The model's
  session conduct was faithful; the Python harness was not running and is
  structurally immune to the drop half (verbatim derivation).

The user then proposed the fix this spec captures: a context-free sub-agent
auditing the deliverable against the session's recorded ground.

## Open decisions closed during to-spec (user rulings)

1. **Scope: the conversational skill only.** The runtime project (runner,
   first real-model session, harness composer) is explicitly out — separate
   track, unchanged priorities.
2. **Seams: pin test + real session.** A pytest pinning the audit instruction
   in the skill file (prior art: the prompt-retirement pins) plus acceptance
   via one real conversational session with transcript verification.
3. **Charter breadth: presence + structural explicitness.** Presence-only
   would have passed the very failure that motivated this spec (the
   Proposition was present in the glossary; the relationship row was the
   missing piece). The two-check charter closes that.
4. **Fallback without a sub-agent tool: weaker same-context pass.** The
   conductor runs the same charter reading only the two artifacts — weaker
   guarantee, but the checklist still forces the sweep; the instruction marks
   it as fallback.

## Carried constraints (from the house)

- ADR-0002 alignment: the audit is information, never a block; no automated
  grader — the charter is coverage of recorded ground, not quality judgment.
- The skill's talking rules govern everything user-facing: findings in the
  domain's terms, no machinery vocabulary.
- Derived-not-persisted family: the audit report itself is never written to
  the session's files.
- The skill stays one self-contained file (symlink deployment to other
  runtimes must keep working), runtime-agnostic in its phrasing.
