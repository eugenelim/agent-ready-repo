# How to: upgrade packs from contract v0.7 to v0.8

> Status: stable. Covers the docs/specs/dropped-primitives-coverage
> transition for both pack authors and adopters.

`dropped-primitives-coverage` bumps the adapter contract from v0.7
to v0.8 and ships two behavioural changes:

1. **Codex agents and hook-wiring now project natively.** Pre-v0.8
   codex dropped both primitive types silently. Post-v0.8, agents
   land at `<root>/.codex/agents/<name>.toml` (TOML format per the
   upstream codex subagents spec) and hook-wiring lands at
   `<root>/.codex/hooks.json` (merged via the existing `merge-json`
   mode, same shape as claude-code's `settings.local.json`).

2. **Dropped-primitives warning rail.** `agentbundle install`
   emits a stderr warning whenever the resolved adapter projects
   any primitive type the pack ships as `dropped`. The install
   does NOT refuse — the compatible primitives still project. The
   warning surfaces what would otherwise be silent degradation
   under codex/kiro/copilot.

## Pack-author surface: bump `[pack.adapter-contract] version`

One-line edit in every shipped pack's `pack.toml`:

```toml
[pack.adapter-contract]
version = "0.8"          # was "0.7"
```

`[pack.install] allowed-adapters` is unchanged from RFC-0011. The
schema accepts the same shape.

The eight bundled packs that bump in this PR:

  - **User-scope-capable packs** (`atlassian`, `figma`, `converters`,
    `contracts`): v0.7 → v0.8. The codex projection target changes
    from "drop agents + hook-wiring silently" to "project both
    natively" at user scope as well as repo scope.
  - **Repo-only packs** (`core`, `governance-extras`,
    `user-guide-diataxis`, `monorepo-extras`): v0.7 → v0.8. Same
    codex projection change.

Two in-tree packs deliberately stay below v0.8:

  - `architect` remains at v0.6 (predates RFC-0013).
  - `credential-brokers` remains at v0.7 (RFC-0013-only; backward-
    compat path keeps it working under the v0.8 contract).

A `< v0.8` pack at codex continues through the legacy resolver path
which still treats `agent` / `hook-wiring` as dropped — fine for
backward compatibility, but the pack won't benefit from the new
projections until it bumps.

## Adopter surface: visible on-disk diff at codex

The behavioural change at codex is the load-bearing one. Three
flavours of adopter walk three different paths.

### Adopter A — codex, fresh install

```
agentbundle install --pack core --scope repo --adapter codex .
```

Post-v0.8, `<root>/.codex/agents/<agent>.toml` and (if the pack
ships hook-wiring) `<root>/.codex/hooks.json` materialise alongside
the pre-existing `<root>/.agents/skills/<skill>/SKILL.md`. The
warning rail names `command(s)` as the one remaining drop:

```
warning: pack core ships 1 command that codex projects as 'dropped';
these primitives will not be installed. The compatible primitives
(agents, hook-bodies, hook-wirings, and skills) will proceed.
```

`command` stays dropped because the upstream codex CLI deprecated
its custom-prompts directory in favour of skills (see
https://developers.openai.com/codex/custom-prompts).

### Adopter B — codex, previously installed under v0.7

If you installed a multi-primitive pack via `--adapter codex` while
the catalogue was at v0.7, your install has a state row + skills +
hook-bodies on disk, but no `<root>/.codex/agents/` or
`<root>/.codex/hooks.json` (those types were `dropped`). The v0.8
projection won't pick up automatically:

  - `agentbundle install` (without `--force`) refuses with
    `already installed; use 'upgrade'`.
  - `agentbundle upgrade` at repo scope uses the dist-tree renderer
    per RFC-0012's Ask-first surface, so it doesn't re-project
    under the v0.8 contract either.
  - `agentbundle install --force` does NOT auto-detect this case
    (AC24(b) shape-mismatch fires on dist-tree files only, not on
    missing-new-projection-paths).

The documented migration path is a **two-step uninstall + install**:

```
agentbundle uninstall --pack <pack> --scope repo .
agentbundle install --pack <pack> --scope repo --adapter codex .
```

Auto-detection of this case is named as an out-of-scope follow-on;
the two-step path is the supported migration today.

### Adopter C — kiro / copilot / claude-code

No on-disk diff at the projection layer for these adapters
(claude-code projects all 5 primitives; kiro 4 of 5 with command
dropped; copilot 2 of 5 with agent + command + hook-wiring dropped).

What's new for non-codex adopters: the warning rail fires at install
time naming what each adapter drops.

  - **claude-code**: silent (no dropped modes).
  - **kiro**: warning names `command` only.
  - **copilot**: warning names `agent`, `command`, and `hook-wiring`.
    Install still completes with rc 0 — the skills + hook-bodies
    project as before.

## Warning rail purpose: visibility, not refusal

The rail exists so adopters see partial installs up front instead
of discovering missing primitives weeks later. Common patterns:

  - **A `core` install via `--adapter copilot` proceeds with skills
    + hook-bodies; agents/commands/hook-wiring don't land.** The
    warning names this clearly. If the adopter needs agents or
    hook-wiring, they switch to `--adapter codex` (now that codex
    projects them natively) or `--adapter claude-code`.
  - **A skills-only pack installs silently under any adapter.** The
    rail's trigger requires the pack to ship at least one drop-
    eligible primitive AND the resolved adapter to drop that type.
    `governance-extras` (skills-only) against copilot fires no
    warning.

The warning short-circuits once per `(root, pack, adapter, scope)`
per process, so repeat `install --force` invocations don't re-emit.
A future RFC can add `--accept-degraded` to silence the rail
entirely if telemetry shows it's been learned-ignored — that's out
of scope for this guide.

## Per-file hook-wiring drops on incompatible adapters

The v0.7 → v0.8 warning rail above fires at the **primitive-type** level:
when an adapter's contract marks a whole primitive type as `dropped`
(Kiro drops all `command`s; Copilot drops `agent` + `command` +
`hook-wiring`), the install proceeds and the rail warns. The follow-on
spec [`incompatible-hook-event-drop`](../../specs/incompatible-hook-event-drop/spec.md)
adds a **per-file** layer to the same warning rail for hook-wirings
whose event isn't in the target adapter's vocabulary.

The motivating concrete case: `packs/core/.apm/hook-wiring/session-start.toml`
declares `[[hooks.SessionStart]]`. Claude Code's `SessionStart` event has
no equivalent in Kiro CLI's `agent-event-vocabulary`
(`agentSpawn / userPromptSubmit / preToolUse / postToolUse / stop`)
or in Kiro IDE's `ide-event-vocabulary`. Pre-spec, `agentbundle validate
packs/core` refused with exit 1 — the whole pack was un-installable
against Kiro because of this one file. Post-spec:

```
$ agentbundle install --pack core --scope repo --adapter kiro .
warning: pack core ships 1 command that kiro projects as 'dropped'; these
primitives will not be installed. Additionally, the following hook-wiring
file(s) will be skipped (event not in adapter vocabulary + kiro requires
'attach-to-agent'): hook-wiring/session-start.toml. The compatible
primitives (agents, hook-bodies, hook-wirings, and skills) will proceed.

$ echo $?
0
```

(The compatible-primitives list is pluralized + lexicographically sorted
+ serial-comma-plus-`and` joined — same grammar PR #156 shipped for the
primitive-type clause. The list names *type-level* compatible primitives;
in the kiro+core case `hook-wirings` appears even though the one file
got dropped because the type itself is still projected for adapters
that admit non-`SessionStart` events.)

Skills, agents, and the pack's other hook-wirings (if any) project
normally. The single incompatible file is named in the warning and
skipped.

`agentbundle validate <pack>` becomes informational rather than refusing:

```
$ agentbundle validate packs/core
info: pack core: the following hook-wiring file(s) will not project to kiro
(event not in adapter vocabulary + kiro requires 'attach-to-agent'):
hook-wiring/session-start.toml.

$ echo $?
0
```

The `info:` line goes to **stdout** (validate's stdout was empty
pre-spec; no CI script can depend on text that didn't exist). The
exit code becomes 0 — the pack is valid; the file just doesn't carry
to every adapter.

**Install-vs-validate parse-fail asymmetry.** A hook-wiring TOML that
**fails to parse** (malformed syntax) has split semantics: `agentbundle
validate` refuses with exit 1 and the existing `failed to parse`
substring on stderr (correctness rail); `agentbundle install`
enumerates the file as a drop entry with reason category
`hook-wiring TOML failed to parse` (single backtick-wrapped phrase) and proceeds. The split is intentional: validate is the
development-time gate where parse failures are loud bugs to fix;
install is the adopter-time degradation rail where the parse failure
becomes one more reason a file won't project. Adopters running
install-without-validate see the file named in the warning rather
than a silent absence.

**What still refuses with exit 1 at validate:**

  - Symlink under `.apm/hook-wiring/` or `.apm/agents/` (security).
  - Malformed `.toml` that fails `tomllib.loads` (correctness).
  - `attach-to-agent = "ghost-agent"` referencing an agent file that
    isn't in `.apm/agents/` (correctness — distinct from "field
    missing" which is the swallowed compatibility case).
  - `attach-to-agent = ""` (explicit empty string — preserved as
    "unknown agent" semantics to match pre-spec behaviour). To get
    the new compatibility-swallow, omit the field entirely rather
    than setting it to an empty string.

## Sibling reading

  - [`docs/specs/dropped-primitives-coverage/spec.md`](../../specs/dropped-primitives-coverage/spec.md):
    the contract for what this guide describes.
  - [`docs/specs/incompatible-hook-event-drop/spec.md`](../../specs/incompatible-hook-event-drop/spec.md):
    the per-file event-level extension this guide's last section covers.
  - [`docs/specs/distribution-adapters/spec.md`](../../specs/distribution-adapters/spec.md):
    the v0.7 → v0.8 Changelog entry name lives here.
  - [`docs/contracts/adapter.toml`](../../contracts/adapter.toml):
    the v0.8 contract data the install handler reads.
