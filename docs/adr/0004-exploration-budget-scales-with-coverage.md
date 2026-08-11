---
status: accepted
---

# Exploration budget scales inversely with Coverage

A pass's exploration depth is bounded by the agent-loop recursion limit. A static limit is wrong at both ends: an under-mapped domain (low Coverage) has much to surface — omissions, ambiguities, Scenarios — and a short limit truncates the Batch prematurely; a well-mapped domain (high Coverage) finds little new and terminates early regardless, so a high limit buys nothing and a low one is harmless. The budget should track how much there is left to discover.

The exploration budget per pass **scales inversely with Coverage** — generous when Coverage is low (early, sparse), lean when high (mature).

**Two guardrails:**
1. **Anchored by the Relevance Filter.** A generous early budget explores Need-relevant ground, not wandering — the Relevance Filter already constrains which Scenarios are worth generating, so more room means more *relevant* exploration, not more drift.
2. **An exploration allowance, never a quality signal.** A high budget gives room to *find* Conflicts, not to *judge* the Model good. Termination stays loop-ending + Satisfaction (per ADR-0002); only the room varies with Coverage.

**Rejected alternative:** a static recursion_limit — truncates under-mapped exploration or wastes budget on mature domains.

**Consequence:** the recursion limit (implementation) becomes a function of Coverage rather than a constant; the subagent limit-propagation care (issue #1698) applies to whatever value is chosen per pass.
