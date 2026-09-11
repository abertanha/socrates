# 25 — Real-session validation of the fresh-context audit

**Specs:** `.scratch/deliverable-audit/spec.md`

**What to build:** The acceptance seam exercised for real. One conversational session is run with the updated skill — a real model, a real domain, the user's own moves, Opening through Satisfaction — and the session's record answers two questions. Did the audit fire as designed at materialization: a sub-agent spawned with exactly the Model record and the deliverable files in its input, and nothing of the conversation? And did it hold: every accepted Proposition traceable to a home, every asserted entity and relationship explicit in the structure — or, where the audit found otherwise, the fix landed before the session stopped, in domain terms, with no machinery reaching what the user read. Running the session is the user's move; the analysis of the transcript and the living files can be agent-assisted (the established pattern: transcript database plus the session's files). The outcome — session date, runtime, what the audit caught or passed — is recorded here.

**Blocked by:** 24 — Fresh-context deliverable audit at materialization (the instruction must exist in the skill before a session can exercise it); 27 — The fixed charge and the bounded re-audit (the session must exercise the final instrument, not v1).

**Status:** ready-for-agent

- [ ] One full session with the updated skill runs Opening → chapters → tail → Satisfaction and materializes with the audit step executed
- [ ] The transcript shows the auditor received only the Model record and the deliverable files — no conversation content reached it
- [ ] Coverage held in the shipped deliverable: every accepted Proposition traceable, asserted entities and relationships explicit (or the audit's findings were fixed before stopping)
- [ ] Nothing of the audit's machinery appeared in what the user read
- [ ] Outcome recorded here: session date, runtime, what the audit caught or passed

## Comments

### 2026-09-11 — mid-cycle evidence: retro-exercise of the audit (not the full acceptance)

The user ran a controlled retro-exercise in the same 2026-09-10 session
("Starting Socrates 2"): the conductor was told to undo its manual fix
and redo the process under the updated skill. Transcript evidence:

- The conductor read the updated skill through the symlinked OpenCode
  copy, identified the deliverable-audit change, and connected it to the
  Parte case unprompted.
- It spawned a read-only audit sub-agent with a charter faithful to the
  skill: fresh reader (no conversation context, stated deliberate), the
  Model record plus the deliverable files, Presence + Structural
  explicitness, the Implementation-Independence modulo, findings named
  by model identifier with home/HOMELESS and IMPLICIT-ONLY/
  MISSING-CARDINALITY categories, never grade/propose. It even hardened
  the prompt against instructions inside the audited files.
- Findings: THREE implicit-only relationships, not one — Ação→Parte
  (the known case) plus Fonte Jurídica→Hierarquia (n:1) and
  Administrador→Fonte Jurídica (1:n), both previously unnoticed. All
  three were presence-passing (content lived inside concept
  descriptions/glossary) — a presence-only charter would have returned
  zero findings, confirming the to-spec ruling on charter breadth.
- The conductor re-derived the affected structure rows (citing the
  ground in each note), aligned the derived diagram, and reported in
  domain terms. The Model record's mtime is untouched (2026-09-10
  13:47); the audit report was not persisted; no machinery leaked
  beyond the user's own framing.

This is NOT the ticket's acceptance: the session was already closed —
the audit ran retro, at the user's request, not at Satisfaction inside a
full Opening→Satisfaction walk. The full session remains required.
Watch-items it surfaced for that run: (a) in a virgin session the final
report must stay purely in domain terms (here the user invoked the
machinery framing first, which the talking rules allow); (b) the
re-derived rows cite model identifiers (D1, TAIL-2, R9) in the
structure's notes — decide whether identifier traceability in the
artifact is wanted or is machinery leakage; (c) the conductor sensibly
included a derived diagram in the audit scope marked "not required" —
cannot arise in a clean session, noted for completeness.

### 2026-09-11 — second specimen: exhaustive independent sweep (fresh-context, clause-level)

A second fresh-context auditor (different runtime/model, same charter plus
an exhaustive-walk demand: every accepted entry traced individually) swept
the same artifacts after the retro-fix. 61 entries walked (34 accepted
propositions + 27 survived scenarios): all traced to a home in substance,
0 fully homeless, 0 missing-cardinality — but:

- **1 IMPLICIT-ONLY the in-session auditor missed**: TICKET ↔ SESSÃO
  (gating/billing) — same class as the Parte case; lives only in prose
  (glossary "gates entry", R-METER-1), absent from the relationship
  inventory and the rendering. The in-session audit's structural sweep
  had a false negative (caught 3 of 4+).
- **1 charter-level gap**: B6's Sessão lifecycle (archive/reactivate)
  lives only in the rendering — which the charter does not count as a
  home.
- **8 clause-level gaps** beyond the charter's "in substance" bar
  (R5 pt-BR language; R2-refinement demand-back; R3 format-reopen;
  R1 hierarchy member enumerations; R9-refinement provenance; R6 LGPD
  naming; R7 authenticate; B6 lifecycle) — several are
  Implementation-Independence-adjacent (authenticate, LGPD): ruling
  needed on whether they are gaps or legitimate exclusions.
- **5 rendering divergences** (state characteristics only in the UML;
  inverse edge; refinement-feed modeled differently; concrete 1..5
  scale) plus 2 incidental defects ("Plataform" typo; duplicated table
  header).

Implications recorded for the real run: (1) an LLM audit pass is itself
lossy — one implicit-only relationship survived it; (2) the charter's
"in substance" presence bar lets clause-level content drop silently.
Candidate spec deltas (NOT decided): exhaustive clause-level walk as the
audit's demanded method; one re-audit after re-derivation. Fixing the
artifacts is the session conductor's move, not this ticket's.

### 2026-09-11 (afternoon) — third specimen: retro under the v2 skill, instrument left on the table

The user re-ran the retro-exercise in the same session after v2
(tickets 26–27) landed on disk via the symlink (fixed charge committed
14:04, review-fixed 14:15; the exercise ran 14:40–14:58). Transcript
evidence:

- **Two audit passes, correct loop shape.** Pass 1 (14:40): 7 findings —
  4 clause-level presence gaps (R5 pt-BR language, R3 format-reopen,
  R7 authentication, R9 provenance) + 3 structure↔chart inequalities
  (PROCESSO→AÇÃO implicit in the chart; Sessão lifecycle only in the
  chart; user→evaluation-history only in the structure). Conductor
  re-derived citing ground; pass 2 (14:50) re-audited and found 2
  residual rendering mismatches (fechada state, Ticket validade); fixed;
  no third audit — the "exactly one, without a loop" discipline held.
- **Outcome vs the exhaustive sweep:** the sharpened targets were hit —
  clause-level gaps v1 could not see (4 of the sweep's 8), the
  lifecycle-lives-only-in-a-rendering gap (B6 now homed in structure),
  both-direction rendering consistency, identifier citations in
  re-derived rows, hierarchy member enumerations in the table. Model
  record untouched; no report persisted.
- **But the instrument was improvised, again — three audits, three
  different prompts.** Pass 1's charge was the 10:44 v1-era text reused
  nearly verbatim from conversation memory (the session compacted at
  14:55; the skill was never re-read in the window); pass 2 was a third
  variant — better than pass 1's (clause-level, both-way consistency),
  which is itself the argument for fixed text: improvisation varies in
  quality run to run. None matched the fenced charge, on disk 36
  minutes before the first call.
- **Consequence — the inference rule's exact target survived again:**
  TICKET ↔ SESSÃO still ships with no relationship row. The glossary
  says the Ticket "gates *entry* into metered work" and R-METER-1 says
  "the paywall and the meter gate entry" — functional grammar, two
  concepts, no inventory row. The v1-era charge pass 1 reused carries
  no grammar list and did not demand it.
- Not caught (open, minor): R2-refinement demand-back clause; R6 LGPD
  regime naming; the duplicated "Level | Level" table header and
  "Plataform" typo (copy defects, out of charter by ruling).
- QUESTION category unexercised (R7 was treated as a plain presence
  gap — defensible under the boundary test's staying side).

Read for the real run: this specimen is adversarial to the skill in a
way a virgin session is not — the conductor here worked from a stale
v1-era memory of the charge; a fresh session reads the v2 skill at
spawn. The specimen's value is the confirmation it lends ticket 27's
premise: the fixed charge is load-bearing precisely because a conductor
with an old prompt cached will reuse it. Watch-item for the real
session: verify the handed charge matches the skill's fenced block
verbatim.
