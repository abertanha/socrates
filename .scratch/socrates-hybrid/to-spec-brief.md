# to-spec brief — socrates-hybrid

## Input (what produced this spec)

The 2026-09-13 architecture conversation, following the three recorded
specimens (dropped relationship; exhaustive sweep with clause-level gaps;
improvised audit charge with the fixed one on disk) and the identity ruling
it provoked.

## User rulings closed during the conversation and this to-spec

1. **Identity**: Socrates ALWAYS runs the deterministic engine, aided by
   deep-agents as in-package machinery. The soft skill-only mode ceases to
   be Socrates — without the engine it is a bootstrap.
2. **The skill calls the engine; the host loop conducts.** No standalone
   REPL, no socrates-owned agent loop. Target: agent harnesses that offer
   code execution (Claude Code, OpenCode, Cursor, pi, …).
3. **No CLI, no MCP** (clarified during to-spec): no console-script
   commands; the invocation is `python3` plus an invocation file/flow —
   the harness's own code execution is the only transport.
4. **The engine lives in the skill's clone** — deployment stays one
   directory (clone or symlink), skill text + engine + invocation files
   together; the bootstrap gate verifies importability.
5. **Language-agnostic Socrates, pt-BR first**: canonical English enums
   stay closed; the conductor is the only language boundary (renders
   questions, classifies replies to canonical tokens, raw preserved,
   ask-never-guess on door ambiguity).
6. **Developer audience legitimates the environment dependency** — the
   zero-dependency property is consciously given up for the engine-backed
   identity.
7. **Seams**: invocation entry functions tested in-process (user-approved);
   pin tradition extends to the v3 skill text and the engine-delivered
   charge; acceptance = one real hybrid session.
8. **Ticket 25 re-pointed** to this spec's acceptance seam (the soft-era
   record becomes optional).

## Carried constraints (from the house)

- ADR-0001 (state in files; derived never persisted), ADR-0002 (no grader;
  information never blocks), ADR-0005's spirit (harness conducts, model
  asks) — the hybrid is its purest expression.
- The v1/v2 "one self-contained skill file" constraint is superseded by the
  directory-as-deployment-unit ruling.
- deepagents remains the in-package machinery (backend, protocol); the
  innovation is the method, not any particular loop.
