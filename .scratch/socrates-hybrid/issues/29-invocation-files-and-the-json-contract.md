# 29 — Invocation files and the JSON contract

**Specs:** `.scratch/socrates-hybrid/spec.md`

**What to build:** The transport that lets a skill call the engine: one thin Python invocation file per engine verb, living in the skill's clone beside the engine, run by the conductor with whatever code execution its runtime offers. Each file parses its JSON input (argument or stdin), makes exactly one engine call, and prints its JSON output — no policy, no orchestration, no state of its own. The verb surface mirrors the engine's mutations — the Opening and the Need with its amendments, proposing, accepting, rejecting, reconciliation, scenarios, assertion tests, the probe batch and its resume, iteration, deferral, the door, satisfaction — plus the read verbs: the pipeline's status, the current pass, and any pending question with its resume contract. Wrong order is refused with the reason and the admissible next verbs, as structured JSON. The tracer bullet: a full pass — Need, propositions accepted, reconciliation, scenarios, assertion tests, a probe that returns its pending question and resumes with a canonical answer, a door closed — driven end to end by calling nothing but the files' entry functions against a temporary working directory.

**Blocked by:** 28 — The AskHuman protocol in the engine (the files can only return questions as data once the engine asks that way).

**Status:** ready-for-agent

- [ ] One invocation file per engine mutation, plus read verbs (pipeline status, current pass, pending question) — each thin: parse, one engine call, serialize
- [ ] JSON in (argument or stdin), JSON out (stdout), errors as structured JSON — never stack traces
- [ ] Order violations refused with reason and admissible next verbs, as JSON
- [ ] A pending question is returned as data; the resume verb carries `{canonical, raw}`
- [ ] Entry functions tested in-process with argv and a temporary working directory, asserting on the JSON (the approved seam)
- [ ] The tracer-bullet pass runs end to end through the files alone (Need → propositions → reconcile → scenarios → tests → probe pending → probe resume → door)
- [ ] Full suite green
