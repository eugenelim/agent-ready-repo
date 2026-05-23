# Spec: adapt-to-project

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)
  (§ *Post-install adaptation*, § *Adopter file safety contract*,
  `[pack.adaptation]` markers); [RFC-0003](../../rfc/0003-spec-and-cli.md)
  (CLI counterpart `agentbundle adapt`);
  [RFC-0004](../../rfc/0004-install-scope-per-pack.md) (install-scope
  dimension — this spec is the follow-on flagged in RFC-0004's
  *Drawbacks* § *`adapt-to-project` discovery doubles its artifact
  surface*);
  [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  (schema authority for `pack.toml` — `[pack.dependencies]`,
  `[pack.install]`, the `<adapt:NAME>` marker-refusal grep);
  [`docs/specs/agent-spec-cli/spec.md`](../agent-spec-cli/spec.md) (the
  *Never write `.adapt-discovery.toml` from the CLI* + *Never invoke
  an LLM* rails + the dual-scope `adapt` AC at lines 609-621);
  [`docs/specs/self-hosting/spec.md`](../self-hosting/spec.md) (AC12).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Scope split with `agentbundle adapt`.** The CLI is the deterministic
> regex-substitution engine for `<adapt:NAME>` markers; this skill is the
> LLM-judgment layer that produces the values, negotiates `.upstream.<ext>`
> companion merges, proposes restructuring of non-canonical content, and
> proposes within-layout consolidations. The skill **shells out to
> `agentbundle adapt --values-from <repo>/.adapt-discovery.toml`** to
> perform the class-1 (substitution) file writes; for classes 2–4 the
> skill writes files directly. The CLI's `adapt` always walks both
> scopes (`<repo>/.adapt-discovery.toml` + `~/.agent-ready/.adapt-discovery.toml`)
> per the agent-spec-cli AC at lines 609-621; this spec inherits that
> walk and adds the LLM-judgment layer on top.

> **Scope-awareness rail (RFC-0004).** This spec ships against
> `[contract] version = "0.2"`. Markers are repo-scope only (RFC-0004
> § *Primitives carrying `<adapt:NAME>` markers are repo-only*), so
> the `[markers]` table appears only in `<repo>/.adapt-discovery.toml`;
> the user-scope file at `~/.agent-ready/.adapt-discovery.toml` carries
> only `[[findings.*]]` arrays. The skill itself (a `core`-pack primitive,
> `allowed-scopes = ["repo"]`) is invoked only inside a repo; it walks
> *both* scopes' state files and `.adapt-discovery.toml` files so user-
> scope `.upstream.<ext>` companions (squatters under `~/.claude/`) and
> user-scope findings get reconciled in the same session that handles
> repo-scope work.

## Objective

Land the LLM-driven counterpart to `agentbundle adapt` as a Claude Code
skill at `packs/core/.apm/skills/adapt-to-project/SKILL.md`, replacing
the stub that ships today. The skill is invoked from inside the
adopter's brownfield repository after they have installed the `core`
pack (and zero or more addon packs that declare core as required) at
repo scope, and walks the adopter through the four classes of change
RFC-0001 § *Post-install adaptation* enumerates — **substitution**,
**augmentation-via-`.upstream.<ext>`-companions**, **discovery +
restructuring** of non-canonical content, and **within-layout
consolidation**. Every change is step-gated and explicitly approved
per change.

Under RFC-0004's scope dimension, the skill writes up to **four**
persistent artifacts:

| Artifact | Repo-scope path | User-scope path |
| --- | --- | --- |
| Canonical handoff TOML | `<repo>/.adapt-discovery.toml` (`[markers]` + `[[findings.*]]`) | `~/.agent-ready/.adapt-discovery.toml` (`[[findings.*]]` only — markers are repo-only) |
| Deferred-work memo | `<repo>/.adapt-pending.md` (deterministically sorted, no timestamps) | `~/.agent-ready/.adapt-pending.md` (same shape) |

The skill also consumes (deletes on read) up to two install-marker
files: `<repo>/.adapt-install-marker.toml` and
`~/.agent-ready/.adapt-install-marker.toml`. For class 1 the skill
produces values into `[markers]` in the **repo-scope** discovery
file (markers do not exist at user scope) and shells out to
`agentbundle adapt --values-from <repo>/.adapt-discovery.toml`; the
CLI's already-pinned dual-scope `adapt` walk handles companion
detection and pending-report writes across both scopes. For classes
2–4 the skill writes files directly under a per-scope path-jail
(repo root for repo scope; `~/` constrained to the adapter's declared
`allowed-prefixes.user` for user scope) with Tier-1/2/3 safety
honoured against both scopes' `.agent-ready-state.toml` files.

The skill is idempotent: a re-run on a fully-adapted repo with
neither marker file on disk produces zero filesystem diff and no new
proposals; previously declined `[[findings.declined]]` are never
re-proposed; previously skipped markers are re-offered.

This spec also addresses two structural gaps RFC-0001 left implicit:

1. **The catalogue is `core + N optional addons`, and the schema
   already says so.** `docs/contracts/pack.schema.json:12-25` declares
   `[pack.dependencies.required]` as an array of `{catalogue, pack,
   version}` objects today, but no consumer enforces it; the three
   addons each ship the *non-conforming* `recommends = ["core"]`
   instead. This spec **lights up enforcement** of the existing
   `[pack.dependencies.required]` schema field at install time and
   migrates the three addons to the conforming shape. No new
   `pack.toml` field is introduced.
2. **Install→adapt handoff.** `agentbundle install --pack <name>
   [--scope ...]` writes `.adapt-install-marker.toml` at the scope's
   root (`<repo>/` or `~/.agent-ready/`) listing the just-installed
   pack and its unresolved markers / dropped companions, then chains
   automatically into `agentbundle adapt` (in-process Python call)
   which walks both scopes. The marker file remains on disk until
   the skill consumes it. On next Claude Code session start in the
   adopter's repo, the core pack's session-start hook reads **both
   scopes' marker files** and surfaces "you have pending adaptations
   from pack(s) X; run `/adapt-to-project`." The CLI never invokes
   the skill; the hook only nudges. The install→adapt *chain* is an
   in-process Python call between two CLI subcommands and respects
   the *Never invoke an LLM* rail.

Success for the adopter is that "I installed core +
monorepo-extras into my existing repo with its own AGENTS.md, its
own docs layout, and a project name our pack templates haven't heard
of" results in class-1 substitutions applied automatically across
both packs at install time, a single visible nudge in their next
session, and a customised merge-aware adopter-edits-preserved tree
after one conversational pass.

### Canonical `.adapt-discovery.toml` schemas (v0.1)

Repo-scope file at `<repo>/.adapt-discovery.toml`:

```toml
# Written by the adapt-to-project skill only. Read by `agentbundle
# adapt --values-from` (markers only — class-1 substitution) and by
# `make build-self`'s marker-resolution path (markers only).

discovery-schema-version = "0.1"

# Marker substitutions. Flat marker → value table. REPO-SCOPE ONLY
# per RFC-0004 § *Primitives carrying <adapt:NAME> markers are
# repo-only*. Keys MUST match the `<adapt:NAME>` regex defined in
# AC14 (lowercase-hyphen); values MUST be strings.
[markers]
project-name = "agent-ready-repo"
owner        = "eugenelim"
repo-url     = "https://github.com/eugenelim/agent-ready-repo"

# Structural findings observed at this scope (companions in <repo>/,
# discovery candidates under the repo tree, consolidation proposals
# against repo-installed packs). The three `kind` values map to
# RFC-0001 § *Post-install adaptation* classes 2, 3, and 4:
# `companion-merge` ↔ class 2, `restructure` ↔ class 3,
# `consolidate` ↔ class 4.
#
# `finding-id` MUST be deterministic across re-runs.
#   Visible form  : `<pack>/<kind>:<8-hex>`  — `/` separates pack
#                   from kind for readability (pack names never
#                   contain `/`).
#   Hashed input  : `<pack>:<kind>:<sorted-source-paths>:<sorted-dest-paths>`
#                   — `:` separates fields because path values may
#                   contain `/`. SHA-1; first 8 hex chars feed the
#                   visible form.
[[findings.accepted]]
finding-id       = "core/restructure:7a3f2c91"
kind             = "restructure"
source-path      = "DESIGN.md"
destination-path = "docs/CHARTER.md"
action           = "move-and-merge"
accepted-at      = 2026-05-22T10:00:00Z

[[findings.declined]]
finding-id       = "user-guide-diataxis/restructure:b819e2d4"
kind             = "restructure"
source-path      = "docs/howto/"
destination-path = "docs/guides/how-to/"
declined-at      = 2026-05-22T10:01:00Z
```

User-scope file at `~/.agent-ready/.adapt-discovery.toml`:

```toml
# Written by the adapt-to-project skill only. Read by `agentbundle
# adapt` during its dual-scope walk. NO `[markers]` table — markers
# are refused at user scope by the distribution-adapters refusal
# rail (RFC-0004 § *Primitives carrying <adapt:NAME> markers are
# repo-only*).

discovery-schema-version = "0.1"

# Findings observed at user scope: squatters under ~/.claude/,
# `.upstream.<ext>` companions in ~/.agent-ready/, consolidation
# proposals against user-installed packs. Schema identical to the
# repo-scope file's findings arrays.
[[findings.accepted]]
finding-id       = "future-user-pack/companion-merge:c4d12f8a"
kind             = "companion-merge"
source-path      = "~/.claude/agents/old-bot.md"
destination-path = "~/.claude/agents/bot.md"
action           = "merge-companion"
accepted-at      = 2026-05-23T15:00:00Z
```

Both consumers (CLI, self-host) refuse `discovery-schema-version`
values they don't recognise with one-line prefixed stderr referencing
this spec. The prior `[accepted]` (CLI) and `[adapt]` (self-host)
table names are no longer recognised; consumers encountering them
refuse with one-line errors naming the migration path. A repo-scope
file that lacks `[markers]` is **valid** (no markers needed — e.g.,
a fresh repo with no addons yet); a repo-scope file with `[markers]`
that contains keys violating the lowercase-hyphen grammar is
refused.

### `.adapt-install-marker.toml` schema (v0.1)

```toml
# Written by `agentbundle install` at the install's scope root after
# every successful install. Consumed (deleted on read) by the
# adapt-to-project skill at session start. Surfaced as a one-line
# nudge by the core pack's session-start hook between writes and
# consumption. Repo-scope marker is added to the default .gitignore
# template; user-scope marker is inside ~/.agent-ready/ (not
# project-tracked).
#
# Scope is encoded in the file's location (`<repo>/` vs
# `~/.agent-ready/`), not as a field — the path is the source of
# truth; a self-describing field would just verify itself.

marker-schema-version = "0.1"

[[packs-installed]]
name               = "monorepo-extras"
version            = "0.1.0"
installed-at       = 2026-05-23T14:00:00Z
unresolved-markers = ["package-manager"]  # repo-scope file only — always [] in user-scope marker
new-companions     = ["packages/_example/AGENTS.upstream.md"]
```

The CLI appends a `[[packs-installed]]` entry on each install via
`os.replace`-based atomic-rename read-modify-write. Two near-
simultaneous installs at the same scope produce two entries. The
skill reads each scope's marker file independently, processes its
entries, and deletes the file.

### Pack dependency surface (existing schema, newly enforced)

The schema for `[pack.dependencies.required]` is already declared at
`docs/contracts/pack.schema.json:12-25` — an array of objects with
fields `{catalogue: string, pack: string, version: string}`. This
spec **enforces it at install time** without introducing a new
field. Addon packs migrate from today's non-conforming
`recommends = ["core"]` flat-string-array to the conforming
object-array shape:

```toml
# packs/<addon>/pack.toml (post-migration)

[pack]
name        = "governance-extras"
version     = "0.1.0"
description = "..."

[[pack.dependencies.required]]
catalogue = "agent-ready-repo"
pack      = "core"
version   = "^0.1"

# Per RFC-0004 § Follow-on artifacts → Pack metadata: explicit
# declaration even though both are built-in defaults, so adopters
# reading the manifest see the constraint declared, not implied.
[pack.install]
default-scope  = "repo"
allowed-scopes = ["repo"]
```

`agentbundle install --pack <name>` resolves declared `required`
entries against the **union** of both scopes' state files and
refuses with `install: pack '<addon>' requires '<dep>' (version
<range>); install <dep> first` when any required pack is absent or
out-of-range at every scope it could be present at. Packs that
genuinely stand alone simply omit the `[pack.dependencies]` table.

## Boundaries

### Always do

- Walk the adopter through changes **one at a time**, with per-change
  explicit approval — *accept*, *edit*, or *skip*. RFC-0001 §
  *Post-install adaptation* step 3 is load-bearing.
- For **class 1 (substitution)**: produce values into `[markers]` in
  `<repo>/.adapt-discovery.toml` only (markers are repo-only per
  RFC-0004); then shell out to `agentbundle adapt --values-from
  <repo>/.adapt-discovery.toml`. The CLI's dual-scope walk per the
  agent-spec-cli AC handles companion detection and pending-report
  writes across both scopes.
- For **class 2 (`.upstream.<ext>` companion merges)**: read both
  the adopter's file and the `.upstream.<ext>` companion; propose a
  merged result inline; accept / edit / skip per file. On accept,
  write the merged result to the original path (in the same scope
  as the companion was found — repo or user) and delete the
  companion. On skip, record under `[[findings.declined]]` in
  *that scope's* discovery file with `kind = "companion-merge"`.
- For **class 3 (discovery + restructuring)** and **class 4
  (within-layout consolidation)**: as RFC-0001 enumerates. Per-
  change approval; recordings land in the scope of the file the
  finding was observed in (e.g., a `DESIGN.md` at repo root is a
  repo-scope finding; a misplaced primitive under `~/.claude/` is a
  user-scope finding).
- Honour the **Tier-1 / Tier-2 / Tier-3 file-safety contract** per
  scope. Read **both** state files at session start —
  `<repo>/.agent-ready-state.toml` (repo scope) and
  `~/.agent-ready/state.toml` (user scope); per RFC-0004's *State
  file per scope* rail under `agent-ready-state.toml schema-version
  = "0.2"`. Compute current SHA-256 hashes against each scope's
  installed files; treat divergence as Tier-2 and surface
  explicitly before any write at that scope. Tier-3 paths are
  off-limits except when an explicit, adopter-approved class-3
  finding names them.
- **Per-scope path-jail.** Confine every write to its scope's
  jail-root: repo-scope writes under the repo root (existing rule);
  user-scope writes under `~/` *and* under one of the adapter's
  declared `allowed-prefixes.user` entries (RFC-0004 § *Path-jail
  per scope, constrained to declared prefixes*). The Claude Code
  adapter's `allowed-prefixes.user` includes `[".claude/",
  ".agent-ready/"]` per the distribution-adapters spec; the skill
  refuses any class-3 destination resolving outside these prefixes
  at user scope.
- **Dirty-state escalation, per-scope mechanic.**
  - **Repo scope:** at session start, run `git status --porcelain`;
    list every dirty path; **stop and wait** for the adopter to
    direct one of: **(a)** proceed against the dirty tree (skill
    skips dirty-path proposals); **(b)** stash or commit and
    re-invoke; **(c)** abandon.
  - **User scope:** `~/.agent-ready/` is not a git repo; dirty-
    detection uses content-hash divergence — compare each tracked
    file's current SHA-256 against the value recorded in
    `~/.agent-ready/state.toml`. Any divergence is named in the
    same escalation message; the same (a)/(b)/(c) options apply
    (where (b) becomes "manually back up the file and re-invoke").
  - When the skill's own write targets (`.adapt-discovery.toml` or
    `.adapt-pending.md` at either scope) are dirty, name them
    explicitly; refuse to overwrite without explicit "proceed".
- **`.adapt-pending.md` is regenerated from scratch each session
  per scope, and is deterministic** — three fixed sections in
  documented order (*Unresolved markers*, *Pending companion
  merges*, *Deferred findings*), entries sorted lexicographically,
  no timestamps. Two consecutive runs against the same pending
  state produce byte-identical content at each scope.
- Read the per-pack `[pack.adaptation]` table from every installed
  pack at every scope it is installed at (both state files);
  propose values for markers a pack has declared (markers are
  repo-only by rail, so only repo-scope installed packs contribute
  marker entries).
- Consume `.adapt-install-marker.toml` at each scope if present
  (read entries, prepend to session-internal proposal queue, delete
  the file). Each scope's marker is independently consumed.
- Re-runs MUST surface only what remains unresolved at either
  scope: markers absent from repo-scope `[markers]`, companions
  still on disk at either scope, findings not yet in either
  `[[findings.accepted]]` or `[[findings.declined]]` at the scope
  they were observed in.

### Ask first

- Touching any file that lives under `packs/<pack>/` itself.
- Proposing a `kind = "restructure"` that crosses pack boundaries.
- **Proposing a `kind = "restructure"` that crosses scope
  boundaries** (e.g., moving a path under `<repo>/` into
  `~/.claude/`). Cross-scope restructures break the
  upgrade/uninstall contract of both scopes.
- Adding any persistent on-disk artifact beyond the four named in
  this spec.

### Never do

- **Never write outside the adopter's per-scope jail.** Repo scope:
  under the repo root. User scope: under `~/` *and* one of the
  adapter's `allowed-prefixes.user` entries.
- **Never write `[markers]` to the user-scope `.adapt-discovery.toml`.**
  Markers are repo-only per RFC-0004.
- **Never write `.adapt-discovery.toml` in any shape other than the
  canonical schema above** at either scope. The SKILL.md body
  instructs the LLM to re-read what it just wrote with
  `python3 -c "import tomllib; tomllib.loads(open('<path>').read())"`
  after every write — read-time refusal at the consumers is the
  gate, but the doctrinal self-check fails fast.
- **Never re-propose a finding recorded under `[[findings.declined]]`
  at the scope it was observed in.** Dedupe key is `(source-path,
  destination-path, kind)`.
- **Never batch-apply changes without per-change approval.**
- **Never paper over inference failures with plausible defaults.**
- **Never touch a Tier-3 path** outside an adopter-approved class-3
  finding (per-scope).
- **Never add a new top-level directory or a new package.**
- **Never add a new third-party Python dependency.**
- **Never shell out to anything other than `agentbundle adapt`**
  for class-1 substitution.
- **Never invoke the skill from the CLI.** The install→adapt nudge
  is a hook reading a marker; the install→adapt chain is an
  in-process Python call between two CLI subcommands.
- **Never bypass dirty-state escalation under any "force" flag.**
- **Never widen the scope of a finding** beyond where it was
  observed (a repo-scope companion never produces a user-scope
  finding entry).

## Testing Strategy

Per the work-loop's three-mode taxonomy:

- **Schema and plumbing invariants — TDD.** Typed `AdaptDiscovery`
  parse (with typed `Finding` entries), consumer-refusal of legacy
  shapes with prefixed stderr, `discovery-schema-version`
  negotiation, per-scope path-jail (CLI side; user-scope
  `allowed-prefixes` enforcement), `[[findings.declined]]` re-
  proposal suppression, `.adapt-pending.md` deterministic-sort
  contract at each scope, idempotency at byte level, marker-regex
  unification, `--values-from` acceptance of canonical `[markers]`
  shape, install-gate enforcing `[pack.dependencies.required]`,
  install→adapt marker-write-and-consume cycle (per-scope),
  dual-state-file Tier-2 detection. Tests at
  `packages/agentbundle/tests/`.
- **Class-1 substitution end-to-end — goal-based check.**
  Brownfield fixture → skill produces `[markers]` (simulated) →
  `agentbundle adapt --values-from <repo>/.adapt-discovery.toml` →
  byte-identical expected output. Single-scope test (markers are
  repo-only).
- **Schema migration — TDD, cross-consumer parametrised.** Both
  consumers refuse legacy and accept canonical with prefixed
  stderr.
- **Cross-spec amendment to distribution-adapters/spec.md —
  goal-based.** The marker-refusal grep declared at RFC-0004 line
  272 (currently `<adapt:[A-Z_][A-Z0-9_]*>`) widens to also match
  the canonical lowercase-hyphen form (`<adapt:[a-z][a-z0-9-]*>`),
  via a regex union, so a user-scope pack carrying lowercase-hyphen
  markers does not bypass the rail.
- **Classes 2–4 LLM-judgment file writes — manual QA matrix.**
  T14 enumerates one row per (class × transition) at each
  exercisable scope, plus cross-cutting rows for dirty-state
  (separately for repo and user) and idempotency. Each row records
  a transcript excerpt + before/after tree fragment under
  `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`.

## Acceptance Criteria

- [ ] **AC1 (skill body — behavior-pinning grep set).**
      `packs/core/.apm/skills/adapt-to-project/SKILL.md` is authored
      (replacing the stub). Five grep checks pin the load-bearing
      *behavior*:
      1. body contains the literal
         `agentbundle adapt --values-from <repo>/.adapt-discovery.toml`
         (class-1 shell-out, repo-scope path explicit);
      2. body contains the literal
         `python3 -c "import tomllib; tomllib.loads(open('<path>').read())"`
         (doctrinal self-check);
      3. body contains the literal phrase
         `never write outside the adopter's per-scope jail`
         (per-scope path-jail rule);
      4. body contains the literal phrase
         `git status --porcelain` (repo-scope dirty-state escalation);
      5. body's *Pre-flight* section contains all three tokens
         `~/.agent-ready/`, `state.toml`, and `Tier-2` (multi-token
         behavioural check — pins that the skill reads the user-
         scope state file for Tier-2 detection, without locking the
         prose to a specific verbatim path).
      Prose copy outside these greps is editorial.
- [ ] **AC2 (canonical schemas, per scope).** The skill writes
      `.adapt-discovery.toml` in the v0.1 shape declared in this
      spec, with the per-scope variants enforced: the repo-scope
      file MAY include `[markers]`; the user-scope file MUST NOT
      include `[markers]`. A round-trip test exercises every field
      on each finding kind. `finding-id` derivation is deterministic:
      the **visible form** is `<pack>/<kind>:<8-hex>` (using `/`
      between pack and kind for readability) and the **hashed input**
      that produces the 8-hex tail is
      `<pack>:<kind>:<sorted-source-paths>:<sorted-dest-paths>`
      (using `:` because path fields may contain `/`).
      `test_finding_id_input_includes_pack_and_kind` asserts pack
      and kind both contribute to the hashed input. A user-scope
      file with `[markers]` causes the loader to raise
      `ConfigError("user-scope .adapt-discovery.toml may not contain a [markers] table; markers are repo-only per RFC-0004")`.
- [ ] **AC3 (class 1 — shell-out to CLI, repo scope).** After the
      substitution-decision phase, the skill invokes
      `agentbundle adapt --values-from <repo>/.adapt-discovery.toml`
      (single shell-out; the repo-scope file is the only file with
      markers). The CLI's dual-scope walk (per `agent-spec-cli/spec.md`
      lines 609-621) handles companion detection and pending-report
      writes at both scopes during the same invocation; the skill
      relies on this behaviour without re-invoking the CLI for the
      user scope.
- [ ] **AC4a (manual QA matrix — exercisable rows).**
      `docs/specs/adapt-to-project/notes/manual-qa-matrix.md` exists
      and the following rows are run end-to-end against real
      fixtures, each capturing a transcript excerpt + before/after
      tree fragment:
      - Repo-scope class-2 × {accept, edit, skip, decline}
      - Repo-scope class-3 × {accept, edit, decline}
      - Repo-scope class-4 × {accept, decline}
      - Cross-cutting: *dirty-state-repo*, *idempotency re-run*,
        *Tier-2 detection-repo*, *cross-scope-restructure × decline*
        (the only outcome AC23 permits — see AC23).
      - User-scope rows that exercise *plumbing only* against the
        synthetic fixture under
        `tests/fixtures/brownfield-adapt-user-home/`:
        *dirty-state-user*, *Tier-2 detection-user*,
        *user-scope path-jail refusal* (one row each).
      Each AC4a row is a hard gate on shipping; "verified by code
      review only" is not an acceptable status for any AC4a row.
- [ ] **AC4b (manual QA matrix — deferred rows).**
      User-scope class-2/3/4 LLM-judgment rows are deferred until a
      user-scope-eligible pack ships (RFC-0004 § *Drawbacks* +
      *Unresolved questions* — APM/Claude-plugins adapter parity
      lands later). The deferred rows are enumerated by name in
      `docs/ROADMAP.md` under this spec's section with the trigger
      "first pack declaring `allowed-scopes = ['user']` lands"; no
      row is silently dropped. AC4b ships as the ROADMAP enumeration
      plus a placeholder section in `manual-qa-matrix.md` naming
      each deferred row and citing the trigger; no fixture, no
      transcript required.
- [ ] **AC5 (idempotency at byte level).** A second skill session
      against a fixture where (a) every pack-declared marker is in
      the repo-scope `[markers]`, (b) every `.upstream.<ext>`
      companion at every scope has been resolved, (c) every
      proposed finding is recorded in either `[[findings.accepted]]`
      or `[[findings.declined]]` at the scope it was observed,
      **and (d) both scopes' `.adapt-install-marker.toml` files are
      absent** produces `git status --porcelain` with zero lines
      against the repo and zero content-hash divergence under
      `~/.agent-ready/`. `.adapt-pending.md` at each scope is
      byte-identical to the prior run's.
- [ ] **AC6 (dirty-state escalation, per scope).** Two fixtures:
      one with pre-staged uncommitted edits to a repo-scope Tier-1
      file, one with content-hash divergence under `~/.agent-ready/`
      against the recorded SHA. In both cases, the skill detects
      the dirty/divergent state at session start, names each
      dirty/divergent path in its first message under separate
      `Repo scope:` / `User scope:` sub-sections, and waits for
      adopter input directing one of (a)/(b)/(c) before any
      class-2/3/4 proposal at the affected scope.
- [ ] **AC7 (path-jail, per scope).**
      **AC7a (CLI repo-scope):** existing `safety.write_jailed`
      tests cover class-1 substitution; a red-team fixture where a
      repo-scope `[markers]` value resolves to `../..` is rejected.
      **AC7b (CLI user-scope):** the CLI's user-scope write path
      (per the existing `agent-spec-cli/spec.md` AC at lines
      550-558) honours `allowed-prefixes.user`; a red-team fixture
      attempting to write under `~/Documents/` is rejected with the
      `agent-spec-cli`-mandated stderr.
      **AC7c (skill side):** SKILL.md body names the per-scope jail
      rule (AC1 grep #3); a matrix row in AC4 demonstrates the
      skill refusing a class-3 destination that escapes either
      jail.
- [ ] **AC8 (CLI schema migration).**
      `packages/agentbundle/agentbundle/commands/adapt.py` reads
      `discovery.markers` via the new `AdaptDiscovery` dataclass.
      Legacy `[accepted]` causes exit non-zero with first stderr
      line exactly
      `adapt: legacy [accepted] table; migrate to [markers] per docs/specs/adapt-to-project/spec.md`.
      A fixture using `[markers]` substitutes correctly. The
      `ConfigError` at the loader carries the unprefixed message;
      both surfaces are tested.
- [ ] **AC9 (self-host schema migration).**
      `packages/agentbundle/agentbundle/build/self_host.py` reads
      `discovery.markers` via the same loader. Legacy `[adapt]`
      causes exit non-zero with first stderr line exactly
      `self-host: legacy [adapt] table; migrate to [markers] per docs/specs/adapt-to-project/spec.md`.
      The repo's own root `.adapt-discovery.toml` migrates from
      `[adapt]` to `discovery-schema-version` + `[markers]` in the
      same PR; `make build-self` and `make build-check` run clean
      against the migrated file.
- [ ] **AC10 (`.adapt-pending.md` deterministic contract, per
      scope).** After a session that leaves work deferred,
      `.adapt-pending.md` exists at each scope where deferred work
      lives (repo, user, or both), contains the three fixed sections
      in documented order, entries sorted lexicographically within
      each section, no timestamps, no carry-over from prior sessions.
      Two consecutive runs against the same pending state produce
      byte-identical content at each scope.
- [ ] **AC11 (stub removal + projection).** The pre-existing stubs
      at `.claude/skills/adapt-to-project/SKILL.md` and
      `packs/core/.apm/skills/adapt-to-project/SKILL.md` are both
      replaced; the in-tree projected copy regenerates
      byte-identically from the pack-side under `make build-self`;
      `make build-check` is green on the migration PR.
- [ ] **AC12 (sibling spec amendments — wording-touchup and
      Changelog only).** No acceptance criterion body that is
      marked `[x]` is rewritten in place; the amendments below are
      either to an unchecked AC or via Changelog:
      - `docs/specs/agent-spec-cli/spec.md` lines 473-479 (an
        unchecked AC). The literal phrase
        `and reads\n      \`.adapt-discovery.toml\` accepted/declined entries without writing to\n      it.`
        (note the leading `and `, line-wrapped before `reads`) is
        replaced in-place with
        `and reads the \`[markers]\` table in \`.adapt-discovery.toml\`\n      per docs/specs/adapt-to-project/spec.md, without writing\n      to it.`.
        T15 grep asserts `accepted/declined entries` no longer
        appears anywhere in `agent-spec-cli/spec.md`.
      - `docs/specs/self-hosting/spec.md` Changelog gains
        `- 2026-05-23: AC12 implementation migrates from reading [adapt] to reading [markers] per docs/specs/adapt-to-project/spec.md; AC12 contract unchanged.`
        AC12 body itself is byte-unchanged.
- [ ] **AC13 (cross-spec index update).** `docs/ROADMAP.md`'s
      *Cross-spec / outside-the-spec-tree* bullet for
      `adapt-to-project` is rewritten to cite this spec as the
      active home while preserving its cross-references to
      `self-hosting`, `agent-spec-cli`, and (newly) `RFC-0004`.
      `docs/specs/README.md`'s *Active specs* table gains a row for
      this spec.
- [ ] **AC14 (marker regex unification).** The CLI's `_MARKER_RE`
      (currently `<adapt:([A-Z_][A-Z0-9_]*)>` at
      `packages/agentbundle/agentbundle/commands/adapt.py:41`)
      widens to `<adapt:([a-z][a-z0-9-]*)>`. The self-host regex
      (currently `<adapt:([A-Za-z0-9_-]+)>` at
      `packages/agentbundle/agentbundle/build/self_host.py:52`)
      narrows to `<adapt:([a-z][a-z0-9-]*)>` for symmetry. Existing
      CLI fixtures (`OWNER` → `owner`) migrate. Both consumers
      leave UPPER_SNAKE markers unchanged with a single stderr
      warning. **The cross-spec dependency on
      `distribution-adapters/spec.md`'s marker-refusal grep (RFC-0004
      line 272) is resolved by AC21.**
- [ ] **AC15 (`--values-from` accepts `[markers]`; refuses
      ambiguous files).** `load_values_from` accepts (in order
      tried) a `[markers]` table or a `[values]` table; presence
      of both raises `ConfigError("ambiguous --values-from file:
      both [markers] and [values] tables present; use one")`. The
      flat-top-level fallback skips `discovery-schema-version`,
      `findings`, and `marker-schema-version` so canonical
      `.adapt-discovery.toml` files pass through cleanly. A user-
      scope `.adapt-discovery.toml` (no `[markers]`, no `[values]`)
      yields an empty value set; no substitution occurs.
- [ ] **AC16 (unknown schema-version refused).** Fixtures with
      `discovery-schema-version = "9.9"` cause both consumers to
      exit non-zero with first stderr line beginning `adapt: ` /
      `self-host: ` and naming `0.1` as the known version.
- [ ] **AC17 (install gate enforces existing schema's
      `[pack.dependencies.required]`, across scopes).** The CLI's
      `install` flow reads the installing pack's
      `[pack.dependencies.required]` array and resolves it against
      the **union** of both state files (`<repo>/.agent-ready-state.toml`
      + `~/.agent-ready/state.toml`). Refusal first-stderr-line:
      `install: pack '<name>' requires '<dep>' (version <range>); install <dep> first`.
      Required pack found at *either* scope satisfies the gate.
      SemVer-range grammar: exactly `^\^([0-9]+)\.([0-9]+)$`;
      unknown shapes raise
      `install: unsupported version range '<range>' for required pack '<dep>'; only ^X.Y is supported`.
      No new `pack.toml` field is introduced; the schema already
      declares the field.
- [ ] **AC18 (addons migrate to conforming dependencies shape +
      explicit scope declarations + contract-version bump).** Each
      addon's `pack.toml` (`packs/governance-extras/`,
      `packs/user-guide-diataxis/`, `packs/monorepo-extras/`):
      (a) removes the non-conforming `recommends = ["core"]` line;
      (b) adds `[[pack.dependencies.required]]` with `catalogue =
      "agent-ready-repo"`, `pack = "core"`, `version = "^0.1"`;
      (c) adds `[pack.install]` with `default-scope = "repo"` and
      `allowed-scopes = ["repo"]` per RFC-0004 § Follow-on
      artifacts → Pack metadata;
      (d) **adds `[pack.adapter-contract] version = "0.2"`** —
      required because `[pack.install]` is a v0.2-only field per
      `distribution-adapters/spec.md` (declarations at v0.1 are
      ignored). Per RFC-0004 line 557-559's atomicity rail this
      bump lands in the same PR as (a)/(b)/(c). Schema-validation
      test asserts each post-migration manifest validates against
      the v0.2 schema. Install-gate test asserts `agentbundle
      install --pack governance-extras` against empty state files
      at both scopes refuses with the AC17 message. `packs/core/pack.toml`
      gains the same `[pack.adapter-contract] version = "0.2"` +
      `[pack.install] default-scope = "repo" allowed-scopes =
      ["repo"]` declarations in the same PR; core ships no
      `[pack.dependencies.required]` (it is the root).
- [ ] **AC19 (install marker write + chained `adapt`, scope-aware).**
      Sub-clauses independently tested:
      - **AC19a (marker write, at install's scope root).** After
        every successful `agentbundle install --pack <name>
        [--scope <s>]`, the CLI appends a `[[packs-installed]]`
        entry to `.adapt-install-marker.toml` at the **install's
        scope root** (`<repo>/` for repo scope; `~/.agent-ready/`
        for user scope). Append via `os.replace` atomic rename.
        The file's *path* encodes scope; no `scope` field is
        written or read (see *§ Install marker schema*).
      - **AC19b (chained `adapt`).** After the marker write, the
        CLI runs `agentbundle.commands.adapt.run(args)` in-process
        (no subprocess; no LLM) with `args.values_from = Path(
        "<repo>/.adapt-discovery.toml")` (regardless of install
        scope — markers are repo-only). The CLI's dual-scope `adapt`
        walk handles both scopes' companions and pending reports.
      - **AC19c (`.gitignore` extension).** `agentbundle scaffold`
        lays down a `.gitignore` containing
        `.adapt-install-marker.toml` (repo-scope marker only —
        user-scope marker lives inside `~/.agent-ready/`, outside
        any repo). T8 has a test.
      - **AC19d (failure-mode robustness).** (i) If
        `<repo>/.adapt-discovery.toml` is absent at install time,
        the chained `adapt` step completes zero with one stderr
        line `adapt: no .adapt-discovery.toml at repo root; markers left unresolved`;
        the marker file is still written; install exits zero. (ii)
        If chained `adapt` raises (malformed
        `.adapt-discovery.toml` at either scope), install exits
        non-zero; the marker file is still on disk; stderr names
        the adapt failure.
- [ ] **AC20 (session-start hook surfaces install markers from
      both scopes).** The core pack's
      `packs/core/.apm/hooks/session-start.sh` is amended to read
      `.adapt-install-marker.toml` at **both** scopes:
      `<repo>/.adapt-install-marker.toml` (path resolved relative
      to the repo root the hook runs in) and
      `~/.agent-ready/.adapt-install-marker.toml`. The union of
      `[[packs-installed]]` entries from both files is rendered as
      one stdout line in the form
      `=== adapt-to-project: <N> pack(s) pending adaptation across <K> scope(s): <names> — run /adapt-to-project ===`
      where `<names>` is the lexicographically-sorted comma-joined
      list and `<K>` is 1 or 2. Silent when both files are absent.
      The existing `patterns.jsonl` block emits first; the nudge
      line second. A shell test fixture asserts the scope-permutation
      matrix: {repo only, user only, both, neither}.
- [ ] **AC21 (cross-spec marker-refusal grep widens to canonical
      syntax — both occurrences).** The UPPER_SNAKE-only regex
      `<adapt:[A-Z_][A-Z0-9_]*>` appears in
      `docs/specs/distribution-adapters/spec.md` at **two**
      locations: line 342 (descriptive prose under *Grep
      semantics*) and **line 759 (inside the contract-load-bearing
      Acceptance Criterion that pins Rail C)**. AC21 amends **both
      occurrences** to also match the canonical lowercase-hyphen
      form — implementation choice between regex union
      (`<adapt:([A-Z_][A-Z0-9_]*|[a-z][a-z0-9-]*)>`) or two
      separate grep passes. T15's verification: a `grep -c
      '<adapt:\[a-z\]\[a-z0-9-\]\*>' docs/specs/distribution-adapters/spec.md`
      returns ≥ 2 (one at each amended location). Widening only the
      line-342 prose without touching the line-759 AC closes the
      spec gap visually but leaves the contract surface intact —
      AC14's lowercase-hyphen markers in a user-scope pack still
      bypass.
      **AC21 carve-out (code-side widening deferred).** The *code*
      implementing Rail C (the validate-time grep in
      `agentbundle.build.validate` or equivalent, owned by
      `distribution-adapters/spec.md`) is **not** amended by this
      PR. AC21 amends the *spec text* — the contract — but the
      code follows when `distribution-adapters/spec.md`'s next
      implementation pass picks up the widened AC. Until then, a
      user-scope pack carrying lowercase-hyphen markers passes
      `validate` in code even though the contract refuses it.
      `docs/ROADMAP.md` gains an entry under
      `distribution-adapters` naming this as a known gap with
      trigger "Rail C grep widening to canonical syntax — paired
      with AC21 of adapt-to-project".
- [ ] **AC22 (skill walks both scopes' state files for Tier-2
      detection; v0.1 detection emits prereq message).** At
      session start the skill reads both
      `<repo>/.agent-ready-state.toml` (if present) and
      `~/.agent-ready/state.toml` (if present); enumerates the
      packs installed at each scope; for each scope's installed
      packs, recomputes SHA-256 hashes of the recorded file paths;
      surfaces every Tier-2 divergence under a scope-tagged
      section of the first message. The skill never writes either
      state file (`init-state --migrate` is the CLI's
      responsibility per RFC-0004 § *Backward compatibility*).
      **v0.1 detection sub-clause:** when either state file
      declares `schema-version = "0.1"` (the pre-RFC-0004 shape
      without explicit `scope` column), the skill emits **one
      stderr-style message** naming
      `agentbundle init-state --migrate <scope>` as the prereq
      for write operations and **continues** the session against
      that file's entries treated as scope-implied (repo for the
      repo-scope file, user for the user-scope file — matching
      the CLI's read-only v0.1 contract per
      `agent-spec-cli/spec.md:565-573`). The skill does **not**
      refuse the session and does **not** invoke the migration
      itself.
- [ ] **AC23 (cross-scope restructure forbidden from executing).**
      A class-3 finding whose `source-path` and `destination-path`
      live at different scopes (e.g., source under `<repo>/`,
      destination under `~/.claude/`) is **not executed as a
      single restructure**. The skill detects the scope crossing,
      names both paths and the crossing in the conversation, and
      offers the adopter exactly two responses:
      **(i) decline** — no file move, no recording at either
      scope, no entry in `[[findings.*]]` (since the rule "Never
      widen the scope of a finding beyond where it was observed"
      would otherwise force a cross-scope recording);
      **(ii) split into two same-scope operations** — the skill
      proposes the cross-scope move as a *pair* of same-scope
      operations (e.g., "copy `<repo>/DESIGN.md` content into a new
      user-scope file" + "delete the repo-scope `DESIGN.md`"), each
      independently per-scope, each recorded in its own scope's
      `[[findings.*]]` after independent accept/decline. The
      adopter approves or declines each split operation
      independently.
      No "execute as cross-scope" outcome exists; this sidesteps
      the recording-scope ambiguity (the source-scope recording
      would mutate user scope invisibly to a user-scope re-run).
      No user-scope-eligible packs ship in v1 so this AC is
      exercised by the AC4a *cross-scope-restructure × decline* row
      against the synthetic user-scope fixture; the *split-into-two*
      path is exercised by code review against the SKILL.md body
      (the body must document the split-into-two prompt verbatim;
      T17 grep asserts this).

## Changelog

- 2026-05-23: initial draft → 1st-pass-review fixes → 2nd-pass-review
  fixes → **post-RFC-0004 rebase reconciliation** (added Constrained-
  by RFC-0004 + distribution-adapters; introduced per-scope schemas
  for `.adapt-discovery.toml`, `.adapt-pending.md`, install marker;
  per-scope path-jail and dirty-state mechanics; dual-state-file
  Tier-2 detection; cross-spec marker-refusal grep widening AC;
  cross-scope restructure escalation AC; addon `[pack.install]`
  declarations; AC count 20 → 23).
- 2026-05-23: 4th-pass-review fixes (Blocker 1: AC21 names both
  amendment locations + tightened verification; Blocker 3: AC23
  forbids cross-scope-restructure execution, offers decline or
  split-into-two only; Concern 4: AC21 carve-out for deferred
  code-side widening; Concern 8: AC22 v0.1-state-file sub-clause;
  Concern 9: AC18(d) `[pack.adapter-contract] version = "0.2"`
  bump for all four packs; nits 5/6/7/10/12 absorbed: scope
  field dropped from install marker schema, AC1 grep #5 →
  multi-token behavioural check, AC4 split into 4a/4b with
  explicit ROADMAP deferral, AC12 quote includes leading `and `,
  AC2 reconciles visible vs hashed finding-id encoding).
