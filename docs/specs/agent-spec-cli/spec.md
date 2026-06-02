# Spec: agent-spec-cli (`agentbundle`)

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0003](../../rfc/0003-spec-and-cli.md) (source);
  [RFC-0004](../../rfc/0004-install-scope-per-pack.md) (contract-v0.2
  amendment — `--scope` surface, `allowed-scopes` refusal, path-jail
  per scope, `~`-expansion, v0.1 state-file refuse-and-explain,
  dual-state-file walking); hard-depends on
  [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)
  (F-spec + F-build) and the sibling spec
  [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  (defines `pack.toml`, `adapter.toml`, the **Tier-1/2/3 file-safety
  contract**, the **`.agentbundle-state.toml` schema** (v0.1 and v0.2,
  with the v0.2 scope column), the **`.upstream.<ext>` companion
  semantics**, the **six-recipe enumeration**, the **five primitive
  types**, the **`[scope]` table** on the adapter contract, the
  **`[pack.install]` table** on `pack.toml`, the **three contract-
  level user-scope refusal rails** (seeds / hooks / marker), and the
  **path-jail-per-scope** rule this CLI honours).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Ship `agentbundle`, the reference CLI for the published adapter contract, as a
Python 3.11+ stdlib-only package at `packages/agentbundle/`. The CLI is the
deterministic counterpart to the LLM `adapt-to-project` skill: it imports the
render pipeline from `agentbundle.build` (the F-build library introduced by
the sibling `distribution-adapters` spec) and exposes eleven pack-aware
subcommands — in canonical install-workflow order (discovery-first):
`list-packs`, `list-targets`, `scaffold`, `install`, `validate`, `render`,
`adapt`, `diff`, `upgrade`, `uninstall`, `init-state` — to adopters in constrained-network or CI
environments. Success means an adopter on a corporate-network sandbox can
(1) fetch a `zipapp` build via `gh release download`, (2) `install` the `core`
pack into a brownfield repo without clobbering pre-existing files, (3) `adapt`
against a `--values-from` TOML to resolve `<adapt:NAME>` markers from
`.adapt-discovery.toml` and surface `.upstream.<ext>` companions for human
merge, and (4) round-trip `validate` + `render` against the conformance
fixtures with byte-identical output to RFC-0001's `make build`. The CLI is
library-first: F-build's render code is imported as `agentbundle.build`, not
invoked via `subprocess`. Every subcommand respects the Tier-1/2/3 file-safety
contract defined in the sibling `distribution-adapters` spec — Tier-1 may be
written, Tier-2 is preserved with a `.upstream.<ext>` companion, Tier-3 is
never touched. The CLI handles **five** primitive types (`skill`, `agent`,
`hook-body`, `hook-wiring`, `command`) and **six** recipe types as enumerated
in the sibling spec. No LLM calls, no third-party Python dependencies, no
writes outside the adopter's repo root.

## Install-scope dimension (CLI surface, contract v0.2)

Per [RFC-0004](../../rfc/0004-install-scope-per-pack.md) the adapter
contract grows a `scope` dimension (`repo` | `user`). The contract,
schema, state-file v0.2 format, and three user-scope refusal rails
(seeds / hooks / marker) are owned by the sibling
[`distribution-adapters`](../distribution-adapters/spec.md) spec; this
section pins the CLI surface that consumes them.

### `--scope` per subcommand

| Subcommand     | `--scope` behaviour                                                                                            |
| -------------- | -------------------------------------------------------------------------------------------------------------- |
| `install`      | **Override.** Defaults to the pack's `default-scope`; refused if the value is not in the pack's `allowed-scopes`. |
| `uninstall`    | **Disambiguator.** Required if the pack is installed at both scopes; inferred otherwise.                       |
| `upgrade`      | **Disambiguator.** Same rule as `uninstall`.                                                                   |
| `diff`         | **Disambiguator.** Same rule.                                                                                  |
| `init-state`   | **Selector.** Which scope's state file to initialize / migrate.                                                |
| `list-targets` | **Read-only filter.** Restricts output to one scope; omitting `--scope` shows both with a scope column.        |
| `list-packs`   | No `--scope` — catalogue query; scope is not yet bound.                                                        |
| `scaffold`     | No `--scope` — always repo-targeted. Refused if `"repo" ∉ allowed-scopes`. Ignores `default-scope`.            |
| `validate`     | No `--scope` — validates the pack's declared `default-scope ∈ allowed-scopes`, the seeds/hooks/`allowed-scopes` consistency, and the schema. |
| `render`       | No `--scope` — pack-local primitive rendering; scope only matters at install.                                  |
| `adapt`        | No `--scope` — walks **both** state files; reads `<repo>/.adapt-discovery.toml` at repo scope and `~/.agentbundle/.adapt-discovery.toml` at user scope. |
| `reconcile`    | **User-scope-only (RFC-0005).** Read-only orphan reporter; `--scope user` is the only accepted value. No `--apply` flag — write-mode reconciliation would re-create the merge-discipline problems RFC-0005 is designed to avoid. |

### Scope-resolution precedence

**CLI flag > pack `default-scope` > built-in `repo`.** A `--scope`
value outside the pack's `allowed-scopes` is refused non-zero with
stderr naming the pack, the requested scope, and the declared set:
`<pack>: scope '<requested>' not in allowed-scopes <declared-set>`.

### Path-jail per scope

Two rails fence every write:

1. **Per-scope root.** At repo scope, the jail is the repo root
   (unchanged). At user scope, the jail is `expanduser("~")`.
2. **Constrained to declared prefixes at user scope.** Every user-
   scope write must resolve under one of the
   `allowed-prefixes.<scope>` entries declared on the adapter's
   `[scope]` table (defined in the sibling spec). A write resolving
   under `~/Documents/` is refused even though it's "inside `~`."
   The CLI exits non-zero with stderr `refusing to write outside
   allowed prefixes for scope '<scope>': <path>`.

### `~`-expansion

`pathlib.Path.expanduser()` runs **once, at scope-resolution time**
— when `install`, `uninstall`, `upgrade`, or `adapt` resolves
`--scope user` to a concrete root. If the result equals the literal
`"~"` (expansion failed) or resolves to `"/"` (corporate sandbox
with `$HOME=/`), the CLI refuses with stderr `cannot resolve user
scope: $HOME unset or invalid`. The resolved absolute scope root is
printed **to stderr** before any write so adopters see the
destination explicitly. The stream choice (stderr, not stdout)
keeps the `installed:` rail's stdout assertions clean.

Windows support is deferred per the existing stdlib-only commitment;
`pathlib.expanduser` handles `%USERPROFILE%`, but cross-platform
conformance is not gated by this amendment.

### `.agentbundle-state.toml` write-time refusal at legacy schemas

The CLI **reads** any legacy state file (`schema-version = "0.1"` —
all-repo-scope; `schema-version = "0.2"` — full v0.2 read with v0.3's
new fields read-time-defaulted) without forcing migration. Any
**write-capable** invocation (`install`, `uninstall`, `upgrade`,
`init-state` *without* `--migrate`) against a legacy file exits
non-zero with stderr `state file at <path> is schema-version
<X>; run 'agentbundle init-state --migrate' first` (where `<X>`
names the actual version found). No silent rewrite — migrations are
additive but adopters running mixed CLI versions across CI and local
must opt in explicitly. The refuse-and-explain shape matches the
major-version refusal rail this spec already pins. v0.2 → v0.3 is
the cheapest possible additive migration (header-only-additive per
[RFC-0005 § State-file
impact](../../rfc/0005-user-scope-hook-support.md#state-file-impact));
v0.1 → v0.3 is performed as a single `init-state --migrate` invocation
that covers both the v0.1 → v0.2 scope-column backfill and the
v0.2 → v0.3 header bump in one re-serialize.

### `installed: <pack> @ <scope>` output

On every successful install the CLI prints `installed: <pack> @
<scope>` to stdout so the adopter sees the scope explicitly.

- *Single-scope install:* one `installed:` line; it is the last
  stdout line before exit zero.
- *Dual-scope `--force` install:* two `installed:` lines, one per
  scope, **in repo-then-user order**, both on stdout. The user-
  scope line is the last stdout line before exit zero.
- *Pre-flight order in dual-scope `--force`.* All preconditions
  for **both** scopes (scope refusal, `~`-expansion, Rails A/B/C
  re-check against resolved pack content, path-jail probe) are
  evaluated **before** any write to either scope's state file. A
  user-scope precondition that fails after the repo write would
  leave a half-applied install on disk; checking both scopes up
  front means a `--force` invocation either writes both scopes
  or writes neither, and the failure mode prints **zero**
  `installed:` lines plus the failing scope's stderr message.
- *`recommends` warnings* (when emitted) go to **stderr** — the
  `note:` convention used elsewhere in this spec is informational
  and stream-separate from the `installed:` rail. Adopter tooling
  can parse stdout for `installed:` lines independently of stderr.

### Dual-scope install conflict + `--force`

Installing pack `<P>` at scope `<S>` when `<P>` is already
installed at the other scope exits non-zero with stderr `<P>
already installed at <other-scope>; pass --force to install at
both`. `--force` carries semantics only on `install`; passing it to
any other verb is rejected with stderr `unknown flag for <verb>:
--force`.
`install` against a pack *already installed at the requested scope*
is refused with stderr `<P> already installed at <scope>; use
'upgrade' to change version`; `--force` does not override that
refusal — it addresses only the cross-scope conflict case, not
in-place re-install. A `--force` install against a pack *not*
already installed at the other scope is accepted as a normal
install (no-op effect from the flag) so wrapper scripts can pass
`--force` idempotently.

After a dual-scope install:

- `uninstall --scope <s>` removes only the named scope's entry; the
  other scope is untouched.
- `upgrade --scope <s>` upgrades only the named scope; per-verb,
  per-scope.
- `diff --scope <s>` reports against the named scope's state file.
- All three verbs require explicit `--scope` while a pack is
  installed at both scopes; the inferred-disambiguator from the
  *§ `--scope` per subcommand* table applies only when the pack is
  at exactly one scope.

### `recommends` across scopes

A pack's `recommends = [...]` is satisfied by an install of the
recommended pack at **any** scope. `install` warns (does not refuse)
when a recommended pack is missing entirely, and lists the scope(s)
the recommended pack is installed at when present.

All warnings are emitted to **stderr** (the `note:` informational
convention; stream-separate from the `installed:` rail). The
warning text distinguishes three cases:

- *Installed at a compatible scope* — the recommended pack is
  present at any scope in its own `allowed-scopes`:
  `note: recommends '<rec>' (found at <observed-scope> scope)`.
- *Missing but installable at the recommending pack's scope* —
  the recommended pack is not installed anywhere **and** the
  recommending pack's installed scope is in the recommended
  pack's `allowed-scopes`:
  `note: recommends '<rec>' (not installed)`.
- *Disjoint `allowed-scopes`* — the recommending pack's installed
  scope is **not** in the recommended pack's `allowed-scopes`.
  Reachable only when `allowed-scopes` is single-valued (a pack
  permitting both scopes can never be disjoint from any
  recommender, so the dual-scope case reduces to one of the two
  cases above). The text names the recommended pack's allowed
  scope:
  - Recommended is repo-only → `note: recommends '<rec>', which
    is repo-only; install it in your active project`.
  - Recommended is user-only → `note: recommends '<rec>', which
    is user-only; install it at user scope`.

The split exists so adopters can tell "I forgot something" apart
from "this combination has a structural mismatch." `recommends` is
informational; it never gates install. A dual-scope install
(`--force`) emits one warning per scope per recommend (so a
single-recommend dual-scope install emits up to two stderr lines).

### `adapt` dual-state-file walk

`adapt` walks **both** state files (`<repo>/.agentbundle-state.toml`
and `~/.agentbundle/state.toml`) and reads
`<repo>/.adapt-discovery.toml` at repo scope and
`~/.agentbundle/.adapt-discovery.toml` at user scope (user-scope
artifacts all live inside the `~/.agentbundle/` namespaced
dot-directory). Findings are recorded against the scope of the
file they were observed in:

- A squatter under `~/.claude/` is a user-scope finding.
- A `.upstream.<ext>` companion in `<repo>/` is a repo-scope
  finding.

`adapt --ci` exits non-zero if **either** scope's
`.adapt-pending.md` is non-empty. The per-scope report locations
match the per-scope state-file locations from the sibling
`distribution-adapters` spec:

| Scope  | Report path                              |
| ------ | ---------------------------------------- |
| `repo` | `<repo>/.adapt-pending.md`               |
| `user` | `~/.agentbundle/.adapt-pending.md`       |

User-scope reports live inside the namespaced
`~/.agentbundle/` dot-directory (the same one that holds the
user-scope state file), not as a bare dotfile in `$HOME`.

## v0.3 user-scope hook handling (RFC-0005)

The v0.3 contract bump (RFC-0005) extends the CLI surface with
user-scope hook-wiring support: `install` / `uninstall` / `upgrade`
thread hook-wiring through the v0.3 merge engines
(`user-merge-json` for Claude Code at user scope;
`merge-into-agent-json` for Kiro at both scopes), `install` gains a
`--force-merge` flag, and a new `reconcile --scope user` subcommand
reports orphans. The full design rationale lives in
[RFC-0005](../../rfc/0005-user-scope-hook-support.md); this section
pins the **CLI surface** the rationale produces.

### `--force-merge` flag on `install`

```
agentbundle install <catalogue> --pack <P> --scope user --force-merge
```

Binding rules (RFC-0005 § Binding and interaction with `--force`):

- **Bound to `install` only.** Passing `--force-merge` to any other
  verb is rejected with stderr `unknown flag for <verb>:
  --force-merge` (mirrors the `--force` binding shape RFC-0004
  established).
- **Bound to `--scope user`.** At repo scope the hook-wiring target
  is a pack-owned file (`.claude/settings.local.json` for Claude
  Code), so adopter collision is structurally a non-case. Refused
  with stderr `--force-merge is bound to user scope; pass --scope
  user or omit --force-merge`. Both the explicit `--scope repo`
  case and the pack-default-resolves-to-repo case refuse.
- **Claude-Code-targeted packs only.** Refused with stderr
  `--force-merge applies only to Claude-Code-targeted packs; pack
  <P> resolves to adapter 'kiro' at user scope`. Kiro's
  `merge-into-agent-json` target is pack-owned (the per-agent
  JSON), so adopter collision is again structurally a non-case.
- **Orthogonal to `--force`.** The two flags address different
  refusals — `--force` is the cross-scope-conflict bypass
  (RFC-0004), `--force-merge` is the adopter-collision bypass
  (RFC-0005). `install --force --force-merge` is permitted and each
  flag covers its own refusal.
- **No-op when no textual collision is detected.** Same
  idempotent-when-no-conflict shape as `--force`, so wrapper
  scripts can pass `--force-merge` unconditionally.

The flag's runtime semantics — adopt the adopter-authored entry,
preserve the original `command` in the state-file snapshot — are
pinned by [RFC-0005 § User-already-set-this-key collision
rule](../../rfc/0005-user-scope-hook-support.md#user-already-set-this-key-collision-rule)
and implemented inside the `user-merge-json` merger.

### `reconcile --scope user` — read-only orphan reporter

```
agentbundle reconcile --scope user
```

Walks two surfaces and reports two classes of orphan grouped by
adapter:

- `~/.claude/settings.json` (Claude Code) and every Kiro agent
  JSON named in user-scope state's `[[installed.hook-wiring-owned]]`
  rows.
- **orphan-in-file** — an `id`-tagged entry the target file claims
  but no installed pack's `hook-wiring-owned` row owns. Surfaces
  when a hand-edit on the settings file (or a Kiro agent JSON) adds
  an entry with an id no pack records.
- **orphan-in-state** — a state row claiming ownership of an entry
  the target file no longer has. Surfaces on hand-delete, on
  multi-machine sync drift, or when the merge target file was
  removed out-of-band.

Output format (stdout):

- `reconcile: all clean` when no orphans exist.
- One `reconcile: <adapter>` heading per adapter with orphans,
  followed by indented per-orphan lines.

**Read-only contract.** The subcommand does **not** register an
`--apply` flag — `argparse` rejects it with the standard
"unrecognized argument" exit code. A write-mode reconciler would
recreate the merge-discipline problems RFC-0005 is designed to
avoid; the adopter takes manual action from the report. The
exclusion is pinned by [RFC-0005 § Follow-on
artifacts](../../rfc/0005-user-scope-hook-support.md#follow-on-artifacts)
("a write-mode `reconcile --apply` is explicitly **not** in this
RFC's scope") and by the user-scope-hooks spec's *Never do*
boundary.

### State schema v0.3 — `[[installed]]` field additions

The state file's `schema-version` bumps from `0.2` to `0.3` per
RFC-0005 § State-file impact. `[[installed]]` rows grow three
optional fields, all with read-time defaults so v0.2-vintage rows
preserved across the header-only migration read correctly without
backfill:

| Field                 | Type                  | Required? | Read-time default                                              |
| --------------------- | --------------------- | --------- | -------------------------------------------------------------- |
| `adapter`             | string                | optional  | `"claude-code"`                                                 |
| `target-file`         | string                | optional  | `"~/.claude/settings.json"` when `adapter` is `"claude-code"`; **required (no default)** when `adapter` is `"kiro"` |
| `hook-wiring-owned`   | array-of-tables       | optional  | `[]`                                                            |

Each `[[installed.hook-wiring-owned]]` entry carries `event` and `id`
(both required strings) and optionally `target-file` (Kiro rows
always carry it; Claude Code rows defaulted at read).

### Migration shape (v0.2 → v0.3)

`init-state --migrate` against a v0.2 state file is
**header-only-additive**: only the `schema-version = "0.2"` line is
rewritten to `"0.3"`. Body bytes are byte-for-byte preserved; no
per-row backfill. Existing rows read with the v0.3 read-time
defaults above. v0.1 → v0.3 retains the full re-serialize shape
(the v0.1 → v0.2 scope-column backfill plus the header bump in one
step). The migration is idempotent — running `--migrate` against an
already-v0.3 file is a byte no-op.

### Refuse-and-explain texts (user-scope merge surfaces)

The v0.3 merge engines surface refuse-and-explain text the CLI
emits verbatim. Both engines are implemented in
`agentbundle/build/projections/` and propagate
`UserMergeRefusal` / `AgentJsonRefusal` to the CLI; install /
uninstall / upgrade catch the exception and print to stderr:

- **Unparseable JSON target** (`~/.claude/settings.json` or
  `<scope-root>/.kiro/agents/<agent>.json`):
  `cannot parse <path>: <error>; fix or back up the file and retry`.
  The file is **not** rewritten; no state is recorded.
- **Wrong-shape `hooks` key** (e.g. `hooks` is an array, or
  `hooks.<event>` is a string): `<path>: <key-path> has unexpected
  shape <type>; expected <expected>`. Where `<key-path>` is
  `hooks` or `hooks.<event>` as relevant.
- **Adopter command collision (Claude Code only)**: `pack <P>'s
  hook <name> at event <event> appears to be already wired in
  <path>; remove the manual entry or pass --force-merge to take
  ownership`. Whitespace-normalised string match per RFC-0005 §
  User-already-set-this-key collision rule.
- **Missing agent file at Kiro merge time** (pipeline-ordering
  invariant violation; reachable only via test instrumentation
  today): `internal: <agent-file> missing at hook-wiring merge
  time; agent must project before wiring`.
- **Path-traversal `attach-to-agent`** (defence-in-depth at install
  and upgrade time): `pack <P>'s hook-wiring <name>.toml declares
  attach-to-agent=<value> which violates the agent-name grammar
  ^[a-z0-9][a-z0-9-]*$ — refusing`.

### Cross-adapter upgrade — refused

`upgrade` refuses when the new pack version resolves to a different
adapter than the recorded `pack_state.adapter` (e.g. Kiro → Claude
Code or vice versa, detected via the
`.apm/agents/`-presence heuristic). Stderr: `pack adapter changed
from '<old>' → '<new>' between versions; run uninstall + install
instead (cross-adapter upgrade is not supported)`. AC19b covers
within-Kiro `attach-to-agent` renames; adapter switches need an
explicit recovery gesture.

## v0.4 kiro-ide-hook primitive (RFC-0005)

The v0.4 contract bump (RFC-0005) extends the CLI surface with the
new `kiro-ide-hook` primitive. (Code shipped in PR #99; contract activation deferred to RFC-0022.)
The primitive carries Kiro's
standalone IDE-event hooks — `.kiro.hook` JSON files Kiro reads on
file create / save / delete, prompt submit, agent stop, and tool /
task events. The full design lives in
[RFC-0005 § Kiro IDE event hooks — new `kiro-ide-hook`
primitive](../../rfc/0005-user-scope-hook-support.md#kiro-ide-event-hooks--new-kiro-ide-hook-primitive);
this section pins the **CLI surface** the rationale produces.

### `install` projection

`install --pack <P>` against a pack shipping `.apm/kiro-ide-hooks/`
content threads the directory through the build pipeline's new
`kiro-ide-hook` projection phase (after `hook-wiring` and before
`command`, per the sibling
[`distribution-adapters/spec.md`](../distribution-adapters/spec.md)'s
`## v0.4 IDE event hooks (RFC-0005)` subsection).

**Pre-install validation — validate-only by design.** The
`check_kiro_ide_hook` rail runs at `validate` time but **not** at
`install` time. This matches the pre-existing convention for the
Kiro vocabulary rails (`check_kiro_event_vocabulary` is also
validate-only); only Rails A/B/C from RFC-0004 are dual-wired.
Adopters who want kiro-ide-hook validation as an install
pre-check run `agentbundle validate <pack>` first; a follow-up
RFC could extend `install` to mirror the existing rails into the
install path, but doing so here would broaden a pattern that
hasn't been challenged.

Per-file projection:

- **askAgent-shaped hooks** (`then.type == "askAgent"` AND raw
  bytes contain no `${` substring) byte-copy via `shutil.copy2`,
  preserving source SHA, key ordering, whitespace, and trailing
  newline.
- **runCommand-shaped hooks with placeholders** (`${...}`
  substring present) parse as JSON, scan `then.command` with a
  single-pass regex, and rewrite each `${hook-body:<name>}` to the
  projected hook-body path (e.g. `./tools/hooks/lint.py` at repo
  scope). The output is re-serialised via `json.dumps(indent=2)`
  with a trailing newline.

Each projected file is recorded under `[pack.<name>.files]` with
its post-write SHA — same Tier-1 record as every other direct-file
projection.

### `uninstall` — per-file Tier-1 path

`uninstall` removes the projected `.kiro.hook` files via the
existing per-file Tier-1 path
([uninstall.py:138-186](../../../packages/agentbundle/agentbundle/commands/uninstall.py)
Tier-1/Tier-2 loop +
[uninstall.py:228, 260-294](../../../packages/agentbundle/agentbundle/commands/uninstall.py)
empty-parent sweep). Every projected file is recorded under
`[pack.<name>.files]` with its SHA; SHA-match deletes (Tier-1),
SHA-mismatch preserves (Tier-2). The pack-namespaced subdirectory
`.kiro/hooks/<pack>/` empties out and the existing best-effort
empty-parent sweep removes it. **No new directory-removal code
path is added** — kiro-ide-hook inherits the property every other
`direct-file` primitive already has.

**Adopter hand-edits preserved.** A hand-edited `.kiro.hook` whose
on-disk SHA no longer matches the state record is treated as
Tier-2: warn-and-preserve, not delete. Same property as every
other `direct-file` primitive. `runCommand`-shaped hooks deserve
a specific operator-facing callout because adopter-edited
`command` strings often encode a *local fix* the pack author
hasn't shipped yet (a patched path, a wrapped invocation, an
added flag) — those edits survive uninstall unless the adopter
removes them out of band. The salience is higher than for an
askAgent prompt edit.

> **RFC drift flagged.** RFC-0005 § State-file impact lines
> 1067-1086 describe uninstall as "unconditional / verbatim" and
> claim adopter hand-edits are "lost on uninstall." That prose
> describes a behaviour `uninstall.py` does *not* implement — the
> shipped command is Tier-2-preserve on SHA mismatch. This spec
> documents actual code behaviour; the RFC-text amendment is
> recorded as a deferred follow-up rather than rolled into this
> PR (which is scoped to the kiro-ide-hook primitive's projection
> + validate rail, not the broader RFC-text reconciliation).

### Build-pipeline ordering invariant — reference

The CLI honours the phase-order invariant the sibling
[`distribution-adapters` spec § *Build-pipeline phase order —
extended*](../distribution-adapters/spec.md#build-pipeline-phase-order--extended)
pins. The order is the single tuple
`hook-body → agent → hook-wiring → kiro-ide-hook → command →
skill`, exported from `agentbundle.build.phase_order.PHASE_ORDER`.
The kiro-ide-hook phase runs after hook-body so
`${hook-body:<name>}` placeholders can resolve to the projected
hook-body path written at the prior phase.

### No state-file shape change

The v0.3 state file (`.agentbundle-state.toml` schema-version
`"0.3"`) carries kiro-ide-hook files in the existing
`[pack.<name>.files]` table — one per projected
`.kiro/hooks/<pack>/<name>.kiro.hook` file, same shape as every
other direct-file projection. No new `kiro-ide-hook-owned` table
is introduced (RFC-0005 § State-file impact, lines 1058-1065): the
pack-namespaced subdirectory layout makes uninstall a per-file
deletion plus the empty-parent sweep, without needing a separate
ownership record.

### User-scope refusal — independent of Rail B

`install --scope user` against any pack shipping
`.apm/kiro-ide-hooks/` content is refused at the contract layer
with the RFC § Scope verbatim stderr

```
pack <P> declares kiro-ide-hook at user scope, but kiro adapter does not support user-scope IDE hooks (Kiro #5440 still open)
```

The refusal is **independent of the existing Rail B**
([`distribution-adapters` § Install-scope dimension → Rail
B](../distribution-adapters/spec.md#contract-level-user-scope-refusal-rails)).
A pack shipping only `.apm/kiro-ide-hooks/` (no `.apm/hooks/` and
no `.apm/hook-wiring/`) does not trigger Rail B — there are no
"hook-shaped primitives" in Rail B's sense — but it does trigger
this new kiro-ide-hook-only refusal because the primitive itself
is repo-only in v1. A pack opting into Rail B with
`user-scope-hooks = true` still refuses for the same reason if it
also ships kiro-ide-hooks. The two refusals are sibling rails;
neither subsumes the other.

When upstream Kiro #5440 closes, the user-scope refusal lifts via
either an in-place RFC amendment (if no state-file shape change is
needed) or a successor RFC.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Honour the Tier-1/2/3 file-safety contract on every subcommand that writes:
  Tier-1 paths (adapter-contract-projected, recorded in
  `.agentbundle-state.toml`) may be created or overwritten; Tier-2 paths (same
  paths, but adopter-edited since install per content-hash comparison) get a
  `.upstream.<ext>` companion next to the original; Tier-3 paths (everything
  else) are read-only to the CLI. The contract, the
  `.agentbundle-state.toml` schema, and the `.upstream.<ext>` semantics are
  owned by the sibling `distribution-adapters` spec (see its Tier-contract
  AC and state-file AC); this CLI consumes them verbatim.
- Import the render pipeline from `agentbundle.build` (the F-build library
  introduced by the sibling spec when it moved F-build under
  `packages/agentbundle/agentbundle/build/`); reuse one implementation rather
  than calling `make build` via `subprocess`. Adapters resolve via the
  imported `agentbundle.build.adapters` registry at runtime, not from baked-in
  constants. The registry contract: `agentbundle.build.adapters` exposes a
  mapping `name → AdapterModule` populated at import time (sibling
  `distribution-adapters` spec pins the `AdapterModule` shape).
- Fetch `git+https://` catalogue URIs via `urllib.request` against GitHub's
  archive endpoint (`https://github.com/<owner>/<repo>/archive/refs/tags/<tag>.tar.gz`,
  `…/archive/refs/heads/<branch>.tar.gz`, or `…/archive/<sha>.tar.gz`) and
  extract with `tarfile` — pure stdlib, no `git`/`gh` subprocess. SSH git URLs
  are deferred to v1.1.
- Resolve the spec version a pack declares by reading `[pack.adapter-contract]
  version` in its `pack.toml`; refuse to operate on packs whose major version
  disagrees with the CLI's own and emit a clear refuse-and-explain message.
  The CLI's own spec version is parsed at import time from the bundled
  canonical `adapter.toml` (`[contract] version`), not hardcoded.
- Confine every write-capable subcommand to paths under the configured
  `--output <dir>` or the resolved repo root; refuse and exit non-zero on any
  attempt to project outside that root (e.g. a malicious projection rule
  resolving to `../../`).
- Preserve the source extension of hook files when projecting and upgrading:
  `.sh` hooks remain `.sh`, `.py` hooks remain `.py`.
- Exit non-zero with a one-line stderr reason on any failure (validation,
  hash mismatch refusal, version mismatch, missing pack, primitive-not-found,
  unreachable catalogue URI); exit zero only when the subcommand's contract
  was satisfied.
- Read configuration and state exclusively from TOML files (`pack.toml`,
  `.agentbundle-state.toml`, `.adapt-discovery.toml`, `--values-from <file.toml>`).
- Resolve `--scope` per § *Install-scope dimension*: CLI flag > pack
  `default-scope` > built-in `repo`. Refuse non-zero when the
  resolved value is not in the pack's `allowed-scopes` with a stderr
  line naming the pack, the requested scope, and the declared set.
- Run the per-scope path-jail on every write: at user scope, the
  jail combines `expanduser("~")` with the adapter's declared
  `allowed-prefixes.<scope>` array; a write resolving inside `~` but
  outside the prefix list is refused.
- Apply `pathlib.Path.expanduser()` to the user-scope root once at
  scope-resolution time; refuse with `cannot resolve user scope:
  $HOME unset or invalid` when the result is literal `"~"` or `"/"`.
  Print the resolved absolute scope root before any write.
- Print `installed: <pack> @ <scope>` on every successful install.
- Walk both state files (`<repo>/.agentbundle-state.toml` and
  `~/.agentbundle/state.toml`) in `adapt`; record findings against
  the scope of the file they were observed in.
- Require explicit `--scope` for `uninstall`, `upgrade`, and `diff`
  when a pack is installed at both scopes; infer when the pack is
  at exactly one scope.

### Ask first

- Adding a new subcommand or flag beyond the eleven enumerated in
  RFC-0003's F-cli. The shape is fixed at this RFC's resolution; expansion
  goes through a new RFC or spec amendment.
- Changing the CLI's name from `agentbundle` (committed at this spec) or the
  package path from `packages/agentbundle/`.
- Introducing a new persisted on-disk artifact (file the CLI writes that
  isn't already in this list: Tier-1 projected files, `.agentbundle-state.toml`,
  `.adapt-pending.md`, `.upstream.<ext>` companions, the user-scope
  state file `~/.agentbundle/state.toml`).
- Extending `--scope` to a subcommand not listed in § *Install-scope
  dimension* — *§ `--scope` per subcommand* is the closed set at
  v0.2.
- Extending `--force` semantics beyond the cross-scope-conflict case
  on `install`. `--force` is bound to `install` only; binding it to
  another verb (or making it override the in-place re-install
  refusal) is an Ask-first change.

### Never do

- Never write outside the adopter's repo root (the directory containing
  `pack.toml` for the operative pack, or the `--output <dir>` target if
  explicitly passed). A path-jail check fences every write call site.
- Never clobber a Tier-2 file (content hash differs from
  `.agentbundle-state.toml`); always emit a `.upstream.<ext>` companion
  instead and let `adapt` or the LLM skill resolve the merge.
- Never touch a Tier-3 file (a path not recorded in
  `.agentbundle-state.toml` under any installed pack's projection).
- Never add a third-party Python dependency. Stdlib only — `tomllib`,
  `argparse`, `hashlib`, `pathlib`, `urllib`, `tarfile`. The sibling
  `distribution-adapters` spec commits to a stdlib-import audit in its build
  (`lint-build.sh` or equivalent); that audit is the structural enforcement
  for this rail — cite it rather than re-implement here.
- Never `subprocess` anything except `gh` for release download. No shelling
  out to `make`, `git`, `diff`, or any other host binary. `git+https://`
  fetch goes through `urllib.request` + `tarfile`, not a `git` subprocess.
- Never invoke an LLM, spawn a Claude session, or call any external
  inference API. The CLI is the deterministic counterpart to LLM skills.
- Never write `.adapt-discovery.toml` from the CLI; the CLI only *reads*
  it (the `adapt-to-project` LLM skill writes it). `<adapt:NAME>` marker
  resolution is the CLI's job (per the sibling `distribution-adapters` spec
  carve-out: `make build --self` resolves markers; adopter installs leave
  markers unresolved for `agentbundle adapt` to consume). Plugin-installed
  pack marker resolution is deferred to the `adapt-to-project` LLM skill;
  out of scope for v1 (RFC-0001 Open Q3).
- Never silently rewrite a `schema-version = "0.1"`
  `.agentbundle-state.toml`. Any write-capable invocation against a
  v0.1 file exits non-zero with the
  `init-state --migrate` refuse-and-explain message defined in
  § *Install-scope dimension*. Reads of a v0.1 file are fine and
  treat every entry as repo-scope.
- Never install a `seeds/`-bearing, hook-bearing, or `<adapt:NAME>`-
  marker-bearing pack at user scope. The three rails live in
  `validate` (sibling `distribution-adapters` spec); `install`
  re-runs each rail against the resolved pack content whenever
  `--scope user` is requested or the pack's `default-scope` is
  `"user"`, closing the widen-after-publish gap.

## Testing Strategy

Each user-visible outcome from the Objective is paired with a mode:

- **Per-subcommand contract — TDD.** Each of the eleven subcommands has a
  contract (inputs, on-disk outputs, exit code, stderr message on failure)
  small enough to pin with a fast unit/integration test. Tests drive the
  implementation; the test asserts on the post-state of a fixture directory
  and on the captured stdout/stderr, not on internal calls.
- **Tier-1/2/3 file-safety invariants — TDD (cross-cutting integration).**
  A single parametrised integration test walks every write-capable
  subcommand (`scaffold`, `install`, `render`, `adapt`, `init-state`,
  `upgrade`, `uninstall`) against the same Tier-1/2/3 fixture and asserts
  the three invariants per command: Tier-1 may change; Tier-2 produces a
  `.upstream.<ext>` companion (original byte-identical); Tier-3 paths are
  byte-identical before and after. The fixture covers both hook extensions
  (`.sh` and `.py`) to pin extension-preservation for `render` and `upgrade`.
- **F-build parity — goal-based check.** A one-liner diffs `agentbundle render
  packs/core --output /tmp/out` against `make build` output for the `core`
  pack; the two outputs must match byte-for-byte. This pins that the CLI uses
  the same render code as F-build (imported as `agentbundle.build`), not a
  fork.
- **Brownfield end-to-end — TDD on fixture + manual QA on a real sandbox.**
  A fixture repo at `packages/agentbundle/tests/fixtures/brownfield/` carries
  pre-existing `AGENTS.md`, `docs/CHARTER.md`, and adopter-owned source files;
  an integration test runs `install` → `adapt --values-from values.toml` →
  `diff` and asserts the resulting tree. The corporate-network sandbox path
  (`gh release download` → `python agentbundle.pyz install`) is **manual QA**
  recorded in the plan because we can't simulate Artifactory + PAT in CI.
- **`zipapp` distribution — goal-based check.** A build step produces
  `dist/agentbundle.pyz`; `python dist/agentbundle.pyz --version` prints the
  CLI version plus the spec version it ships against. Exit 0 is the check.
- **Conformance suite execution — TDD (partial at v1).** `agentbundle
  validate packs/core` runs schema conformance now. `agentbundle validate
  --strict packs/core` runs the conformance fixtures (one per target adapter
  at v0.1) and asserts pass/fail; **behavioural `--strict` is partial at v1
  because the F-conformance fixtures are owned by RFC-0003's deferred
  conformance work** — when fixtures are absent, `--strict` warns and exits
  zero on the schema portion. Full `--strict` lands at v1.1 once
  F-conformance ships.

The typical mix is heavy on TDD because most CLI behaviour is contract-shaped;
`zipapp` distribution and the sandbox round-trip are the goal-based and manual
QA tails respectively.

## Acceptance Criteria

- [x] `packages/agentbundle/` exists with `pyproject.toml`, `agentbundle/`,
      and `tests/`, following the `packages/_example/` layout. The package
      contains `agentbundle/build/` (F-build library, owned by the sibling
      `distribution-adapters` spec) and the CLI imports it cleanly as
      `import agentbundle.build` — no `sys.path` manipulation, no subprocess
      to `tools/build/build.py`.
- [x] `python -m agentbundle --version` prints both the CLI version and the
      spec version it ships against (`v0.1` at first release). The spec
      version value is parsed **at import time** from the bundled canonical
      `adapter.toml`'s `[contract] version` field. A test proves the
      read-at-import semantics: it captures the on-disk value, imports the
      package, mutates `adapter.toml` on disk to a different version, then
      asserts that `python -m agentbundle --version` still prints the
      original (import-time) value — not the post-mutation value.
- [x] All eleven subcommands from RFC-0003 F-cli, in canonical
      install-workflow order (discovery-first: `list-packs`, `list-targets`,
      `scaffold`, `install`, `validate`, `render`, `adapt`, `diff`,
      `upgrade`, `uninstall`, `init-state`), are implemented, each with a
      passing contract test asserting exit code, stdout/stderr, and on-disk
      post-state for at least one happy-path fixture. RFC-0003 enumerates
      the same eleven subcommands in a different (descriptive) order; this
      spec freezes the canonical install-workflow order.
- [x] `agentbundle render packs/core --output /tmp/out` produces a tree that
      is byte-identical to `make build` output for `packs/core` (F-build parity
      gate). `render` handles all five primitive types (`skill`, `agent`,
      `hook-body`, `hook-wiring`, `command`) and preserves source extensions
      for hook files (`.sh` and `.py`).
- [x] A single cross-cutting integration test proves the Tier-1/2/3
      invariants hold for every write-capable subcommand (`scaffold`,
      `install`, `render`, `adapt`, `init-state`, `upgrade`, `uninstall`)
      against one shared fixture: Tier-1 may change; Tier-2 paths produce a
      `.upstream.<ext>` companion and the original is unchanged; Tier-3
      paths are byte-identical before and after. The fixture covers both
      `.sh` and `.py` hooks to pin extension preservation.
- [x] Every write-capable subcommand refuses to write outside the configured
      `--output` / repo root: a fixture pack with a projection rule
      attempting `../../malicious` is rejected with exit non-zero and a
      one-line stderr "refusing to write outside repo root: <path>".
- [x] `agentbundle install --pack core <catalogue-uri>` at v1 accepts two
      catalogue URI forms: local paths (relative or absolute, e.g.
      `./catalogues/foo` or `/abs/path`) and git over HTTPS
      (`git+https://github.com/<owner>/<repo>[@<ref>]` where `<ref>` is a
      tag, branch, or commit SHA). HTTPS fetch goes through
      `urllib.request` + `tarfile` against GitHub's
      `https://github.com/<owner>/<repo>/archive/...` endpoint (no `git`
      subprocess). Unreachable URLs exit non-zero with a one-line stderr
      naming the tarball URL the CLI tried to fetch. `git+ssh://...` URLs
      exit non-zero with stderr "SSH git URLs deferred to v1.1; use https
      or local path."
- [x] `agentbundle install --pack <new>` against the brownfield fixture
      leaves all pre-existing adopter files unchanged and drops
      `.upstream.<ext>` companions for every Tier-2 collision. When an
      `.agentbundle-state.toml` already exists (e.g. from a prior `install
      --pack <other>`), the new install **merges**: adds a `[pack.<new>]`
      table without modifying existing `[pack.<other>]` tables.
- [x] `agentbundle adapt --values-from tests/fixtures/values.toml` resolves
      every `<adapt:NAME>` marker in projected files (the CLI is the
      resolver for adopter installs, per the sibling spec's carve-out),
      writes a `.adapt-pending.md` report listing each `.upstream.<ext>`
      companion with a one-line diff summary,
      and reads the `[markers]` table in `.adapt-discovery.toml`
      per docs/specs/adapt-to-project/spec.md, without writing
      to it.
- [x] `agentbundle adapt --ci` exits non-zero whenever any `.upstream.<ext>`
      companion remains on disk (so CI flags pending companions for human
      review). "Resolved" means the companion file no longer exists; the
      `--ci` exits-zero path is verified by a fixture where every companion
      has been removed.
- [x] `agentbundle upgrade --pack <name> --skill <skill> --to <version>`
      moves only the named primitive; `.agentbundle-state.toml` records the
      resulting mixed-version pack state and subsequent whole-pack upgrades
      surface the mixed state before proceeding. The same flag shape works
      for `--agent`, `--hook`, `--seed`, and `--command`. **Flag-to-primitive
      mapping:** `--skill` → `skill`, `--agent` → `agent`, `--command` →
      `command`, `--seed` → `seeds/` content (not a primitive type per the
      sibling spec, but a movable unit), and `--hook <name>` is atomic over
      the matching `hook-body` (`.apm/hooks/<name>.{sh,py}`) **and** the
      matching `hook-wiring` (`.apm/hook-wiring/<name>.toml`) of the same
      name — wiring co-moves with its body so a per-hook upgrade can never
      land a torn pair. Naming a non-existent primitive (`--skill foo`
      where `foo` isn't in the pack) exits non-zero with one-line stderr
      "primitive 'foo' not in pack <pack>".
- [x] `agentbundle validate packs/core` exits 0 on schema-valid v0.1
      fixtures and exits 1 with a one-line reason on a schema-invalid
      fixture. `agentbundle validate --strict packs/core` additionally runs
      the v0.1 conformance fixtures **when they exist** (full strict
      behaviour deferred to v1.1 alongside F-conformance from RFC-0003);
      when fixtures are absent, `--strict` warns on stderr and exits zero
      on the schema portion. `validate` checks recipes against the
      six-type enumerated set defined in the sibling `distribution-adapters`
      spec.
- [x] `dist/agentbundle.pyz` runs end-to-end on a Python 3.11 environment
      with no third-party packages installed (`pip list` shows only stdlib).
      Manual QA in a corporate-network sandbox confirms `gh release download`
      → `python agentbundle.pyz install` works.
- [x] **Ship-time prerequisite:** the git tag `contract-v<version>` (e.g.
      `contract-v0.1`) exists in this repo's history before
      `dist/agentbundle.pyz` is uploaded as a release asset, so the
      `--version` spec field has a canonical referential anchor in git
      history.
- [x] `pip list --format=freeze` inside `packages/agentbundle/` lists zero
      runtime dependencies (test-only dev-deps allowed). The sibling
      `distribution-adapters` spec's stdlib-import audit (its build's
      `lint-build.sh` equivalent) provides the structural lint that
      catches drift; cite it here rather than duplicate.
- [x] `agentbundle.build.adapters` exposes a mapping `name → AdapterModule`
      populated at import time (the `AdapterModule` shape is pinned by the
      sibling `distribution-adapters` spec's registry contract AC). A test
      asserts: `import agentbundle.build.adapters as A; assert isinstance(
      A.registry, Mapping); assert set(A.registry).issuperset({"claude_code",
      "kiro", "copilot", "codex"})`.
- [x] A version-mismatch fixture (pack declares spec `v2.0`, CLI ships
      `v0.1`) causes every subcommand to refuse with a stderr line naming
      both versions; no partial behaviour observed.
- [x] **(RFC-0004)** `--scope {repo,user}` is accepted on `install`,
      `uninstall`, `upgrade`, `diff`, `init-state`, and
      `list-targets` only. Passing `--scope` to `list-packs`,
      `scaffold`, `validate`, `render`, or `adapt` exits non-zero
      with stderr `unknown flag for <verb>: --scope`. The flag's
      semantics match the table in § *Install-scope dimension*:
      override on `install`; disambiguator on `uninstall` / `upgrade`
      / `diff`; selector on `init-state`; read-only filter on
      `list-targets`.
- [x] **(RFC-0004)** Scope resolution follows CLI flag > pack
      `default-scope` > built-in `repo`. A `--scope <s>` value not
      in the pack's `allowed-scopes` exits non-zero with stderr
      `<pack>: scope '<requested>' not in allowed-scopes
      <declared-set>`. A test pins the precedence: a pack declaring
      `default-scope = "repo"` resolves to repo when no flag is
      given; passing `--scope user` against an `allowed-scopes`
      that excludes user is refused; passing `--scope user` against
      a pack declaring `allowed-scopes = ["repo", "user"]` resolves
      to user.
- [x] **(RFC-0004)** Path-jail extended: every user-scope write
      resolves under one of the adapter's
      `allowed-prefixes.<scope>` entries (declared in the sibling
      spec's `[scope]` table) or the CLI refuses non-zero with
      stderr `refusing to write outside allowed prefixes for scope
      '<scope>': <path>`. The repo-scope jail (writes under repo
      root) is unchanged. A test fixture with a projection rule
      resolving under `~/Documents/` (inside `~`, outside the
      declared `[".claude/", ".agentbundle/"]` prefixes) is refused.
- [x] **(RFC-0004)** `~`-expansion runs once at scope-resolution
      time. When the result is literal `"~"` (expansion failed) or
      `"/"` ($HOME=/), every `--scope user` invocation exits non-
      zero with stderr `cannot resolve user scope: $HOME unset or
      invalid`. When expansion succeeds, the CLI prints the
      resolved absolute scope root to stderr before any write.
- [x] **(RFC-0004)** Write-capable invocations against a v0.1
      `.agentbundle-state.toml` exit non-zero with stderr `state
      file at <path> is schema-version 0.1; run 'agentbundle
      init-state --migrate' first`. Read-only invocations
      (`list-targets`, `diff`, `adapt` without `--values-from`)
      against the same v0.1 file succeed, treating every entry as
      repo-scope. `init-state --migrate` rewrites a v0.1 file to
      v0.2 idempotently; the writer's contract is owned by the
      sibling `distribution-adapters` spec.
- [x] **(RFC-0004)** Every successful `install` prints `installed:
      <pack> @ <scope>` to stdout. A single-scope install emits one
      line as the last stdout content before exit zero. A
      dual-scope `--force` install emits two lines, **repo first,
      user second**, both on stdout; the user-scope line is the
      last stdout content. Verified by capturing stdout and
      asserting the exact line sequence per case.
- [x] **(RFC-0004)** Dual-scope conflict on `install`: when pack
      `<P>` is already installed at the other scope, the install
      exits non-zero with stderr `<P> already installed at
      <other-scope>; pass --force to install at both`. `--force`
      install proceeds in this case; `--force` install of a pack
      *not* already at the other scope succeeds as a normal install
      (idempotent flag). `--force` against a pack *already*
      installed at the requested scope is refused with stderr `<P>
      already installed at <scope>; use 'upgrade' to change
      version`. Passing `--force` to any verb other than `install`
      exits non-zero with stderr `unknown flag for <verb>:
      --force`. After a dual-scope install, `uninstall --scope`,
      `upgrade --scope`, and `diff --scope` are required (refused
      with `<P> installed at multiple scopes; pass --scope {repo,
      user}` when omitted).
- [x] **(RFC-0004)** `recommends` cross-scope: an `install` warns
      (does not refuse) on **stderr** when a recommended pack is
      missing or scope-disjoint. Warning text per § *`recommends`
      across scopes*:
      `note: recommends '<rec>' (found at <observed-scope> scope)`,
      `note: recommends '<rec>' (not installed)`,
      `note: recommends '<rec>', which is repo-only; install it in
      your active project`, or
      `note: recommends '<rec>', which is user-only; install it at
      user scope`. The disjoint-case text names the *recommended*
      pack's allowed scope, not the recommending pack's installed
      scope. A dual-scope `--force` install emits one warning per
      scope per recommend.
- [x] **(RFC-0004)** `adapt` walks **both**
      `<repo>/.agentbundle-state.toml` and
      `~/.agentbundle/state.toml`, reads
      `<repo>/.adapt-discovery.toml` at repo scope and
      `~/.agentbundle/.adapt-discovery.toml` at user scope, and
      writes the pending report to `<repo>/.adapt-pending.md` at
      repo scope and `~/.agentbundle/.adapt-pending.md` at user
      scope. `adapt --ci` exits non-zero if *either* scope's
      `.adapt-pending.md` is non-empty. Findings are recorded
      against the scope of the file they were observed in (a
      squatter under `~/.claude/` is a user-scope finding; a
      `.upstream.<ext>` companion in `<repo>/` is a repo-scope
      finding).
- [x] **(RFC-0004)** `validate` against a v0.2 pack whose
      `default-scope` is not in `allowed-scopes` exits non-zero
      with stderr `pack <name>: default-scope '<requested>' not
      in allowed-scopes <declared-set>`. The schema-level
      `default-scope ∈ allowed-scopes` invariant (owned by the
      sibling `distribution-adapters` spec's `pack.schema.json`)
      is the structural enforcement; this AC pins the CLI's
      user-facing stderr text.
- [ ] **(RFC-0005 v0.4)** `install --pack <P>` against a pack
      shipping `.apm/kiro-ide-hooks/<*>.kiro.hook` files projects
      each file to `<scope-root>/.kiro/hooks/<pack>/<name>.kiro.hook`
      via the new `kiro-ide-hook` projection phase. askAgent hooks
      with no `${` substring in their raw bytes byte-copy
      verbatim (SHA equality between source and target); hooks
      containing `${hook-body:<name>}` placeholders in
      `then.command` parse, expand each placeholder verbatim and
      single-pass against the same-pack hook-body's projected
      path, and re-emit via `json.dumps(indent=2)` with a trailing
      newline. Tests pin both paths.
- [ ] **(RFC-0005 v0.4)** `uninstall` removes the projected
      `.kiro.hook` files via the existing per-file Tier-1 path
      ([uninstall.py:138-186](../../../packages/agentbundle/agentbundle/commands/uninstall.py)
      + [:228, 260-294](../../../packages/agentbundle/agentbundle/commands/uninstall.py)).
      SHA-match deletes (Tier-1); SHA-mismatch preserves (Tier-2)
      — adopter hand-edits to projected `.kiro.hook` files
      survive uninstall, with `runCommand`-shaped hooks the
      higher-salience subset because adopter-edited `command`
      strings often encode local fixes. No new directory-removal
      code path is added; the empty-parent sweep already removes
      `.kiro/hooks/<pack>/` once every recorded file deletes.
- [ ] **(RFC-0005 v0.4)** Build-pipeline phase order is the tuple
      `("hook-body", "agent", "hook-wiring", "kiro-ide-hook",
      "command", "skill")` exported from
      `agentbundle.build.phase_order.PHASE_ORDER`. The CLI
      honours this order whenever it calls into the build
      pipeline. Cross-pack ordering is not introduced.
- [ ] **(RFC-0005 v0.4)** No state-file shape change. The v0.3
      schema (`schema-version = "0.3"`) carries kiro-ide-hook
      files in the existing `[pack.<name>.files]` table — one
      entry per projected `.kiro.hook` file, same shape as every
      other direct-file primitive. The
      `[[installed.hook-wiring-owned]]` table introduced at v0.3
      is **not** extended; kiro-ide-hook files need no separate
      ownership record because the pack-namespaced subdirectory
      layout makes uninstall a per-file path.
- [ ] **(RFC-0005 v0.4)** `install --scope user` against any
      pack shipping `.apm/kiro-ide-hooks/` content is refused at
      the contract layer with stderr `pack <P> declares
      kiro-ide-hook at user scope, but kiro adapter does not
      support user-scope IDE hooks (Kiro #5440 still open)`. The
      refusal is independent of Rail B — a pack shipping only
      `.apm/kiro-ide-hooks/` (no `.apm/hooks/`, no
      `.apm/hook-wiring/`) still refuses at user scope because
      the *primitive* is repo-only in v1, even though Rail B is
      vacuously satisfied. A pack opting into Rail B with
      `user-scope-hooks = true` still refuses on this rail if it
      also ships kiro-ide-hooks.

## Changelog

- 2026-05-26: RFC-0012 / `repo-scope-per-adapter-projection`
  amendment — the `install` CLI surface gains a new
  `--emit-install-routes` boolean flag (catalogue-publishing
  opt-in; bound to `--scope repo`; mutually exclusive with
  `--adapter` at that scope). The pre-existing
  `install: --adapter is bound to --scope user` refusal is
  **removed**: `--adapter` is admitted at both scopes now. The
  install handler's six-step (0–5) adapter resolver gains an
  explicit `scope` parameter and scope-branches at steps 0, 1, 4,
  and 5; the repo-scope branch does **not** probe `<repo>/.<ide>/`
  (load-bearing asymmetry per RFC-0012 § *Alternatives* #4). See
  [RFC-0012](../../rfc/0012-repo-scope-per-adapter-projection.md)
  for the full surface.
- 2026-05-24: RFC-0005 v0.4 amendment — added `## v0.4
  kiro-ide-hook primitive (RFC-0005)` subsection between the
  v0.3 user-scope-hook surfaces and Boundaries. Pins the
  `install` projection (askAgent byte-copy vs runCommand
  parse-expand-emit paths), the `uninstall` per-file Tier-1
  semantics with adopter-hand-edit preservation, the
  build-pipeline phase-order reference (single source of truth
  in the sibling distribution-adapters spec), the no-state-shape-
  change claim, and the user-scope refusal that is independent of
  Rail B. Six new AC items tagged `(RFC-0005 v0.4)`. The RFC
  drift in § State-file impact (uninstall described as
  "unconditional / verbatim") is documented as a deferred
  follow-up rather than rolled into this PR.
- 2026-05-23: bookkeeping reconciliation — the 17 pre-amendment
  ACs flipped `[ ]` → `[x]` against on-disk evidence. PR #23
  shipped the v1 CLI surface; PR #26 + the RFC-0004 follow-on
  PRs closed the 10 `(RFC-0004)`-tagged ACs (already `[x]`).
  Known carryovers remain: SSH `git+ssh://` URLs in `install`
  (deferred to v1.1; refusal text shipped); full `--strict`
  conformance against F-conformance fixtures (deferred per
  RFC-0003); user-scope hook-wiring merge story; system-wide
  `global` scope; APM/Claude-plugins parity. These live as
  carve-outs inside the relevant ACs (AC7/AC12) rather than as
  separate open checkboxes.
