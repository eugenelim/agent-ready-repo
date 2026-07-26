# `new-package` reference

The authoritative description of what the `new-package` skill produces and the conventions the `packages/_example/` template carries.

Skill source: [`new-package`](../../../../packs/monorepo-extras/.apm/skills/new-package/SKILL.md).

## Trigger

The skill fires on phrases like "new package", "create a package called…", or "add a library for…". It does **not** handle new top-level directories (those need an RFC) or new apps (those go in `apps/`, not `packages/`).

## Pre-scaffold checks

Before creating anything, the skill confirms:

1. The package belongs in `packages/` (a shared library), not `apps/` (a deployable).
2. The name is unique within `packages/` and reasonably descriptive.
3. No existing package should grow the functionality instead.

If the package's purpose isn't clear in one sentence, the skill asks the user to articulate it before scaffolding.

## Directory structure

The skill creates two directories with separate `mkdir -p` calls (so the snippet works in shells without brace expansion — POSIX `sh`, Windows PowerShell, dash):

```
packages/<name>/src
packages/<name>/tests
```

## Files generated

| File | Audience | Contents |
| --- | --- | --- |
| `package.json` (or equivalent) | Tooling | The project's standard fields. The equivalent is whatever your workspace uses — `Cargo.toml`, `go.mod`, and so on. |
| `README.md` | Humans | What the package is, how to install it, and one realistic usage example. |
| `AGENTS.md` | Agents | Package-specific rules that don't fit in the root `AGENTS.md`. |
| `src/index.<ext>` | Code | A placeholder export. |
| `tests/index.test.<ext>` | Code | A passing placeholder test. |

## Post-scaffold steps

After the files exist, the skill:

1. Wires the package into the workspace config — `pnpm-workspace.yaml`, a `Cargo.toml` workspace, `go.work`, or whichever applies.
2. Runs the install command to verify the workspace picks the package up.
3. Runs the test command to verify the placeholder test passes.
4. Adds the package and its purpose to `docs/architecture/overview.md`.

## The `packages/_example/` template

`monorepo-extras` ships a template package at `packages/_example/`. It's the copy-to-start reference, and the `new-package` skill follows its layout.

### `packages/README.md`

The `packages/` directory README states the convention: shared libraries consumed by apps and other packages, one directory per package, each owning its own build and test surface. It points at `_example/` as the template and notes that cross-package work — anything touching more than one package — goes through the `work-loop` skill.

### `packages/_example/README.md`

A human-facing package README with four sections:

- **Install** — a fenced block for the package manager's install command.
- **Usage** — one realistic example, not a full API reference.
- **API reference** — a pointer to generated docs or a `docs/` subpage, not a duplicated dump.
- **Contributing** — links to the repository-root `AGENTS.md` and `docs/CONVENTIONS.md`, plus the package's own `AGENTS.md` for any package-specific rules.

### `packages/_example/AGENTS.md`

The per-package agent-context template. It opens with a reminder that the root `AGENTS.md` already covers monorepo-wide conventions, so this file carries only package-specific content, structured as:

- **What this package is** — one sentence.
- **Public surface** — what's exported versus internal, and what counts as a public interface (the things whose changes must be coordinated with consumers).
- **Constraints particular to this package** — runtime version targets, avoided dependencies, performance budgets, backward-compatibility windows.
- **How to test this package** — only if the test command differs from the monorepo default; otherwise omitted.
- **When changes here need an ADR** — for packages with heightened sensitivity (auth, data layer, public SDKs), the categories of change that trigger an ADR.

## Conventions the template carries

- **Two audiences, two files.** `README.md` is for human consumers; `AGENTS.md` is for agents. They don't repeat each other.
- **Per-package `AGENTS.md` stays specific.** It extends or overrides the root `AGENTS.md` — it never copies it.
- **Each package owns its own build and test surface.** One directory per package.
- **Public surface is explicit.** The template makes you state what's exported versus internal, because that boundary defines what consumers depend on.
- **Don't duplicate API docs in the README.** Link to generated docs or a `docs/` subpage instead.
