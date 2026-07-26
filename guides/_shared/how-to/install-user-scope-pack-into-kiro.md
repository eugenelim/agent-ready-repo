# How to: install a user-scope pack into Kiro

**Use this when:** You use Kiro and want to install a user-scope-capable pack from the catalogue into `~/.kiro/skills/`.
**Prerequisites:** Kiro CLI installed with `~/.kiro/` present and `agentbundle` CLI on your PATH; see [Prerequisites](#prerequisites).
**Result:** A user-scope pack installed at `~/.kiro/skills/` and tracked in `~/.agentbundle/state.toml`.

User-scope packs travel across projects via your IDE's per-user configuration directory. This guide covers landing one of the catalogue's user-scope-capable packs (e.g. `atlassian`, `figma`, `converters`, `contracts`) into Kiro's home tree at `~/.kiro/skills/`.

## Prerequisites

- Kiro CLI installed; `~/.kiro/` exists. The resolver detects Kiro by probing for this directory — if it isn't present yet, run any Kiro command once (e.g. `kiro --version`) to scaffold the home tree before installing.
- The agentbundle CLI installed. The fastest route is the [from-clone install](install-agentbundle-from-clone.md); see also the [zipapp release](../../../../README.md#install) on the README.

## Install

From any directory (user-scope installs don't need a project context):

```bash
agentbundle install --pack atlassian --scope user <catalogue>
```

The CLI's six-step resolver picks Kiro automatically when:

1. The pack's `[pack.install] allowed-adapters` includes `kiro` (the install refuses if the pack you chose doesn't).
2. Only `~/.kiro/` is present among the user-scope-capable adapters' CLI homes (`~/.claude/`, `~/.kiro/`, `~/.codex/`).

If multiple adapter homes are populated (a multi-IDE machine), the resolver picks the first match in the pack's `allowed-adapters` declared order. To override, pass `--adapter kiro` explicitly.

On success, stdout includes:

```
installed: atlassian @ user via kiro
```

with an optional `(other declared adapters: …; use --adapter to override)` suffix when more than one CLI home is populated.

## Where the pack lands

```
~/.kiro/skills/atlassian-jira/SKILL.md
~/.kiro/skills/atlassian-jira-align/SKILL.md
~/.kiro/skills/atlassian-confluence-crawler/SKILL.md
…
~/.agentbundle/credentials.env   (created on first credentialed-skill run)
~/.agentbundle/state.toml         (the install-time state file)
```

The state file records `adapter = "kiro"` for the pack — this is the hint that subsequent `agentbundle upgrade` invocations consult to avoid re-resolving against your filesystem.

## Upgrade

```bash
agentbundle upgrade --pack atlassian <catalogue>
```

Upgrade reuses the recorded adapter from `~/.agentbundle/state.toml`, so adding a second CLI home post-install (e.g. installing Claude Code later) does not migrate the pack — it stays at Kiro until you uninstall and reinstall.

## Uninstall

```bash
agentbundle uninstall --pack atlassian --scope user
```

Removes the `~/.kiro/skills/<pack>/` tree the pack owns and updates `~/.agentbundle/state.toml`. CLI-shared infrastructure under `~/.agentbundle/` stays — that's `agentbundle`'s own state, not the pack's.

## See also

- [Install agentbundle from a clone](install-agentbundle-from-clone.md)
- [Install a user-scope pack into Codex](install-user-scope-pack-into-codex.md)
- [Upgrade an installed pack](upgrade-packs.md)
- [`docs/rfc/0011-pack-allowed-adapters.md`](../../../rfc/0011-pack-allowed-adapters.md) — the contract
