# Configure your agent adapter

**Use this when:** You work across several IDEs or want to pin a non-default adapter instead of relying on auto-detection.
**Prerequisites:** `agentbundle` CLI on your PATH.
**Result:** A pinned default adapter (or per-install `--adapter` override) so every install targets the correct IDE without re-specifying the flag.

Installs auto-detect the agent you're working in and fall back to **Claude Code** when there's nothing to detect. To work across several IDEs — or to pin a different default — configure the adapter explicitly.

## Pin a default adapter

```bash
agentbundle config set adapter cursor
```

This is user-global: set it once and it applies whether you install into a repo or at user scope. Every later install targets the pinned adapter.

## Override for a single install

```bash
# Repo scope
agentbundle install --pack core --adapter codex

# User scope
agentbundle install --pack desk-research --scope user --adapter codex
```

Per-install `--adapter` beats the pinned default, which beats auto-detect. Re-running an install keeps whatever adapter that install already uses — an upgrade won't reset it.

## Supported agents

`claude-code`, `cursor`, `codex`, `copilot`, `gemini`, `kiro-ide`, `kiro-cli`

See the [adapter support matrix](../reference/adapter-support.md) for a breakdown of which agent supports skills, subagents, commands, and hooks — and where each gracefully degrades.
