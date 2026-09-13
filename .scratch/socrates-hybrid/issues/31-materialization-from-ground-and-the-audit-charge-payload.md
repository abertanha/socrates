# 31 — Materialization from ground and the audit charge payload

**Specs:** `.scratch/socrates-hybrid/spec.md`

**What to build:** The end of the session, composed by the engine instead of authored by the model. The materialization verb derives the deliverable from the recorded ground — the Need, the accepted Propositions, the relationships and cardinalities the ground asserts — writing the canonical files verbatim from the record, every shipped line traceable to its ground entry by identifier. The audit stops depending on the conductor reading anything: an audit-charge invocation returns the fixed charge — the v2 charter semantics verbatim, self-standing, hardening included — and the skill's audit section becomes pure process around that payload: hand the charge to a fresh-context sub-agent spawned by whatever mechanism the host offers, with exactly the Model record and the deliverable; re-derive affected files through the engine; then exactly one bounded re-audit of the touched entries; the report is information, never a block, and never persisted. The pins extend: the charge payload matches its source of truth verbatim, and the deliverable's rows cite their ground identifiers.

**Blocked by:** 29 — Invocation files and the JSON contract (the materialization and the charge ride the invocation surface).

**Status:** ready-for-agent

- [ ] The materialization verb composes the deliverable from the recorded ground (verbatim derivation — the dropped-relationship class dies by construction)
- [ ] Every shipped row cites the ground entry it derives from, by identifier
- [ ] The audit-charge invocation returns the fixed charge verbatim — self-standing, hardening and report format included
- [ ] The skill's audit section is process over the payload: fresh-context auditor via the host's mechanism, exactly the two artifact sets, one bounded re-audit, report never persisted
- [ ] Pins: the charge payload verbatim against its source; identifier citations in composed rows
- [ ] Full suite green
