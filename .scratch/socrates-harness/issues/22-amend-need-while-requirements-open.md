# 22 — Amend the Need while Requirements is open

**Specs:** `.scratch/need-refinement/spec.md`

**What to build:** The Need stops being frozen at the Opening's first raw answer. While the Requirements chapter is open — its first pass, or a reopening through Iteration — the orchestrator can propose amending the Relevance Filter. The model declares the reshaped Need and the reason; the user confirms at an interrupt presenting the current Need and the proposed one side by side with the reason, as one comparison question in the session's plain conversational terms. On confirmation the Need is rewritten with the amendment recorded beneath it — superseded shape plus reason, newest last, no separate store (reasons always survive). A declined amendment leaves the Need exactly as it was and returns to the model as a normal declined action. Attempted anywhere else the amendment is redirected with the established payload: pre-Opening names the Opening (the Need does not exist yet); any other chapter and the tail name the Iteration path — a Need-level shift outside Requirements is an L4-grade event that travels through Iteration, which reopens Requirements and re-admits the amendment. Amendments govern future filtering only: recorded Scenarios and Acceptances are the user's decisions and never cascade, and relevance already judges at record time, so anything recorded after an amendment falls under the new filter. The state × availability matrix extends by one column; admissibility stays a deterministic, pure rule over persisted facts — counting, never judgment (ADR-0002).

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] The amendment is admitted exactly while Requirements is open — its first pass or an Iteration reopening — and nowhere else (pure rule, tested on its own: same facts, same availability)
- [ ] Pre-Opening attempts redirect naming the Opening; any other chapter and the tail redirect naming the Iteration path
- [ ] After an L4 reopen of Requirements, the amendment is admissible again
- [ ] The interrupt carries the current Need, the proposed Need, and the reason as one comparison question, in plain conversational terms — no machinery leaks
- [ ] Confirmation rewrites the Need with the amendment recorded beneath it — superseded shape plus reason, newest last
- [ ] A declined amendment leaves the Need untouched and returns to the model as a normal declined action
- [ ] Scenarios recorded after an amendment are judged under the new Need; previously recorded Scenarios and Acceptances stand untouched
- [ ] The redirect payload keeps the established shape — `ok:false`, current conduction state, attempted tool, admissible next steps
- [ ] Full suite green; zero new test seams (orchestration seam + the pure rule, per the spec's testing decisions)
