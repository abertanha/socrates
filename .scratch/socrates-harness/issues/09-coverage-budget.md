# 09 — Coverage-driven exploration budget (ADR-0004) + subagent propagation

**What to build:** Coverage is measured pass-over-pass from declining signals (e.g., Conflicts surfaced per pass). The per-pass recursion limit is selected ∝ 1/Coverage — generous when Coverage is low (sparse, early), lean when high (mature) — anchored by the Relevance Filter so a generous early budget explores Need-relevant ground, not drift. The chosen limit is explicitly propagated to subagents (#1698 — they otherwise silently fall back to 25). The budget is an exploration allowance, never a quality signal (ADR-0002).

**Blocked by:** 04 — Probe loop (needs passes running to measure Coverage).

**Status:** ready-for-agent

- [ ] Coverage is read pass-over-pass from declining signals (e.g., Conflicts surfaced per pass).
- [ ] The per-pass recursion limit scales inversely with Coverage.
- [ ] The chosen limit is propagated to spawned subagents (no silent fallback to 25 — issue #1698).
- [ ] The budget is an exploration allowance, not a quality gate.
