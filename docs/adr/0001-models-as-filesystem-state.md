---
status: accepted
---

# Models live in the virtual filesystem, not in conversation

The three Modeling Activities run as isolated `deepagents` subagents, each with fresh context that returns only a final report; nothing in one subagent's conversation survives into the next. For Domain Modeling to act on the Requirements a prior activity produced — or for Iteration to reopen an earlier Model — that Model must exist somewhere every phase can read and write.

We therefore treat Models as the **shared state of the pipeline, materialized as files in the `deepagents` virtual filesystem** (this glossary, requirements specs, behavioral specs, ADRs) — never as content held in the agent's conversation or memory alone. Conversation is ephemeral transport; the filesystem is the model.

**Consequence:** every model-changing step ends by writing the Model to the filesystem, and every phase begins by loading the relevant Models from it. The filesystem is not a convenience here — it is the only seam through which a non-linear, multi-subagent pipeline can share state at all.
