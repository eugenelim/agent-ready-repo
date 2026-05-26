# Spec: distribution-adapters

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md), [RFC-0002](../../rfc/0002-self-hosting.md), [RFC-0004](../../rfc/0004-install-scope-per-pack.md) (contract-v0.2 amendment — install-scope dimension)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Stand up the in-repo distribution machinery RFC-0001 commits to: a canonical
per-IDE **adapter contract** (TOML + JSON-Schema validator), a stdlib-only
Python **build pipeline** that consumes it, and four **reference adapters**
(Claude Code, Kiro, Copilot, Codex) that together project each of the four
packs (`core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`)
into ecosystem-native distribution artifacts. The user is the contributor or
adopter who runs `make build`: a single command must turn the source tree
under `packs/` into one installable APM package per pack at `dist/apm/<pack>/`
and one installable Claude Code plugin per pack at
`dist/claude-plugins/<pack>/`, plus a shared
`dist/claude-plugins/marketplace.json` aggregating every per-pack plugin
entry. The same pipeline, invoked as `make build --check`, must run in
dry-run mode against this repo's own self-host projection and exit non-zero
on any drift between source and on-disk projection — the gate RFC-0002 wires
into CI. Success is shaped by RFC-0001's three Success criteria: contract
validates against its own schema for all four reference targets; the build
pipeline produces installable artifacts on a clean checkout; the self-host
diff is a no-op.

This spec also pins:

- The **shape** of two schemas the rest of the catalogue reads: `pack.toml`
  (per-pack metadata, dependencies, adaptation manifest, and `seeds/` list)
  and `.claude-plugin/plugin.json` (the per-pack Claude Code plugin
  manifest). RFC-0002's self-host spec and RFC-0003's CLI spec reference
  these definitions — they are not redefined elsewhere.
- The **Tier-1/2/3 contract** (which files the bundle owns, which it shares
  with adopter edits, which it never touches) and the
  `.agentbundle-state.toml` schema and `.upstream.<ext>` companion semantics
  that operationalise it. **This spec pins the schemas only; the
  lifecycle behaviour** (companion-file creation/removal,
  `.agentbundle-state.toml` writes, Tier-2 detection on initial install)
  **is implemented by sibling specs** — `self-hosting` for `make build
  --self` and RFC-0003's CLI for install/update flows. No task in this
  plan implements Tier-2 behaviour; it pins the contract the consumers
  obey.
- The enumerated **recipe set** — the six recipe types RFC-0001 and RFC-0002
  jointly define. Any seventh recipe type requires an RFC or spec amendment.

## Projection modes (defined)

The seven projection modes RFC-0001 enumerates and this spec ships in
`adapter.toml`. Sibling specs reading this spec for projection-mode
semantics should find them here; AC #2's enum is defined-by-reference
to this list.

- **`direct-directory`** — copy a source directory tree byte-for-byte to
  the projected path. Default `on-conflict`: `prompt-then-preserve`.
  **Symlink-pass-through invariant**: implementations use
  `shutil.copytree(..., symlinks=True)` semantics — symlinks in the
  source are preserved as symlinks in the projection (never
  dereferenced at projection time), so a pack with a relative
  internal symlink projects the link literal, not the target body.
  This is a path-traversal safety invariant: a malicious pack with a
  symlink to `/etc/passwd` cannot exfiltrate that file into the
  adopter's tree.
- **`direct-file`** — copy a single source file byte-for-byte to the
  projected path. Default `on-conflict`: `prompt-then-preserve`.
- **`merge-json`** — deep-merge the source's JSON payload into a managed
  key of a target JSON file. Other keys are untouched. Default
  `on-conflict`: `merge-managed-key-only`.
- **`instruction-file`** — wrap source content as a per-file instruction
  document with adapter-declared frontmatter (e.g. Copilot's `applyTo`).
  Default `on-conflict`: `prompt-then-overwrite`.
- **`managed-block-inline`** — write the source content between
  delimiter strings inside a target text file; content outside the
  delimiters is preserved. Default `on-conflict`: `preserve-outside-block`.
- **`degraded-info-log`** — emit an `[info]` line on stderr at build
  time, write no file. Used historically when an adapter lacked a
  schema for a primitive (RFC-0001 Unresolved Q1, Kiro hook wiring —
  closed by RFC-0005's `merge-into-agent-json`).
- **`user-merge-json`** — array-append-with-id merge into a
  hand-edited shared user-settings file (Claude Code user scope —
  `~/.claude/settings.json` under `managed-key.user`). Distinct from
  `merge-json`: the target file is **not** pack-owned, so adopter-
  authored entries are never reordered or rewritten. Owned entries
  are tagged with a synthetic `id = "<pack>:<basename>"` so uninstall
  is precise. Defined by [RFC-0005 § `hook-wiring` for Claude Code at
  user scope](../../rfc/0005-user-scope-hook-support.md#hook-wiring-for-claude-code-at-user-scope--user-merge-json-mode);
  full merge / idempotency / failure-mode rules in the
  [`user-merge-json` subsection below](#user-merge-json-mode-claude-code-user-scope).
- **`merge-into-agent-json`** — array-append-with-id merge into a
  pack-owned agent JSON (Kiro at both scopes —
  `<scope-root>/.kiro/agents/<attach-to-agent>.json` under
  `managed-key = "hooks"`). The agent file is pack-owned, so the
  shared-file disciplines of `user-merge-json` (adopter-edit
  preservation) don't apply, but the per-agent target is. Defined by
  [RFC-0005 § `hook-wiring` for Kiro at both
  scopes](../../rfc/0005-user-scope-hook-support.md#hook-wiring-for-kiro-at-both-scopes--merge-into-agent-json-mode);
  full rules in the [`merge-into-agent-json` subsection
  below](#merge-into-agent-json-mode-kiro-at-both-scopes).
- **`dropped`** — explicit no-op; no output file, no warning. The
  contract carries the `dropped` rule so the missing pair is intentional,
  not an oversight.

## Default-recipe behaviour

Plain `make build` (no flags) invokes only the three RFC-0001 recipes —
`per-pack-claude-plugin`, `per-pack-apm-package`, and `marketplace` —
producing `dist/` output without touching the working tree. `make build
--self` (and `--check`, its dry-run sibling) project the four reference
adapters directly into the working tree per the spec § Tier model
contract. The RFC-0002 self-host recipes (`per-pack-overlay`,
`composite-agents-md`, `composite-marketplace`) ship as recipe metadata
+ expansion-shape API in this spec; their **on-disk writers** are
implemented by sibling spec `self-hosting`. The split keeps `make
build` deterministic and side-effect-free against the working tree —
the property that lets CI run it without pre-cleanup.

## Tier model and adopter-edit semantics

The Tier model is the bundle-format contract for "what a file's owner is at
any moment." All adapters, recipes, the CLI, and `adapt-to-project` consume
it identically. RFC-0001 § Catalogue boundaries and update model is the
upstream source.

- **Tier-1 — bundle-owned, projected.** Files at adapter-contract paths
  that the adopter does not edit. The CLI install, `make build`, and the
  adapt step are free to (re)write these. Examples: `.claude/skills/<pack>/`,
  generated `dist/` content, `.kiro/skills/<name>/`. Tier-1 is the default
  for any output an adapter projects from a primitive.
- **Tier-2 — bundle-origin, adopter-edited.** Files that the bundle
  originally seeded but the adopter has since modified. Detection: the
  per-file SHA-256 in `.agentbundle-state.toml` no longer matches the
  bundle's last-installed content. Writes never clobber: an update drops a
  companion file at `<filename>.upstream.<ext>` (e.g. `AGENTS.md` stays;
  `AGENTS.upstream.md` is dropped next to it). `adapt-to-project` walks
  these companions, prompts the adopter per file, and removes the
  `.upstream.<ext>` once resolved.
- **Tier-3 — adopter-owned, untouched.** Files outside adapter-contract
  paths. The bundle never writes these; the adapt step may propose changes
  but only with per-file approval.

**`.upstream.<ext>` companion semantics.**
- *Filename rule:* `<stem>.upstream.<ext>` for a file at `<stem>.<ext>`
  (e.g. `AGENTS.md` → `AGENTS.upstream.md`; `docs/CHARTER.md` →
  `docs/CHARTER.upstream.md`). For files without an extension, the rule is
  `<stem>.upstream` with no extension.
- *Lifecycle:* created by `make build` (in `--self` mode) or by a CLI
  install/update when the target is detected as Tier-2; removed by
  `adapt-to-project` after the adopter resolves the conflict (keep, merge,
  or overwrite). Companions are tracked in `.agentbundle-state.toml`.
- *Initial install:* when a fresh install lands on a pre-existing
  adopter-edited file (Tier-3 → Tier-2 fast-path), the install drops a
  `.upstream.<ext>` companion rather than overwriting.

**`.agentbundle-state.toml` schema (this spec, v0.1).**

```toml
schema-version = "0.1"

[pack.<name>]                       # one section per installed pack
installed-version = "0.2.0"          # the pack version that produced the recorded hashes
source = "agent-ready-repo"          # catalogue identifier
install-route = "cli"                # "cli" | "apm" | "claude-plugin"
primitives = ["skill", "agent", "hook-body", "hook-wiring", "command"]
                                     # the primitive types this pack projects (subset of: skill, agent, hook-body, hook-wiring, command)

[pack.<name>.files]                  # per-file SHA-256 hash recorded at install time
"<projected-path>" = { sha = "<hex64>", from-pack-version = "<semver>" }
```

The CLI spec (RFC-0003) consumes this schema; this spec pins it. Per-pack
version drift (the third file in RFC-0001's sketch) is permitted —
`from-pack-version` is per-file. Subsequent schema evolution moves the
`schema-version` field forward.

## Recipe set (enumerated)

The recipe types this spec supports — and the only ones the build pipeline
recognises without an RFC or spec amendment:

| Recipe type | Source RFC | Output |
| --- | --- | --- |
| `per-pack-claude-plugin` | RFC-0001 | `dist/claude-plugins/<pack>/` (one per pack) |
| `per-pack-apm-package` | RFC-0001 (RFC-0010 install-marker artifacts) | `dist/apm/<pack>/` (one per pack); the install-marker artifact pair `.apm/hooks/install-marker.{json,py}` is derived per `docs/specs/apm-install-route-parity/spec.md` AC11 |
| `marketplace` | RFC-0001 | `dist/claude-plugins/marketplace.json` (aggregate) |
| `per-pack-overlay` | RFC-0002 | self-host overlay of `.apm/` + `seeds/` into the working tree |
| `composite-agents-md` | RFC-0002 | composed `AGENTS.md` (or any composite text file) at the repo root *(this spec ships the recipe metadata + expansion-shape API; the on-disk writer is implemented by sibling spec `self-hosting`)* |
| `composite-marketplace` | RFC-0002 | composite of per-pack plugin manifests for the self-host marketplace *(this spec ships the recipe metadata + expansion-shape API; the on-disk writer is implemented by sibling spec `self-hosting`)* |

Any seventh recipe type requires a new RFC or a spec amendment — see
Boundaries *Ask first*.

## Primitive types and per-adapter projections

Five primitive types, projected by four reference adapters. Every (primitive,
adapter) pair has an explicit projection rule; the contract enumerates all
twenty pairs. Missing pairs default to `dropped` only when the contract
declares it so explicitly — no implicit defaults.

| Primitive | Source path (in `packs/<pack>/`) | Claude Code | Kiro | Copilot | Codex |
| --- | --- | --- | --- | --- | --- |
| `skill` | `.apm/skills/<name>/` | `direct-directory` → `.claude/skills/<name>/` | `direct-directory` → `.kiro/skills/<name>/` | `instruction-file` → `.github/instructions/<name>.instructions.md` | `direct-directory` → `.agents/skills/<name>/` |
| `agent` | `.apm/agents/<name>.md` | `direct-file` → `.claude/agents/<name>.md` | `direct-file`\* (with `kiro-agent-frontmatter-v0.9` rewrite) → `.kiro/agents/<name>.json` | `dropped` | `dropped` |
| `hook-body` | `.apm/hooks/<name>.{sh,py}` | `direct-file` — repo: `tools/hooks/<name>.{sh,py}`; user: `.claude/hooks/<pack>/<name>.{sh,py}` | `direct-file` — repo: `tools/hooks/<name>.{sh,py}`; user: `.kiro/hooks/<pack>/<name>.{sh,py}` | `direct-file` → `tools/hooks/<name>.{sh,py}` | `direct-file` → `tools/hooks/<name>.{sh,py}` |
| `hook-wiring` | `.apm/hook-wiring/<name>.toml` | repo: `merge-json` (under `hooks` key of `.claude/settings.local.json`); user: `user-merge-json` (under `hooks` key of `.claude/settings.json`) | `merge-into-agent-json` (RFC-0005 — under `hooks` key of `.kiro/agents/<attach-to-agent>.json`) | `dropped` | `dropped` |
| `command` | `.apm/commands/<name>.md` | `direct-file` → `.claude/commands/<name>.md` | `dropped` | `dropped` | `dropped` |

\* The Kiro `agent` row's `mode = "direct-file"` is retained for v0.3
contract continuity; the implementation is semantically a
*markdown-frontmatter → JSON-field rewrite*, not a byte-for-byte copy.
RFC-0005 / T7 introduced the JSON emission once Kiro published the
[custom-agents configuration reference](https://kiro.dev/docs/cli/custom-agents/configuration-reference/)
confirming agents are JSON. A future contract bump could rename the
mode (e.g. `agent-md-to-json`); the rename is deferred behind landing
the implementation.

**Hook extensions.** A hook is a script; the runtime is determined by the
file extension. The build pipeline projects `hook-body` byte-for-byte —
`.sh` stays `.sh`, `.py` stays `.py`. No conversion. Both extensions are
valid in `packs/<pack>/.apm/hooks/`.

**`hook-wiring` source format.** One TOML file per hook at
`.apm/hook-wiring/<name>.toml`. Each file declares the `[hooks]` entries
the adapter merges into its target file per the table above. The
optional top-level `attach-to-agent` field names a same-pack agent
(required for Kiro projection; ignored by Claude Code) — see [RFC-0005
§ Pack-side schema —
`attach-to-agent`](../../rfc/0005-user-scope-hook-support.md#pack-side-schema--the-attach-to-agent-field).

**Build-pipeline phase order.** Per [RFC-0005 § Build-pipeline ordering
invariant](../../rfc/0005-user-scope-hook-support.md#build-pipeline-ordering-invariant),
the pipeline projects primitives in the fixed order
**`hook-body` → `agent` → `hook-wiring` → `command` → `skill`** within
each pack. `merge-into-agent-json` reads the agent JSON the agent
projection wrote, so agents must land first. Cross-pack ordering is
not introduced — packs install serially today and no pack writes into
another pack's agent file. T7 enforces the invariant in the pipeline
iterator.

### Uniform multi-pack entry point — `direct-directory` adapters

Per [RFC-0009 § Adapter contract change](../../rfc/0009-codex-native-skills.md#adapter-contract-change),
every `direct-directory` adapter (`codex`, `claude-code`, `kiro`)
exposes
`project_packs(pack_paths: list[Path], contract, output_root)` as its
canonical orchestrator-facing entry point. Single-pack `project()`
is retained as a convenience wrapper that calls
`project_packs([pack_path], ...)`. `self_host.py` routes the
adapters in its `SELF_HOST_ADAPTERS` allow-list — narrowed by
RFC-0009 to `("claude-code",)` — through `project_packs`; `codex`
and `kiro` expose `project_packs` for adapter-API parity but are
not invoked from self-host (their working-tree projections would
duplicate every skill body and overload the maintainer). Other
orchestrator-style callers route through the same multi-pack
surface so the union of skill names across a multi-pack call is
observable in one place — which is what the orphan sweep below
needs.

**Same-name collision rule**: deterministic last-wins, uniformly
across all three adapters. Pack source order is as supplied to
`project_packs(pack_paths, ...)` by the caller; the last pack's
`<name>` overwrites earlier packs' projections of the same name
(the projection step `rmtree`s the destination before `copytree`).

### Orphan-skill cleanup invariant — `direct-directory` `skill` projections

Per [RFC-0009 § Failure modes](../../rfc/0009-codex-native-skills.md#failure-modes),
every `direct-directory` projection of the `skill` primitive runs a
post-projection orphan sweep that removes any child directory of
the projected skill target whose name is **not in the union of source skill names across the call's pack list**.
The union (not per-pack) is load-bearing: a pack shipping a subset
of skills must co-exist with another pack that ships the union
complement, and a per-pack sweep would orphan-clean the other
pack's skills.

The sweep is implemented as a shared helper
(`agentbundle.build.projections.direct_directory.sweep_orphans`) so
all three adapters compute orphan membership identically.

The sweep is **bound to the `skill` primitive only** — other
`direct-directory` primitives opt in explicitly, never automatically.
Symlinks at the target-dir root are removed via `Path.unlink()`
(never followed); non-symlink subdirectories are removed via
`shutil.rmtree`. The symlink rule preserves the symlink-pass-through
invariant above.

## Install-scope dimension (contract v0.2)

Per [RFC-0004](../../rfc/0004-install-scope-per-pack.md) the adapter
contract grows a **scope** dimension. The dimension lives in the
contract (not the CLI) so catalogue indexers, third-party validators,
and `agentbundle validate` all agree on what a malformed pack looks
like. The CLI surface that consumes the dimension — `--scope`
precedence, refusal text, dual-state-file walking, the
`installed: <pack> @ <scope>` rail — is owned by the sibling
[`agent-spec-cli`](../agent-spec-cli/spec.md) spec; this spec ships the
contract, the schemas, and the validation rails.

### Scope enum

A new enum `scope` with two values:

| Value  | Meaning                                                | Root path (Claude Code adapter) |
| ------ | ------------------------------------------------------ | ------------------------------- |
| `repo` | Project-local — lives next to the code it governs.     | `<repo>/.claude/`               |
| `user` | User-local — shared across every repo the user opens.  | `~/.claude/`                    |

`global` (system-wide) is deliberately absent — no adapter has a
system-wide root, and adding it later is a one-line schema bump against
an already-versioned contract.

### `[scope]` table on the adapter contract

Each `[adapter.<name>]` block gains an optional `[adapter.<name>.scope]`
table. Adapters omitting it are repo-only; new adapters that want
user-scope support declare both roots and the user-scope
prefix-allow-list.

```toml
[adapter."claude-code".scope]
repo = "."
user = "~"
allowed-prefixes.user = [".claude/", ".agentbundle/"]
```

Two prefixes ship in the v0.2 contract for Claude Code's user
scope: `.claude/` (where projected primitives land) and
`.agentbundle/` (the namespaced dot-directory holding CLI
infrastructure — user-scope state file, per-scope
`.adapt-discovery.toml`, per-scope `.adapt-pending.md`, and any
`.upstream.<ext>` companions the CLI writes at user scope). The
two-prefix shape exists so the path-jail rail covers *every*
write the CLI performs, including its own state-file and pending-
report writes; carving out CLI infrastructure paths from the
jail would be a foot-gun, so the prefixes carry both surfaces
declaratively.

`allowed-prefixes.<scope>` is constrained at the schema level, not
adapter-trusted. Each entry must be a non-empty, forward-slash-relative
path that:

- does not equal `"/"`,
- does not begin with `/`,
- contains no `..` segments after normalisation,
- ends with `/` to force prefix matching at directory boundaries.

The array must be non-empty for any scope it declares. The conformance
suite refuses adapters declaring `["/"]`, `[""]`, `["../"]`, `[".."]`,
or empty arrays — without this rail an adapter author could neuter the
jail by listing a root-equivalent prefix.

### `[pack.install]` table on `pack.toml`

`pack.toml` gains a `[pack.install]` table:

```toml
[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
```

- **`default-scope`** — the scope used when the adopter passes no
  `--scope`. One of `"repo"` | `"user"`. Required.
- **`allowed-scopes`** — the scopes this pack permits, as an array
  subset of `{"repo", "user"}`. Defaults to `[default-scope]` (i.e.
  "only the default") when omitted.

The cross-field invariant **`default-scope ∈ allowed-scopes`** is
enforced in `pack.schema.json` as a jsonschema `if`/`then` block so the
rule holds outside the CLI — every consumer of the schema refuses a
malformed pack identically.

### v0.1 vs v0.2 contract acceptance

A pack's contract version is declared in its `pack.toml`'s
`[pack.adapter-contract] version` field (per RFC-0001). The v0.2 CLI
applies two acceptance rules:

- **v0.1 packs** (`[pack.adapter-contract] version = "0.1"`) — accepted
  with implied defaults: `default-scope = "repo"`,
  `allowed-scopes = ["repo"]`. Any `[pack.install]` table on a v0.1
  pack is ignored — the implied defaults apply uniformly to all v0.1
  packs. A pack omitting `[pack.adapter-contract] version` is treated
  as `"0.1"` for legacy-acceptance.
- **v0.2 packs** (`[pack.adapter-contract] version = "0.2"`) — refused
  by `validate` if `[pack.install]` is missing.

The legacy default exists *only* for the legacy contract version. The
silent-default temptation is cheaper one PR but worse forever — pack
authors who never open their `pack.toml` would be implicitly opted *out*
of user scope without intent.

### Contract-level user-scope refusal rails

Three rails refuse a user-scope install at the **contract** level —
they fire regardless of CLI flags, hold for any v0.2 pack the build
pipeline or `agentbundle` produces or consumes, and re-check at install
time against the resolved pack content (closing the
widen-after-publish gap). Each rail is necessary; together they are
not sufficient — content-portability bugs the rails can't see
(hardcoded `AGENTS.md` references, vocabulary leakage) are the broader
*falsifiable test* defined in RFC-0004 § Per-pack default and
allowance.

**Rail A — `seeds/`-bearing packs.** A pack whose source tree contains
a non-empty `seeds/` directory cannot declare `"user"` in
`allowed-scopes`. `seeds/docs/`, `seeds/packages/` at user scope would
project to `~/docs/specs/`, `~/packages/_example/` — nonsense
paths. `validate` rejects mismatches.

**Rail B — hook-shaped primitives (conditional, RFC-0005).** A pack
whose source tree contains a non-empty `.apm/hooks/` or
`.apm/hook-wiring/` directory cannot declare `"user"` in
`allowed-scopes` **unless** the pack opts in via `[pack.install]
user-scope-hooks = true` *and* the target adapter declares a working
user-scope `hook-wiring` mode. Two adapter shapes satisfy the latter
condition:

- **Claude Code shape:** adapter declares `target.user` for
  `hook-body` *and* `mode.user = "user-merge-json"` for `hook-wiring`.
- **Kiro shape:** adapter declares `target.user` for `hook-body`
  *and* `mode = "merge-into-agent-json"` for `hook-wiring` (single
  mode, no scope qualifier — the agent-file target is
  scope-conditional via `<scope-root>` resolution) *and* an
  `[adapter.<name>.scope]` table making user scope reachable.

A pack with `user-scope-hooks = true` whose target adapter satisfies
neither shape is refused at scope-resolution time with
`adapter <name> does not declare a hook-wiring mode that supports
user scope; pack <P> requires it` per
[RFC-0005 § Rail B — user-scope
lift](../../rfc/0005-user-scope-hook-support.md#rail-b--user-scope-lift).

The opt-in flag (`user-scope-hooks`) is the consent gesture
RFC-0005 introduces — pack-authoring a user-scope hook is a
materially different responsibility from authoring a repo-scope one
(no per-project isolation; harder for the adopter to attribute
breakage; on Claude Code, shared file with other tools). The flag
has no meaning at repo scope and is ignored if `"user" ∉
allowed-scopes`. A pack lacking the flag is refused at user scope
with the prior v0.2 Rail B text.

**Rail C — `<adapt:NAME>`-marker-bearing primitives.** A primitive
file containing one or more `<adapt:NAME>` markers cannot install at
user scope: markers resolve from `.adapt-discovery.toml` to per-repo
values, and a single file at `~/.claude/` can only carry one
resolution. A pack with `"user"` in `allowed-scopes` must contain no
`<adapt:NAME>` markers in its projected primitive files.

- *Scope of the rail.* Rail C fires **only when the pack declares
  `"user" ∈ allowed-scopes`.** Repo-only packs are not inspected, so
  SKILL.md files that *document* the marker syntax (e.g. the
  `adapt-to-project` skill) are not refused.
- *Grep semantics.* Strict regex `<adapt:[a-z][a-z0-9-]*>`
  (canonical lowercase-hyphen form, per adapt-to-project AC14/AC21) **or** the legacy
  UPPER_SNAKE form `<adapt:[A-Z_][A-Z0-9_]*>`. Implementations
  MAY use a union regex `<adapt:([A-Z_][A-Z0-9_]*|[a-z][a-z0-9-]*)>`
  or two separate grep passes; both forms refuse Rail C. Markers in
  any byte position of any primitive file under the pack's source paths
  (`.apm/skills/`, `.apm/agents/`, `.apm/commands/`). Skill
  directories are walked **in `sorted(os.walk(...))` order** so the
  "first offending path" reported in the stderr message is
  deterministic across runs and platforms. Non-UTF-8 files
  (binaries) are skipped silently.
  `hook-body`/`hook-wiring` are already user-scope-refused
  by Rail B, so a marker check on them is unreachable; `seeds/` is
  already user-scope-refused by Rail A, so the marker rail's input
  never includes `seeds/`. No markdown parsing — the grep runs
  against raw file bytes.

**Enforcement points.** `validate` runs all three rails at
pack-validation time. `install` re-runs each rail against the resolved
pack content whenever `--scope user` is requested or the pack's
`default-scope` is `"user"`. The double-check closes the
widen-after-publish gap: a pack published as `["repo"]` (not
inspected) cannot install at user scope after flipping its
`allowed-scopes` to include `"user"` without passing every rail at
install time.

### Path-jail per scope

Two extensions to the write-jail rail:

1. **Per-scope root.** At repo scope, the jail is the repo root
   (unchanged). At user scope, the jail is `expanduser("~")`.
2. **Constrained to declared prefixes at user scope.** A `..`-escape
   check alone is insufficient at user scope — a buggy projection
   rule resolving under `~/Documents/` stays "inside the jail." Every
   user-scope write must resolve under one of the
   `allowed-prefixes.<scope>` entries declared on the adapter's
   `[scope]` table or the CLI refuses non-zero. Repo-scope writes are
   unchanged — the repo root *is* the prefix.

### State file per scope

| Scope  | Location                                  |
| ------ | ----------------------------------------- |
| `repo` | `<repo>/.agentbundle-state.toml`          |
| `user` | `~/.agentbundle/state.toml`               |

User-scope state lives inside a namespaced dot-directory
(`~/.agentbundle/`), not as a bare dotfile in `$HOME`. The
dot-directory is the future home for other user-scope artifacts
(`.adapt-discovery.toml`, `.upstream.<ext>` companions, pending
reports). Repo-scope state location is unchanged. Each file records
only the packs installed at *that* scope.

### `.agentbundle-state.toml` schema (v0.2)

```toml
schema-version = "0.2"

[pack.<name>]                        # one section per installed pack
installed-version = "0.2.0"
source = "agent-ready-repo"
install-route = "cli"
scope = "repo"                       # new in v0.2: "repo" | "user"
primitives = ["skill", "agent", "hook-body", "hook-wiring", "command"]

[pack.<name>.files]
"<projected-path>" = { sha = "<hex64>", from-pack-version = "<semver>" }
```

The `scope` column is required on every `[pack.<name>]` entry in
v0.2. Other fields are unchanged from v0.1.

**Read-time compatibility.** The CLI reads any `schema-version = "0.1"`
state file as *all entries at repo scope* (no migration forced at
read).

**Write-time refusal.** Any write-capable invocation against a v0.1
state file exits non-zero with stderr `state file at <path> is
schema-version 0.1; run 'agentbundle init-state --migrate' first`.
No silent rewrite — migration is destructive (irreversible without
backup) and an adopter running mixed CLI versions across CI and local
must opt into the file-format change explicitly. The refuse-and-
explain shape matches the major-version refusal rail in the sibling
CLI spec.

**`init-state --migrate`.** Rewrites a v0.1 state file to v0.2,
adding an explicit `scope = "repo"` column to each entry and bumping
`schema-version`. Idempotent and additive.

- *No automatic backup.* The migration is destructive (the v0.1
  file is replaced in place via tmp + `os.replace`); no
  `<path>.v01.bak` is written. Adopters running mixed CLI
  versions across CI and local must back up the file
  out-of-band before invoking `--migrate`. The
  refuse-and-explain rail above gives the adopter that signal
  before any write; an explicit `--migrate` is the consent
  gesture.

The `agentbundle-state.toml` `schema-version` is a separate version
axis from the adapter contract `[contract] version`. Both bump in
this amendment, but they gate different things — contract version
drives the major-version-disagreement refusal for *packs*; state-file
schema-version drives the refuse-and-explain at write-time. An
adopter must reason about both.

## v0.3 user-scope hook handling (RFC-0005)

The v0.3 contract bump adds two new projection modes
(`user-merge-json` for Claude Code at user scope and
`merge-into-agent-json` for Kiro at both scopes), plus a per-pack
opt-in flag (`[pack.install] user-scope-hooks`), plus optional
state-file fields for ownership tracking. The contract version
[bumps to `"0.3"`](#contract-version-bump-02--03) at the bottom of
this section.

### `user-merge-json` mode (Claude Code user scope)

Merges a pack's `.apm/hook-wiring/*.toml` content into the
hand-edited shared `~/.claude/settings.json` under the `hooks` key.
The mode is distinct from `merge-json` in three load-bearing ways:

1. **Target file is adopter-shared, not pack-owned.** Adopter
   hand-edits to top-level keys (`theme`, `model`, `env`, …) are never
   read or rewritten.
2. **Array-append-with-id, not key-replace.** Each owned entry carries
   a synthetic `id = "<pack>:<basename>"` (see [RFC-0005 § Merge
   semantics step 2](../../rfc/0005-user-scope-hook-support.md#merge-semantics)).
3. **Per-event arrays auto-initialise.** A missing `hooks` object is
   created as `{}`; a missing `hooks.<event>` is created as `[]`. Only
   present-with-wrong-type refuses (see *Failure modes* below).

**Idempotency.** Reinstalling the same pack at the same version is a
no-op: identical `id`s replace in place, position preserved. The
on-disk file diff is empty for a same-version reinstall. RFC-0005's
contract is byte-for-byte, not just JSON-equivalent.

**Adopter collision.** An adopter-authored entry under `hooks.<event>`
whose `command` field matches an incoming pack command (after
whitespace normalisation) causes `install` to refuse with `pack <P>'s
hook <name> at event <event> appears to be already wired in <path>;
remove the manual entry or pass --force-merge to take ownership`.
`--force-merge` (Claude Code user scope only) adopts the entry; the
original command is preserved in the state-file snapshot. Binding
details for `--force-merge` live in [RFC-0005 § User-already-set-this-key
collision rule](../../rfc/0005-user-scope-hook-support.md#user-already-set-this-key-collision-rule).

**Cross-pack ordering.** Multiple packs may wire entries to the same
event; their entries coexist as separate items in
`hooks.<event>`, each tagged with its own `id`. The CLI never reorders
adopter-touched arrays. Within a single install session, ties break
by ASCII codepoint order on the lowercased pack name; within a single
pack wiring N hooks for one event, entries land in
`sorted(os.walk(...))` order over `.apm/hook-wiring/<name>.toml`
filenames (the same `sorted(os.walk(...))` determinism rule [skill-
directory enumeration uses](#primitive-types-and-per-adapter-projections),
applied to the hook-wiring source surface).

**Uninstall.** `unproject` walks the user-scope state's per-pack
`hook-wiring-owned` rows, removes every `(event, id)` pair from the
in-memory `hooks.<event>` arrays, and rewrites the file. Empty
`hooks.<event>` arrays are removed (not left as `[]`). Adopter-
authored entries are never inspected beyond identity comparison. The
implementation lives at
`packages/agentbundle/agentbundle/build/projections/user_merge_json.py`.

**Failure modes.**

- **Unparseable JSON:** refuse with `cannot parse <path>: <error>;
  fix or back up the file and retry`. File is not rewritten; no state
  is recorded.
- **Wrong-shape `hooks`:** refuse with `<path>: hooks has unexpected
  shape <type>; expected object`.
- **Wrong-shape `hooks.<event>`:** refuse with `<path>: hooks.<event>
  has unexpected shape <type>; expected array`.

Failure-mode rules are RFC-0005 § Failure modes for unparseable user
settings verbatim.

### `merge-into-agent-json` mode (Kiro at both scopes)

Merges a pack's `.apm/hook-wiring/*.toml` content into a pack-owned
agent JSON at `<scope-root>/.kiro/agents/<attach-to-agent>.json` under
the `hooks` key. The mode reuses `user-merge-json`'s
array-append-with-id discipline, with one structural difference: the
target file is **pack-owned**, so adopter-edit preservation does not
apply — adopter hand-edits to the projected agent JSON are squatting on a
managed surface (the next upgrade replaces the file via the agent
primitive's `direct-file` projection, dropping the edits).

**Adapter declaration.** Kiro declares the mode plus an
`agent-event-vocabulary` array (the events the namespace accepts):

```toml
[adapter.kiro.projections.hook-wiring]
mode = "merge-into-agent-json"
target.repo = ".kiro/agents/<attach-to-agent>.json"   # resolves under <repo>/
target.user = ".kiro/agents/<attach-to-agent>.json"   # resolves under ~/
managed-key = "hooks"
agent-event-vocabulary = [
  "agentSpawn",
  "userPromptSubmit",
  "preToolUse",
  "postToolUse",
  "stop",
]
```

`<attach-to-agent>` is the pack-side TOML's `attach-to-agent` value
resolved per wiring entry (a same-pack agent name; `validate` refuses
otherwise — see [RFC-0005 § Pack-side
schema](../../rfc/0005-user-scope-hook-support.md#pack-side-schema--the-attach-to-agent-field)).

**`agent-event-vocabulary`.** A declarative array of event-name
strings. `validate` refuses any wiring TOML naming an event outside
this list with `pack <P>'s hook-wiring <name>.toml uses event '<E>';
not in adapter 'kiro' agent-event-vocabulary` (RFC-0005 § Repo-scope
Kiro promotion). The Claude Code projections do not declare
`agent-event-vocabulary`; the per-adapter vocabulary gate fires only
when the resolved target adapter declares the field.

**Idempotency, conflict, failure modes.** Same rules as
`user-merge-json`, except the failure path
`internal: <agent-file> missing at hook-wiring merge time; agent must
project before wiring` fires if the build-pipeline ordering invariant
(see [§ Build-pipeline phase order
above](#primitive-types-and-per-adapter-projections)) is violated —
the agent JSON must exist before any wiring merges run.

**Uninstall.** `unproject` walks `hook-wiring-owned` rows whose
`target-file` matches the agent JSON path, removes the entries, and
rewrites the file. The agent JSON itself is removed by the `agent`
primitive's `direct-file` projection uninstall, not by
`merge-into-agent-json`. The implementation lives at
`packages/agentbundle/agentbundle/build/projections/merge_into_agent_json.py`
**(landing in T6 — module does not exist yet at the time of this
amendment)**.

### `[contract] version` bump 0.2 → 0.3

`docs/contracts/adapter.toml`'s `[contract] version` bumps from
`"0.2"` to `"0.3"` (T1, RFC-0005). The conformance suite picks up
the new modes, the scope-conditional `target` shape, the
`agent-event-vocabulary` field, the `[pack.install] user-scope-hooks`
flag, and the v0.3 state-file additions (optional `adapter`,
`target-file`, `hook-wiring-owned`).

### `[contract] version` bump 0.1 → 0.2

`docs/contracts/adapter.toml`'s `[contract] version` bumps from
`"0.1"` to `"0.2"`. The conformance suite (sibling spec
`agent-spec-cli` §`validate --strict`, when its fixtures land) adds
per-scope cases: every contract change above (allowed-prefixes
constraints, scope-keyed state-file rule, Rails A/B/C, path-jail per
scope) appears as a conformance case the v0.2 contract must satisfy.

## v0.4 IDE event hooks (RFC-0005)

The v0.4 contract bump adds a sixth primitive — `kiro-ide-hook` —
for Kiro's standalone IDE-event hook surface
([`kiro.dev/docs/hooks/`](https://kiro.dev/docs/hooks/),
[`hooks/types`](https://kiro.dev/docs/hooks/types),
[`hooks/examples`](https://kiro.dev/docs/hooks/examples/)). The
primitive ships alongside the v0.3 user-scope hook surfaces, sits
at repo scope only in v1 (user-scope refused until upstream Kiro
[#5440](https://github.com/kirodotdev/Kiro/issues/5440) closes), and
extends the build pipeline's phase order so its placeholder
expansion can resolve to projected `hook-body` paths.

### Primitive declaration

A sixth `[primitive]` table entry sources files under a new pack
path:

```toml
[primitive."kiro-ide-hook"]
source-path = ".apm/kiro-ide-hooks/"
```

Source files are hand-authored JSON, one file per hook, named
`<name>.kiro.hook` (compound `.kiro.hook` extension — Kiro reads
files by this filter; the inner `.kiro` segment is part of the
filename, not the directory).

### Kiro adapter projection — `direct-file` with placeholder expansion

```toml
[adapter.kiro.projections.kiro-ide-hook]
mode = "direct-file"
target.repo = "<probe-pinned per Q6 — see probes.md>"
on-conflict = "prompt-then-preserve"
ide-event-vocabulary = <probe-pinned per Q11 — see probes.md>
ide-action-vocabulary = <probe-pinned per Q11 — see probes.md>
```

**The `target.repo` string, `ide-event-vocabulary` array, and
`ide-action-vocabulary` array are intentionally not pre-filled
here.** RFC-0005's declined-pattern discipline explicitly bars
inferring those values from community examples; T-CONTRACT writes
them once the operator runs the Q6 / Q11 probes and pins outcomes
in [`docs/specs/kiro-ide-hook/probes.md`](../kiro-ide-hook/probes.md).
The shape of each field is fixed (string; array-of-string with
`minItems: 1`); only the *content* is probe-gated.

The mode is the existing `direct-file`; no new mode is introduced.
The novelty is two declarative-vocabulary arrays sitting alongside
the v0.3 `agent-event-vocabulary` field, plus a single-pass
placeholder substitution applied during projection.

**Target template substitution.** `<pack>` resolves to the pack's
directory name; `<name>` resolves to the source file's bare name
(filename minus `.kiro.hook`). Pack-namespacing keeps two packs
shipping `on-save.kiro.hook` from colliding and makes uninstall a
directory removal — the existing per-file Tier-1/Tier-2 path plus
its empty-parent sweep handles it without state-schema additions
([RFC-0005 § State-file impact](../../rfc/0005-user-scope-hook-support.md#state-file-impact)).

**Probe-gated values.** The exact `target.repo` string above and
the `ide-event-vocabulary` array are gated on two probes against a
real Kiro install before the v0.4 declaration ships in
`adapter.toml`:

- **Q6 — recursion + extension filter.** Determines whether Kiro
  reads `.kiro/hooks/<subdir>/*.kiro.hook` recursively and whether
  it filters by the `.kiro.hook` extension or parses every file.
  The 2×2 (RFC-0005 § Unresolved Q6) picks the canonical target
  string. The `yes-recursion × no-extension-filter` quadrant
  additionally triggers a cross-primitive `hook-body` user-scope
  retarget from `.kiro/hooks/<pack>/` to `.kiro/hook-bodies/<pack>/`
  to avoid Kiro parsing shell scripts as hooks.
- **Q11 — vocabulary fixture.** At least one IDE-UI-authored
  `.kiro.hook` file is captured under
  `packages/agentbundle/tests/fixtures/kiro_ide_hook/captured/`;
  the captured `when.type` / `then.type` strings become the
  canonical entries above.

The probes and probe outcomes are recorded in
[`docs/specs/kiro-ide-hook/probes.md`](../kiro-ide-hook/probes.md);
the v0.4 declaration in `adapter.toml` is the contract-version
write that ships in the same commit as the pinned values.

### Other adapters — `dropped`

`claude-code`, `codex`, and `copilot` each declare an explicit
`mode = "dropped"` row for `kiro-ide-hook`, same pattern as
`command` (dropped for Codex / Copilot) and `agent` (dropped for
Codex / Copilot). Adapter-side declaration is required so
`validate` knows the primitive exists; pack authors who don't
target Kiro can leave `.apm/kiro-ide-hooks/` empty without
refusal.

### Validate rail

Five refusal paths fire when a pack ships at least one
`.apm/kiro-ide-hooks/<*>.kiro.hook` file and the target adapter
is `kiro`:

1. **Missing required field** — `name`, `version`, `when.type`,
   `then.type`. Refusal:
   `pack <P>'s kiro-ide-hook <file> is missing required field <field>`.
2. **`when.type` out of `ide-event-vocabulary`** — refused with
   `pack <P>'s kiro-ide-hook <file> uses event '<type>'; not in adapter 'kiro' ide-event-vocabulary`.
3. **`then.type` out of `ide-action-vocabulary`** — refused with
   `pack <P>'s kiro-ide-hook <file> uses action '<type>'; not in adapter 'kiro' ide-action-vocabulary`.
4. **Malformed placeholder** in `then.command` — any `${...}` that
   doesn't `fullmatch` the strict grammar
   `\$\{hook-body:[a-zA-Z0-9_-]+\}` refused with
   `pack <P>'s kiro-ide-hook <file> contains malformed placeholder '<text>'; expected ${hook-body:<name>} with name matching [a-zA-Z0-9_-]+`.
5. **Unresolvable placeholder** — well-formed `${hook-body:<name>}`
   whose `<name>` is not a same-pack hook-body refused with
   `pack <P>'s kiro-ide-hook <file> references unknown hook-body '${hook-body:<name>}'; no such hook-body in pack`.

RFC-0005 § Substitution rules clause 1 fences the placeholder scan
to `then.command` only; placeholder-shaped text in `then.prompt`
(askAgent), `name`, `description`, `when.patterns`, or any other
field passes through verbatim (the `prompt` text is for the agent,
not the bundler). Semantic correctness of `when.patterns` (glob
validity) and `then.command` shell syntax is **not** in the rail's
scope — runtime issues surface at execute time.

The rail's vocabulary checks (2 + 3) are no-ops when the adapter
declares no vocabulary — same shape as `agent-event-vocabulary`'s
no-op for Claude Code. Pre-v0.4 contracts have no vocabulary
declaration; refusal paths 1 / 4 / 5 still fire because they're
vocabulary-independent.

### Build-pipeline phase order — extended

The pipeline projects primitives in the fixed order

```
hook-body → agent → hook-wiring → kiro-ide-hook → command → skill
```

within each pack. Two real dependencies drive the order:
`hook-wiring ← agent` (Kiro's `merge-into-agent-json` reads the
projected agent JSON, established at v0.3) and `kiro-ide-hook ←
hook-body` (placeholder expansion needs the projected hook-body
path). Every other ordering is a tiebreak pinned for operational
determinism — log ordering, partial-state-on-failure semantics,
rollback target — not byte-identity of the projected files.
RFC-0005 § Substitution rules → *Why serial rather than
DAG-parallel* spells this out. `phase_order.py` exports the tuple;
every reference adapter imports it.

### User-scope refusal (v1)

`kiro-ide-hook` is refused at user scope at the contract layer
until upstream Kiro #5440 closes. `~/.kiro/hooks/` is not on
Kiro's read path today, so projecting there would land an inert
file. The CLI refuses with

```
pack <P> declares kiro-ide-hook at user scope, but kiro adapter does not support user-scope IDE hooks (Kiro #5440 still open)
```

per RFC-0005 § Scope. The refusal is independent of Rail B (the
existing user-scope hook-shaped refusal in
§ *Install-scope dimension*) — a `kiro-ide-hook`-only pack with
`user-scope-hooks = true` still refuses because the *primitive*
is repo-only in v1. When Kiro #5440 closes, the user-scope refusal
lifts via either an in-place RFC amendment (if no state-file shape
change is needed) or a successor RFC.

### `[contract] version` bump 0.3 → 0.4

`docs/contracts/adapter.toml`'s `[contract] version` bumps from
`"0.3"` to `"0.4"` in the same PR as the v0.4 declaration table.
The conformance suite picks up the new primitive, the new
`ide-event-vocabulary` / `ide-action-vocabulary` projection fields,
and the v0.4 phase-order extension. Existing v0.3-shaped adapter
declarations remain valid (the new primitive is optional;
non-Kiro adapters inherit `dropped`). Pack metadata files that
don't ship `.apm/kiro-ide-hooks/` need no change. The
`adapter-contract.version` enum in `pack.schema.json` extends to
include `"0.4"` in the same commit as the contract write so a v0.4
pack can declare its target contract version without a schema
refusal.

The v0.4 declaration is **probe-gated** per the Q6 / Q11 outcomes
recorded in [`docs/specs/kiro-ide-hook/probes.md`](../kiro-ide-hook/probes.md);
shipping v0.4 with a target string or vocabulary list that has to
change on first use would be a contract-version lie (RFC-0005
§ *Gating verifications before contract version 0.4 ships*).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Place the canonical adapter contract at
  `docs/contracts/adapter.toml` with a sibling
  `adapter.schema.json`. This supersedes RFC-0001's original
  `docs/specs/adapter-contract/contract.toml` convention (see
  [RFC-0001 § Amendments](../../rfc/0001-bundle-distribution-by-adapter-spec.md#amendments));
  do not move it under `docs/specs/distribution-adapters/`.
- Use Python stdlib only (target 3.11+ for `tomllib`). Every adapter, every
  recipe consumer, every validator runs without `pip install`.
- Place build-pipeline code at `packages/agentbundle/agentbundle/build/`,
  with recipes under `packages/agentbundle/agentbundle/build/recipes/`,
  adapter implementations at
  `packages/agentbundle/agentbundle/build/adapters/{claude_code,kiro,copilot,codex}.py`,
  and the validator harness at
  `packages/agentbundle/agentbundle/build/validate.py`. The CLI imports
  `agentbundle.build` as a library; `tools/build/build.py` is a thin shim
  (≤ 10 lines, no logic) that calls `python -m agentbundle.build`.
- Implement all seven projection modes from RFC-0001
  (`direct-directory`, `direct-file`, `merge-json`, `instruction-file`,
  `managed-block-inline`, `degraded-info-log`, `dropped`) and honor each
  mode's per-RFC default `on-conflict` value.
- Enumerate every (primitive, adapter) pair in `adapter.toml`. Missing
  pairs default to `dropped` only when the contract states so explicitly.
- Validate pack-internal name uniqueness (no two skills with the same local
  name inside the same pack) at build time; allow cross-pack name reuse.
- Source named frontmatter mappings (e.g. `kiro-agent-frontmatter-v0.9`)
  from the contract TOML's `[frontmatter-mapping.*]` tables — adapters
  consume them generically, never via Python lookup tables.
- Source per-adapter frontmatter defaults (e.g. Copilot's `applyTo: "**"`)
  from `[frontmatter-default.*]` tables — adapters never hardcode the
  default.
- Exit non-zero with a one-line stderr message when validation or drift
  detection fails (so CI and the work-loop's `scripts/loop-cohort.py check` see the signal).
- Treat `make build --check` as exactly `make build --self --dry-run` plus
  a strict exit code: non-zero on any drift, regardless of warning level.
  The two commands share rendering; `--check` only differs in its gate
  contract.
- When sibling specs reference `pack.toml` or `.claude-plugin/plugin.json`
  shapes, they must link to this spec — flag in PR review if they inline
  the schema instead.
- Enforce the `default-scope ∈ allowed-scopes` invariant in
  `pack.schema.json` (jsonschema `if`/`then`), not in CLI code, so
  catalogue indexers and third-party validators refuse a malformed
  pack identically.
- Run the three contract-level user-scope refusal rails (Rails A/B/C
  in § *Install-scope dimension*) at `validate` time **and** re-run
  each rail at `install` time against the resolved pack content
  whenever the install resolves to user scope.
- Apply `pathlib.Path.expanduser()` to the `[scope]` table's `user`
  root **once, at scope-resolution time** (when an `install`,
  `uninstall`, `upgrade`, or `adapt` invocation resolves `--scope
  user` to a concrete root). If the result equals literal `"~"`
  (expansion failed) or resolves to `"/"` (corporate sandbox with
  `$HOME=/`), refuse with stderr `cannot resolve user scope: $HOME
  unset or invalid`.

### Ask first

- Adding any projection mode beyond the seven RFC-0001 lists.
- Adding any adapter target beyond the four reference adapters.
- Adding any recipe type beyond the six enumerated in *Recipe set*.
- Schema changes to `pack.toml` or `.claude-plugin/plugin.json` beyond
  the RFC-named fields (these are consumed by RFC-0002 and RFC-0003).
- Any change to `make build`'s seven-subcommand surface (`build`, `build
  PACK=`, `build RECIPE=`, `--self`, `--self --dry-run`, `--check`,
  `--scaffold OUTPUT=`).
- Adding a `global` (system-wide) value to the `scope` enum. Not
  reserved, not refused — absent. RFC-0004 § Alternatives considered
  §6 rejects pre-emptive reservation; adding `global` later is a
  one-line schema bump against an already-versioned contract.
- Translating between adapter event vocabularies. The
  `agent-event-vocabulary` field gates wiring projections at
  `validate` time; a pack targeting both adapters ships separate
  wiring TOMLs per adapter. Adding a translation layer that lets a
  Claude-Code-shaped wiring run on Kiro (or vice versa) needs its own
  RFC — RFC-0005 § What this RFC does NOT do explicitly excludes it.

*(Two prior items here are now closed by RFC-0005: Kiro hook-wiring
projection out of `degraded-info-log` is replaced by
`merge-into-agent-json` at repo scope (T1 contract bump); hook-shaped
primitives at user scope are no longer unconditionally refused by
Rail B (it lifts on `[pack.install] user-scope-hooks = true` plus a
working user-scope adapter mode).)*

### Never do

- **No new top-level directory.** Everything lands under existing
  `docs/`, `packages/`, `tools/`, `packs/`, or `dist/` (and `dist/` is
  git-ignored build output, not source). New top-level paths go through RFC.
- **No Python module outside `packages/agentbundle/` for build-pipeline
  code.** `tools/build/build.py` is a thin shim only (no logic, ≤ 10
  lines, imports and calls `agentbundle.build.main`). Adapters, recipes,
  the validator, the contract loader, and tests all live under
  `packages/agentbundle/agentbundle/build/`.
- **No non-stdlib Python dependency.** No `requirements.txt`, no
  third-party imports, no vendored libraries. `packages/agentbundle/`
  has a `pyproject.toml` for packaging metadata only — its `dependencies`
  array is empty. The build pipeline imports only from the standard library.
- **No install-time placeholder substitution — except `make build --self`.**
  Every other mode (`make build`, adopter `agentbundle install`, APM
  `apm install`, Claude `/plugin install`) copies `<adapt:NAME>` markers
  through unchanged. `make build --self` is the *one authorised mode*
  that runs marker resolution as a final build step against this repo's
  concrete values; the resolver itself belongs to the `adapt-to-project`
  skill, which materialises `.adapt-discovery.toml` from this repo's
  values before the build step consumes it. RFC-0001 Open Q3
  (`<adapt:NAME>` for plugin-installed packs) stays deferred to
  `adapt-to-project`.
- **No edits to skill-owned template assets.** Templates are governance
  scaffolding that ships to adopters via the skill that creates instances
  of them (`.claude/skills/<skill>/assets/<template>`); this spec produces
  distribution machinery, not template changes. Historical note: when this
  spec was first authored, templates lived under `docs/_templates/`; they
  were relocated to per-skill `assets/` folders to comply with the
  agentskills.io spec layout — see Changelog 2026-05-24.
- **No silent overwrite semantics encoded outside the contract.** Every
  projection rule's `on-conflict` value lives in `adapter.toml` and is
  carried through into the rendered artifact's manifest (so downstream
  install tools and the adapt step honor RFC-0001's per-mode defaults).
  Adapters never hardcode an `on-conflict` policy.
- **No conformance test suite in this spec.** A *full* per-adapter
  conformance suite is RFC-0003's work; this spec ships unit-level
  projection tests per adapter only.
- **No silent rewrite of a `schema-version = "0.1"` state file.** A
  write-capable invocation against a v0.1 state file exits non-zero
  with the `init-state --migrate` refuse-and-explain message defined
  in § *Install-scope dimension*. Migration is destructive
  (irreversible without backup); an adopter running mixed CLI versions
  across CI and local must opt into the file-format change
  explicitly.
- **No user-scope install of a `seeds/`-bearing, hook-bearing, or
  `<adapt:NAME>`-marker-bearing pack** (Rails A/B/C in § *Install-scope
  dimension*). Each rail is checked at `validate` time **and** re-run
  at `install` time against the resolved pack content.

## Testing Strategy

Three behaviors close this spec; each gets one mode and one verification
artifact.

- **Contract + schema validation — TDD.** The `adapter.toml`/`adapter.schema.json`
  pair is pure data with a compressible invariant ("the contract validates
  against the schema; every adapter block enumerates every (primitive,
  adapter) pair; every projection rule has a defined `on-conflict`"). TDD
  because the invariant is what we ship; the test pins it directly, and
  the same harness powers the validator the build pipeline calls at startup.
- **Per-adapter projection rules — TDD.** Each of the four adapters maps
  source primitives to outputs by deterministic rules — pure functions
  with edge cases (collisions, frontmatter normalization, managed-block
  delimiters, dropped primitives, degraded-info-log emission). TDD because
  each rule is a compressible invariant and the rule set is what the
  contract calls out as the *specification*.
- **End-to-end build pipeline — goal-based check.** `make build` against
  the four reference packs on a clean checkout produces the expected
  `dist/apm/<pack>/` and `dist/claude-plugins/<pack>/` directory shapes
  plus `dist/claude-plugins/marketplace.json`. The one-liner *is* the
  contract: `make build && test -f dist/claude-plugins/marketplace.json
  && test -d dist/apm/core && …`. No mocking layer, no internal
  assertions; the artifact-on-disk verifies. Same for `make build
  --check` (the self-host gate): one-liner asserts the command exits zero
  on a clean tree.

No manual QA: there is no UI surface, no human gesture under test.

## Acceptance Criteria

- [x] `docs/contracts/adapter.toml` exists, covers all four
  reference adapters (`claude-code`, `kiro`, `copilot`, `codex`), names
  the five primitive types (`skill`, `agent`, `hook-body`, `hook-wiring`,
  `command`), enumerates every (primitive, adapter) pair explicitly, and
  validates against a sibling `docs/contracts/adapter.schema.json`.
- [x] All seven projection modes (`direct-directory`, `direct-file`,
  `merge-json`, `instruction-file`, `managed-block-inline`,
  `degraded-info-log`, `dropped`) appear in `adapter.schema.json` as the enum of
  legal `mode` values, and every projection rule in `adapter.toml`
  carries an `on-conflict` value matching RFC-0001's per-mode default
  table (or an explicit override from the legal set).
- [x] `pack.toml` shape is pinned in
  `docs/contracts/pack.schema.json` and referenced from
  `adapter.toml`. The schema accepts `[pack]`, `[pack.dependencies]`
  (with `required`/`recommended`/`conflicts` keys), `[pack.adaptation]`,
  and `[pack.seeds]` tables per RFC-0001. The schema enforces shape
  only: `[pack.adaptation] infer-from` must be a string (a non-string
  is rejected); the semantic set of legal `infer-from` values lives in
  the `adapt-to-project` skill, not in this schema. A missing
  `[pack.dependencies.required]` array is *optional* (no required
  field). The schema's pass/fail tests pin both outcomes plus a
  `[pack.seeds]` shape check (entries must be relative-path strings;
  an absolute path or a non-string is rejected).
- [x] `.claude-plugin/plugin.json` shape is pinned in a sibling
  `plugin-manifest.schema.json` validating the hand-authored per-pack
  manifests. Each pack's manifest is hand-authored at
  `packs/<pack>/.claude-plugin/plugin.json`; the build copies it
  unmodified into `dist/claude-plugins/<pack>/`.
- [x] `packages/agentbundle/agentbundle/build/` runs under `python3
  --version` 3.11+ with zero non-stdlib imports (verified by
  `tools/lint-build.sh` and the `pre-pr.sh` hook — a wrong `import yaml`
  surfaces in the offending PR, not at end-of-stream). The CI job that
  runs `pre-pr.sh` exits non-zero on any non-stdlib import under
  `packages/agentbundle/agentbundle/build/`.
- [x] `validate.py` implements a stdlib-only JSON-Schema subset (object,
  array, string, integer, boolean, enum, required, pattern, items,
  `properties` and `additionalProperties` for object recursion — and
  only these). The subset is documented in T1a's *Approach*. AC #1
  verifies `validate.py` accepts the conforming `adapter.toml` and
  rejects each mutation enumerated in `test_contract.py`. `properties`
  and `additionalProperties` are load-bearing — every shipped schema
  (`adapter.schema.json`, `pack.schema.json`, `plugin-manifest.schema.json`)
  uses them to recurse into nested objects.
- [x] `make build` on a clean checkout, against the four reference
  fixture packs under
  `packages/agentbundle/agentbundle/build/tests/fixtures/packs/`
  (`core`, `governance-extras`, `user-guide-diataxis`,
  `monorepo-extras`), produces `dist/apm/<pack>/` and
  `dist/claude-plugins/<pack>/` directories for each of the four
  reference packs and a single `dist/claude-plugins/marketplace.json`
  listing every per-pack plugin entry; exit code zero. **Materialisation
  of production packs in a top-level `packs/` directory is out of
  scope** — that migration is RFC-0001's F-dist follow-on. This spec
  ships the pipeline; production packs land separately.
- [x] Each adapter (`claude_code`, `kiro`, `copilot`, `codex`) has a
  per-adapter unit-test file under
  `packages/agentbundle/agentbundle/build/tests/` covering every
  projection mode that adapter's `adapter.toml` block uses (e.g.
  Copilot exercises `instruction-file`, `direct-file`, and `dropped`;
  Codex exercises `managed-block-inline`, `direct-file`, and `dropped`)
  plus the named frontmatter mapping or default where the contract
  declares one. Idempotence is asserted for `merge-json` (Claude Code)
  as well as `managed-block-inline` (Codex): running each adapter twice
  against the same fixture yields byte-identical output.
- [x] The build pipeline's validation step (not any individual adapter)
  rejects a pack whose `.apm/skills/`, `.apm/agents/`, `.apm/hooks/`,
  `.apm/hook-wiring/`, or `.apm/commands/` contains two primitives with
  the same local name (pack-internal uniqueness per RFC-0001 §
  Pack-internal naming and collision policy), with a non-zero exit and
  a stderr message naming both paths.
- [x] `make build --check` (dry-run self-host build + diff against
  on-disk projection) exits zero on a clean tree and exits non-zero
  with a per-file drift listing on any divergence. CI wiring of this
  gate is RFC-0002's spec's job; this spec ships the command.
- [x] `make build --self` writes projected output to the working tree,
  resolves `<adapt:NAME>` markers against `.adapt-discovery.toml` as a
  final step (the one authorised mode for marker resolution per
  Boundaries § Never do), **refuses on a dirty tree without `--force`
  and exits non-zero with stderr naming the refusal** (verified by a
  T7 test against a dirty-tree fixture), and (with `--force`) honours
  each adapter's declared `on-conflict` policy from `adapter.toml` —
  `--force` overrides only the dirty-tree refusal, never the
  per-adapter on-conflict default. The substitution pass (read
  `.adapt-discovery.toml`, replace `<adapt:NAME>` markers across
  rendered output) is implemented by T7; the *materialisation* of
  `.adapt-discovery.toml` from repo values lives in the
  `adapt-to-project` skill (out of scope here — T7 ships only the
  consumer). Sibling spec `self-hosting` cites this AC.
- [x] The supported recipe set is exactly the six types named in
  § Recipe set (`per-pack-claude-plugin`, `per-pack-apm-package`,
  `marketplace`, `per-pack-overlay`, `composite-agents-md`,
  `composite-marketplace`); a seventh requires an amendment to this
  spec or a new RFC. Sibling specs (self-hosting, CLI) cite this AC
  when consuming the recipe set.
- [x] No new top-level source **directory** is introduced. Verified by
  `comm -23 <(git ls-tree -d --name-only HEAD | sort) <(git ls-tree
  -d --name-only "$(git merge-base HEAD main)" | sort)` returning an
  empty set after the change lands — the `-d` flag scopes the audit
  to directories (so `Makefile`, `.gitignore`, and other root-level
  files this spec touches do not trip it), and the merge-base
  comparison keeps the audit correct after a merge from `main` into
  the feature branch. `dist/` is git-ignored and does not count. No
  non-stdlib Python import is added (verified by the import-audit
  check above).
- [x] Plain `make build` (no flags) produces only `dist/apm/<pack>/`,
  `dist/claude-plugins/<pack>/`, and `dist/claude-plugins/marketplace.json`
  — it does **not** invoke the three self-host recipes
  (`per-pack-overlay`, `composite-agents-md`, `composite-marketplace`).
  The working tree is unchanged after the run (verified by `git
  status` against the working tree before and after, returning byte-
  identical output). This pins the property § Default-recipe behaviour
  declares; T8 owns the test.
- [x] **(RFC-0004)** `docs/contracts/adapter.toml` carries
  `[contract] version = "0.2"` and a `[adapter."claude-code".scope]`
  table declaring `repo = "."`, `user = "~"`, and
  `allowed-prefixes.user = [".claude/", ".agentbundle/"]` (the
  two-prefix shape covers both projected primitives and CLI
  infrastructure writes — see § *`[scope]` table on the adapter
  contract*). `adapter.schema.json`
  defines the optional `[scope]` table and enforces the
  `allowed-prefixes.<scope>` constraints (non-empty array; each
  entry forward-slash-relative, not `"/"`, not beginning with `/`,
  no `..` after normalisation, trailing `/`). A test asserts the
  schema rejects each of `["/"]`, `[""]`, `["../"]`, `[".."]`, and
  `[]` for `allowed-prefixes.user`.
- [x] **(RFC-0004)** `docs/contracts/pack.schema.json` requires
  `[pack.install]` on any pack declaring
  `[pack.adapter-contract] version = "0.2"` (jsonschema `if`/`then`
  on the contract-version field), with `default-scope ∈ {"repo",
  "user"}` and `allowed-scopes` a non-empty array subset of
  `{"repo", "user"}` defaulting to `[default-scope]`. A second
  `if`/`then` block enforces `default-scope ∈ allowed-scopes`.
  Tests pin: a v0.2 pack without `[pack.install]` is rejected;
  a v0.2 pack with `default-scope = "user"` and
  `allowed-scopes = ["repo"]` is rejected; a v0.1 pack without
  `[pack.install]` is accepted; a v0.1 pack *with* a stray
  `[pack.install]` table is accepted (the table is ignored at
  CLI consumption per § *Install-scope dimension*).
- [x] **(RFC-0004)** `validate.py` runs Rails A/B/C against every
  pack: Rail A refuses any pack containing a non-empty `seeds/`
  directory and declaring `"user" ∈ allowed-scopes`; Rail B refuses
  any pack whose source tree contains a non-empty `.apm/hooks/` or
  `.apm/hook-wiring/` directory and declaring `"user" ∈
  allowed-scopes`; Rail C refuses any pack declaring `"user" ∈
  allowed-scopes` and containing one or more files matching
  the canonical lowercase-hyphen form `<adapt:[a-z][a-z0-9-]*>`
  **or** the legacy UPPER_SNAKE form `<adapt:[A-Z_][A-Z0-9_]*>`
  (per adapt-to-project AC14/AC21) under `.apm/skills/`, `.apm/agents/`,
  or `.apm/commands/`. Rail C walks those directories in
  `sorted(os.walk(...))` order (deterministic across runs and
  platforms) and skips non-UTF-8 (binary) files silently. Each
  rail's stderr message names the offending pack and the first
  offending path. Tests pin one positive case (rail accepts a
  clean pack) and one negative case (rail rejects with the named
  stderr) per rail, plus one binary-file skip test for Rail C.
- [x] **(RFC-0004)** `.agentbundle-state.toml` `schema-version`
  bumps to `"0.2"`. Every `[pack.<name>]` entry in v0.2 carries a
  required `scope = "repo" | "user"` column. The CLI **reads** any
  v0.1 file as all-repo-scope without forcing migration; any
  **write-capable** invocation against a v0.1 file exits non-zero
  with stderr `state file at <path> is schema-version 0.1; run
  'agentbundle init-state --migrate' first`. The
  `init-state --migrate` writer rewrites a v0.1 file to v0.2
  idempotently (adding `scope = "repo"` to each entry; bumping
  `schema-version`); running it twice against the same v0.2 file
  is a no-op exit-zero. The user-scope state file lives at
  `~/.agentbundle/state.toml` (a namespaced dot-directory under
  `$HOME`, not a bare dotfile).
- [x] **(RFC-0004)** The four shipped packs at
  `packs/{core,governance-extras,monorepo-extras,user-guide-diataxis}/pack.toml`
  **add** an explicit `[pack.adapter-contract] version = "0.2"`
  field (the field was previously absent — packs were
  legacy-treated as `"0.1"` per § *Install-scope dimension*'s
  acceptance rule) and **add** an explicit `[pack.install]` table
  with `default-scope = "repo"` and `allowed-scopes = ["repo"]`.
  The values are written out even though both are the built-in
  defaults so adopters reading the TOML see the constraint
  declared, not implied. The `[pack.adapter-contract]` version
  addition and the `[pack.install]` declaration land in the **same
  PR** as the contract / schema amendment so the catalogue's
  published packs and the CLI release land in lockstep.
- [ ] **(RFC-0005 v0.4)** `docs/contracts/adapter.toml` declares a
  sixth `[primitive."kiro-ide-hook"]` table with
  `source-path = ".apm/kiro-ide-hooks/"` and a sibling
  `[adapter.kiro.projections.kiro-ide-hook]` table with `mode =
  "direct-file"`, `target.repo` (probe-pinned per Q6),
  `on-conflict = "prompt-then-preserve"`, and the two declarative
  vocabulary arrays `ide-event-vocabulary` (probe-pinned per Q11)
  and `ide-action-vocabulary = ["askAgent", "runCommand"]`. Every
  other adapter (claude-code, codex, copilot) declares an explicit
  `primitive = "kiro-ide-hook", mode = "dropped"` row. `[contract]
  version` bumps `"0.3" → "0.4"` in the same commit; the
  `pack.schema.json` `adapter-contract.version` enum extends to
  include `"0.4"` in lockstep.
- [ ] **(RFC-0005 v0.4)** `adapter.schema.json` adds
  `"kiro-ide-hook"` to `primitive.required` and declares
  `ide-event-vocabulary` + `ide-action-vocabulary` as optional
  array-of-string fields (`minItems: 1`, `items.type = "string"`)
  under `projections.<primitive>.properties`. The implicit
  acceptance of these fields (the inner object's open
  `additionalProperties`) is now explicit. Tests pin: schema
  accepts non-empty vocabularies, refuses empty arrays, refuses
  non-string items.
- [ ] **(RFC-0005 v0.4)** The `kiro-ide-hook` validate rail
  (`scope_rails.check_kiro_ide_hook`) refuses every malformed
  hook with one of five RFC-named stderr strings (missing required
  field; out-of-vocabulary `when.type`; out-of-vocabulary
  `then.type`; malformed placeholder in `then.command`;
  unresolvable placeholder). The rail's vocabulary checks (2 + 3)
  fire only when the adapter declares the corresponding vocabulary
  field — same no-op-when-absent shape as
  `agent-event-vocabulary` for Claude Code.
- [ ] **(RFC-0005 v0.4)** Placeholder substitution in
  `then.command` is single-pass, verbatim (no shell quoting),
  applied at projection time only by the dedicated
  `projections.kiro_ide_hook` module. Resolved text is not
  re-scanned. The scan surface is fenced to `then.command`;
  placeholder-shaped text in `then.prompt`, `name`, `description`,
  or `when.patterns` passes through. Tests pin the fence by
  asserting a `${hook-body:unknown}` substring inside
  `then.prompt` does not refuse and is preserved verbatim.
- [ ] **(RFC-0005 v0.4)** Build-pipeline phase order
  (`agentbundle.build.phase_order.PHASE_ORDER`) is the tuple
  `("hook-body", "agent", "hook-wiring", "kiro-ide-hook", "command",
  "skill")`. Two real dependencies drive the order
  (`hook-wiring ← agent`, `kiro-ide-hook ← hook-body`); every
  other ordering is a tiebreak pinned for operational determinism.
- [ ] **(RFC-0005 v0.4)** User-scope `kiro-ide-hook` is refused
  at the contract layer with stderr `pack <P> declares
  kiro-ide-hook at user scope, but kiro adapter does not support
  user-scope IDE hooks (Kiro #5440 still open)`. The refusal is
  independent of Rail B — a kiro-ide-hook-only pack with
  `user-scope-hooks = true` still refuses because the *primitive*
  is repo-only in v1.
- [ ] **(RFC-0008)** The adapter contract
  (`docs/contracts/adapter.toml`) declares `install-routes` on
  `[adapter."claude-code"]` per RFC-0008 / spec
  `claude-plugins-install-route`. The conformance suite ships a
  *marker presence* and a *scope refusal* case per declared install
  route; the per-route fixtures live in
  `packages/agentbundle/tests/integration/test_claude_plugins_install_route.py`.
  The Claude-plugins *marker presence* case is asserted on **session
  2 or later** until upstream
  [`anthropics/claude-code#10997`](https://github.com/anthropics/claude-code/issues/10997)
  ships a fix.
- [ ] **(RFC-0010)** apm-route conformance cases; per-target
  coverage matrix. The adapter contract
  (`docs/contracts/adapter.toml`) declares `"apm"` on
  `[adapter."claude-code"].install-routes` per RFC-0010 / spec
  `apm-install-route-parity`. The conformance suite ships a
  *marker presence* and a *scope refusal* case for the APM route
  alongside the existing claude-plugins cases; the per-route
  fixtures live in
  `packages/agentbundle/tests/integration/test_apm_install_route.py`.
  The APM *marker presence* case is asserted on session 2 or later
  at Claude Code targets (the `#10997` first-session quirk applies
  to `SessionStart` at Claude Code regardless of route); at the
  other three HookIntegrator-covered targets (Copilot, Cursor,
  Gemini), the per-target first-session behaviour is deferred to
  the manual-QA matrix per
  `docs/specs/apm-install-route-parity/spec.md` AC17 — transcript
  arrival is the close criterion, not a blocker on this PR. The
  conformance suite enumerates the four covered HookIntegrator
  targets and the three uncovered ones (Codex, OpenCode,
  Windsurf), with the
  `agentbundle adapt --scope <project|user>` manual-fallback
  gesture documented per uncovered target.

## Changelog

- 2026-05-26: contract bumps v0.6 → v0.7 per `docs/specs/credential-broker-contract/spec.md` — header-comment update naming RFC-0013; `.agentbundle/` prefix non-regression pinned across the three user-scope adapters (claude-code, kiro, codex). Two new build-pipeline primitive classes registered: `shared-libs/` (many-to-many byte-identical projection into consumer skills' `scripts/` directories gated by `metadata.auth: creds`; drift gate per `credential-broker-contract` AC23; inter-pack basename collision is hard-error) and `adapter-root-bins/` (single-target projection to `$HOME/.agentbundle/bin/<basename>.py` at user scope, POSIX mode `0o755`; path-jail compliance per `credential-broker-contract` AC22). No conformance-suite addition to `distribution-adapters/spec.md` — per its own scope statement that *full* per-adapter conformance is RFC-0003's work; the two primitive classes are pinned by `credential-broker-contract`'s own ACs (AC20–AC23 for `shared-libs/`; AC22 for `adapter-root-bins/`).
- 2026-05-26: contract bump v0.6 → v0.7 per
  [RFC-0012 / `repo-scope-per-adapter-projection`](../../rfc/0012-repo-scope-per-adapter-projection.md).
  Every shipped adapter declares `allowed-prefixes.repo` on its
  `[adapter.<name>.scope]` table; Copilot gains a scope table for
  the first time (`repo` only — no user-scope analogue). Schema
  enforces `repo` and `allowed-prefixes` mandatory on every scope
  table; `user` stays optional. Conformance cases: per-IDE
  projection at repo scope for each shipped adapter
  (`<repo>/.claude/skills/`, `<repo>/.kiro/skills/`,
  `<repo>/.agents/skills/`, `<repo>/.github/instructions/`) plus
  the `--emit-install-routes` dist-tree fallback. The legacy
  dist-tree producer at `--scope repo .` becomes an opt-in behind
  the new flag (one transitional release with `DeprecationWarning`,
  per RFC-0012 § *Alternatives* #6).
- 2026-05-24: install-routes contract AC added per docs/specs/claude-plugins-install-route/spec.md — conformance suite ships marker-presence and scope-refusal cases per declared install route.
- 2026-05-25: contract bumps v0.4 → v0.5 per docs/specs/apm-install-route-parity/spec.md — "apm" appended to install-routes on [adapter."claude-code"].
- 2026-05-25: APM-route conformance AC added per docs/specs/apm-install-route-parity/spec.md — conformance suite ships marker-presence and scope-refusal cases for the APM route; four-of-seven HookIntegrator coverage documented; the `per-pack-apm-package` recipe row notes the install-marker artifact derivation.
- 2026-05-24: RFC-0005 v0.4 amendment — added `## v0.4 IDE event
  hooks (RFC-0005)` subsection between v0.3 user-scope hook
  handling and Boundaries. Pins the new `kiro-ide-hook` primitive,
  the Kiro `[adapter.kiro.projections.kiro-ide-hook]` table shape
  (mode / target / on-conflict / vocabularies), the five validate-
  rail refusal paths, the `then.command`-fenced single-pass
  placeholder substitution, the build-pipeline phase-order
  extension (`kiro-ide-hook` between `hook-wiring` and `command`),
  the user-scope refusal text, and the probe-gated `[contract]
  version` bump `"0.3" → "0.4"` (gated on Q6 recursion/extension
  probe and Q11 vocabulary-fixture capture per RFC-0005 § Gating
  verifications). Six new AC items tagged `(RFC-0005 v0.4)`. The
  schema and rail land in this PR; the v0.4 contract-table write
  and the schema's `primitive.required` extension are deferred to
  the probe-gated T-CONTRACT commit so a contract-version lie is
  impossible.
- 2026-05-24: templates relocated from `docs/_templates/` into the
  owning skills' `assets/` folders to comply with the agentskills.io
  skill-layout spec (skills are self-contained units; `references/` for
  read-on-demand material, `assets/` for material the skill copies
  elsewhere). `docs/_templates/` is no longer a projected path. The
  *Never do* item under §Boundaries was rewritten in place to point at
  the new location while preserving the rule's intent (no edits to
  template assets from this spec). The Rail A example was rewritten
  with `~/docs/specs/` since `~/docs/_templates/` no longer exists.
- 2026-05-23: bookkeeping reconciliation — the 14 pre-amendment
  ACs flipped `[ ]` → `[x]` against on-disk evidence in
  `packages/agentbundle/agentbundle/build/` (contract loader, four
  reference adapters, recipe loader, validate, self-host, scope
  rails) and `docs/contracts/`. The 5 `(RFC-0004)`-tagged ACs are
  already `[x]` from the v0.2 contract bump. The Rail C code-side
  marker-regex widening (paired with adapt-to-project AC21) is
  the only ROADMAP-tracked code gap on this spec and is not an
  unchecked AC here.
