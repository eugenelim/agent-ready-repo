# RFC-0004: Install-scope dimension — repo or user — defaulted and constrained per pack

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-23
- **Date closed:** 2026-05-23
- **Extends:** [RFC-0001](0001-bundle-distribution-by-adapter-spec.md)
  — adds a scope dimension to the adapter contract and Tier-1/2/3
  file-safety rails.
- **Amends:** [RFC-0003](0003-spec-and-cli.md) — `agentbundle` CLI
  surface gains `--scope`, `allowed-scopes` refusal, and
  scope-aware path-jail.
- **Touches:** [RFC-0002](0002-self-hosting.md) — the build
  pipeline must produce v0.2 state files.

## Summary

This RFC adds a **scope** dimension (`repo` | `user`) to the adapter
contract. Pack authors declare both a `default-scope` and an
`allowed-scopes` set in `pack.toml`. The four shipped packs
(`core`, `governance-extras`, `user-guide-diataxis`,
`monorepo-extras`) declare **`allowed-scopes = ["repo"]`** — they
cannot be installed at user scope, period; the CLI refuses any
other `--scope` against them. The dimension exists so a future
pack whose content is genuinely cross-project can ship at user
scope cleanly. No such pack ships in this RFC; the value-prop is
the dimension itself. **No user-scope pack lands in this
RFC.** `global` (system-wide) is deliberately absent: no adapter
has a system-wide root.

## Motivation

No shipping pack today *needs* user scope. The four packs we ship
are all repo-shaped (AGENTS.md seeds, CONVENTIONS, RFC/ADR
ceremony, monorepo scaffolding, project documentation). Why land
the dimension at all, then?

**Anticipated consumer shape.** Some pack content is genuinely
cross-project — *style-only* primitives that travel cleanly across
every repo an adopter opens, without per-repo file references,
without `<adapt:NAME>` markers, and without dependence on the
local repo's convention vocabulary. Examples of the shape (not
commitments to specific packs): a style-only review discipline
that finds bugs without naming our docs tree; a personal-knowledge
skill that operates over the adopter's notes; an IDE-personalisation
profile. The current `core` reviewer agents are *not* this shape —
they reference `AGENTS.md` and `docs/CONVENTIONS.md` by name and
would import this project's posture into every repo at user scope.
A future user-scope pack would need to be content-portable from
the start. Whether such a pack ships is a separate decision; this
RFC neither commits to nor blocks one. The near-term value of
this RFC is the dimension itself, not any specific consumer.

**Why land the dimension ahead of any consumer.** Scope mechanics
are non-trivial: path-jail at user scope, state-file location,
`~`-expansion failure modes, projection-rule forks for hook-shaped
primitives, `recommends` across scopes, backward compatibility for
existing state files. Landing those decisions under the pressure
of a concurrent pack release means corners cut. Landing them
deliberately, with no pack riding the same merge train, means the
spec amendments can be argued on their own merits.

**Two failure modes the dimension solves once a real user-scope
pack lands.**

1. **Cross-project primitives become squatters.** An adopter who
   wants a personal reviewer in every repo today copies files into
   `~/.claude/` by hand — outside the Tier model, outside upgrade,
   outside uninstall. Exactly the problem RFC-0001 set out to
   solve at the repo level.
2. **Repo-only is wrong for some upcoming packs.** A personal-
   reviewers pack at repo scope bloats every project's `.claude/`
   and rots when the project is archived. Repo scope is wrong by
   construction for content that isn't *about* the project.

**Why the existing user-level surfaces aren't enough.** Claude Code
already reads from `~/.claude/` (user settings, user skills/agents/
commands); the CLI just can't reach it. APM installs system-wide
by default; mapping our packs onto APM cleanly requires a
user-scope path on our side.

## Proposal

### The scope dimension

A new enum **`scope`** is added to the adapter contract:

| Value  | Meaning                                                | Root path (Claude Code adapter) |
| ------ | ------------------------------------------------------ | ------------------------------- |
| `repo` | Project-local — lives next to the code it governs.     | `<repo>/.claude/`               |
| `user` | User-local — shared across every repo the user opens.  | `~/.claude/`                    |

`global` (system-wide) is deliberately absent — no adapter has a
system-wide root, and adding it later is a one-line schema bump
against an already-versioned contract. See
[Alternatives considered](#alternatives-considered) §6.

### Per-pack default *and* allowance

`pack.toml` gains a `[pack.install]` table:

```toml
[pack]
name = "core"
version = "0.1.0"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
```

Two fields:

- **`default-scope`** — the scope used when the adopter passes no
  `--scope`. One of `"repo"` | `"user"`.
- **`allowed-scopes`** — the scopes this pack permits, as an array.
  An adopter passing `--scope <s>` where `<s>` is not in
  `allowed-scopes` is refused at install time with a stderr message
  naming the pack and its declared set.

**`[pack.install]` is required when the pack declares
`[contract] version = "0.2"`.** A pack's contract version is
declared in its `pack.toml`'s `[pack.adapter-contract] version`
field (per RFC-0001). Acceptance rule:

- **v0.1 packs** (`[pack.adapter-contract] version = "0.1"`) —
  accepted by a v0.2 CLI with implied defaults: `default-scope =
  "repo"`, `allowed-scopes = ["repo"]`. The legacy default exists
  *only* for the legacy contract version. This keeps any
  already-published v0.1 pack installable without re-tagging.
- **v0.2 packs** (`[pack.adapter-contract] version = "0.2"`) —
  `agentbundle validate` refuses any pack omitting `[pack.install]`.
  A silent default is cheaper one PR but worse forever — pack
  authors who never open their `pack.toml` would be implicitly
  opted *out* of user scope without intent.

Within `[pack.install]`, `default-scope` is required and
`allowed-scopes` defaults to `[default-scope]`.

The four shipped packs gain `[pack.install]` and bump their
`[pack.adapter-contract] version` to `"0.2"` in the **same PR**
as the contract amendment, so the catalogue's published packs and
the CLI release land in lockstep. Out-of-tree v0.1 packs continue
to install via the legacy path; a v0.1 pack that carries a stray
`[pack.install]` table (out-of-spec for v0.1) has the table
ignored — implied defaults apply uniformly to all v0.1 packs. A
pack omitting `[pack.adapter-contract] version` is treated as
`"0.1"` for legacy-acceptance.

When `[pack.install]` is present but `allowed-scopes` is omitted,
it defaults to `[default-scope]` — i.e. "only the default." A pack
that wants to permit installation at both scopes declares
`allowed-scopes = ["repo", "user"]` explicitly. The
`default-scope ∈ allowed-scopes` invariant is enforced **in
`pack.schema.json`** as a jsonschema cross-field constraint
(`if/then` block), so the rule holds outside the CLI — catalogue
indexers, third-party validators, and `agentbundle validate` all
refuse a malformed pack identically.

**The four shipped packs all declare `allowed-scopes = ["repo"]`:**

| Pack                   | `default-scope` | `allowed-scopes` | Falsifiable test                                            |
| ---------------------- | --------------- | ---------------- | ----------------------------------------------------------- |
| `core`                 | `repo`          | `["repo"]`       | Ships AGENTS.md seed, CONVENTIONS, hooks, conventions-check, and reviewer agents that textually reference `AGENTS.md` / `docs/CONVENTIONS.md` by name — none of which serves a different repo verbatim. (The reviewer agents would mechanically *load* at user scope but would import this project's vocabulary into every repo the adopter opens; that's a content-portability fail, not a contract refusal.) |
| `governance-extras`    | `repo`          | `["repo"]`       | RFC/ADR templates and ceremony are per-project; an RFC about "what should this codebase do?" can't live at user scope. |
| `user-guide-diataxis`  | `repo`          | `["repo"]`       | Scaffolds `docs/guides/` for *this project's* users; no project = no scaffolding target. |
| `monorepo-extras`      | `repo`          | `["repo"]`       | `new-package` scaffolds in `packages/`; meaningless without a monorepo. |

The "falsifiable test" is: *does the same file content serve every
repo verbatim?* If yes, the pack is a user-scope candidate. If no
— because the content carries `<adapt:NAME>` markers, references
specific paths, names project-specific docs, or bakes in
convention vocabulary — the pack is repo-only. The four packs all
fail the test: `core`'s reviewer agents reference `AGENTS.md` and
`docs/CONVENTIONS.md` by name (a *content* fail, not a marker
fail — see [Motivation](#motivation) for the style-vs-content
split); the other three carry seeds, hooks, or per-project
ceremony.

### Adopter override

```bash
agentbundle install --pack <name> --scope user <catalogue-uri>
```

Precedence: **CLI flag > pack `default-scope` > built-in `repo`**.
A `--scope` value outside the pack's `allowed-scopes` is refused
non-zero with a message naming the pack, the requested scope, and
the declared set.

### Adapter-level scope roots and projection forks

`adapter.toml` gains a `[adapter.<name>.scope]` table:

```toml
[adapter."claude-code".scope]
repo = "."
user = "~"
allowed-prefixes.user = [".claude/"]
```

`allowed-prefixes.<scope>` is **constrained at the schema level**,
not adapter-trusted: each entry must be a non-empty,
forward-slash-relative path that (a) does not equal `"/"`, (b) does
not begin with `/`, (c) contains no `..` segments after
normalization, and (d) ends with `/` to force prefix matching at
directory boundaries. The array must be non-empty for any scope it
declares. The conformance suite refuses adapters declaring
`["/"]`, `[""]`, `["../"]`, `[".."]`, or empty arrays — without
this rail an adapter author could neuter the jail by listing a
root-equivalent prefix.

Projection `target-path` values remain relative to the resolved
scope root *for primitives whose projection is uniform across
scopes*. The "one table, two roots" claim **fails for two of the
five primitives** under Claude Code:

- **`hook-body`** projects to `tools/hooks/` at repo scope but
  Claude Code reads user-scope hook bodies from `~/.claude/`
  (not `~/tools/`). The path is not a simple reroot.
- **`hook-wiring`** projects to `.claude/settings.local.json` at
  repo scope but the user-scope settings file is
  `~/.claude/settings.json` (no `.local`), and the merge semantics
  for hooks under a hand-edited user settings file are not
  designed.

**Until the user-scope hook-wiring merge story is designed
(deferred to a follow-up RFC), hook-shaped primitives are refused
at user scope.**
The contract enforces this by refusing any user-scope install of a
pack whose `[pack.install]` set includes `"user"` *and* whose
projected primitive set includes `hook-body` or `hook-wiring`. The
only currently shipped pack containing hooks is `core`, which
already declares `allowed-scopes = ["repo"]`; nothing breaks
today. A future user-scope pack carrying hooks lands behind a
follow-up RFC that designs the user-scope hook-wiring merge mode
(likely `user-merge-json` or equivalent). `validate` enforces the
constraint at pack-validation time so a malformed
`allowed-scopes`-includes-`user`-with-hooks pack is caught before
install.

### `seeds/` content is repo-only

Every shipped pack carries a `seeds/` tree whose top-level layout
is `seeds/docs/`, `seeds/packages/`, etc. At user scope these
would project to `~/docs/_templates/`, `~/packages/_example/` —
nonsense paths. The contract enforces: **a pack containing a
non-empty `seeds/` directory cannot declare `"user"` in
`allowed-scopes`.** `validate` rejects mismatches.

### Primitives carrying `<adapt:NAME>` markers are repo-only

A primitive file containing one or more `<adapt:NAME>` markers
cannot install at user scope: markers resolve from
`.adapt-discovery.toml` to per-repo values, and a single file at
`~/.claude/` can only carry one resolution. **A pack with
`"user"` in `allowed-scopes` must contain no `<adapt:NAME>`
markers in its projected primitive files.**

*Scope of the rail.* The rail fires **only when the pack declares
`"user" ∈ allowed-scopes`.** Repo-only packs are not inspected —
the rail's whole purpose is to keep markers out of user-scope
content, so a `["repo"]` pack is uninteresting to it. This means
SKILL.md files that *document* the marker syntax (e.g. the
`adapt-to-project` skill itself) are not refused by the rail
because their packs declare `allowed-scopes = ["repo"]`. A
user-scope-eligible pack that wants to document the marker syntax
must use HTML entities (`&lt;adapt:NAME&gt;`) or refer to the
syntax abstractly — a reasonable constraint for content-portable
packs.

*Implementation.* The grep is strict: `<adapt:[A-Z_][A-Z0-9_]*>`
in any byte position of any primitive file under the pack's source
paths (`.apm/skills/`, `.apm/agents/`, `.apm/commands/`). Skill
directories are walked recursively; non-UTF-8 files (binaries) are
skipped. `hook-body`/`hook-wiring` are already user-scope-refused
by the [hook rail](#adapter-level-scope-roots-and-projection-forks),
so a marker check on them is unreachable. `seeds/` is already
user-scope-refused by the [seeds rail](#seeds-content-is-repo-only),
so the marker rail's input never includes `seeds/`. No markdown
parsing required — the grep runs against raw file bytes.

*Enforcement point.* `validate` runs the grep at
pack-validation time; `install` **re-runs the grep against the
resolved pack content** whenever `--scope user` is requested or
the pack's `default-scope` is `"user"`. This closes the
widen-after-publish gap: a pack published as `["repo"]` (not
inspected) cannot install at user scope after flipping its
`allowed-scopes` to include `"user"` without passing the rail at
install time. The seeds and hook rails follow the same pattern —
`install` re-checks every contract-level user-scope refusal
against the resolved pack, regardless of any prior `validate`
state.

*Necessary, not sufficient.* A pack that passes the marker grep
can still ship content-portability bugs the contract does not
catch — e.g. an agent body that hardcodes the path `AGENTS.md`,
or a skill that names this project's convention vocabulary
literally. The [falsifiable test](#per-pack-default-and-allowance)
in the per-pack table is the broader rule (*does the same file
content serve every repo verbatim?*); the marker rail is the
subset the contract can mechanically enforce. Pack authors
targeting user scope must satisfy both — the rail by construction,
the test by judgment.

### Path-jail per scope, constrained to declared prefixes

Two changes to the write-jail rail:

1. **Per-scope root.** At repo scope, the jail is the repo root
   (unchanged). At user scope, the jail is `expanduser("~")`.
2. **Constrained to declared prefixes at user scope.** A `..`-escape
   check alone is insufficient at user scope — a buggy or
   malicious projection rule resolving under `~/Documents/`
   stays "inside the jail." The contract adds an
   `allowed-prefixes.user` array on each adapter's `[scope]` table
   (default for Claude Code: `[".claude/"]`); every user-scope
   write must resolve under one of those prefixes or the CLI
   refuses non-zero. Repo-scope writes are unchanged — the repo
   root *is* the prefix.

### State file per scope

| Scope  | Location                                  |
| ------ | ----------------------------------------- |
| `repo` | `<repo>/.agent-ready-state.toml`          |
| `user` | `~/.agent-ready/state.toml`               |

User-scope state lives inside a namespaced dot-directory
(`~/.agent-ready/`), not as a bare dotfile in `$HOME`. The
dot-directory is the future home for other user-scope artifacts
(`.adapt-discovery.toml`, `.upstream.<ext>` companions, pending
reports). Repo-scope state location is unchanged. Each file
records only the packs installed at *that* scope; CLI subcommands
that enumerate installed packs read both files.

### `~`-expansion semantics

The CLI applies `pathlib.Path.expanduser()` to scope-root strings
**once, at scope-resolution time** (i.e. when an `install`,
`uninstall`, `upgrade`, or `adapt` invocation resolves `--scope
user` to a concrete root). If the result equals the literal `"~"`
(expansion failed) or resolves to `"/"` (corporate sandbox with
`$HOME=/`), the CLI refuses with stderr
`cannot resolve user scope: $HOME unset or invalid`. Windows
support is deferred per the agent-spec-cli spec's stdlib-only
commitment; `pathlib.expanduser` handles `%USERPROFILE%`, but
cross-platform conformance is not gated by this RFC.

### `recommends` across scopes

A pack's `recommends = [...]` is satisfied by an install of the
recommended pack at **any** scope. `install` warns (does not
refuse) when a recommended pack is missing entirely, and lists
the scope(s) the recommended pack is installed at when present:
`note: recommends 'core' (found at repo scope)`. Cross-project
packs can recommend project-shaped packs without forcing
co-located scope.

**Warning text distinguishes two cases.** When the recommended
pack's `allowed-scopes` is disjoint from the recommending pack's
installed scope, the warning text says so:
`note: recommends 'core', which is repo-only; install it in your active project`.
When the recommended pack is simply missing but installable at the
same scope, the warning says
`note: recommends 'core' (not installed)`. The split exists so
adopters can tell "I forgot something" apart from "this
combination has a structural mismatch."

`recommends` is informational; it does not gate install. A
dual-scope install (`--force`) emits one warning per scope.

### Backward compatibility for existing state files

Adopters today carry `<repo>/.agent-ready-state.toml` with
`schema-version = "0.1"` and no scope metadata.

- **Read.** The CLI reads any `schema-version = "0.1"` state file
  as *all entries at repo scope*. No migration is forced at read
  time.
- **Migrate (explicit).** `agentbundle init-state --migrate`
  rewrites a v0.1 state file to v0.2, adding an explicit
  `scope = "repo"` column to each entry and bumping
  `schema-version`. The migration is idempotent and additive.
- **Write against a v0.1 file is refused.** Any write-capable
  invocation (`install`, `uninstall`, `upgrade`) against a v0.1
  state file exits non-zero with stderr
  `state file at <path> is schema-version 0.1; run 'agentbundle init-state --migrate' first`.
  No silent rewrite: migration is destructive (irreversible
  without backup) and an adopter running mixed CLI versions across
  CI and local must opt into the file-format change explicitly. The
  refuse-and-explain shape matches the major-version refusal rail
  already in [`agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md).

The agent-ready-state.toml `schema-version` is a separate version
axis from the adapter contract `[contract] version` — see
[Drawbacks](#drawbacks). Both bump in the spec amendment, but they
gate different things and an adopter must reason about both.

### CLI surface

The eleven enumerated subcommands gain `--scope` as follows:

| Subcommand     | `--scope` behaviour                                                                                |
| -------------- | -------------------------------------------------------------------------------------------------- |
| `install`      | **Override.** Refused if not in pack's `allowed-scopes`. Default: pack's `default-scope`.          |
| `uninstall`    | **Disambiguator.** Required if pack is installed at both scopes; otherwise inferred.               |
| `upgrade`      | **Disambiguator.** Same rule as `uninstall`.                                                       |
| `diff`         | **Disambiguator.** Same rule.                                                                      |
| `init-state`   | **Selector.** Which scope's state file to initialize / migrate.                                    |
| `list-targets` | **Read-only filter.** Restricts output to one scope; omitting shows both with a scope column.      |
| `list-packs`   | No `--scope`. Catalogue query; scope is not yet bound at this point.                               |
| `scaffold`     | Always repo-targeted (generates `seeds/` content into a project tree). No `--scope`; ignores `default-scope`. Refused if `"repo" ∉ allowed-scopes`. |
| `validate`     | No `--scope`. Validates the pack's declared `default-scope ∈ allowed-scopes`, the seeds/hooks/`allowed-scopes` consistency, and the schema. |
| `render`       | No `--scope`. Pack-local primitive rendering; scope only matters at install.                       |
| `adapt`        | No `--scope`. Walks **both** state files; reads `<scope-root>/.adapt-discovery.toml` per scope. Findings are recorded against the scope of the file they were observed in (a squatter under `~/.claude/` is a user-scope finding; a `.upstream.<ext>` companion in `<repo>/` is a repo-scope finding). `adapt --ci` exits non-zero if **either** scope's `.adapt-pending.md` is non-empty. |

On every successful install the CLI prints
`installed: <pack> @ <scope>` so the adopter sees the scope
explicitly.

### What this RFC does NOT do

- **No user-scope pack.** This RFC introduces the dimension only;
  every pack we ship today declares `allowed-scopes = ["repo"]`.
  Any follow-up user-scope pack lands as a separate RFC + PR.
- **No per-item scope.** A pack installs at one scope; every
  primitive in that pack lives at that scope.
- **Cross-scope conflict — install refuses unless `--force`.**
  Installing pack `<P>` at scope `<S>` when `<P>` is already
  installed at the other scope exits non-zero with stderr
  `<P> already installed at <other-scope>; pass --force to install at both`.
  `--force` carries semantics only on `install`; passing it to
  any other verb is rejected (`unknown flag for <verb>`). `install`
  against a pack *already installed at the requested scope* is
  refused with `<P> already installed at <scope>; use 'upgrade' to change version`;
  `--force` does not override that refusal — it addresses only the
  cross-scope conflict case, not in-place re-install. A
  `--force` install against a pack *not* already installed at the
  other scope is accepted as a normal install (no-op effect from
  the flag), so wrapper scripts can pass `--force` idempotently.
  After a dual-scope install:
  - `uninstall --scope <s>` removes only the named scope's entry;
    the other scope is untouched.
  - `upgrade --scope <s>` upgrades only the named scope; per-verb,
    per-scope.
  - `diff --scope <s>` reports against the named scope's state
    file.
  - All three verbs require explicit `--scope` while a pack is
    installed at both scopes; the inferred-disambiguator from the
    CLI surface table applies only when the pack is at exactly one
    scope.
- **No `global` (system-wide) scope.** Not reserved, not refused
  — absent.
- **No user-scope hook support.** See
  [Adapter-level scope roots](#adapter-level-scope-roots-and-projection-forks)
  for the rule; the deferral is canonical there.

## Alternatives considered

1. **Do nothing — keep repo-only.** Adopters who want cross-project
   skills copy files into `~/.claude/` by hand, with no upgrade or
   uninstall path. Blocks any pack whose natural home is the user
   level (any cross-project, content-portable pack the dimension
   would support). The manual copy is a Tier-3 squatter the CLI
   can't see — exactly the problem RFC-0001 set out to solve at
   the repo level.

2. **Per-item scope (override per skill / agent within a pack).**
   Maximally flexible but multiplies state-file bookkeeping by the
   cardinality of primitives in a pack, breaks "install/uninstall
   is atomic per pack," and asks the pack author to make a scoping
   decision they're unlikely to get right for every adopter.
   Rejected: an item that belongs at a different scope should be
   its own pack.

3. **Adopter-only scope (no pack default).** Adopter passes
   `--scope` every time. Forces every adopter to re-derive a
   decision the pack author already knows the answer to. Rejected.

4. **Scope as a separate CLI mode (`install-user` vs `install`).**
   Doubles the subcommand surface and doesn't carry a default per
   pack. Rejected: scope is a parameter, not a verb.

5. **Couple scope to adapter (e.g. APM = user, Claude Code =
   repo).** Hard-code per adapter. Breaks the moment any adapter
   supports both (Claude Code already does). Rejected.

6. **Reserve `global` in the enum, refuse it in v0.x.**
   "Future-friendly." Rejected: no adapter today has a system-wide
   root, so the value would be a refused-but-present footgun.
   Contract is already versioned; adding `global` later is one
   TOML line plus a conformance case. Don't design for hypothetical
   requirements.

7. **Hardcode the four shipped pack names in the CLI as
   repo-only.** Avoids the `allowed-scopes` field. Rejected: pack
   constraints belong with the pack, not in the CLI; third-party
   catalogues need the same declarative shape; the
   reviewer/scaffold/validate rails all need pack-author intent in
   the file, not in CLI source.

8. **Land the dimension *with* the first user-scope pack, not
   ahead of it.** Cheaper in PR count. Rejected: scope mechanics
   are non-trivial (path-jail, state-file location, `~`-expansion,
   projection forks, `recommends` interaction, backward compat)
   and landing them under the pressure of a concurrent pack means
   corners cut. The named consumer (a future reviewer-agents pack)
   becomes a one-day PR once this RFC is in.

## Drawbacks

- **State-file count doubles.** Two state files mean more code
  paths to test (path-jail, tier classification, upgrade,
  uninstall, `init-state` migration, `adapt` discovery walk).
- **Three version axes coexist after this RFC; two of them bump.** The adapter
  contract version (`[contract] version` in `adapter.toml`) bumps
  from `0.1` → `0.2`; the state-file schema (`schema-version` in
  `.agent-ready-state.toml`) bumps from `0.1` → `0.2`; the
  pack-spec version (`version` in `pack.toml`) is per-pack and
  unchanged by this RFC. The two bumps gate different things — the
  contract version drives the major-version-disagreement refusal
  for *packs* (per `agent-spec-cli/spec.md`); the state-file
  schema-version drives the refuse-and-explain at write-time
  documented in [Backward compatibility](#backward-compatibility-for-existing-state-files).
  Adopters must upgrade their CLI to install any v0.2 pack *and*
  explicitly run `init-state --migrate` against existing v0.1 state
  files. Refuse-and-explain on both rails is already in scope for
  the spec amendments.
- **`~`-expansion is a new failure mode.** Wrong `$HOME` in CI or
  a corporate sandbox = wrong install location or refusal.
  Mitigation: the resolved absolute scope root is printed before
  any write, and the CLI refuses if the resolved root equals
  literal `~` or resolves to `/`.
- **Cross-scope upgrades get awkward.** Upgrading `core` at one
  scope doesn't upgrade a same-name pack installed at the other.
  `upgrade --scope all` is tempting but hides bugs; the CLI
  requires an explicit `--scope` when a pack is installed at both.
- **Hook-shaped packs are user-scope-forbidden until a follow-up
  RFC.** A real constraint for the future user-scope pack
  ecosystem; not a constraint on anything shipping today.
- **`[scope]` table on `adapter.toml` is optional but recommended.**
  Adapters omitting it are repo-only. New adapters that want
  user-scope support must declare `[scope]` and
  `allowed-prefixes.user` — one additional table per adapter, not
  a per-projection rewrite.
- **The spec amendment is atomic across two version axes and six
  CLI changes.** Contract version `0.1 → 0.2`, state-file
  `schema-version 0.1 → 0.2`, plus `--scope` on six subcommands,
  `--force` on `install`, `~`-expansion handling,
  `allowed-prefixes` enforcement, dual-state-file walking, and the
  `installed: <pack> @ <scope>` output rail. A partially-landed
  amendment leaves the CLI in an incoherent state — e.g. v0.2
  contract handling shipped but v0.2 state-file handling not, so
  a v0.2 pack installs but the resulting state file is malformed
  for the read path. **Mitigation:** the spec amendment lands as a
  single PR; the four shipped packs' `[pack.install]` declarations
  and `[pack.adapter-contract] version` bumps land in the *same*
  PR as the CLI changes. RFC-0002's self-hosting re-overlays after
  merge. No incremental sub-feature lands ahead of the full
  amendment.
- **`adapt-to-project` discovery doubles its artifact surface.**
  Two `.adapt-discovery.toml` files (one per scope), two
  `.adapt-pending.md` reports, and two `adapt --ci` exit codes to
  reconcile. A squatter at one scope that belongs to a pack at the
  other scope is a *Tier-3-at-the-wrong-scope* finding with no
  pre-existing handler in the Tier model. The CLI's routing rule
  (findings recorded against the scope they were observed in) is
  pinned in [CLI surface](#cli-surface); the LLM skill's interaction
  with that rule is owned by the discovery spec and flagged for the
  follow-on amendment.

## Unresolved questions

- **Claude Code's primitive-resolution order (repo > user).**
  Claude Code itself decides which copy of a same-name primitive
  wins when both scopes carry it; the contract does not. A future
  user-scope pack whose content references a recommended pack's
  primitive may get either copy depending on Claude Code's
  documented behaviour. The contract surfaces the duplication via
  `list-targets`; the runtime resolution is out of contract scope.
- **APM and Claude-plugins adapter parity.** APM defaults to user;
  Claude-plugins caches at `~/.claude/plugins/cache/`. Both
  adapters land *after* this RFC. Will their conventions force a
  schema revision? Tentative answer: contract bumps to `0.3` then
  if needed, with conformance-suite cases added per scope.
- **Should `[pack.install]` carry more fields than `default-scope`
  and `allowed-scopes`?** A `requires-confirmation = true` flag for
  user-scope packs is plausible (a future user-scope pack may want it).
  Out of scope; opens a door but doesn't walk through it.

## Follow-on artifacts

On acceptance — **all artifacts below land in a single PR** (per
[Drawbacks § spec-amendment atomicity](#drawbacks)). A sub-feature
merged ahead of the others leaves the CLI in an incoherent state.



- **ADR:** *Install-scope is a per-pack default + allowance, not a
  per-item or adopter-only choice.* Records the rejection of
  alternatives 2, 3, 7, and 8.
- **Spec amendment:**
  [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md)
  gains:
  - The `[scope]` table in the adapter contract, with
    `allowed-prefixes.user` array.
  - Scope-keyed state-file rule (`~/.agent-ready/state.toml`).
  - Scope-aware path-jail acceptance criterion.
  - `seeds/`-bearing-pack, hook-bearing-pack, and
    `<adapt:NAME>`-marker-bearing-pack refusal at user scope,
    enforced by `validate` (`validate` greps projected primitives
    for markers and reports the first offending file).
  - `agent-ready-state.toml` schema bump to `"0.2"` with explicit
    `scope` column per entry; `init-state --migrate` semantics.
  - `[contract] version` bump from `0.1` to `0.2`; conformance
    suite adds scope cases.
- **Spec amendment:**
  [`docs/specs/agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md)
  gains:
  - `--scope` flag on `install` (override), `uninstall` / `upgrade`
    / `diff` / `init-state` (disambiguator), `list-targets`
    (read-only filter).
  - Scope-resolution precedence rule (CLI flag > pack default >
    built-in `repo`).
  - `allowed-scopes` refusal logic.
  - Path-jail extended with user-scope `allowed-prefixes`
    enforcement.
  - `~`-expansion rule and refusal conditions.
  - Refuse-and-explain on write to a v0.1 state file; stderr
    points at `agentbundle init-state --migrate`. No silent
    rewrite.
  - `installed: <pack> @ <scope>` output rail.
- **Schema:** `pack.schema.json` gains a **required**
  `[pack.install]` table (under `[contract] version = "0.2"`) with
  `default-scope ∈ {"repo","user"}` and
  `allowed-scopes ⊆ {"repo","user"}`. The cross-field invariant
  `default-scope ∈ allowed-scopes` is enforced in the schema via
  a jsonschema `if`/`then` block so the rule holds outside the
  CLI. `adapter.schema.json` gains the `[scope]` table with
  `allowed-prefixes.<scope>` array constraints (non-empty,
  forward-slash-relative, no `..`, no `/`, trailing `/`).
- **Pack metadata:** the four shipped packs grow explicit
  `[pack.install] default-scope = "repo"` and
  `allowed-scopes = ["repo"]` (even though both are the built-in
  defaults) so adopters reading the TOML see the constraint
  declared, not implied.
- **CONVENTIONS:** one paragraph under the pack-catalogue section
  pointing at scope as the dimension publishers choose and
  adopters can override within the publisher's declared set.
- **Migration note for third-party pack authors:** a one-page
  how-to under `docs/guides/how-to/` covering the v0.1 → v0.2 pack
  upgrade — which fields to add, the `validate` exit codes,
  examples for the implied-defaults case, and the marker rail's
  rule when `"user" ∈ allowed-scopes`.
