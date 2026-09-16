# 04 — The session's anchor

**Specs:** `.scratch/socrates-seam/spec.md`

**What to build:** The session stops living wherever the conductor
happens to be, and the first question stops costing 35k tokens. Before
the first verb runs, the conductor establishes with the user where this
session's directory lives — the working directory's `.socrates/` is the
offered default, never a silent choice; the specimen's Model landed in
the user's home directory because nobody asked. Every invocation of the
session then passes that root, giving the standing same-root rule the
first half it lacked. When a conductor resumes and the expected root
holds no session state, that absence is a question — look elsewhere for
the state, or start fresh — never a silent re-greet; the never-re-greet
rule gains the branch it lacked for the moved-cwd case. And the skin
teaches the invocation recipe it currently makes the conductor discover
by spelunking: each verb file is a program, executed with the session
root and the JSON payload as arguments — runtime unnamed, transport
unchanged. The startup's biggest cost (source discovery to reconstruct
what 16 of 17 verb files already carry as an entry point) dies.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Before the first verb, the conductor establishes the session's
      root with the user; the working directory's `.socrates/` is the
      offered default, and a silent choice is pinned absent
- [ ] Every invocation passes that same root — the establishment rule
      and the same-root rule pin together as one conduct
- [ ] Absent state at the expected root is a question (resume elsewhere
      vs start fresh), never a silent re-greet or an improvised new
      session
- [ ] The invocation recipe is taught: verb files are programs, run
      with the session root and the JSON payload — no runtime named,
      no console command invented
- [ ] Flattened-phrase pins for establishment, missing-state question,
      and recipe; mechanism scans confirm nothing runtime-specific
      crept in
- [ ] Full suite green

## Verification

Run the project gate. Demo the slice end-to-end: from a bare skill
load, the taught recipe executes a read verb with an explicit root
without reading any engine source; an empty expected root triggers the
taught question, not a greeting.
