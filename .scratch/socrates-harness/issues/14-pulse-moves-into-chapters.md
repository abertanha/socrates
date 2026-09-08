# 14 — The pulse moves into the chapters

**Specs:** `.scratch/session-conduction/spec.md` (D1 — chapters with internal pulse; D5 — mechanism)

**What to build:** The pass/Probe pulse — budget selection, Reconciliation (from pass 2), Scenarios, Assertion Tests, Probe — migrates from the orchestrator's surface into the chapter specialists' toolsets, making each Modeling Activity one regime: propose, lapidate, resolve under one roof. The orchestrator keeps the Opening, the doors, and the tail. The Coverage-selected exploration budget must keep riding the passes wherever they run, with explicit subagent propagation (never the silent fallback — issue #1698).

**Blocked by:** 13 — Conduction core (the derived-state reader and redirect contract exist to migrate onto).

**Status:** ready-for-agent

- [ ] A chapter specialist runs a full pass inside its chapter (propose → budget → Scenarios → Assertion Tests → Probe) in a scripted session
- [ ] Subagent invokes still carry the Coverage-selected recursion limit explicitly; propagation assertions carry over
- [ ] The orchestrator surface no longer exposes the pulse tools
- [ ] Existing orchestration tests re-scripted to the in-chapter flow (per-activity stubbed models are the prior art), all green
- [ ] Reconciliation-from-pass-2 and Probe interrupt payloads unchanged in shape
