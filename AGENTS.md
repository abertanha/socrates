# Socrates

Socrates is a maieutic agent harness, built on the LangChain `deepagents` v0.7 library, specialized for the logical-conceptual, long-reasoning front-end of software development — requirements, domain modeling, and behavioral specification. It elicits a Conceptual Domain Model through questioning, not top-down authoring.

The domain glossary lives at `CONTEXT.md`; architectural decisions at `docs/adr/`.

## Agent skills

### Issue tracker

Issues and specs live as markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical triage roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
