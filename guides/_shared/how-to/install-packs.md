---
title: "Install packs for your agent"
summary: "Install packs into a repository or your home directory for Claude Code, Codex, Cursor, Copilot, Gemini CLI, or Kiro, with profiles and a dry-run preview."
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

Install one pack, a curated set, or the whole lifecycle into the agent tool you use. You need the [`agentbundle` command](install-agentbundle.md).

## Install a pack

```bash
agentbundle list-packs
agentbundle install --pack core
```

`<catalogue>` is an optional last argument: a local path or `git+https://github.com/<owner>/<catalogue>`. Leave it out to use your configured source. See [Configure agentbundle](configure-agentbundle.md#choose-the-catalogue-source).

```bash
agentbundle install --pack <name> git+https://github.com/<owner>/<catalogue>
agentbundle list-installed
```

`install --pack` refuses an in-place re-install. Use [`upgrade`](upgrade-packs.md) to change a version.

The command hashes every projected file into `.agentbundle-state.toml`, so later upgrades are exact. See [After the install](#after-the-install) for the next step.

## Choose a scope

Each pack has a default scope. `--scope` overrides it where the pack allows both.

`--scope repo` writes into the current repository, so the whole team shares the pack and it is versioned with the code.

`--scope user` writes into your home directory, so the pack follows you across every repository.

```bash
agentbundle install --pack desk-research --scope user
```

Each pack declares which scopes it allows. The [Packs page](/agent-ready-repo/docs/packs/) lists the default scope of every pack.

## Target an agent

The command detects your agent and falls back to Claude Code. Override it with `--adapter`:

```bash
agentbundle install --pack core --adapter codex
agentbundle install --pack core --adapter cursor
agentbundle install --pack desk-research --scope user --adapter codex
```

| `--adapter` | Agent | Gets |
| --- | --- | --- |
| `claude-code` | Claude Code | Skills, subagents, commands, hooks |
| `codex` | OpenAI Codex | Skills, subagents, hooks. No slash commands. |
| `cursor` | Cursor | Skills, subagents without a tool allowlist, commands, hooks |
| `copilot` | GitHub Copilot | Skills, subagents, hooks. Repo-scope hooks need a trusted folder. Repo scope only. |
| `gemini` | Gemini CLI | Skills, subagents, commands, hooks |
| `kiro-ide` | Kiro IDE | Skills, subagents, hook files. No commands. |
| `kiro-cli` | Kiro CLI | Skills, subagents, hooks. No commands. |

`kiro` is a deprecated alias for `kiro-ide`. See [Adapter support](../reference/adapter-support.md) for the full matrix. To pin a default, see [Configure agentbundle](configure-agentbundle.md#set-a-default-adapter).

`--adapter` works at both scopes. It must be in the pack's `allowed-adapters`. If it is not, the install refuses and names the field. An upgrade keeps the adapter the pack was installed with.

## Codex and Kiro user-scope notes

User-scope packs include `atlassian`, `figma`, `converters`, and `contracts`.

**Codex.** The command looks for `~/.codex/` or `~/.agents/skills/`. Either one is enough. Skills land in `~/.agents/skills/`.

```bash
agentbundle install --pack figma --scope user <catalogue>
```

```text
installed: figma @ user via codex
```

State goes in `~/.agentbundle/state.toml`. Credentials go in `~/.agentbundle/credentials.env`, created on the first credentialed-skill run. `~/.codex/plugins/` is Codex's own plugin route and does not share state with this one. Pick one route per pack.

**Kiro.** The command looks for `~/.kiro/`. If it is missing, run any Kiro command once, such as `kiro --version`. Skills land in `~/.kiro/skills/`.

```bash
agentbundle install --pack atlassian --scope user <catalogue>
```

```text
installed: atlassian @ user via kiro
```

With several IDE homes present, the command takes the first match in the pack's `allowed-adapters` order. Pass `--adapter` to choose.

Upgrade reuses the adapter recorded in state, so adding a second IDE later does not move the pack:

```bash
agentbundle upgrade --pack figma <catalogue>
```

To change adapter, uninstall and install again with `--adapter`:

```bash
agentbundle uninstall --pack figma --scope user
agentbundle install --pack figma --scope user --adapter kiro-ide <catalogue>
```

## Install a profile

A profile is a curated set of packs at one fixed scope.

```bash
agentbundle list-profiles <catalogue>
agentbundle install --profile <name> <catalogue>
agentbundle install --profile full-ceremony git+https://github.com/<owner>/<catalogue>
agentbundle install --profile solution-architect <catalogue> --adapter codex
```

| Profile | Scope | Installs |
| --- | --- | --- |
| `solution-architect` | user | `architect`, `desk-research`, `contracts` |
| `inception` | user | `desk-research`, `product-engineering`, `architect` |
| `full-ceremony` | repo | `core`, `governance-extras`, `product-documentation`, `monorepo-extras` |

The command checks every pack's preconditions before it writes anything. It installs in dependency order onto one adapter. A pack already installed is reported `already present, skipped`.

:::caution
- `--profile` and `--pack` cannot be combined.
- `--scope` is rejected with `--profile`. The profile sets its scope.
- A pack already installed at the other scope blocks the profile. Uninstall it there first.
- A failure mid-batch is not rolled back. Run the command again to resume.
- There is no `upgrade --profile` or `uninstall --profile`. Act on each pack, for example `agentbundle uninstall --pack <name>`.
:::

## Install the whole lifecycle

No single command does it, because shaping is user scope and building is repo scope. Run these in order.

```bash
agentbundle install --profile full-ceremony .
agentbundle install --profile inception
```

In a fresh agent session, run `adapt-to-project` for a read-only readiness check. For a new repository, use `init-project` instead. Then install the packs your team uses from neither profile. The [Packs page](/agent-ready-repo/docs/packs/) lists every pack with what it does and its default scope. For example:

```bash
agentbundle install --pack release-engineering .
```

`release-engineering` needs `core`, so install `full-ceremony` first. Check the result with `workspace status` in a new session. A just-installed skill is not available to a session that was already running.

## Preview before you install

```bash
agentbundle install --pack core --dry-run
agentbundle install <catalogue-uri> --pack core --dry-run
agentbundle upgrade --pack core --dry-run
agentbundle upgrade <catalogue-uri> --pack core --dry-run
```

The `--dry-run` flag writes no file, companion, state, or marker. Each line reads `<action> <tier> <path>`.

```text
overwrite tier-1 .claude/agents/reviewer.md
companion tier-2 .claude/skills/work-loop/SKILL.md -> .claude/skills/work-loop/SKILL.upstream.md
dry-run: 20 file(s) — 19 overwrite, 1 companion. Nothing written.
```

- `create` is a new file. `overwrite` replaces a file the bundle owns. `companion` keeps your edit and writes the upstream copy beside it.
- It lists projected files, not governance seeds such as `AGENTS.md`. A real install still creates them.
- `agentbundle install --dry-run --force` is refused. `--force` removes leftover files and rewrites state.
- A preview exits 0 even with companions, because `--dry-run` only informs. `agentbundle diff` is the verb that gates on drift. It exits non-zero when the real run would fail early, for example on an unresolvable catalogue.

## Install as a Claude plugin

Claude Code can install user-scope packs as plugins, with auto-update. A `SessionStart` hook derived into each **published** pack's `.claude-plugin/plugin.json` can run the marker writer.

```bash
claude plugin marketplace add <owner>/<catalogue>
claude plugin install <pack>@<catalogue>
```

For this catalogue:

```bash
claude plugin marketplace add eugenelim/agent-ready-repo
claude plugin install architect@agent-ready-repo
claude plugin install desk-research@agent-ready-repo
```

Inside a Claude Code session, the same steps are `/plugin marketplace add <owner>/<catalogue>` and `/plugin install <pack>@<catalogue>`. Update with `/plugin update <pack>@<catalogue>`. The Claude apps use **Customize › Plugins › Personal plugins › "+"** instead. Register the marketplace in each place you work.

**The plugin route is user-scope only.** A plugin lives in your global cache, so the marketplace carries only packs whose `allowed-scopes` admits `user`. Repo-scoped packs install with `agentbundle`: `core`, `governance-extras`, `iac-terraform`, `monorepo-extras`, `release-engineering`, `user-guide-diataxis`.

Plugin and APM installs print no `Next:` line. Invoke `adapt-to-project` yourself, and run `agentbundle init-state` once so upgrades have a baseline.

:::caution
Added the marketplace before 2026-08? Run `claude plugin marketplace update <catalogue>` and reinstall your packs. Older entries installed but delivered nothing. Check with `claude plugin details <pack>@<catalogue>`, for example `claude plugin details <pack>@agent-ready-repo`; `claude plugin marketplace update agent-ready-repo` refreshes this catalogue. A healthy pack reports a non-zero skill count.
:::

Catalogue maintainers can emit the APM and Claude plugin dist trees at repo scope. The plugin tree (`claude-plugins/<pack>/`) is written only for packs whose `allowed-scopes` admits `user`, so a repo-only pack such as `core` gets `apm/<pack>/` alone. This flag cannot be used with `--adapter`:

```bash
agentbundle install --pack architect --scope repo --emit-install-routes .
```

## After the install

Installing `core` at repo or local scope ends with this line:

```text
Next:     Ask your agent to run adapt-to-project for a read-only readiness check; start a new session if the skill is unavailable.
```

What each scope leaves behind:

- Repo scope writes seeds when the pack declares them, writes `.adapt-install-marker.toml`, and chains `agentbundle adapt`.
- Local scope deliberately omits seeds. No marker, layout section, or chained `adapt`.
- Plugin and APM installs print nothing, so invoke `adapt-to-project` directly.

A lifecycle hook may repeat that nudge. It is never the only path. Whether a hook runs is the runtime's decision, so the installer guarantees the projected files, the state for the scope you chose, and the printed line. It does not guarantee hook execution or context injection.
