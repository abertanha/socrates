# to-spec brief — socrates-seam

## Input (what produced this spec)

The fifth specimen (first full session on the deployed hybrid, ticket-25
comment 2026-09-16) analyzed end-to-end from the OpenCode session store and
the engine's on-disk state; the fourth specimen's still-open carryovers; and
the independent writing-to-agents evaluation of the deployed skill, with
per-point dispositions debated and recorded before this spec was drafted.

## User rulings closed during the conversation and this to-spec

1. **Seams**: the two existing seams only — the in-process invocation
   surface for engine behavior, the skill-text pin surface for conductor
   discipline. No new seams (kills the clock-injection seam that latency
   enforcement would have needed).
2. **Ask–answer binding: record and expose, never enforce.** Timestamps on
   the pending marker and the resume echo; the Satisfaction warning counts
   the answers that arrived faster than a human can read their question.
   Latency refusal rejected as a heuristic (sleepable, false-positive-prone,
   nondeterministic); kept on record as a future option with the recorded
   data as its evidence base.
3. **The treadmill extends**: lapidated = ≥1 recorded Scenario AND recorded
   assertion outcomes for the Proposition — the ticket-17 ruling amended on
   specimen evidence (the record, not the run, is what the engine trusts).
4. **The runtime-agnostic pin stands** against the evaluation's P1 remedy:
   no runtime mechanism is named for the audit; the declared-degradation
   clause is the honest fix. P8 (menu tension) rejected as already
   adjudicated in the text.

## What the evaluation contributed, after adjudication

Accepted: identity at the gate (P0), audit-degradation honesty (P1, half),
rooting + missing-state branch (P2), non-Refusal error path (P3), re-ask
exit (P4, text not engine), realpath derivation replacing the absolute path
(P5), language amendment (P6), post-compaction re-read (P7, lighter than a
budget). Rejected: naming a runtime sub-agent; context budgets; a
forensics-style health apparatus; engine-side latency enforcement.

## What only the specimen could give

The compound self-answers with stale raws (one "ok" → three accepts), the
exactly-two-Scenarios filing, the discarded `survives: true` outcomes, the
audit that never ran, the invented session root, the 35k startup spent
discovering a recipe 16/17 verb files already carry, and the fabricated
door activity the engine accepted. The spec's four moves are these, plus
the evaluation's survivors, folded into the two ruled seams.
