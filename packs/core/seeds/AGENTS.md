# AGENTS.md

> This is the canonical agent context file. Adapt the marked identity and command
> sections to this repository; keep universal rules here and scoped deltas nearby.

## What this repo is

This is <project-name> — a <one-line description of what it does and for whom>.

Read [the architecture overview](docs/architecture/overview.md) before exploring unfamiliar areas, if it exists.

## Keeping changes minimal

- Scope changes precisely to the request; defer unrelated cleanup.
- Surface assumptions before building, and stop for conflicting requirements.
- Prefer the simplest obvious solution; add an option, abstraction, or dependency only when needed.
- Add types and docstrings to code you change; validate boundaries the change crosses.
- Do not silently work around a source-of-truth conflict; state the evidence and trade-off.

## Source of truth

| Question | Home |
| --- | --- |
| Project scope | `docs/CHARTER.md` |
| Decisions and proposals | `docs/adr/` and `docs/rfc/` |
| Durable feature contract, when one exists | `docs/specs/<feature>/` |
| Current architecture | `docs/architecture/` |
| Product direction and history | `docs/product/` |
| User and maintainer guidance | `docs/guides/` or `guides/` |
| Repeating agent workflow | its `SKILL.md` |
| Mechanically knowable fact | code, schema, manifest, test, or linter |

## How we work

Use the `work-loop` skill for repository changes as its instructions require.
It owns mode selection, required artifacts, planning, verification, review,
recovery, and completion. Keep repository-specific process detail in its owning
workflow or reference documentation; commit and pull-request conventions live in
[docs/CONVENTIONS.md](docs/CONVENTIONS.md).

## Commands you'll need

```bash
<install command>
<test command>
<lint command>
<build command>
```

<!-- Optional infrastructure hooks for work-loop: deploy; smoke (post-deploy verify-status / end-to-end); teardown; seed-test-data. Add applicable commands here. -->

## Check before acting

- Get user confirmation before destructive commands or irreversible operations.
- Verify a function exists before importing it.
- Record a new dependency in the owning package instructions or an ADR before adding it.

## Security and privacy

Never commit personal information or credentials. Use generic placeholders in
repository artifacts and follow the security workflow for security-boundary changes.

**blessed security tools/helpers:** list this repository's sanctioned helpers by
boundary here. This declaration takes precedence over inferred alternatives.
External quality gate: none declared; declare one here when applicable.

## Scoped instructions

The nearest `AGENTS.md` above the file being edited applies. Read it before acting
in that directory; use scoped files only for action-changing directory deltas.

## When this file is wrong

Report stale or conflicting instructions rather than silently working around them.
Update the owning source, not a generated projection.
