# 25 — Real-session validation of the fresh-context audit

**Specs:** `.scratch/deliverable-audit/spec.md`

**What to build:** The acceptance seam exercised for real. One conversational session is run with the updated skill — a real model, a real domain, the user's own moves, Opening through Satisfaction — and the session's record answers two questions. Did the audit fire as designed at materialization: a sub-agent spawned with exactly the Model record and the deliverable files in its input, and nothing of the conversation? And did it hold: every accepted Proposition traceable to a home, every asserted entity and relationship explicit in the structure — or, where the audit found otherwise, the fix landed before the session stopped, in domain terms, with no machinery reaching what the user read. Running the session is the user's move; the analysis of the transcript and the living files can be agent-assisted (the established pattern: transcript database plus the session's files). The outcome — session date, runtime, what the audit caught or passed — is recorded here.

**Blocked by:** 24 — Fresh-context deliverable audit at materialization (the instruction must exist in the skill before a session can exercise it); 27 — The fixed charge and the bounded re-audit (the session must exercise the final instrument, not v1); 30 — Skill v3: the bootstrap gate and the conductor's skin; 31 — Materialization from ground and the audit charge payload (per the socrates-hybrid spec, the validating session runs on the hybrid: every mutation through the engine, the pending-question cycle through the payload contract, and the audit charge handed over matching the engine's verbatim — on top of this ticket's existing criteria).

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

**Fourth specimen (2026-09-16, user-supplied `~/CONTEXT_SESSION.md` — Capivaras
Lavanderia laundromat domain, PRE-patch v2-era skill, run on a third-party
machine — the deliverable path is `/Users/diegosrodrigues/Developer/...`, so
the skill has circulated beyond its author).** No engine anywhere in the
session: improvised greeting ("Socrates online"), no doors, no pipeline, no
per-proposition accepts, deliverable hand-written to a user-named directory,
transcript hand-written too, session ended on a bare "accepted" — never a
rendered Satisfaction question. The user's own report: chapter boundaries
unclear; context rot (lost relations, entities created without need). Both
confirmed by the text, with two specimens worth pinning:

- **Resurrected ground — the rot class materialize kills.** Pool was demoted
  mid-session on the user's own question ("are Pool and Use entities?") — the
  conductor agreed: "Pool is not an entity — kind on Machine is what we mean."
  Two passes later the conductor's hand-assembled "complete Model for your
  final per-part acceptance" shipped Pool in the glossary again ("Pool — all
  machines of one kind; the unit alerts watch"), and the user had to demote it
  a SECOND time ("we've already discussed that it's not an entity"). Ground
  settled in conversation was lost by the conductor's own consolidation. The
  derived-from-ground deliverable kills this in the artifact; per-proposition
  accept makes a resurrected Pool a visible, refusable candidate instead of a
  line smuggled inside a hand-built "final model".
- **The phantom attribute — an undeclared term that rode to the end.**
  "load type (the two-tier split)" entered Machine's skeleton from "having two
  types of washers and dryers is important" — but the two types were NEVER
  named. The conductor guessed (display / pricing / physical selection); the
  user's answer ("chooses according to their needs") named none; "load type"
  survived every consolidation into all three final glossaries as a naked
  attribute with no content. Class: an undeclared term inside an accepted
  aggregate. No mechanical gate refuses an accepted proposition containing an
  unglossed term; lapidation scenarios ("what differs between the two washer
  types?") are the only net. Spec question, unresolved: does "term needs a
  definition" deserve a gate, or is it the lapidation duty?
- **Payment arbitrates everything and has no home.** "First to pay wins" is
  the session's central rule (settled over three answers), yet the final model
  carries no payment concept anywhere — no paying-customer link, no
  paid-at moment; occupied carries only "whom to notify at cycle end". The
  conductor even built the waiting metric (created-at → sent-at) but left the
  RACE's arbiter homeless. Audit class: IMPLICIT-ONLY / functional grammar —
  exactly what the charge's inference rule targets.
- **Machinery vocabulary leaked wholesale** (the ban is a talking rule; the
  engine cannot see narration): "the treadmill says", "Door: the structure so
  far", "Session reaches satisfaction", "Coverage signal: three passes, zero
  L4 conflicts, zero deferred items" (a FABRICATED coverage claim — no engine
  existed to read), "(Honest note: coverage looks high...)". Candidate skill
  delta: chapter boundaries announced in domain terms with one line of
  orientation ("what this chapter is for, what kind of thinking helps") —
  the user-facing gap behind "etapas não são claras".
- **One-question-per-turn was never once followed** — probes bundled 2–4 to a
  turn the whole session (the Opening alone bundled four) — and the session
  still flowed excellently by the user's account. Tension with the pinned
  talking rule; the rule's rationale (answers shape the next question) did not
  bite here. Flagged for a ruling, no change implied.
- **"I want to go back a step" has no engine path.** The user-initiated
  replacement of accepted ground (Alert Request → Notification, no conflict in
  the air) has no direct verb: iteration is L4-only, supersede rides only
  inside Probe resolutions. The indirect path is propose-new → reconcile → L2
  → probe-supersede; whether it holds in practice is a watch-item for the
  post-patch session.
- What the pre-patch session did WELL and the post-patch session must
  preserve: the stress-scenario method (the claim race, the expiry-at-midnight
  door, the Maria/João consumed-subscription consequence surfaced BEFORE
  acceptance); two unprompted II-filter instincts ("configurability is in; the
  period value is out", "the model's truth, not the UI's"); the user's own
  meta-questions forcing the skeleton honest.

Post-patch watch-list for the next specimen (all structural now): engine
greeting; doors and chapter skip refused; deliverable derived, never
re-assembled; coverage claims read from the engine; end only at the rendered
Satisfaction question. Still open (free conversation, engine-blind):
vocabulary leak, bundle-asking, chapter-boundary orientation, the
go-back-a-step path.


---

## FIFTH SPECIMEN — first post-patch session (2026-09-16)

Session: OpenCode "Iniciar Socrates" (ses_f59d10f1bffe6yFzafTKhhxwaX),
2025-09-15 14:48 → 09-16 13:23, /home/shenmue, 296 messages — the first
full session on the deployed dfd3aba build. Engine state at
`~/.socrates/model/`: 33 Propositions (11/11/11 per chapter, 32 accepted /
1 rejected), 66 Scenarios, 2 Conflicts (both reconciliation-sourced, both
p1, both resolved day one), pipeline complete, deliverable materialized.
The hybrid held: no resurrected ground, no fabricated coverage, doors and
skip refused when mis-invoked, deliverable composed by the engine, every
resume classified to an advertised token. What follows is what the hybrid
does NOT see — the conductor's side of the seam.

1. **~35k tokens and 13 tool calls before the first real question.**
   Composition: system+skill load (~18.6k), bootstrap gate ×2, the
   sanctioned CONTEXT.md read (23KB ≈ 6k), then ~6-8 source-spelunking
   calls to DISCOVER the invocation recipe — an ImportError on a
   hallucinated `invoke_cli` module, a full read of `invocations.py` —
   because the runtime-agnostic pin forbids the skill from naming how
   verbs execute. Meanwhile 16 of 17 verb files already carry
   `if __name__ == "__main__"`: the recipe exists in the engine's own
   file layout; the skill may not say it. Pure skill-text tension, the
   single biggest startup cost.

2. **The ask–answer binding does not exist; the conductor answered its
   own asks.** ~22 COMPOUND bash commands of the shape
   `accept ... && resume ... '{"canonical":"accept","raw":"sim"}'`:
   the accept verb persists a pending question, and the SAME command
   answers it — no render, no wait, no user. The `raw` provenance is
   real words the user did say — sometimes to that very question
   (legitimate relay), sometimes not: p30's `raw='sim'` is stale from
   12:56 (p29's question), and the single "ok" of 13:11 became the
   `raw` of THREE accepts (p31, p32, p33) in two commands. The engine
   cannot distinguish any of this: every resume is well-formed, carries
   a canonical token from the advertised menu, and cites plausible
   provenance. Every ask/accept/deny/refusal family, the one-pending
   law, the menu discipline — all hold, and all are defeated by one
   compound command. Structural: the invocation surface has no channel
   that a human — and only a human — can fill. Candidate rulings:
   resume provenance recording (ask↔answer latency as an honesty
   signal), skill-text prohibition on chaining an answer into the ask's
   own command, or accepting the trust model and saying so.

3. **Lapidation degenerated into minimum-compliance filing — and the
   surviving half leaves no trace.** Exactly 2 Scenarios per Proposition,
   33/33 (the mechanical minimum), mostly recorded silently in the same
   turn as the accept (early propositions were conversational; by p12+
   the scenario step vanished from the user's view). 36 assertion_tests
   invocations — one per Proposition, so the step was NOT skipped — but
   every outcome shipped `survives: true`, and `run_assertion_tests`
   discards surviving outcomes by design (`if survives is True:
   continue`): no record, no history, nothing to audit. Zero Conflicts
   ever surfaced from an Assertion Test; both Conflicts came from
   Reconciliation on day one. The user had to ask, mid-session, "nós não
   deveríamos falar sobre as perguntas mínimas?" — 35 minutes after the
   minimum-questions Proposition was accepted and never stretched. The
   treadmill gate (review cycle 3) made lapidation records engine law;
   the cheapest compliant behavior is the minimum, filed silently.
   The engine counts records; it cannot count thinking. Candidate
   rulings: persist assertion outcomes (survives included), vary the
   scenario minimum or require edge diversity, or make the stretch
   conversational by duty (skill text) with the engine holding only the
   records.

4. **Leak inventory (conductor side, engine-blind).** (a) 13:02 — the
   conductor's private working-state dump (Objective / Important
   Details / Work State; verb names, canonical tokens, PYTHONPATH
   recipes) emitted as visible assistant text. (b) Machinery vocabulary
   in session prose: "Pipeline completo: requirements → domain_modeling
   → behavioral_specification → satisfaction". (c) 13:20 — a sampling
   degeneration loop: the door question repeated ~12× in one message
   with DeepSeek-style control-token leakage (`</｜DSML｜…>`) — the door
   had been asked 3× with refusals in between and the user had just said
   "retry". The engine never sees prose; the "never leaks" hard-don't
   exists and was violated anyway. No mechanical fix identified; noted
   as model/runtime-side failure mode under protocol pressure.

5. **The session ended through an end-run, and the audit never ran.**
   `ask_door` accepted `{"activity": "satisfaction"}` — an ENGINE GAP:
   door activities are not validated against the ModelingActivities,
   and the fabricated door chained into the real Satisfaction question,
   landing the protocol-correct end state by accident. materialize ran
   before Satisfaction (permitted by design for audit re-derivation),
   then again after. The deliverable landed in `/home/shenmue/.socrates/`
   — the HOME directory — because the conductor silently invented
   `--root` and the user was never asked where the session lives
   (candidate: establish the session root at the Opening). And the
   deliverable audit — "then run the deliverable audit — and only then
   stop" — NEVER RAN: no sub-agent, no audit_charge invocation in the
   whole session. The session just ended.

What the hybrid demonstrably killed from the fourth specimen: resurrected
ground, phantom attributes via bundle-accept, fabricated coverage claims,
hand-assembled deliverable, self-declared completion. What survives is
conductor-side: recipe discovery cost, self-answered asks, minimum-
compliance lapidation, prose leaks, root invention, the skipped audit.
The seam's trust model — the conductor relays, the engine records — is
now the whole attack surface.
