# The knowledge base

The repo accumulates practitioner-level lessons in
`docs/knowledge/patterns.jsonl`: patterns ("when you touch X, also
remember Y"), gotchas ("the auth middleware caches tokens for 15
minutes"), and antipatterns ("don't mock the database in integration
tests"). One JSON object per line, scoped to a file glob. The schema
and curation conventions live in
the repository's `docs/knowledge/README.md`.

**Why a separate bucket.** ADRs answer *why we decided X*;
`architecture/` describes *current structure*; `guides/` is for
*users*. Knowledge entries are practitioner residue — the things you
learn by building, not by deciding or documenting. They earn a home
because they're scoped to globs (a deliberate retrieval for `packages/auth`
should return the auth gotchas, not every lesson the repo ever learned)
and kept current (edit or remove entries as the codebase changes —
git history is the record; see `docs/knowledge/README.md § Curation`).

**How agents see it.** The normal session-start hook does not load the file into
model context. An operator can explicitly invoke
`tools/hooks/session-start.py --show-knowledge`, optionally filtered by a path
or narrower glob, for curation. Matching uses Python's `fnmatch` with the
caller's `--scope` value as the *path* argument and the entry's
stored glob as the *pattern*, so an agent working in
`packages/auth/server.ts` gets entries scoped to `packages/auth/**`
plus any repo-wide `*` entries. The work-loop SKILL's
*Capture what was learned*
section points contributors at this file as the destination for
pattern/gotcha/antipattern-shaped learnings; other shapes still go
where they already belong (AGENTS.md, skill bodies, architecture/).
