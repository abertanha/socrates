# 12 — Fix: confirm/decline parsing is contextual to the action's polarity

**What to build:** A cross-polarity answer ("reject" at an Accept interrupt, "accept" at a Reject interrupt) must decline the action — never confirm it. A shared affirmative set across opposite-polarity questions confirms the wrong action: "reject" answering "Do you Accept Proposition p1?" accepted p1.

**Status:** done

- [x] "reject" at an Accept interrupt declines Acceptance — Proposition stays Candidate, tool returns `ok:false` with `declined`.
- [x] "accept" at a Reject interrupt declines Rejection — Proposition stays Candidate, Rejection Guardrail untouched.
- [x] Generic confirmations ("yes", "confirm", "ok", …) still confirm either action; polarity words confirm only their own.
- [x] All four call sites thread the interrupt kind (session accept/reject + Modeling Activity accept/reject).

## Comments

- Defect found in the initial codebase assessment (2026-09-04): `_CONFIRMED_ANSWERS` in `src/socrates/tools.py` was shared by both polarities, so the semantics established by commit `28e222c` ("interrupt answers parsed as confirm/decline; declined actions return ok:false with Proposition status preserved") were contradicted by the implementation. Spec right, code wrong — quick task, no spec change (CONTEXT.md is silent on answer parsing).
- Fix: `_GENERIC_CONFIRMS` ∪ per-action polarity words in `_ACTION_CONFIRMS`, keyed by the interrupt `kind`; `_is_confirmed(answer, action)`. The cross-polarity word falls through to a decline (status preserved), consistent with how any other non-affirmative answer is handled.
- Verification: `tests/test_proposition_lifecycle.py::test_cross_polarity_answer_never_confirms_the_opposite_action` kills the old parsing (fails against pre-fix `tools.py`, passes post-fix). Gate: `.venv/bin/pytest -q` → 24 passed, 0 failed.
