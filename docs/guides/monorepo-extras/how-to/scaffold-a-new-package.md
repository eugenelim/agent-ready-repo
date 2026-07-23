# Scaffold a new package

**Use this when:** you need a new shared library under `packages/` that matches monorepo conventions from the first commit.
**Prerequisites:** `monorepo-extras` (requires `core`) installed at repo scope; what you're building is a shared library, not a deployable app.
**Result:** a scaffolded `packages/<name>/` directory with standard files, workspace config wired, a passing placeholder test, and an entry added to `docs/architecture/overview.md`.

You need a new shared library under `packages/`. You want it to match every other package in the monorepo from the first commit. Ask your agent and let the `new-package` skill do the scaffolding.

## Before you start

Two things have to be true:

- You've installed `monorepo-extras` (it requires `core`). The skill is repo-scope — it scaffolds into `packages/`, which only makes sense in a monorepo.
- What you're building is a **shared library**, not a deployable app. Libraries go in `packages/`; apps go in `apps/`. New top-level directories need an RFC, not this skill.

## Do it

Ask your agent in plain language:

```
Scaffold a new package called billing.
```

That's the trigger. The skill confirms the package belongs in `packages/`, that the name is unique and descriptive, and that no existing package should grow this functionality instead. If your one-sentence purpose isn't clear, it asks before scaffolding — answer, and it continues.

From there it creates `packages/billing/src` and `packages/billing/tests`, drops in the standard files (`package.json` or equivalent, a human-facing `README.md`, a per-package `AGENTS.md`, a placeholder `src` export, and a passing placeholder test), wires the package into your workspace config, runs install and test to prove the workspace picks it up, and adds the package to `docs/architecture/overview.md`.

For the full list of what lands on disk and the conventions each file carries, see [What `new-package` generates](../reference/new-package.md).

## Fill in the per-package AGENTS.md

The scaffold gives you an `AGENTS.md` stub for the package. Keep it **specific**. The root `AGENTS.md` already covers monorepo-wide rules, so the per-package file should only carry:

- What this package does, in one sentence.
- Anything unusual about its build, test, or release.
- Constraints particular to this package (for example, "targets Node 18; do not use Node 20+ APIs").
- Public interface boundaries — what's exported versus internal.

If you find yourself copying the root `AGENTS.md`, stop. The agent already has that context.

## Pitfalls

- **One more tiny package isn't free.** Before scaffolding, check whether an existing package should absorb the functionality. Proliferating single-purpose packages is its own maintenance problem, and the skill will push back if that's the better move.
- **`apps/` is not `packages/`.** A deployable belongs in `apps/`. This skill only scaffolds libraries.
- **`overview.md` drift is expected.** The skill adds your package to `docs/architecture/overview.md`. If that's the only edit to the file in weeks, that's fine — the map is meant to drift slowly.

## See also

- [What `new-package` generates](../reference/new-package.md) — the files, the template, and the conventions each carries.
- The skill itself: [`new-package`](../../../../packs/monorepo-extras/.apm/skills/new-package/SKILL.md).
