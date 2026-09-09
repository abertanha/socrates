# 21 — Prompt retirement + ADR-0005

**Specs:** `.scratch/session-conduction/spec.md` (D5 — prompt retirement; D7 — registration)

**What to build:** With the conduction enforcing everything the prompt used to request, the system prompt's ordered discipline (the seven "Session discipline" items) retires into an advisory persona — how to talk, vocabulary stance, never the order. The method's order lives in one enforced place. The architecture decision is recorded as ADR-0005: the harness conducts, the model asks; the method's order never lives in a prompt again — including the rejected node-graph alternative recorded as the evolution path. The glossary stands untouched — EXCEPT the conduction terms (routed here by user ruling, 2026-09-09): *treadmill*, *lapidate*, *quiet*, *chapter*, *door*, and *valve* are load-bearing in user-facing strings (redirect reasons, prompts) and need glossary entries in the harness's own register, written at concept level; landing them here keeps one glossary-touching ticket.

**Blocked by:** 20 — Only-sink (the last conduction property the discipline items used to carry).

**Status:** done (2026-09-09)

- [x] The system prompt carries no ordered discipline — persona and how-to-talk only
- [x] ADR-0005 records the decision, the state-governed-surface mechanism, and the node-graph as the recorded evolution path
- [x] The full suite is green with the slimmed prompt — every formerly-requested behavior is now enforced (including the loop-guard and the doors)
- [x] The conduction terms (treadmill, lapidate, quiet, chapter, door, valve) land in CONTEXT.md at concept level, in the harness's own register
- [x] No other glossary changes; ADR-0001..0004 untouched

## Verification

Gate: `.venv/bin/pytest -q` — **80 passed** (75 pre-existing + 5 in `tests/test_prompt_retirement.py`). TDD followed: the new suite first failed against the old prompt (4 red — the persona test already passed, correctly: the persona is what stays), then green on the retirement.

Implementation: `src/socrates/session.py` (SYSTEM_PROMPT rewritten), `docs/adr/0005-harness-conducts-model-asks.md`, `CONTEXT.md` (new **Session conduction** cluster between the pipeline and the maieutic method).

### Rulings

- **What the advisory persona carries:** the how-to-talk section stays verbatim (the spec's Deferred Ideas pin "persona slimming beyond the discipline retirement" to real-session evidence — no slimming here), plus a new "How the session runs — the harness conducts, you ask" section stated as fact, never order: the harness enforces the order so the model need not manage it; a redirect payload is the map back (follow `admissible_next`); the session ends only through the user's Satisfaction. The conduct terms are named and pointed at the glossary. The retired imperatives are pinned absent by test (no "Session discipline" header, no numbered lines, none of the seven items' distinctive phrases, no `call `` ` imperative anywhere).
- **Scope: the orchestrator prompt only.** The ticket's letter names the system prompt's seven items. The chapter specialists' ACTIVITY_PROMPTS still narrate the in-chapter pulse (`_ACTIVITY_PULSE`) — partly enforced (pass-2 reconcile gate, quiet, treadmill), partly advisory (L1–L3 routing prose). Recorded as deliberate: it is the specialists' working brief inside one conducted chapter, and the first real-model session's watch-list already carries "prompt duplicating enforced rules" as the place to retire further prose with evidence.
- **Glossary register:** six terms as a new **Session conduction** cluster, each a concept-level paragraph plus the register's `_Avoid_` line — Chapter (an activity as lived in one session), Door (the user-confirmed close, three answers, a steering wheel), Quiet (counting, never judgment), Lapidate (worked through a pass; ≥1 recorded Scenario), Treadmill (≤1 unlapidated at any moment), Valve (proposing never queues). "Tail" and "steering wheel" stay deliberately un-promoted (the user ruling listed exactly six terms).
- **ADR-0005** follows the house format (title, decision bolded, two guardrails tied to ADR-0001/0002, the node graph as rejected-and-recorded evolution path, consequence naming the pinning test).
