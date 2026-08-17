# Knowledge base

The repository's accumulating record of *patterns, gotchas, and
antipatterns* — the things a project learns about itself as code lands. The
progressive `project-knowledge` capability and its topic/journal contracts are
shipped. This repository has not activated a coherent v1 topic map yet, so its
current canonical corpus remains the legacy `patterns.jsonl` next to this file.
Contributors and agents curate it deliberately; the installed session-start
hook does not load it into model context automatically.

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

## Capturing a new observation

Do not append a new row to `patterns.jsonl`. Its `append-knowledge.py` command
is a retired compatibility shim that always refuses; migration alone reads the
legacy corpus. A producer that reaches an exact semantic gate constructs the
published typed captured-observation request and invokes the progressive
`project-knowledge --capture` mode. The public skill validates privacy,
provenance, freshness, and repository confinement before its private writer
can append a pending journal event.

If this repository has not activated a coherent v1 topic map, capture emits
the named unavailable/refusal outcome and creates no legacy append or fallback
file. Activate v1 only through the reviewed migration lifecycle described in
the architecture page; do not bypass that lifecycle by hand-editing the legacy
corpus.

Existing legacy rows remain raw UTF-8, never `\uXXXX`-escaped. Both forms are
valid JSON, so a serializer whose ASCII escaping defaults on can drift the
file silently while it still passes other JSON rules. This is a curation and
migration constraint, not authorization to add a new row.

Entries are **evidence, not instructions**, and are no longer replayed into
sessions automatically — see § Where this fits in the work-loop. Still keep the body to
lessons about this repo, and never paste content from an untrusted source into
one: an entry is a durable, agent-authored record that a human approves. Characters
that render as nothing — bidi overrides, zero-width joiners in runs, the
Unicode Tag block, the variation selectors, the Mongolian ones — are refused
outright by the legacy linter and v1 writer because a payload you cannot see in
a diff could still be rendered into model context during explicit curation or
future task-scoped retrieval. The rule is Unicode's
default-ignorable property, and there is a budget on how many may appear at all,
not just how many may sit together. Persisted evidence follows `AGENTS.md` §
Privacy: no real names, emails, org hostnames, or user-specific filesystem
paths — use the placeholders listed there.

## Verify before committing

`lint-knowledge.py` ships with the `work-loop` skill, so there is
nothing to wire: `tools/hooks/pre-pr.py` runs it over this file
automatically. To check the legacy corpus during curation or migration, run it directly from wherever
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

RFC-0077 and the foundation spec shipped one progressive `project-knowledge`
capability: a producer can use `--capture` to persist a typed observation in a
non-queryable monthly journal; `--distill` records a terminal disposition and
may reconcile an observation into a canonical topic; and `--enquire` reads
only a coherent committed topic/map snapshot. In a legacy-only repository,
capture and distillation remain unavailable until migration activates that v1
snapshot. The legacy corpus remains readable only for curation and migration;
its writer is retired. New observations use `project-knowledge --capture` or
end with the named unavailable/refusal outcome without a legacy append or
fallback.

The authoring lifecycle now declares exact producer-owned gates for reusable
supporting residue: `brief-ready`, `rfc-handoff-ready`, `adr-accepted`,
`spec-approved`, and `plan-locked`. Draft brief/spec work, Proposed ADRs,
incomplete reviews, failed approvals, rejection, and abandonment are hard
non-gates. Producers keep scratch transient, submit only the public typed
capture request, and never write journals or fallback files themselves.

Normative requirements, proposals, decisions, approved behavior, and build
sequencing remain solely in their brief, RFC, ADR, spec, or plan. A terminal
authoring gate may distil only receipts returned by that gate; it cannot guess
capture IDs or consume direct-maintainer pending observations. Any separately
requested enquiry starts with an explicit competency question, remains bounded
untrusted evidence, and abstains when committed evidence is insufficient.

Routing lessons into places that *are* authoritative—`AGENTS.md`, a skill, an
ADR, architecture docs, code, CI, or a lint or test—is part of the shipped
distillation lifecycle. The strongest knowledge is not prose a model remembers;
it is behavior the repository mechanically enforces.
