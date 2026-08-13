# Knowledge base

The repository's accumulating record of *patterns, gotchas, and
antipatterns* — the things a project learns about itself as code lands.
It lives at `patterns.jsonl` next to this file; contributors and agents curate
it deliberately, but the installed session-start hook does not load it into
model context automatically.

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

A loop has finished. You ask: *what would have made this work materially
better — more correct, complete, reliable, recoverable, secure,
privacy-preserving, deterministic, reproducible, operable, maintainable,
reviewable, efficient, or independent of hidden context?* Speed is one useful
signal, not the objective. Record a learning when knowing it would materially
change a future approach along one or more of those quality attributes.

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
entry with **six required keys — `id`, `kind`, `scope`, `title`,
`body`, `source`** (plus optional `tier`). Omitting `source` is the
usual mistake:

```json
{"id": "K-NNNN", "kind": "pattern", "scope": "packages/auth/**", "title": "Always parameterize SQL queries", "body": "Use parameterized queries everywhere — string-concatenated SQL has bitten us twice. The `db.query()` helper enforces this; reach for it instead of raw drivers.", "source": "PR#42"}
```

<!-- The knowledge linter's self-test parses the field table below and the
     `kind` row to check them against the linter. Keep each field's name
     backticked in the first column on a single line; keep every kind
     backticked on the kind row. Don't split rows across lines. -->

| Field | Type | Notes |
|---|---|---|
| `id` | `K-\d{4,}` | Unique, zero-padded to four digits. Conventionally sequential, but the linter only enforces uniqueness — gaps are fine. |
| `kind` | `pattern` \| `gotcha` \| `antipattern` | Exactly one of these three values. |
| `scope` | glob(s) | Path pattern(s) this applies to — `packages/auth/**`, `src/cli/*.py`, or `*` for repo-wide. Comma-separate for multiple patterns: `"src/lint-*.py, packages/auth/**"`. |
| `tier` | `"invariant"` \| `"observation"` | Optional, default `"observation"`. A routing hint for curation and future retrieval. It no longer grants automatic prompt authority or causes session replay. During an explicit `--show-knowledge --scope ...` curation render, `invariant` entries remain visible regardless of the scope filter. |
| `title` | string | One-line summary; aim for under 80 characters. |
| `body` | string | The lesson itself. A paragraph or two is enough; if you find yourself writing more, the entry probably wants to be split. |
| `source` | string | Where this came from: `PR#42`, `ADR-0007`, `issue#13`, etc. |

Length and character limits: the writer caps `title` at 120 codepoints, `body` at 2000, `scope` at 200 and `source` at 120; the gate uses a looser ceiling, since entries predating both run over the cap. Tab is fine anywhere. A newline is fine in `body` only — session-start indents each body line, but prints `id`/`kind`/`scope`/`title` on one unindented line and `source` on its own, so a newline elsewhere forges a line in what it replays. Other control characters, characters that render as nothing, and runs of more than eight spaces are refused.

One gap is known and accepted: strong right-to-left characters reorder adjacent punctuation under the bidi algorithm without any control character present, so a value mixing them with ASCII can render in a different order than it is stored. The explicit bidi controls are refused; the implicit reordering is not detected.

The format is JSONL (one JSON object per line, no commas, no wrapping
array) so it grows by append and reads line-by-line.
`lint-knowledge.py` validates the file. `tools/hooks/session-start.py` can
render it only when explicitly invoked with `--show-knowledge`; normal session
startup does not read it into model context.

## Appending an entry

Use the writer that ships beside the linter — it allocates the next free `id`,
writes the line, and refuses anything the linter would reject, so a bad entry
never reaches the file. Run it from wherever your agent tool installed the
skill (`.claude/skills/`, `.agents/skills/`, `.kiro/skills/`, `.apm/skills/`):

```bash
python3 .claude/skills/work-loop/scripts/append-knowledge.py \
  --kind gotcha --scope 'packages/auth/**' \
  --title 'Token cache survives a role change' \
  --body 'The auth middleware caches tokens for 15 minutes — invalidate it manually after a role change.' \
  --source 'PR#42'
```

Hand-editing works too, with one rule the writer enforces for you: **entries are
raw UTF-8, never `\uXXXX`-escaped.** Both forms are valid JSON, so a file written
with `json.dumps(entry)` — whose `ensure_ascii` defaults to `True` — drifts to
escapes silently while still linting clean under every other rule. Write `—`,
not `\u2014`; if you serialize with Python, pass `ensure_ascii=False`.

Entries are **evidence, not instructions**, and are no longer replayed into
sessions automatically — see § Where this fits in the work-loop. Still keep the body to
lessons about this repo, and never paste content from an untrusted source into
one: an entry is a durable, agent-authored record that a human approves. Characters
that render as nothing — bidi overrides, zero-width joiners in runs, the
Unicode Tag block, the variation selectors, the Mongolian ones — are refused
outright, by the writer and by the linter, because a payload you cannot see in
a diff could still be rendered into model context during explicit curation or
future task-scoped retrieval. The rule is Unicode's
default-ignorable property, and there is a budget on how many may appear at all,
not just how many may sit together. Entries are committed and permanent, so they follow `AGENTS.md` § Privacy: no real names, emails, org hostnames, or user-specific filesystem paths — use the placeholders listed there.

## Verify before committing

`lint-knowledge.py` ships with the `work-loop` skill, so there is
nothing to wire: `tools/hooks/pre-pr.py` runs it over this file
automatically. To check as you write, run it directly from wherever
your agent tool installed the skill (`.claude/skills/`, `.agents/skills/`,
`.kiro/skills/`, `.apm/skills/`):

```bash
python3 .claude/skills/work-loop/scripts/lint-knowledge.py; echo "exit=$?"
```

Run it **unfiltered** and read its exit code. Never pipe a gate through
`tail` or `grep` to judge it: `<gate> | tail -2` reports *tail's* exit
code — always 0 — and truncates away the `✖ <file>:<line>:` lines that
name what is wrong, so an entry with a missing `source` key reads as
clean locally and fails in CI.

The session-start hook is not a substitute — it skips a malformed line
silently rather than failing the session.

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

The session-start hook does **not** read this file. Whatever that hook prints
becomes model context before the user's first prompt — and again on resume,
clear, compaction and fork — so replaying agent-captured prose there would turn
one influenced session into a standing instruction for every session after it.
Entries are captured from material the work-loop encountered; being committed
makes them reviewed, not authoritative.

The renderer is still reachable on request, for curation:

```bash
python3 tools/hooks/session-start.py --show-knowledge [--scope <path-or-glob>]
```

Harvesting these into the places that *are* authoritative — AGENTS.md, a skill,
an ADR, architecture docs, or a lint or test — is the distill-knowledge path's
job. The strongest knowledge is not prose a model remembers; it is behaviour the
repository mechanically enforces.
