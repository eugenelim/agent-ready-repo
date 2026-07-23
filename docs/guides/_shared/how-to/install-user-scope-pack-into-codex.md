# How to: install a user-scope pack into Codex

This guide covers landing a user-scope-capable pack from the catalogue into Codex's home tree at `~/.agents/skills/`.

## Prerequisites

- Codex CLI installed. The resolver probes for *either* `~/.codex/` (Codex CLI's config home) *or* `~/.agents/skills/` (the skills root the projection writes to). Having either is enough — if you haven't populated `~/.codex/` yet, the first install will create `~/.agents/skills/` itself.
- The agentbundle CLI installed (see [from-clone](install-agentbundle-from-clone.md) or the README's zipapp route).

## Install

```bash
agentbundle install --pack figma --scope user <catalogue>
```

The resolver picks Codex automatically when:

1. The pack's `[pack.install] allowed-adapters` includes `codex` (the install refuses if the pack you chose doesn't).
2. Only `~/.codex/` or `~/.agents/skills/` is present (multi-IDE machines tie-break on declared order; pass `--adapter codex` to override).

On success:

```
installed: figma @ user via codex
```

## Where the pack lands

```
~/.agents/skills/figma-figma/SKILL.md
~/.agents/skills/figma-figma/scripts/cli.py
~/.agentbundle/credentials.env   (created on first credentialed-skill run)
~/.agentbundle/state.toml
```

Codex's skills root is `~/.agents/skills/` regardless of where the Codex CLI's own config lives. The asymmetry — probe at `~/.codex/`, write to `~/.agents/skills/` — is intentional: it matches Codex CLI's documented behaviour and is encoded in the `[adapter.codex.scope]` table of the bundled adapter contract (v0.6+).

## Interaction with `~/.codex/plugins/`

`~/.codex/plugins/` is Codex CLI's marketplace install route. This guide covers the `agentbundle install` CLI route, which writes `~/.agents/skills/` directly. The two surfaces don't share state — Codex's plugin manager doesn't see agentbundle-installed packs, and vice versa. A sibling RFC (not yet opened) would add codex-plugins parity; until then, pick one route per pack and stick with it.

## Upgrade

```bash
agentbundle upgrade --pack figma <catalogue>
```

Upgrade reuses the recorded adapter from state; cross-adapter migration requires uninstall + reinstall.

## Uninstall

```bash
agentbundle uninstall --pack figma --scope user
```

## See also

- [Install agentbundle from a clone](install-agentbundle-from-clone.md)
- [Install a user-scope pack into Kiro](install-user-scope-pack-into-kiro.md)
- [Upgrade an installed pack](upgrade-packs.md)
- [`docs/rfc/0011-pack-allowed-adapters.md`](../../../rfc/0011-pack-allowed-adapters.md)
- [`docs/rfc/0009-codex-native-skills.md`](../../../rfc/0009-codex-native-skills.md) — the projection that writes to `~/.agents/skills/`
