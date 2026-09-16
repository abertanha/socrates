"""Virtual-filesystem paths for the Conceptual Domain Model."""

NEED_PATH = "/model/need.md"
PROPOSITIONS_PATH = "/model/propositions.json"
REJECTION_GUARDRAIL_PATH = "/model/rejection_guardrail.json"
PIPELINE_PATH = "/model/pipeline.json"
SCENARIOS_PATH = "/model/scenarios.json"
BATCHES_PATH = "/model/batches.json"
CONFLICTS_PATH = "/model/conflicts.json"
INFERENCE_STATE_PATH = "/model/inference_state.json"
NOTIFICATIONS_PATH = "/model/notifications.json"
COVERAGE_PATH = "/model/coverage.json"
# The AskHuman pending-question marker (ticket 28) — session state, not
# derivation (ADR-0001): it records that a question stands open.
PENDING_QUESTION_PATH = "/model/pending_question.json"
# The answer log (socrates-seam ticket 01) — when each answer arrived
# against when its question was asked. Facts, never gates.
ANSWERS_PATH = "/model/answers.json"
# Conceptual Domain Model deliverable (ticket 11 — settled layout).
DELIVERABLE_GLOSSARY_PATH = "/model/deliverable/glossary.md"
DELIVERABLE_STRUCTURE_PATH = "/model/deliverable/structure.md"
DELIVERABLE_RULES_PATH = "/model/deliverable/rules.md"
