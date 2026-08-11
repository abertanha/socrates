# 01 — Walking skeleton: Opening → Need → Satisfaction, FS-persisted, with the model-provider test seam

**What to build:** The thinnest end-to-end path through every layer. A user starts a session; an interrupt-gated Opening elicits the Need; the Need is persisted as the Model's first content in the virtual filesystem; the user signals Satisfaction; the session ends. Stands up the deepagents wrapper, a virtual-FS backend, and the model-provider boundary (real + stub) so every later ticket tests orchestration through a stubbed provider. Proves ADR-0001 (FS-state) and ADR-0002 (no grader; Satisfaction is human).

**Blocked by:** None — can start immediately.

**Status:** done

- [x] A session can be started and reaches an interrupt-gated Opening that elicits the Need from the user.
- [x] The Need is written to the virtual filesystem as the Model's first content (ADR-0001).
- [x] The user's explicit Satisfaction terminates the session — no automated "done" judgment (ADR-0002).
- [x] The model provider sits behind a boundary with a stub implementation, and one orchestration test uses the stub to assert the Need is persisted and Satisfaction ends the session.

## Comments

- Implemented as `create_socrates_session` + `StubChatModel`. Opening (`run_opening`) interrupt-elicits the Need and writes `/model/need.md`; Satisfaction (`await_satisfaction`) is interrupt-gated; session ends when the user resumes and the agent loop terminates (`state.next == ()`). Orchestration coverage: `tests/test_walking_skeleton.py`.
