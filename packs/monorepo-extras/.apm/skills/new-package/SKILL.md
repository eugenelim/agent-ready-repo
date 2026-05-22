---
name: new-package
description: Use this skill when the user wants to scaffold a new package in the monorepo's `packages/` directory. Triggers on "new package", "create a package called…", "add a library for…". Don't use for new top-level directories (those need an RFC) or for new apps (which go in `apps/`, not `packages/`).
dependencies: []
---

# Skill: new-package

Scaffold a new package under `packages/` with the conventions every package
in this monorepo follows.

## When to invoke

Confirm:

1. It belongs in `packages/` (shared library), not `apps/` (deployable).
2. Its name is unique within `packages/` and reasonably descriptive.
3. There isn't an existing package that should grow this functionality
   instead — proliferating tiny packages is its own problem.

If the package's purpose isn't clear in one sentence, ask the user to
articulate it before scaffolding.

## Procedure

1. Create the directory structure:

   ```bash
   mkdir -p packages/<name>/{src,tests}
   ```

2. Add the standard files:
   - `package.json` (or equivalent) with the project's standard fields
   - `README.md` aimed at *human* consumers — explains what the package is,
     how to install it, and gives one realistic usage example
   - `AGENTS.md` aimed at *agents* — package-specific rules that don't fit
     in the root AGENTS.md
   - `src/index.<ext>` with a placeholder export
   - `tests/index.test.<ext>` with a passing placeholder test

3. Wire the package into the workspace config (e.g., `pnpm-workspace.yaml`,
   `Cargo.toml` workspace, `go.work` — whichever applies).

4. Run the install command to verify the workspace picks it up.

5. Run the test command to verify the placeholder test passes.

6. Update `docs/architecture/overview.md` to list the new package and what
   it's for. (If this update would be the only change to overview.md in
   weeks, that's fine — overview.md is meant to drift slowly.)

## What goes in the per-package AGENTS.md

Keep it specific. The root AGENTS.md already covers monorepo-wide things.
Per-package AGENTS.md should cover only:

- What this package does (one sentence).
- Anything unusual about its build, test, or release.
- Constraints particular to this package (e.g., "this package targets
  Node 18; do not use Node 20+ APIs").
- Public interface boundaries — what's exported vs. internal.

If you find yourself copying the root AGENTS.md, stop. The agent already has
that context.
