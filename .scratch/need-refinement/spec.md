---
Status: ready-for-agent
Feature: need-refinement
---

# Spec: Need refinement — amend the Relevance Filter while Requirements is open

## Problem Statement

The Need — the Relevance Filter that judges every later Proposition — is written exactly once, verbatim, from the user's first answer to the Opening question, and nothing can ever change it. A real first answer is broad ("a chatbot to assist lawyers"); the filter that actually bounds the Model emerges only through interviewing, and shifts again when early Propositions reveal the deliverable is broader or narrower than first said. The harness pins the raw first utterance forever: every Scenario's relevance, the Need gate, and the deliverable's grounding are all judged against a filter the user never got to sharpen. The only workaround is starting the session over.

## Solution

The Need becomes amendable while the Requirements chapter is open — its first pass, or a reopening through Iteration. The model declares an amendment carrying the reshaped Need and the reason; the user confirms at an interrupt (the same propose/confirm pair the doors use); on confirmation the Need is rewritten with the amendment recorded beneath it — the superseded shape and the reason survive, because reasons always survive. A declined amendment leaves the Need exactly as it was. Out-of-state attempts receive an explaining redirect: a Need-level shift outside Requirements is an L4-grade event that travels through Iteration, which reopens Requirements and re-admits the amendment. Amendments govern future filtering only — derived facts recompute at read time; recorded Scenarios and Acceptances are the user's decisions and never cascade. The Satisfaction warning carries the session's amendments, so an early close is informed about the filter's history, not just its conflicts.

## User Stories

1. As a user, I want to sharpen the Need after the Opening's first raw answer, so that the filter judging every Proposition is the one we distilled together, not my first sentence.
2. As a user, I want every amendment to require my explicit confirmation, so that the Relevance Filter never shifts behind my back.
3. As a user, I want the superseded shape and the reason kept beneath the new Need, so that what the session used to believe stays auditable.
4. As a user, I want to decline an amendment, so that a mis-shaped proposal leaves the Need untouched and the session continues.
5. As a user, I want the amendment question to show the current Need and the proposed one side by side, so that confirming is a real comparison, not a leap of faith.
6. As a user, I want an amendment attempted outside Requirements to be redirected with the current state and the admissible path, so that a late Need-shift is carried honestly through Iteration instead of being silently impossible.
7. As a user, I want an L4 Conflict that invalidates a Need assumption to reopen Requirements and re-admit amendment, so that the filter is fixable exactly when the ground under it moves.
8. As a user, I want my recorded Scenarios and Acceptances to survive an amendment untouched, so that my past decisions are never silently re-made by a filter change.
9. As a user, I want every Scenario recorded after an amendment to be judged by the new Need, so that the filter is live, not cached.
10. As a user, I want the Satisfaction warning to list the session's amendments with their reasons, so that closing the Model early is informed by the filter's history.
11. As a user, I want the deliverable grounded in the final Need, so that what ships reflects the last thing we agreed, not the first.
12. As a user, I want amendment availability derived from persisted facts at every step, so that the Model's filesystem remains the single source of truth.
13. As a user, I want amendment admissibility to be counting over facts, never judgment, so that no automated grader sneaks in through the Need.
14. As a user, I want the amendment interrupt in the session's plain conversational terms, so that the machinery never leaks into my interview.
15. As a developer running the harness, I want the amendment rule deterministic and pure — same persisted facts, same availability — so that sessions are reproducible and the rule is testable on its own.
16. As a developer running the harness, I want out-of-state amendment attempts to cost one turn and teach the way back, so that the model is never stranded silent at the seam the old harness left.

## Implementation Decisions

- `amend_need` lives on the orchestrator (session) surface, not a chapter specialist's: the Need is session-level and never a Proposition — it stands above the pipeline. The gate lives in the conduction governor that already rules that surface. (Confirmed with the user.)
- Admissibility: the Requirements chapter is open — its first pass, or a reopening through Iteration. Pre-Opening redirects (the Need does not exist yet; the Opening creates it). Any other chapter and the tail redirect naming the Iteration path, per the conflict-level rule that an invalidated Need assumption goes all the way to Requirements.
- The interrupt carries the current Need, the proposed Need, and the reason, as one comparison question; English-only answer vocabulary, consistent with the deferred bilingual confirm/decline work.
- On confirmation the Need file is rewritten and the amendment recorded within it — superseded shape plus reason, newest last. No separate amendment store: availability of everything else derives at read time, and the amendment record is part of the artifact the Need already is.
- On decline the Need is untouched and the decline is returned to the model as a normal declined action.
- No retroactive cascade: recorded Scenarios and Acceptances stand (user decisions, not derived facts); relevance enforcement already reads the Need at record time, so post-amendment Scenario recording judges under the new filter with no new wiring.
- The Satisfaction warning gains the session's amendments (with reasons) alongside deferred Conflicts and unvisited chapters.
- The state × availability matrix extends by one column; the redirect payload keeps its established shape — `ok:false`, the current conduction state, the attempted tool, the admissible next steps.

## Testing Decisions

- Good tests assert external behavior only: tool-result JSON (the redirect and its named state), interrupt payloads (the amendment comparison, confirm and decline), virtual-filesystem state (the rewritten Need and its amendment record), and the Satisfaction warning payload.
- Seams — confirmed with the user, zero new seams: the existing orchestration seam (a Socrates session driven by the stubbed model provider, scripting tool calls and resolving interrupts) plus direct tests of the pure facts→availability rule for the new admissibility column. Prior art: the conduction gate and redirect tests, the opening-presentation tests, the only-sink guard tests, and the deferral criticality-warning payload tests.

## Out of Scope

- A distillation window inside the Opening (multi-exchange interviewing before the Need is pinned) — amend-in-chapter covers the observed behavior; revisit with first-real-session evidence.
- The cross-chapter valve (structural ground born during Requirements cannot be birthed immediately) — an adjacent conduction delta, its own cycle.
- Prior-model import (adopting a previous session's deliverable mid-session) — its own cycle.
- Bilingual answer vocabularies — the deferral ruling stands.
- Any re-examination or cascade over previously accepted ground on amendment.

## Further Notes

- Evidence lineage: the first real conversational session (2026-09-10, OpenCode "Starting Socrates 2", run with the `/socrates` skill) — the usable Need emerged ~5 distillation exchanges after the raw first answer, and was amended once mid-Requirements when a Proposition revealed the deliverable was broader than first said. Input brief and open-decision record: the feature's directory in `.scratch/`, alongside this spec.
- The conversational session that exposed this gap is also the strongest argument for the fix: its conduction held end-to-end (three doors, tail, Satisfaction) precisely because its living files let the interview reshape the Need — the one move the mechanical harness could not make.
