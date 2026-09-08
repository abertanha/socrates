# 20 — Only-sink: Satisfaction as the only end

**Specs:** `.scratch/session-conduction/spec.md` (D4 — doors as steering wheel + only-sink)

**What to build:** The session can no longer end behind the user's back. An outer loop-guard re-injects the session with a state redirect when the model stops without Satisfaction; termination happens exclusively through an affirmative Satisfaction answer (closing the ADR-0002 conformance gap — today the loop ends whenever the model goes quiet). The tail keeps the full pulse plus Satisfaction always available. The Satisfaction warning gains a chapters-never-visited line alongside the criticality-weighted deferred conflicts — informed early closure, never blocked.

**Blocked by:** 17 — Treadmill, quiet, and the three-answer door (the door interrupt's Satisfaction answer and the final surface shape).

**Status:** ready-for-agent

- [ ] A session whose model stops calling tools is re-injected with a redirect naming the state — not terminated
- [ ] Termination happens only via an affirmative Satisfaction answer through the interrupt
- [ ] Door-close interrupts offer Satisfaction as the third answer (the steering wheel)
- [ ] An early Satisfaction warns with the chapters never visited, alongside the weighted deferred conflicts
- [ ] The warning stays non-blocking — closing with doors open remains the user's call
