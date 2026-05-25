# How to upgrade a pack from contract v0.1 to v0.2

This is a one-page checklist for third-party pack authors. The v0.2 contract amendment ([RFC-0004](../../rfc/0004-install-scope-per-pack.md)) adds an **install-scope dimension** — every v0.2 pack declares whether it ships at `repo` scope, `user` scope, or both. v0.1 packs keep installing under the legacy default (`repo`), so an upgrade is optional but recommended; new packs should target v0.2 directly.

## When to upgrade

- You publish a pack to a catalogue the v0.2 CLI consumes and want to expose `--scope` semantics to adopters.
- You want adopters to see your scope choice declared in `pack.toml` instead of inferred from the CLI's legacy default.
- You ship content that genuinely fits user scope (cross-project skills, agents, commands with no per-repo dependence).

You can stay on v0.1 if your pack only ever ships at `repo` scope and you don't need the explicit declaration; the v0.2 CLI accepts v0.1 packs with implied `default-scope = "repo"`, `allowed-scopes = ["repo"]`. A stray `[pack.install]` table on a v0.1 pack is ignored at CLI consumption time.

## Fields to add

Add both tables to `pack.toml`:

```toml
[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"          # required: "repo" | "user"
allowed-scopes = ["repo"]       # optional; defaults to [default-scope]
```

`default-scope` is required when the contract version is `"0.2"`. `allowed-scopes` is optional; when omitted, it implicitly equals `[default-scope]` (i.e. "only the default").

Pack authors who want adopters to be able to install at both scopes declare:

```toml
[pack.install]
default-scope = "repo"
allowed-scopes = ["repo", "user"]
```

The cross-field invariant `default-scope ∈ allowed-scopes` is enforced in `pack.schema.json` — every consumer of the schema refuses a malformed pack identically.

## `validate` exit codes

Run `agentbundle validate <pack-path>` after editing `pack.toml`. The CLI exits non-zero (with a one-line stderr reason) on any of these:

- Missing `[pack.install]` under a v0.2 pack.
- `default-scope` value outside `{"repo", "user"}`.
- `default-scope` not in `allowed-scopes`.
- `allowed-scopes` is empty or contains a value outside `{"repo", "user"}`.

When `"user" ∈ allowed-scopes`, three additional **content rails** fire:

- **Rail A — `seeds/`.** A pack containing a non-empty `seeds/` directory cannot declare `"user" ∈ allowed-scopes`. Seeds project to per-project paths and don't survive a user-scope install.
- **Rail B — hook-shaped primitives.** A pack containing a non-empty `.apm/hooks/` or `.apm/hook-wiring/` directory cannot declare `"user" ∈ allowed-scopes` until the user-scope hook-wiring merge story is designed in a follow-up RFC.
- **Rail C — `<adapt:NAME>` markers.** A pack declaring `"user" ∈ allowed-scopes` cannot carry the marker regex `<adapt:[A-Z_][A-Z0-9_]*>` in any file under `.apm/skills/`, `.apm/agents/`, or `.apm/commands/`. Markers resolve from `.adapt-discovery.toml` to per-repo values, so a file at `~/.claude/` can only carry one resolution.

`validate` names the offending pack and the first offending path; the rails fire once per pack (Rail A first, then B, then C). `install --scope user` re-runs each rail against the resolved pack content, closing the widen-after-publish gap.

## Implied defaults — when both fields can be omitted

A v0.1 pack with no `[pack.adapter-contract]` (or `version = "0.1"`) gets the implied defaults `default-scope = "repo"`, `allowed-scopes = ["repo"]`. The v0.2 CLI accepts these packs as legacy; an adopter passing `--scope user` against a v0.1 pack is refused with the standard `allowed-scopes` violation.

A v0.2 pack with only `default-scope` declared (no `allowed-scopes`) gets the implied `allowed-scopes = [default-scope]` at CLI consumption time. The schema accepts this shape; the CLI's `--scope` resolution treats it as if `allowed-scopes` were written out explicitly.

```toml
# Example: v0.2 pack permitting only its default scope.
[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
# allowed-scopes omitted → implicitly ["repo"]
```

## When `"user" ∈ allowed-scopes` — the content-portability test

The schema rails catch the *mechanical* failures (seeds, hooks, markers). They don't catch every content-portability bug — a pack that hardcodes `AGENTS.md` paths or names this project's convention vocabulary literally will pass `validate` and still misbehave at user scope.

Apply this falsifiable test before declaring `"user" ∈ allowed-scopes`:

> *Does the same file content serve every repo verbatim?*

If yes, the pack is a user-scope candidate. If no — because the content carries `<adapt:NAME>` markers (caught by Rail C), references specific paths, names project-specific docs, or bakes in convention vocabulary (not caught) — the pack is repo-only.

## State-file migration

The `.agentbundle-state.toml` schema bumped to `"0.2"` alongside the contract. v0.1 state files are read by the v0.2 CLI as all-repo-scope; **writes** against a v0.1 file are refused with a refuse-and-explain message pointing at `agentbundle init-state --migrate`. The migration is destructive (irreversible without backup) and idempotent: an adopter running mixed CLI versions across CI and local must opt into it explicitly.

```bash
$ agentbundle init-state --migrate
init-state --migrate: /path/to/.agentbundle-state.toml → schema-version 0.2
```

For pack authors there's no state-file change to ship — adopters migrate their own state files when they upgrade the CLI.
