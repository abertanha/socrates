---
status: accepted
---

# No automated grader — Satisfaction is human

Verified that `deepagents` ships no grader, evaluation loop, hill-climb, reward, or self-critique mechanism; its only termination is the agent loop ending (`recursion_limit`, tool/subagent caps, or the model deciding it is done). We do **not** build one on top.

A single Inference Engine pass terminates by borrowing that built-in loop termination — and that delimits a Batch. The overall Mapping terminates at **Satisfaction**, the user's explicit signal — never an automated judgment.

Ground truth for a Conceptual Domain Model lives in the user's head; no metric reaches it. An eval loop would optimize a proxy the agent can measure, not actual model correctness, and would tend to close the loop without the human who actually knows the domain. For a modeling task, human-in-the-loop (Satisfaction + Probes) is the correct design, not a limitation.

**Rejected alternative:** a self-grading loop (LLM-as-judge scoring the Model, hill-climbing until the score plateaus) — rejected because the score is a proxy for a truth the judge cannot access.

**Consequence:** Socrates never declares a Model done on its own; termination always returns to the user. `recursion_limit` becomes a Batch-boundary mechanism, not a quality mechanism — which makes the subagent limit landmine (issue #1698, subagents silently falling back to 25) directly relevant.
