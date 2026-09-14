# 30 — Skill v3: the bootstrap gate and the conductor's skin

**Specs:** `.scratch/socrates-hybrid/spec.md`

**What to build:** The skill rewrites as the conductor's skin over the engine. It opens with the bootstrap gate: the conductor verifies, through the harness's own code execution, that the engine is importable from the skill's clone — and where it is not, the skill prints the installation steps and refuses to conduct (no engine, no Socrates). Past the gate, the skill teaches one thing: when to invoke which verb — phrased runtime-agnostically, naming no mechanism, in the pinned tradition. The talking rules carry the language boundary: the session's language is declared once at the Opening; every pending-question payload is rendered to the user in that language; the user's reply is classified into a canonical token with the raw words preserved; between closing a door and satisfaction the conductor asks, never guesses; a refusal from the engine is repaired in conversation, never argued with. The ordering prose of earlier versions is retired — the order of the method lives in the engine's refusals now, and the skill says so nowhere: it stops prescribing sequence entirely. An ADR records the identity ruling — skill-conducted, engine-enforced, host loop, no CLI — so the architecture's why outlives the conversation that decided it. The pins extend in the tradition: the gate present, no runtime mechanism named, the translation and ask-never-guess rules held, and the ordering prose gone by omission.

**Blocked by:** 29 — Invocation files and the JSON contract (the skin instructs verbs that must exist to be called).

**Status:** done

- [x] The bootstrap gate: engine import verified through code execution; on failure, installation steps shown and the session refused
- [x] When-to-invoke-which-verb guidance, runtime-agnostic — no mechanism named anywhere
- [x] The language boundary taught: session language declared at the Opening; payloads rendered in it; replies classified to canonical tokens; raw preserved; ask-never-guess between close and satisfaction
- [x] Ordering prose retired by omission — the skill prescribes no sequence the engine can refuse
- [x] The ADR of the identity ruling written and linked (skill-conducted, engine-enforced, host loop, no CLI)
- [x] Pins: gate present, no mechanism named, translation and ambiguity rules held, ordering prose absent
- [x] Full suite green

## Verification

TDD: `tests/test_skill_v3_skin.py` written first against the seam (the
skill artifact + the ADR, one read, flattened-whitespace phrase pins) —
15 tests, confirmed red (14 failed with no v3 skin, 1 passed: the
mechanism scan against v2, which v3 then had to keep passing against
itself). Green with the rewrite: gate present with teeth ("no engine,
no Socrates", refusal + installation steps returning to the gate via
`pyproject.toml`/import path), all 17 `INVOCATIONS` names taught with
one resume verb and `{canonical, raw}`, pending questions as data with
accepted answers + meanings, the language boundary (declared once at
the Opening, classified into a canonical token, provenance, only
language boundary), ask-never-guess, never improvise the opening,
refusals repaired (admissible next verbs, never argue, never improvise
around), the conductor never edits the session files (`engine writes`,
`.socrates/`), resume reconstructs through the reads (never re-greet),
and the ordering prose retired by omission — the twelve retired phrases
absent and zero numbered lines in the file. The mechanism scan holds
over the whole file including the copied audit section (no runtime
named anywhere).

`tests/test_skill_deliverable_audit.py` kept green verbatim: the audit
section (charge block included) copied unchanged from v2 — the charge's
migration to an engine payload is ticket 31's, not this ticket's — so
the materialization anchor sits before the audit heading, the audit
before "The Model's files", the stop tied to the audit, and exactly one
fenced block. The only v2 words dropped are the ones this ticket
retires: the greeting block (the opening verb owns it), the numbered
walk and the sequence imperatives (the engine's refusals own them), and
the hand-editing guidance (the engine writes, atomically).

Full suite: **203 passed** (was 188; +15 skin pins, zero legacy pins
changed).

## Rulings

- **The head/tail split is load-bearing**: the skin pins scan the text
  before the audit heading (`_head()`), the audit pins own everything
  from it down. The resume-reconstruction rule (never re-greet) failed
  its pin from the tail — the reads paragraph in "The verbs" section
  now carries it, and the "Model's files" section repeats it. Two
  suites, two territories, one file.
- **Ordering retires by omission, not prohibition**: the three
  chapters' voices stay (the conductor needs to know what each chapter
  is *for* to propose well), but the file never states an order — the
  active chapter is "the engine's fact", the rhythm is described as
  what the verbs exist for, and the refusal is the teacher.
- **The mechanism ban binds the whole file, audit section included**:
  v2's audit text was already clean ("whatever agent mechanism your
  runtime offers, none named here"); v3 keeps it that way, so the
  audit stays runtime-agnostic with the skin.
- **Case-sensitive pins, lowercase imperatives**: the tradition's
  phrase pins match case, so the skin states its laws mid-sentence
  ("never improvise the opening", "never argue") rather than as
  sentence-initial prose. The pins teach the prose style.
- **The materialization anchor constrains wrapping**: the audit pin
  indexes the raw text for "materialize the Conceptual Domain Model",
  so the Satisfaction paragraph wraps around the anchor, never inside
  it. Noted for ticket 31, which moves this paragraph's subject to the
  engine's payload.
