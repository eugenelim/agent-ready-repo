A pack is a set of agent workflows you install together. Each pack does one kind of work, such as research, architecture, or the build loop.

## What a pack installs

- **Skills.** Workflows your agent picks up from what you ask for.
- **Subagents.** Specialists the agent hands a bounded task, such as an independent reviewer.
- **Hooks and commands.** Automatic checks and explicit entry points, where your agent supports them.
- **Seeds and settings.** Starter files and defaults a pack needs in the repository.

Everything lands as plain files you can read. `agentbundle` installs and upgrades them; it does not run your agent.

## Repo scope

A repo-scope install writes into the repository, for example `.claude/skills/`. You commit those files with the code.

Use repo scope for how the team works. Everyone who clones the repository gets the same skills, hooks, and checks, at the same version. A change to them goes through review like any other change.

```bash
agentbundle install --pack core
```

`core`, `governance-extras`, `iac-terraform`, `monorepo-extras`, `release-engineering`, and `catalogue-curation` install only at repo scope.

## User scope

A user-scope install writes into your home folder, for example `~/.claude/skills/`. It follows you into every repository and nobody else sees it.

Use user scope for your own tools, such as research, architecture, or document conversion.

```bash
agentbundle install --pack desk-research --scope user
```

Each pack has a default scope. The tables below show it, and `--scope` overrides it where the pack allows both.

## Claude plugins

In Claude Code you can install user-scope packs from the plugin marketplace instead of with `agentbundle`:

```bash
claude plugin marketplace add eugenelim/agent-ready-repo
claude plugin install architect@agent-ready-repo
```

Repo-scope-only packs are not in the marketplace. Install those with `agentbundle`, so the team shares one version.

## Profiles

A profile installs a set of packs in one command:

| Profile | Scope | Packs |
|---|---|---|
| `inception` | user | desk-research, product-engineering, architect |
| `solution-architect` | user | architect, desk-research, contracts |
| `full-ceremony` | repo | core, governance-extras, product-documentation, monorepo-extras |

```bash
agentbundle install --profile inception
```

## Upgrade

`agentbundle upgrade --pack <name>` brings a pack to the latest version. If you edited an installed file, your version stays and the new one lands beside it as `<name>.upstream` for you to merge.
