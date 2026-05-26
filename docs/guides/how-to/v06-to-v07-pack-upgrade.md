# How to: upgrade packs from contract v0.6 to v0.7

> Status: stable. Covers the RFC-0012 transition for both pack
> authors and adopters.

RFC-0012 bumps the adapter contract from v0.6 to v0.7 and ships a
new repo-scope default behaviour: `agentbundle install --pack X
--scope repo .` now lands the pack at the resolved adapter's
project-local skills directory (`<repo>/.claude/skills/`,
`<repo>/.kiro/skills/`, `<repo>/.agents/skills/`, or
`<repo>/.github/instructions/`). The legacy dist-tree shape
(`<repo>/claude-plugins/<pack>/`, `<repo>/apm/<pack>/`) moves behind
the explicit `--emit-install-routes` flag.

## Pack-author surface: bump `[pack.adapter-contract] version`

The bump itself is one line in every pack's `pack.toml`:

```toml
[pack.adapter-contract]
version = "0.7"          # was "0.6" (or "0.2" for repo-only packs)
```

`[pack.install] allowed-adapters` is unchanged from RFC-0011. The
schema accepts the same shape.

### Two starting points

- **User-scope-capable packs** (`atlassian`, `figma`, `converters`,
  `contracts` in the bundle's own catalogue) move from v0.6 → v0.7.
  The CLI's six-step (0–5) resolver picks the same adapter the v0.6
  lookup would have picked; downstream packs that declare an
  identical `allowed-adapters` list don't see any behaviour change
  at user scope.

- **Repo-only packs** (`core`, `governance-extras`,
  `user-guide-diataxis`, `monorepo-extras`) jump from v0.2 → v0.7
  in one step. **This is load-bearing**: without the bump the
  resolver's legacy heuristic at step 5 still fires at repo scope
  for these packs and cannot route them to `codex` or `copilot`
  via the no-flag default. RFC-0012's Drawback #7 names this
  case explicitly.

## Adopter surface: visible on-disk diff at `--scope repo`

The behavioural change at repo scope is intentional. Three flavours
of adopter walk three different paths.

### Adopter A — Claude Code, no flags

```
agentbundle install --pack core --scope repo .
```

The pack lands at `<repo>/.claude/skills/`, `<repo>/.claude/agents/`,
etc. Pre-RFC-0012 this command landed at
`<repo>/claude-plugins/core/...` and `<repo>/apm/core/...`. The
state file records `adapter = "claude-code"` and stdout reads
`installed: core @ repo via claude-code`.

### Adopter B — Kiro / Codex / Copilot

```
agentbundle install --pack atlassian --scope repo --adapter kiro .
agentbundle install --pack atlassian --scope repo --adapter codex .
agentbundle install --pack atlassian --scope repo --adapter copilot .
```

Each lands at the IDE's project-local directory:
`<repo>/.kiro/skills/`, `<repo>/.agents/skills/`, or
`<repo>/.github/instructions/`. `--adapter` is now admitted at both
scopes (the legacy `install: --adapter is bound to --scope user`
refusal is gone).

### Adopter C — catalogue maintainer scripting publishing

If your existing script runs `agentbundle install --scope repo .`
to produce dist-tree artifacts (`claude-plugins/<pack>/`,
`apm/<pack>/`) for a catalogue publishing job, add
`--emit-install-routes`:

```
agentbundle install --pack core --scope repo --emit-install-routes .
```

This restores the pre-RFC-0012 dist-tree producer behaviour. The
flag carries a `DeprecationWarning` from day one and is targeted
for removal in the next minor — RFC-0012 § *Alternatives considered*
#6.

## Who is affected by the v0.6 → v0.7 transition

The visible-diff case is **adopters who passed `--scope repo`
against one of the four user-scope-capable packs (`atlassian`,
`figma`, `converters`, `contracts`) in the RFC-0011 → RFC-0012
window**. Their existing on-disk layout is the dist-tree shape;
the post-RFC-0012 default would land them in the per-IDE shape
without an explicit fix.

Self-identification predicate:

```bash
ls <repo>/claude-plugins/ <repo>/apm/ 2>/dev/null
```

If the listing finds pack subdirectories for any of those four
packs, you are in scope. The corrective path:

1. **Uninstall the dist-tree shape**:

   ```bash
   agentbundle uninstall --pack atlassian --root <repo>
   ```

   Repeat for every pack the listing surfaced.

2. **Reinstall at the new per-IDE shape**:

   ```bash
   agentbundle install --pack atlassian --scope repo --adapter <kiro|codex|copilot|claude-code> .
   ```

   Or omit `--adapter` to pick up `DEFAULT_ADAPTER` (currently
   `claude-code`). The install records the resolved adapter in
   `<repo>/.agentbundle-state.toml` so subsequent upgrades respect
   the choice (RFC-0011 AC10b's state-hint short-circuit extends to
   repo scope).

If both `<repo>/claude-plugins/` and `<repo>/apm/` are absent or
empty, you are not in scope.

## Trigger (b) cross-invocation false positive

The CLI's orphan-projection refusal at install start fires when
`state.toml` has no row for the pack AND on-disk artifacts exist
under the resolved adapter's `allowed-prefixes.repo`. This catches
prior installs that crashed mid-write.

**The same signal also fires** when an adopter ran
`--emit-install-routes` legitimately for one install (laying
dist-tree files) and *then* ran `--scope repo` without the flag on
the same root for a different pack — the CLI can't distinguish "a
prior install crashed" from "dist-tree files remain from a
deliberate prior invocation". The pinned stderr message already
names `--force` as the resolution:

```
install: orphan projection files for pack <name> at <paths> —
prior install interrupted; rerun with --force to clean and
reinstall, or delete the listed paths and rerun
```

If you recognise the listed paths as legitimate dist-tree output
from a prior `--emit-install-routes` invocation, either:

- Pass `--force` to delete them and re-run with per-IDE projection.
- Delete the listed paths by hand if you want them gone for other
  reasons.

The false positive is documented here rather than fixed via a
state-schema field because adding a `cli_version` field to
`state.toml` would have required a state-schema version bump and a
read-side migration path — both more expensive than the one-line
`--force` corrective the message already names.

## State-file semantics

`state.toml` v0.3 (unchanged by RFC-0012) tracks per-relpath SHAs.
The `[pack.<name>].adapter` field records which adapter the pack
was installed under; uninstall and upgrade consult it for the
state-hint short-circuit (RFC-0011 AC10b, now scope-uniform). The
field is omitted from the serialised state when its value equals
`DEFAULT_ADAPTER` (`"claude-code"`) — the implicit-default contract
that pre-dates RFC-0012.
