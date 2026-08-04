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
| `guides/` | User-facing docs. Diátaxis. |
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
| `scope` | glob(s) | Path pattern(s) this applies to — `packages/auth/**`, `src/cli/*.py`, or `*` for repo-wide. Comma-separate for multiple patterns: `"src/lint-*.py, packages/auth/**"`. |
| `tier` | `"invariant"` \| `"observation"` | Optional, default `"observation"`. `"invariant"` entries are always injected by session-start regardless of `--scope`; use for lessons that apply everywhere. |
| `title` | string | One-line summary; aim for under 80 characters. |
| `body` | string | The lesson itself. A paragraph or two is enough; if you find yourself writing more, the entry probably wants to be split. |
| `source` | string | Where this came from: `PR#42`, `ADR-0007`, `issue#13`, etc. |

The format is JSONL (one JSON object per line, no commas, no wrapping
array) so it grows by append and reads line-by-line. `tools/lint-knowledge.py`
validates the file; `tools/hooks/session-start.py` reads it.

## Curation

This file is a **living representation** of what practitioners should
know right now — not an immutable audit log. Keep it accurate:

- **Edit** an entry's body, title, or scope when the lesson changes.
- **Remove** an entry when the underlying code is gone, the constraint
  no longer applies, or the lesson has been promoted to a canonical
  location (AGENTS.md, CONVENTIONS.md, architecture doc).
- **Add** a note in the body when an edit would otherwise be confusing
  (`"Previously covered X; promoted to packages/AGENTS.md"`).

When a lesson is promoted to a canonical location, remove the entry
and note the destination in the PR description — don't duplicate.

Git history records what existed before. You don't need entries for
that.

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
