# Knowledge base

The repository's accumulating record of *patterns, gotchas, and
antipatterns* — the things a project learns about itself as code lands.
It lives at `patterns.jsonl` next to this file; agents prime from it at
session start, contributors curate it by hand.

This is deliberately different from the documents that already exist:

| Where | What goes there |
|---|---|
| `docs/adr/` | Decisions ("we chose X over Y because…"). Immutable. |
| `docs/architecture/` | Current code structure. Living. |
| `docs/guides/` | User-facing docs. Diátaxis. |
| **`docs/knowledge/patterns.jsonl`** | **Practitioner-level lessons: patterns, gotchas, antipatterns. Scoped to file globs.** |

ADRs answer *why was this decided*. Knowledge entries answer *what
should the next person avoid stepping on, or repeat*.

## When to add an entry

A loop has finished. You ask: *what would have made this go faster?*
Three answers worth recording here:

- **Pattern.** "When you touch X, also remember Y." A repeatable shape
  that worked once and will work again. Example: "Every package's
  `bootstrap()` should call `validateConfig()` first."
- **Gotcha.** A non-obvious cost or constraint that bit you. Example:
  "The auth middleware caches tokens for 15 minutes — invalidate it
  manually after a role change."
- **Antipattern.** A shape that looked appealing but rotted. Example:
  "Don't mock the database in integration tests; we got burned last
  quarter when mocked tests passed but the prod migration failed."

If the lesson is about *current code structure*, it belongs in
`architecture/`. If it's a *decision*, it belongs in `adr/`. If it's
*how to use the product*, it belongs in `guides/`. Knowledge entries
are the residue that doesn't fit those buckets — *practice* rather
than structure, decision, or instruction.

## Schema

`patterns.jsonl` is line-delimited JSON. Each non-empty line is one
entry:

```json
{"id": "K-NNNN", "kind": "pattern", "scope": "packages/auth/**", "title": "Always parameterize SQL queries", "body": "Use parameterized queries everywhere — string-concatenated SQL has bitten us twice. The `db.query()` helper enforces this; reach for it instead of raw drivers.", "source": "PR#42"}
```

<!-- schema-drift test in tools/test-lint-knowledge.sh parses the field
     table below and the `kind` row. Keep each field's name backticked
     in the first column on a single line; keep every kind backticked
     on the kind row. Don't split rows across lines. -->

| Field | Type | Notes |
|---|---|---|
| `id` | `K-\d{4,}` | Unique, zero-padded to four digits. Conventionally sequential, but the linter only enforces uniqueness — gaps are fine. |
| `kind` | `pattern` \| `gotcha` \| `antipattern` | Exactly one of these three values. |
| `scope` | glob | Path pattern this applies to — `packages/auth/**`, `src/cli/*.py`, or `*` for repo-wide. |
| `title` | string | One-line summary; aim for under 80 characters. |
| `body` | string | The lesson itself. A paragraph or two is enough; if you find yourself writing more, the entry probably wants to be split. |
| `source` | string | Where this came from: `PR#42`, `ADR-0007`, `issue#13`, etc. |

The format is JSONL (one JSON object per line, no commas, no wrapping
array) so it grows by append and reads line-by-line. `tools/lint-knowledge.py`
validates the file; `tools/hooks/session-start.py` reads it.

## Curation

Entries are *append-only by default*. If a lesson stops being true (the
underlying code changed, the constraint went away), the right move is
to **add a new entry** that says so, citing the old `id` in the body —
not to edit the old one. This keeps the knowledge base honest about
*when* a lesson was true.

**Supersession lives in the body, by design.** The schema has no
`supersedes` field; the linter rejects unknown keys. Citing the old
entry's id in the new entry's `body` is the convention. We chose
human-readable prose over a machine-checkable field because
supersession is rare enough that the cost of curating a separate
field outweighed the legibility gain.

Genuine corrections (typo, wrong file path) are fine to fix in place;
those are clerical, not historical.

When an entry's scope no longer matches anything (the package was
removed), leave it as-is. The next reader can see the path is gone and
infer the entry is historical. Removing entries hides the history of
what you used to worry about.

## Where this fits in the work-loop

The `work-loop` skill's *Capture what was learned*
section points back at this file. When a loop
captures a learning that fits the pattern/gotcha/antipattern shape, the
canonical home is here. Other kinds of learning still go where they
already belong (AGENTS.md, skill bodies, architecture/).

The session-start hook ([`tools/hooks/session-start.py`](../../tools/hooks/session-start.py))
reads this file and prints the entries — optionally filtered by glob —
so a fresh agent session starts with the relevant patterns already in
context.
