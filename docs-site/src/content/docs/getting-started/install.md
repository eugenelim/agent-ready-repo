---
title: Install Routes
description: Four ways to get packs into your agent.
---

Four ways to get packs into your agent. Pick the one that matches your workflow.

## Route 1: agentbundle CLI (recommended)

The standard route. Installs into the current repo (repo scope) or your home directory (user scope).

```bash
python -m pip install agentbundle
agentbundle install --pack core
```

### Key commands

```bash
# See all available packs
agentbundle list-packs

# See what you have installed
agentbundle list-installed

# Install at user scope (follows you across every project)
agentbundle install --pack desk-research --scope user

# Install a profile (curated pack bundle)
agentbundle install --profile solution-architect

# Preview before writing any files
agentbundle install --pack core --dry-run

# Upgrade to the latest version
agentbundle upgrade --pack core

# Target a specific agent adapter
agentbundle install --pack core --adapter cursor
agentbundle config set adapter cursor  # set once, apply everywhere
```

### Adapters

Auto-detects your agent. Override with `--adapter`:

| Adapter flag | Agent |
|---|---|
| `claude-code` | Claude Code (default fallback) |
| `codex` | OpenAI Codex |
| `cursor` | Cursor |
| `copilot` | GitHub Copilot |
| `gemini` | Gemini CLI |
| `kiro-ide` | Kiro IDE |
| `kiro-cli` | Kiro CLI |

## Route 2: Claude Plugins

Install directly from Claude's plugin marketplace without touching the CLI.

First, add the marketplace (one-time setup):

```bash
claude plugin marketplace add eugenelim/agent-ready-repo
```

Then install any pack using `<pack>@agent-ready-repo`:

```bash
claude plugin install core@agent-ready-repo
claude plugin install desk-research@agent-ready-repo
```

:::caution[Added this marketplace before 2026-08?]
Run `claude plugin marketplace update agent-ready-repo`, then reinstall your
packs. Entries published before then used a plugin source Claude Code could not
resolve to a subdirectory, so `claude plugin install` reported success but
delivered nothing. Check with `claude plugin details <pack>@agent-ready-repo` —
a healthy pack reports a non-zero skill count. A cached catalogue keeps serving
the old entries until you update it.
:::

Available for all 20 packs (catalogue-curation is an operator-only pack not published to the marketplace). Pack names match the directory names under `packs/`.

## Route 3: APM (Agent Package Manager)

For teams using APM as their primary package manager:

```bash
apm install eugenelim/core
apm install eugenelim/desk-research --scope user
```

## Route 4: Local clone

For catalogue contributors or teams building their own fork:

```bash
git clone https://github.com/eugenelim/agent-ready-repo
cd agent-ready-repo
python -m pip install -e packages/agentbundle
agentbundle install --pack core
```

With an editable install, `agentbundle` defaults to the local clone as its catalogue source — so `list-packs` shows local state and installs come from your working tree.

---

## Scopes

Every pack has a natural install scope:

| Scope | Where it lands | When to use |
|---|---|---|
| `repo` | `.claude/skills/`, `.codex/`, etc. in the current repo | Skills specific to this project |
| `user` | `~/.claude/skills/`, etc. in your home dir | Skills that follow you across all repos |

The pack's README documents which scope it defaults to. Override with `--scope user` or `--scope repo`.

## File safety

Installs never silently overwrite your edits. If a file you've modified would be overwritten, it lands as `<name>.upstream` instead — a companion file you merge at your own pace. Your edits are always preserved.

[File safety contract explained](../guides/_shared/explanation/file-safety-contract/)
