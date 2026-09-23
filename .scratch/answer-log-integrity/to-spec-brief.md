# to-spec brief — answer-log-integrity

## Input (what produced this spec)

Review cycle 4 over dfd3aba..c9f24eb (the six socrates-seam tickets):
finding #3, confirmed — a corrupt `answers.json` is silently truncated
(`read_answer_log` swallows the parse failure into `[]`; the next
`record_answered` reads that `[]` and overwrites the file). The fix
order the user set (7 → 8 → 1 → 4 → 2, landed as 4d00e10) deferred
this one pending a spec; the user asked for the shortest spec first.

## What the code contributed

Read at the source before drafting: the backend's write is
`O_WRONLY | O_CREAT | O_TRUNC` with no temp-and-rename (a partial
write is the corruption path), its `WriteResult` is ignored at
`record_answered`'s call site (a failed write is a silent loss), and
every state file except the answer log already fails loudly on
corruption (parsers raise; transport converts; the ticket-06 error
path faces it) — which frames the scope to the log alone.

## Rulings relied on (none new)

- Data, never enforcement (ticket 01): the log refuses and routes
  nothing; a failed write rides the result, never fails the resume.
- Present-or-absent signals (ticket 01): the unreadable condition rides
  the warning as `answer_log_unreadable`, never zero-filled prose.
- Declared degradation, never silent (socrates-seam move 3): the
  marker entry keeps the condition visible after the repair.
- Read verbs stay side-effect-free (house design): the reader reports,
  the writer repairs.

## Deliberately small

Three engine moves, one seam, zero skin changes, no new rulings — the
shortest spec the deferred findings admit. Finding #5 (lapidation
upgrade stranding) remains open and still requires the user's ruling
before it can be a spec at all.
