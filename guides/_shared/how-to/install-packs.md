---
title: "Install packs for your agent"
summary: "Install packs for Claude Code, Codex, Cursor, Copilot, Gemini CLI, or Kiro, one at a time or as a profile."
pack: _shared
kind: how-to
aliases:
  - guides/_shared/explanation/install-routes
  - guides/_shared/how-to/install-a-profile
  - guides/_shared/how-to/install-user-scope-pack-into-codex
  - guides/_shared/how-to/install-user-scope-pack-into-kiro
  - guides/_shared/how-to/install-the-whole-lifecycle
  - guides/_shared/how-to/preview-install-or-upgrade
---

# Install packs for your agent

Install a pack and your agent picks up its skills in the next session. You need [`agentbundle`](install-agentbundle.md).

## Install a pack

See what the catalogue offers, then install a pack from inside your repository:

```bash
agentbundle list-packs
cd path/to/your-repo
agentbundle install --pack core
```

Start a new agent session so it loads the new skills.

## Ask your agent

Your agent can run the install for you:

```text
Use agentbundle to install the core pack into this repository.
```

It runs the command and tells you to start a new session.

## Choose a scope

Install a personal tool into your home folder instead of the repository:

```bash
agentbundle install --pack desk-research --scope user
```

Repo scope is shared with your team and versioned with the code. User scope follows you into every repository. The [Packs page](/agent-ready-repo/docs/packs/) shows each pack's default.

## Pick your agent

In a repository, `agentbundle` installs for Claude Code unless you name another agent:

```bash
agentbundle install --pack core --adapter codex
```

For a user-scope install it looks in your home folder for `~/.claude/`, `~/.codex/`, or `~/.kiro/` and picks the first match. Cursor and Gemini CLI are never detected, so name them with `--adapter`, or [save a default](configure-agentbundle.md#set-your-agent) once.

The adapters are `claude-code`, `codex`, `cursor`, `copilot`, `gemini`, `kiro-ide`, and `kiro-cli`. [Adapter support](../reference/adapter-support.md) shows what each one receives.

## Install a profile

Install a ready-made set of packs in one command:

```bash
agentbundle install --profile inception
```

`inception` and `solution-architect` install at user scope. `full-ceremony` installs the team set at repo scope.

## Preview first

See every file an install would write, without writing anything:

```bash
agentbundle install --pack core --dry-run
```

## Install as a Claude plugin

In Claude Code, add the marketplace once, then install a pack:

```bash
claude plugin marketplace add eugenelim/agent-ready-repo
claude plugin install desk-research@agent-ready-repo
```

**The plugin route is user-scope only.** A plugin lives in your global cache, so the marketplace carries only packs whose `allowed-scopes` admits `user`. Repo-scoped packs install with `agentbundle`: `core`, `catalogue-curation`, `governance-extras`, `iac-terraform`, `monorepo-extras`, `release-engineering`, `user-guide-diataxis`.

## After the install

Installing `core` at repo scope ends with a `Next:` line. It asks you to run `adapt-to-project`, a read-only check of how ready the repository is.

Local scope deliberately omits seeds. No marker, layout section, or chained `adapt`. Plugin and APM installs print no `Next:` line, so run `adapt-to-project` yourself.

A lifecycle hook may repeat that nudge. It is never the only path: the installer guarantees the projected files, the state for the scope you chose, and the printed line. It does not guarantee hook execution or context injection. A `SessionStart` hook derived into each **published** pack's `.claude-plugin/plugin.json` can run the marker writer.

Next, [configure agentbundle](configure-agentbundle.md) to save your agent. The [command reference](../reference/agentbundle.md#install-details) covers profiles, Codex and Kiro detection, and preview output in full.
