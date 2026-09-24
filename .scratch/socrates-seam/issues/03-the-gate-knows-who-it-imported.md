# 03 — The gate knows who it imported

**Specs:** `.scratch/socrates-seam/spec.md`

**What to build:** The bootstrap gate stops verifying importability and
starts verifying identity. Today any package named `socrates` on the
import path passes, and a stale or foreign engine would enforce a
divergent method in Socrates' name, silently. The package gains an
identity/version marker; after the import succeeds, the gate asserts
that the imported package resolves inside the repository derived from
the skill file's own resolved real location — and a wrong-engine import
is refused with wording distinct from a missing engine (the install
steps are for the absent; the wrong-engine refusal says what happened:
another Socrates answered). The document stops carrying any machine's
absolute path (the skill has already circulated to a third-party
machine where it rots): the repository root and the glossary path are
derived by resolving the skill file's real location, through symlinks —
the same root the gate imports from. No runtime is named anywhere; the
runtime-agnostic pin holds.

**Blocked by:** None — can start immediately.

**Status:** done (2026-09-24)

- [ ] The package exposes an identity/version marker — importable,
      stable, asserted by test
- [ ] After import, the gate's taught check asserts the imported package
      resolves inside the repository derived from the skill file's
      resolved real location
- [ ] A wrong-engine import and a missing engine are distinct failures
      with distinct wording (identity, not installation)
- [ ] The skill derives the repository root AND the glossary path by
      resolving its own real location through symlinks; no absolute path
      to any machine's tree remains in the text
- [ ] The "three directories up" arithmetic is taught against the
      RESOLVED location, robust to the skill file being a symlink
- [ ] No runtime named — mechanism scans hold
- [ ] Flattened-phrase pins for the identity clause and the derivation;
      the removed absolute path stays removed (pin its absence)
- [ ] Full suite green

## Verification

Run the project gate. Demo the slice end-to-end: from the deployed
symlinked skill surface, the gate passes against the clone; with a
decoy `socrates` package ahead on the import path, the gate refuses
with the wrong-engine wording.
