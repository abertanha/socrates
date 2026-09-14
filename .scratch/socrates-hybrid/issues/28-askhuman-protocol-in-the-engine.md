# 28 — The AskHuman protocol in the engine

**Specs:** `.scratch/socrates-hybrid/spec.md`

**What to build:** The engine's asking points stop interrupting mid-method and start returning questions as data. Today every human decision — the Opening's Need confirmation, Need amendments, the Probe's Batch resolutions, Iteration's confirm, the doors' three answers, Satisfaction — rides a graph interrupt that folds asking and applying into one call. This ticket splits them: a verb that needs a decision persists a pending-question marker in the session state and returns the payload — the question, the accepted canonical answers with their meanings, and the resume contract — and the resume arrives on a later call carrying the canonical token plus the user's raw words (the token drives the machine, the raw rides as provenance). Exactly one question is pending at a time; another asking verb while one is pending is a refusal naming the pending question; a non-canonical token is a structured refusal the conductor repairs; the door's close-versus-satisfaction ambiguity is surfaced as ask-never-guess. The boundary itself is pluggable so the engine asks without knowing who answers. The method's semantics are unchanged — the same elenchus through different plumbing — and the engine's suite adapts with them, staying green. The superseded standalone session layer keeps working by wiring its interrupts to the new boundary.

**Blocked by:** None — can start immediately.

**Status:** done

- [x] Every asking point in the engine returns a pending-question payload (`question`, `accepted_answers` with `meanings`, resume contract) instead of interrupting inline
- [x] The pending marker persists in the session state; exactly one pending question at a time (a second asking verb refuses, naming the pending one)
- [x] Resume carries `{canonical, raw}` — canonical token drives, raw preserved as provenance
- [x] A non-canonical or invalid token is a structured refusal, never a crash, never a silent default
- [x] Door ambiguity between close and satisfaction surfaces as ask-never-guess
- [x] The engine's suite stays green with the new plumbing, semantics unchanged
- [x] The standalone session layer keeps working (its interrupts wired to the new boundary)
- [x] Full suite green

## Verification

Implemented in 683b0b9 (TDD: 23 protocol tests written failing first, then the boundary). Gate **141 passed** (118 before + 23 new, `tests/test_askhuman_protocol.py`).

- **The boundary** (`asking.py`): `PENDING_QUESTION_PATH` marker (ADR-0001 — state, not derivation); `begin_pending`/`require_pending`/`guard_pending`/`clear_pending`; `AskRefusal` carrying the JSON-ready refusal (reason, the pending question it names, `accepted_tokens`, `ask_again`); `parse_envelope` ({canonical, raw} in, bare legacy values as their own canonical); closed English token sets (door/confirm/satisfaction/free-text) with their resume contracts.
- **The verbs** (`verbs.py`): ask/apply pairs for Opening (free-text → Need), Need amendment, accept, reject, door, Satisfaction. The ask's full context rides inside the persisted payload — resumes are parameterless besides the answer, so a session is resumable from the state files alone (user story 10). The door's `satisfaction` token clears the door question and begins the Satisfaction question in the same resume, returning it as `pending` for the caller to surface.
- **The engine split** (`inference.py`): `probe_batch` (ask — creates the Batch, persists the question, returns the payload) / `probe_resume` (apply); `run_iteration` (ask) / `iteration_resume` (apply, `_parse_iteration_confirm` as the canonical validator wrapped into a refusal). Transactionality holds across the split: a malformed resume rolls back to the **asked** state — the Batch stays presented, its conflicts open, the question pending — and the repaired resume resolves the same Batch (the old seam erased the Batch on rollback because ask and apply were one call). `interrupt_probe`/`interrupt_iteration` are gone; `inference.py` no longer imports langgraph.
- **The session adapter** (`tools.py`): every asking tool = ask → `interrupt(payload)` → classify (legacy English vocabulary, three-way: token / token / None) → resume, with `_conduct` translating `AskRefusal` into the structured JSON the conductor repairs. All orchestration flows passed unchanged; three tests were adapted, none for behavior loss (see Rulings).
- Payload continuity: the interrupt values keep their legacy fields (`kind`, `batch_id`, `conflicts`, `activity`, `greeting`, `deferred_warning`, `answers`, …) so every existing pin on interrupt payloads holds — the contract keys are additions.

## Rulings

- **The mumble default is retired, the mumble safety is kept.** The door on an unrecognized answer used to silently return `not_yet`; it now returns a structured refusal with the pending question alive (`ok: false, refused: true, accepted_tokens, ask_again`) and the conductor asks again. The pinned invariant survives — a mumble never closes a chapter and never routes to Satisfaction — only the silence dies (criterion "never a silent default", applied to the door and the confirm/decline and Satisfaction classifiers alike: a word that classifies to nothing re-asks). `test_conduction.py`'s mumble case was adapted to the refusal shape accordingly.
- **Explicit vocabulary vs. guessing in the legacy adapter.** The adapter's classifiers (door word-sets, confirm/decline with cross-polarity, `is_affirmative_satisfaction` + explicit negatives) classify what vocabulary matches and refuse the rest. The `"satisf"` substring heuristic stays in the session adapter (its era's classifier, test-pinned); the **engine** boundary accepts exact tokens only — `satisfeito`, `satisfied`, any non-token is refused (pinned by `test_door_ambiguity_asks_never_guesses`). The hybrid's conductor replaces the adapter's classifier entirely (the spec's language boundary).
- **Raw provenance rides in results, not (yet) in the decision records.** Every successful resume echoes `answer: {canonical, raw}`. Probe/iteration conflict resolutions and the Need file keep their existing recorded shapes; folding raw words into those records is left to 29/31 if the conductor needs it there.
- **One-pending is engine law, including probe-vs-iteration.** While a probe question is pending, `run_iteration` (and every other asking verb) refuses naming the probe; the conductor finishes or defers the open Batch first. This generalizes conduction's "no new pass while a Batch awaits" to every question.
- **Accept/reject pre-validate before asking** (an unknown proposition id is refused before the user is interrupted) — a tightening with no legacy test depending on the old ask-then-fail order. Per-surface touch semantics preserved exactly: session accepts/rejects re-raise deferred conflicts, chapter-specialist ones do not (as before).
- **`inference.py` commit note.** The standing "user's uncommitted edit — never commit" rule was honored by flagging before commit: at session start the file was clean in the working tree (the edit had been resolved beforehand), the whole diff was this refactor, and the user approved the commit explicitly.
