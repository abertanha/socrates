# 17 — Treadmill, quiet, and the three-answer door

**Specs:** `.scratch/session-conduction/spec.md` (D2 — treadmill with valve; D3 — door close; matrix in D6)

**What to build:** In-chapter conduction. The treadmill: at most one unlapidated Proposition at any moment (lapidated = has been through ≥1 pass) — proposing the next opens only after the previous is lapidated; no new pass while a Batch awaits the user; proposing itself stays always available (the maieutic valve: ground revealed during Probe resolution is born immediately as the single unlapidated). Quiet is counting: every Proposition born in the chapter has ≥1 pass and no Batch is pending on any ground; deferred Conflicts never block. `complete_modeling_activity` becomes a declaration that interrupts the user with three answers: close / not yet / Satisfaction.

**Blocked by:** 13 — Conduction core; 14 — The pulse moves into the chapters.

**Status:** ready-for-agent

- [ ] Proposing while another Proposition is unlapidated redirects (treadmill), except the valve: ground born from Probe resolution enters immediately as the single unlapidated
- [ ] A pass attempt while a Batch awaits the user redirects
- [ ] Declaring completion with unlapidated Propositions or a pending Batch redirects — quiet is counting
- [ ] The door-close interrupt carries the three answers; "not yet" keeps the chapter open with the valve live
- [ ] A deferred Conflict does not block the door — it rides to the Satisfaction warning
- [ ] Nothing in quiet is a quality judgment: bookkeeping only (ADR-0002)
