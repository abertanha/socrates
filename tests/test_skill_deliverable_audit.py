"""Ticket 24 — fresh-context deliverable audit at materialization.

The conversational skill materializes the deliverable by hand, and
authorship loses things: the session that motivated this ticket recorded
the ground faithfully, then dropped an asserted relationship from the
structure file — and only the user's own later audit caught it. The fix
lives in the skill: before stopping, a fresh reader with no access to the
conversation checks the accepted ground against the deliverable —
presence and structural explicitness, nothing else.

Seam: the skill artifact itself, pinned the way the prompt-retirement
tests pin the system prompt — one file read, many small assertions, so
the audit instruction cannot quietly vanish and its binding limits
cannot quietly blunt. (Acceptance beyond the pin — a real session — is
ticket 25.)

Ticket 26 sharpens the charter where the first real exercises showed it
leaking: presence walks by assertion (a Proposition "covered in
substance" while a clause is gone is the failure mode), explicitness
infers relationships from functional grammar, renderings are checked
both ways without ever counting as a home, the filter gains a
clause-level boundary, and doubt ships as a QUESTION — never silence.
The v1 pins below were kept green through the rewrite on purpose: the
sharpening may not erode the boundaries v1 set.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "socrates" / "SKILL.md"

# The materialization paragraph, anchored by its own verb phrase — not by
# an incidental example that a future edit could reword.
MATERIALIZATION_ANCHOR = "materialize the Conceptual Domain Model"
AUDIT_HEADING = "### The deliverable audit"
FILES_SECTION_HEADING = "## The Model's files"


def _skill() -> str:
    return SKILL.read_text()


def _flat() -> str:
    return " ".join(_skill().split())


def _audit_section() -> str:
    text = _skill()
    return text[text.index(AUDIT_HEADING) : text.index(FILES_SECTION_HEADING)]


def test_the_audit_sits_between_materialization_and_stop() -> None:
    text = _skill()
    audit = text.index(AUDIT_HEADING)
    assert text.index(MATERIALIZATION_ANCHOR) < audit, (
        "the audit must live with the Satisfaction materialization"
    )
    assert audit < text.index(FILES_SECTION_HEADING), (
        "the audit is session order, not file documentation"
    )
    flat = _flat()
    # The stop is tied to the audit. The bare-retirement check is global
    # on purpose: the session has exactly one end, so a second bare
    # "Then stop." anywhere would itself be a stop detached from the
    # audit.
    assert "Then stop." not in flat, "a stop detached from the audit appeared"
    assert "Then run the deliverable audit" in flat, "stop not tied to the audit"
    assert "only then stop" in flat, "the ordering is unstated"


def test_the_auditor_is_a_fresh_reader_handed_exactly_two_artifacts() -> None:
    flat = _flat()
    assert "spawn a sub-agent" in flat, "no fresh reader is spawned"
    # Runtime-agnostic: no mechanism is named, the runtime's own is used.
    assert "whatever agent mechanism your runtime offers" in flat, (
        "the instruction names a runtime mechanism"
    )
    # Fresh context: the conversation never reaches it.
    assert "no access to this conversation" in flat, "the auditor may see the talk"
    assert "exactly two things" in flat, "the handoff is not bounded"
    assert "the session's Model record and the deliverable files" in flat, (
        "the two artifacts are not named"
    )


def test_the_charter_is_the_accepted_ground_found_whole() -> None:
    flat = _flat()
    assert "carries the accepted ground whole" in flat, "the charge is stated weakly"
    assert "Presence" in flat, "the presence check is missing"
    assert "Structural explicitness" in flat, "the explicitness check is missing"
    assert "traceable to a home" in flat, "presence has no home criterion"
    # The Parte case, pinned: an asserted relationship may not hide as a
    # characteristic of another concept, and stated cardinality must
    # surface.
    assert "never ships only as a characteristic" in flat, (
        "the attribute escape hatch reopened"
    )
    assert "cardinality where the ground states it" in flat, (
        "cardinality became optional again"
    )


def test_the_charter_reads_modulo_the_implementation_independence_filter() -> None:
    flat = _flat()
    assert "modulo the Implementation-Independence filter" in flat, (
        "the filter's exclusions count as gaps again"
    )
    assert "is not missing" in flat, "the exclusion is not marked as by-design"


def test_presence_walks_by_assertion() -> None:
    """Ticket 26 — the presence bar decomposes: content is lost at the
    granularity of the clause, so the walk and the finding both work at
    that granularity."""
    flat = _flat()
    assert "decomposes into the assertions it makes" in flat, (
        "presence still walks at Proposition granularity"
    )
    assert "traceable to a home of its own" in flat, (
        "assertions are not traced individually"
    )
    assert "names the assertion, not just the Proposition" in flat, (
        "findings stop at the Proposition"
    )
    # The v1 bar is retired by omission: the phrase that let a clause
    # vanish under a covered-looking Proposition is gone from the skill.
    assert "in substance" not in flat, (
        "the per-proposition 'in substance' bar survived the sharpening"
    )


def test_explicitness_infers_relationships_from_functional_grammar() -> None:
    """Ticket 26 — the Parte class generalized: the ground may word a
    relationship as function rather than linkage, and the audit must
    read it anyway."""
    flat = _flat()
    assert "any functional grammar between two concepts" in flat, (
        "the inference rule is not stated"
    )
    assert (
        "conditions, gates, meters, defines, produces, contains, or derives"
        in flat
    ), "the functional grammar list drifted or lost a verb"
    assert "carry it with the cardinality the ground states" in flat, (
        "inferred relationships are not held to the cardinality bar"
    )


def test_renderings_are_checked_both_ways_and_never_a_home() -> None:
    """Ticket 26 — the B6 case: a lifecycle lived only inside a derived
    diagram, and nothing looked there."""
    flat = _flat()
    assert "never a home" in flat, "a rendering can count as a home again"
    assert "content found only in a rendering is a finding" in flat, (
        "the nothing-lives-only-there direction is unchecked"
    )
    assert "diverges from the structure's inventory" in flat, (
        "the rendering-must-reflect direction is unchecked"
    )


def test_the_filter_s_clause_boundary() -> None:
    """Ticket 26 — the filter was clear at artifact level and ambiguous
    at clause level; the boundary is now stated with both sides."""
    flat = _flat()
    assert "obligations and constraints of the product" in flat, (
        "the staying side of the boundary is unnamed"
    )
    assert "conformity to a named legal regime" in flat, (
        "the legal-regime exemplar is gone"
    )
    assert "what is billable" in flat, "the billable-unit exemplar is gone"
    assert "the mechanisms that implement them do not" in flat, (
        "the going side of the boundary is unnamed"
    )


def test_unsure_is_a_question_never_silence() -> None:
    """Ticket 26 — every filter ambiguity resolved itself in silence;
    now doubt is a finding category."""
    flat = _flat()
    assert "QUESTION" in flat, "the QUESTION category is missing"
    assert "never a silent pass" in flat, "doubt may pass in silence again"


def test_the_auditor_never_judges_and_its_report_never_blocks() -> None:
    flat = _flat()
    assert "never judges quality" in flat, "a grader crept in"
    assert "never proposes" in flat, "the auditor proposes now"
    assert "never reopens the Model" in flat, "the audit can reopen the Model"
    assert "information, never a block" in flat, "the report became a gate"


def test_the_model_s_negative_space_is_not_the_audit_s_business() -> None:
    flat = _flat()
    assert "negative space, not gaps" in flat, "rejections count as omissions"
    assert "the warning's business, not the audit's" in flat, (
        "deferred Conflicts are double-reported"
    )


def test_findings_carry_the_proposition_identifier() -> None:
    """Findings are identifier-level traces: the Proposition named, its
    home named — or the homelessness flagged."""
    flat = _flat()
    assert "by its identifier" in flat, "findings are not identifier-traced"
    assert "homeless flag" in flat, "the homeless case is unnamed"


def test_findings_rederive_the_artifact_and_the_ground_stands() -> None:
    flat = _flat()
    assert "re-derive the affected deliverable file" in flat, "ground is re-made"
    assert "the recorded ground stands untouched" in flat, "ground is not protected"
    # The user reads domain terms, never the audit's machinery — and a
    # clean audit is silent: the session ends exactly as it ended before
    # this ticket.
    assert "the audit's own vocabulary never reaches the user" in flat, (
        "machinery may leak into the interview"
    )
    assert "domain's own terms" in flat, "findings are not in domain terms"
    assert "changes nothing" in flat, "a clean audit adds noise"
    assert "exactly as you otherwise would" in flat, "the ending changed"


def test_the_fallback_pass_when_no_sub_agent_exists() -> None:
    flat = _flat()
    assert "If the runtime offers no sub-agent" in flat, "the fallback is missing"
    assert "dedicated pass" in flat, "the fallback is not a dedicated pass"
    # Honest about being the weaker guarantee — pinned by its full
    # sentence, so deleting the admission breaks the pin.
    assert "weaker, since your memory of the conversation is present" in flat, (
        "the fallback no longer admits its weakness"
    )
    assert "reading only the Model record and the deliverable files" in flat, (
        "the fallback reads more than the two artifacts"
    )


def test_the_report_is_never_persisted() -> None:
    flat = _flat()
    assert "Never write the audit's report" in flat, "the report may be persisted"
    assert "derived check, not ground" in flat, "the report became ground"


def test_no_runtime_tool_is_named_in_the_audit() -> None:
    audit_section = _audit_section()
    for tool in ("Task tool", "Agent tool", "subagent:", "claude"):
        assert tool not in audit_section, f"runtime tool named: {tool!r}"
