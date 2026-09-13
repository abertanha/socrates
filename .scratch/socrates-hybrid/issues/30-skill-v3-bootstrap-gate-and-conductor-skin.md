# 30 — Skill v3: the bootstrap gate and the conductor's skin

**Specs:** `.scratch/socrates-hybrid/spec.md`

**What to build:** The skill rewrites as the conductor's skin over the engine. It opens with the bootstrap gate: the conductor verifies, through the harness's own code execution, that the engine is importable from the skill's clone — and where it is not, the skill prints the installation steps and refuses to conduct (no engine, no Socrates). Past the gate, the skill teaches one thing: when to invoke which verb — phrased runtime-agnostically, naming no mechanism, in the pinned tradition. The talking rules carry the language boundary: the session's language is declared once at the Opening; every pending-question payload is rendered to the user in that language; the user's reply is classified into a canonical token with the raw words preserved; between closing a door and satisfaction the conductor asks, never guesses; a refusal from the engine is repaired in conversation, never argued with. The ordering prose of earlier versions is retired — the order of the method lives in the engine's refusals now, and the skill says so nowhere: it stops prescribing sequence entirely. An ADR records the identity ruling — skill-conducted, engine-enforced, host loop, no CLI — so the architecture's why outlives the conversation that decided it. The pins extend in the tradition: the gate present, no runtime mechanism named, the translation and ask-never-guess rules held, and the ordering prose gone by omission.

**Blocked by:** 29 — Invocation files and the JSON contract (the skin instructs verbs that must exist to be called).

**Status:** ready-for-agent

- [ ] The bootstrap gate: engine import verified through code execution; on failure, installation steps shown and the session refused
- [ ] When-to-invoke-which-verb guidance, runtime-agnostic — no mechanism named anywhere
- [ ] The language boundary taught: session language declared at the Opening; payloads rendered in it; replies classified to canonical tokens; raw preserved; ask-never-guess between close and satisfaction
- [ ] Ordering prose retired by omission — the skill prescribes no sequence the engine can refuse
- [ ] The ADR of the identity ruling written and linked (skill-conducted, engine-enforced, host loop, no CLI)
- [ ] Pins: gate present, no mechanism named, translation and ambiguity rules held, ordering prose absent
- [ ] Full suite green
