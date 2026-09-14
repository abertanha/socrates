---
status: accepted
---

# The skill conducts, the engine enforces

Socrates ran as two things that never met: a conversational skill whose
every guarantee was requested of the model, and a deterministic engine
whose every rule was pinned by tests but which had never driven a real
session. The evidence against the first is on record across three
specimens — an audit re-run from the conductor's stale memory while the
fixed instrument sat on disk, session artifacts churned and corrupted by
free-form file editing before self-repairing, and door answers routed by
fuzzy wording. The engine answers all three by construction, but a user
running Socrates inside an agent harness does not meet a Python library;
they meet the skill. Requested guarantees are one distracted turn away
from ignored guarantees.

**The decision: skill-conducted, engine-enforced, host loop, no CLI.**

The skill stays the session's voice — persona, talking rules, the
language boundary — and invokes the engine for every state mutation
through small invocation files that live beside it. The host harness's
own code execution is the only transport; there is no console-script
CLI, no MCP server, no separate runtime to operate. The engine lives in
the skill's clone — deploying Socrates is cloning or symlinking one
directory — and a bootstrap gate opens every session: the conductor
verifies through code execution that the engine imports from the clone
and, where it does not, prints installation steps and refuses to
conduct. No engine, no Socrates.

**The contract between them is AskHuman.** An asking verb never blocks:
it returns a pending-question payload — the question, its accepted
canonical answers with their meanings, the resume contract — and
persists a pending marker in the session state; the resume arrives on a
later invocation as `{canonical, raw}`, the canonical token driving the
machine and the raw words riding as provenance. Exactly one question is
pending at a time. Wrong order is refused — every refusal names its
reason and the admissible next verbs — and the ordering prose the older
skills carried retires by omission: the order of the method lives in
the engine's refusals now, and the skill stops prescribing sequence
entirely.

**The conductor is the only language boundary** (language-agnostic,
pt-BR first): the session's language is declared once at the Opening;
pending-question payloads are rendered to the user in that language;
the user's free replies are classified into canonical tokens with their
exact words preserved; the canonical English enums never open. Between
closing a door and Satisfaction the conductor asks, never guesses.

**Rejected alternatives.** The TUI product (the earliest shape): nothing
in the method needs one, and the user's sessions already live in agent
harnesses. The standalone deepagents session loop as the product
surface (its own system-prompt loop and guard): superseded by this
ruling — its guarantees were the request-shaped ones this ADR retires;
deleting it is a follow-up cleanup, out of scope here. An MCP server:
one more runtime to operate, and the host already has code execution.

**Consequences:** the skill's unit of deployment is the directory (the
one-file constraint of v1/v2 is superseded); the invocation files stay
thin — parse, one engine call, serialize, no policy (pinned by
`tests/test_invocation_files.py`); the skill's text is pinned as the
conductor's skin — gate present, no mechanism named, translation and
ambiguity rules held, ordering prose absent
(`tests/test_skill_v3_skin.py`); the audit's fixed charge migrates from
the skill file to an engine payload (ticket 31); ADR-0001 (derived
never persisted — the pending marker included) and ADR-0002
(information never blocks — every warning included) stand unchanged,
and ADR-0005's ruling inverts to its purest form: the harness conducts
through the engine, the model asks.
