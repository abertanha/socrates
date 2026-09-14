"""The invocation surface — one thin file per engine verb (ticket 29).

Each file is parse, one engine call, serialize: the transport lives in
``socrates.invocation`` alone. The mutations are the engine's ask/apply
pairs plus its single-verb mutations; the reads report state. The resume
is one file for every kind — the pending payload carries its kind, so
the conductor answers the question it was shown and never picks a verb.
"""

INVOCATIONS = (
    # Mutations — the human decisions (ask here, resume through resume/)
    "opening",
    "amend_need",
    "accept",
    "reject",
    "door",
    "satisfaction",
    "resume",
    # Mutations — the engine's work
    "propose",
    "reconcile",
    "scenarios",
    "assertion_tests",
    "probe",
    "iteration",
    "defer",
    # The session's end — composed by the engine (ticket 31)
    "materialize",
    # Reads
    "pipeline_status",
    "current_pass",
    "pending_question",
    "audit_charge",
)
