# Monorepo Extras

Your agent can scaffold a new package in your monorepo's `packages/` directory from a template.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it from inside the monorepo, alongside Core:

```bash
cd path/to/your-repo
agentbundle install --pack monorepo-extras
```

## What your agent can do

- Scaffold a new package, such as `billing`, in `packages/`.
- Start it from the example template in `packages/_example/`.
- Add the `packages/` layout and a README that explains it.

## Skills

- **`new-package`** — Scaffolds a package in `packages/`. It does not create new top-level directories (those need an RFC) or apps (those go in `apps/`).

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, Kiro IDE, and Kiro CLI. Install [Core](../core/README.md) (`^4.0`) first or alongside. See [Scaffold a new package](../../guides/monorepo-extras/how-to/scaffold-a-new-package.md).

## Questions

**Can it add a new top-level directory?** No. A new top-level directory needs an RFC.

**Can it add an app?** No. Apps go in `apps/`, and this skill scaffolds packages only.

**Does it work without a monorepo?** It is not useful there. `new-package` scaffolds into `packages/`, so the pack installs at repo scope only.

## Details

Scope: repo (default) · Version: 0.1.10 · Source: [packs/monorepo-extras](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/monorepo-extras)
