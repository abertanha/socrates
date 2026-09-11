"""Ticket 24 — fresh-context deliverable audit at materialization.

The conversational skill materializes the deliverable by hand, and
authorship loses things: the session that motivated this ticket recorded
the ground faithfully, then dropped an asserted relationship from the
structure file — and only the user's own later audit caught it. The fix
lives in the skill: before stopping, a fresh reader with no access to the
conversation checks coverage of the accepted ground — presence and
structural explicitness, nothing else.

Seam: the skill artifact itself, pinned the way the prompt-retirement
tests pin the system prompt — one file read, many small assertions, so
the audit instruction cannot quietly vanish and its binding limits
cannot quietly blunt. (Acceptance beyond the pin — a real session — is
ticket 25.)
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "socrates" / "SKILL.md"

MATERIALIZATION_MARKER = '"120 minutes" is out'
AUDIT_HEADING = "### The deliverable audit"
FILES_SECTION_HEADING = "## The Model's files"


def _skill() -> str:
    return SKILL.read_text()


def _flat() -> str:
    return " ".join(_skill().split())


def test_the_audit_sits_between_materialization_and_stop() -> None:
    text = _skill()
    audit = text.index(AUDIT_HEADING)
    assert text.index(MATERIALIZATION_MARKER) < audit, (
        "the audit must live with the Satisfaction materialization"
    )
    assert audit < text.index(FILES_SECTION_HEADING), (
        "the audit is session order, not file documentation"
    )
    flat = _flat()
    # The stop is tied to the audit: the old bare stop after the
    # materialization paragraph is retired, and the new ordering says so.
    assert "Then stop." not in flat
    assert "Then run the deliverable audit" in flat
    assert "only then stop" in flat


def test_the_auditor_is_a_fresh_reader_handed_exactly_two_artifacts() -> None:
    flat = _flat()
    assert "spawn a sub-agent" in flat
    # Runtime-agnostic: no mechanism is named, the runtime's own is used.
    assert "whatever agent mechanism your runtime offers" in flat
    # Fresh context: the conversation never reaches it.
    assert "no access to this conversation" in flat
    assert "exactly two things" in flat
    assert "the session's Model record and the deliverable files" in flat


def test_the_charter_is_coverage_only() -> None:
    flat = _flat()
    assert "coverage of the accepted ground" in flat
    assert "Presence" in flat
    assert "Structural explicitness" in flat
    assert "traceable to a home" in flat
    # The Parte case, pinned: an asserted relationship may not hide as an
    # attribute, and stated cardinality must surface.
    assert "never ships only as an attribute" in flat
    assert "cardinality where the ground states it" in flat


def test_the_charter_reads_modulo_the_implementation_independence_filter() -> None:
    flat = _flat()
    assert "modulo the Implementation-Independence filter" in flat
    assert "is not missing" in flat


def test_the_auditor_never_judges_and_its_report_never_blocks() -> None:
    flat = _flat()
    assert "never judges quality" in flat
    assert "never proposes" in flat
    assert "never reopens the Model" in flat
    assert "information, never a block" in flat


def test_the_model_s_negative_space_is_not_the_audit_s_business() -> None:
    flat = _flat()
    assert "negative space, not gaps" in flat
    assert "the warning's business, not the audit's" in flat


def test_findings_rederive_the_artifact_and_the_ground_stands() -> None:
    flat = _flat()
    assert "re-derive the affected deliverable file" in flat
    assert "the recorded ground stands untouched" in flat
    # The user reads domain terms, never machinery — and a clean audit is
    # silent: the session ends exactly as it ended before this ticket.
    assert "domain's own terms" in flat
    assert "changes nothing" in flat
    assert "exactly as you otherwise would" in flat


def test_the_fallback_pass_when_no_sub_agent_exists() -> None:
    flat = _flat()
    assert "If the runtime offers no sub-agent" in flat
    assert "dedicated pass" in flat
    # Honest about being the weaker guarantee: the author's context is
    # still present.
    assert "weaker" in flat
    assert "reading only the Model record and the deliverable files" in flat


def test_the_report_is_never_persisted() -> None:
    flat = _flat()
    assert "Never write the audit's report" in flat
    assert "derived check, not ground" in flat


def test_no_runtime_tool_is_named_in_the_audit() -> None:
    text = _skill()
    audit_section = text[
        text.index(AUDIT_HEADING) : text.index(FILES_SECTION_HEADING)
    ]
    for tool in ("Task tool", "Agent tool", "subagent:", "claude"):
        assert tool not in audit_section, f"runtime tool named: {tool!r}"
