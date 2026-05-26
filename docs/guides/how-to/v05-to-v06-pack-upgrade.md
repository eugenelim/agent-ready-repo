# How to: upgrade a pack from v0.5 to v0.6

The v0.6 adapter contract (RFC-0011 / pack-allowed-adapters) adds
one optional field — `[pack.install] allowed-adapters` — and a
new `[adapter.codex.scope]` table. This guide is for pack authors
whose packs currently declare `[pack.adapter-contract] version = "0.5"`
(or earlier) and want to opt into the new resolver behaviour.

## What changed

- A new `[pack.install] allowed-adapters` field declares which user-
  scope-capable adapters the pack travels with. Three values are
  admitted today: `claude-code`, `kiro`, `codex`.
- Codex gained a `[scope]` table in the bundled adapter contract, so
  user-scope codex installs are now a first-class resolver target.
- The legacy "look for `.apm/agents/` to decide kiro" heuristic stays
  alive for packs that don't declare `allowed-adapters` — there is no
  forced migration.

## When to bump

Bump to v0.6 + declare `allowed-adapters` when:

- Your pack ships skills (or other content) that is portable across
  Claude Code, Kiro, and Codex — i.e., no IDE-specific agent shape,
  no harness-pinned binaries.
- You want adopters' user-scope installs to land in their IDE's home
  tree, not just Claude Code's.

Stay at v0.5 (or earlier) when:

- Your pack is repo-only.
- Your pack is meaningfully Claude-Code-specific (uses subagents,
  binds to Claude-Code-only frontmatter).

## How to bump

In `packs/<name>/pack.toml`:

```toml
[pack.adapter-contract]
version = "0.6"

[pack.install]
default-scope = "user"
allowed-scopes = ["user", "repo"]
# RFC-0011 / pack-allowed-adapters. Declared order also drives the
# greenfield fallback (claude-code matches DEFAULT_USER_SCOPE_ADAPTER).
allowed-adapters = ["claude-code", "kiro", "codex"]
```

Run `agentbundle validate packs/<name>` to confirm the new field
schema-validates and clears the cross-field user-scope-capability
check.

## Refusal paths the validator now enforces

- **Empty array** — `allowed-adapters = []` is refused. The field is
  optional; omit it instead of declaring an empty list.
- **Duplicates** — `["claude-code", "claude-code"]` is refused.
- **Unknown adapters** — `["windsurf"]` is refused because windsurf
  is not in the bundled contract's shipped-adapter set.
- **User-scope-incapable adapter on a user-scope pack** —
  `allowed-scopes = ["user"]` with `allowed-adapters = ["copilot"]` is
  refused because Copilot has no `[adapter.copilot.scope].user` table
  (Copilot user-scope is explicitly out of scope per the RFC; a
  sibling RFC would change this).

The validator messages are pinned in the spec; tests in the catalogue
assert against the exact strings.

## User-scope-only semantics

`allowed-adapters` has no repo-scope semantics. `agentbundle install
--scope repo` continues to emit `dist/apm/<pack>/` and
`dist/claude-plugins/<pack>/` regardless of `allowed-adapters`. The
post-merge erratum on RFC-0011 spells this out — the original
proposal carried a repo-scope filter that pre-EXECUTE review showed
to be a no-op against the actual repo-scope projection shape.

## What happens at install time

For v0.6+ packs declaring `allowed-adapters`:

1. The CLI refuses publisher-vs-installer drift early — a pack
   declaring an adapter the bundled contract no longer ships fails
   before any byte is written, with `install: pack '<name>' declares
   allowed-adapter '<adapter>' which is not admitted by adapter
   contract v<X.Y> shipped with agentbundle <cli-version>`.
2. `--adapter <name>` (if passed) wins, validated against the pack's
   `allowed-adapters` set.
3. The state-recorded adapter (on upgrade) wins next.
4. Otherwise, the CLI walks `allowed-adapters` in declared order
   against the adopter's populated `~/.<ide>/` homes; first match
   wins.
5. Greenfield (no CLI home present) falls back to
   `DEFAULT_USER_SCOPE_ADAPTER` (currently `claude-code`); declared
   order otherwise.

## The legacy path

A `< 0.6` pack — or a v0.6+ pack that omits `allowed-adapters` —
falls through to the legacy heuristic at step 5: a pack shipping
`.apm/agents/<name>.md` resolves to Kiro; everything else resolves
to Claude Code. No behavioural change from v0.5.

## See also

- [`docs/rfc/0011-pack-allowed-adapters.md`](../../rfc/0011-pack-allowed-adapters.md)
- [`docs/specs/pack-allowed-adapters/spec.md`](../../specs/pack-allowed-adapters/spec.md)
- [Install a user-scope pack into Kiro](install-user-scope-pack-into-kiro.md)
- [Install a user-scope pack into Codex](install-user-scope-pack-into-codex.md)
