# Spec: self-hosting

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md), [RFC-0002](../../rfc/0002-self-hosting.md)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Naming note (drafting drift in RFC-0002).** RFC-0002 contains five
> drafting-drift items this spec normalises against the on-disk scaffold:
> (1) it refers to this work as `self-hosting-bootstrap` in some places
> (Composition with RFC-0001, Follow-on artifacts) — the canonical spec
> directory is `docs/specs/self-hosting/`; (2) it uses plural
> `docs/rfcs/` / `docs/adrs/` paths — this spec adopts the singular
> `docs/rfc/` / `docs/adr/` that match the repo on disk; (3) it points
> at `tools/build/recipes/self-host.toml` — recipes live under
> `packages/agentbundle/agentbundle/build/recipes/` per the sibling
> distribution-adapters spec's *Always do* enumeration; (4) it shows
> hook bodies as `packs/<pack>/.apm/hooks/<name>.py` — both `.sh` and
> `.py` are valid per the sibling spec's hook extension policy, and
> today's hooks ship as `.sh`; (5) RFC-0002 writes the entry points as
> `make build-self` and `make build-check`, but Make parses
> `--self` and `--check` as unknown Make options rather than target
> arguments — the on-disk Makefile (landed by the sibling
> distribution-adapters spec's T8) implements them as separate targets
> `make build-self` and `make build-check`, with `DRY_RUN=1` and
> `FORCE=1` as variables. This spec adopts the target-form surface
> throughout. `§` in this spec means "section."
>
> **Schema authority.** The sibling spec at
> [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
> defines `pack.toml`, `.claude-plugin/plugin.json`, the Tier-1/2/3 contract,
> the `.agent-ready-state.toml` schema, and the `.upstream.<ext>` semantics.
> It also enumerates the six projection recipe types
> (`per-pack-claude-plugin`, `per-pack-apm-package`, `marketplace`,
> `per-pack-overlay`, `composite-agents-md`, `composite-marketplace`) and
> the five primitive types (`skill`, `agent`, `hook-body`, `hook-wiring`,
> `command`). This spec references those definitions; it does not redefine
> them.

## Objective

This repo becomes the first consumer of its own build pipeline. A single
command, `make build-self`, reads every `packs/<pack>/.apm/` and
`packs/<pack>/seeds/` tree plus the adapter contract and projects a Claude
Code overlay onto the repo itself — every path listed in RFC-0002's
*Projected* table lands at its target location, byte-for-byte identical to
what would result if an adopter had installed every pack and run the
adaptation step against this repo's concrete values. A CI gate,
`make build-check`, runs on every PR and refuses to merge if any
projected path on disk diverges from what the pipeline would emit. After
cutover, the only legitimate way to change a projected path's content is
to edit its pack-side source and re-project; direct edits to projected
paths are caught and bounced. Success for a maintainer is that the same
muscle memory used by adopters — edit `packs/<pack>/.apm/...` or
`packs/<pack>/seeds/...`, run `make build-self`, commit — is the only
muscle memory that produces a green PR for changes to the bundle.

## Boundaries

### Phased rollout (discovered constraint)

The sibling distribution-adapters spec's T6 landed the build pipeline's
recipe loader and three of the six recipe types as runtime logic
(`per-pack-claude-plugin`, `per-pack-apm-package`, `marketplace`); the
three composite types (`per-pack-overlay`, `composite-agents-md`,
`composite-marketplace`) landed as metadata-only TOML stubs without the
runtime that drives seed-projection, AGENTS.md body+footer composition,
or root-marketplace aggregation. The Codex adapter additionally
overwrites the managed block per-pack (last pack wins) when multiple
packs ship skills, which makes a multi-pack AGENTS.md projection
incorrect under the current code shape. These gaps surfaced during
EXECUTE and are too large to close in this migration PR.

This spec therefore partitions its scope into **two cutover phases**:

- **Phase 1 (this PR).** Adapter-driven `.apm/` primitives only. The
  *Projected* set in this phase is exactly the Claude Code adapter's
  five direct outputs: `.claude/skills/<name>/`, `.claude/agents/<name>.md`,
  `.claude/commands/<name>.md`, `tools/hooks/<name>.<ext>`, and the
  `hooks` key of `.claude/settings.local.json`. The Phase-1 PR ships
  packs/* sources, the recipe TOMLs, `.adapt-discovery.toml`, the
  `make build-check` workflow, and the CONVENTIONS amendment. Seeds
  (under `packs/*/seeds/`) are authored but not yet projected — they
  ship as Source and the gate ignores them.
- **Phase 2 (follow-up PR).** Seed projection (`docs/CHARTER.md`,
  `docs/CONVENTIONS.md`, seed READMEs, `docs/_templates/*`,
  `packages/_example/`, `packages/README.md`), AGENTS.md body+footer
  composition (with the Codex multi-pack aggregation fix or an
  alternative composition path), `.claude-plugin/marketplace.json`
  aggregation, and the `CLAUDE.md → AGENTS.md` symlink projection.
  Phase 2 lifts these paths from Source to Projected and extends the
  gate accordingly.

Every *Always do*, *Ask first*, *Never do*, Acceptance Criterion, and
test below carries an implicit "Phase 1 only" unless it names Phase 2
explicitly. Phase-2-deferred items are tagged `(Phase 2)`.

### Always do

- Read source-of-truth from `packs/*/.apm/` (including
  `packs/<pack>/.apm/skills/`, `packs/<pack>/.apm/agents/`,
  `packs/<pack>/.apm/hooks/`, `packs/<pack>/.apm/commands/`, and
  `packs/<pack>/.apm/hook-wiring/`), `packs/*/seeds/` (authored in
  Phase 1, projected in Phase 2), the adapter
  contract at `docs/specs/adapter-contract/`, and the build pipeline at
  `packages/agentbundle/agentbundle/build/` (with a thin shim at
  `tools/build/build.py`; the user-facing entry points are still
  `make build-self` and `make build-check`). In Phase 1, project to
  exactly the five Claude Code adapter outputs enumerated above.
- Restrict the self-host runner to the `claude-code` adapter in Phase 1.
  The other contract-declared adapters (`kiro`, `copilot`, `codex`)
  remain in the contract for distribution builds, but the self-host
  runner's `SELF_HOST_ADAPTERS` allow-list contains only `claude-code`
  so projections into `.kiro/`, `.github/instructions/`, and AGENTS.md's
  managed block do not fire under `make build-self`. Phase 2 widens the
  allow-list once the Codex multi-pack aggregation gap is closed.
- *(Phase 2)* Compose root `AGENTS.md` from BOTH `packs/core/seeds/AGENTS.md`
  (the body) AND `packs/core/seeds/_agents-footer.md` (the pointer
  footer, appended after the body, LF-normalised). The
  `composite-agents-md` recipe defined in the distribution-adapters
  spec drives this composition. Authored as a recipe TOML in Phase 1;
  the runtime that consumes it ships in Phase 2.
- Preserve hook source extension. A hook is a script; the build pipeline's
  `[primitive.hook-body]` projection copies `.sh` or `.py` through
  unchanged. Today's `tools/hooks/*.sh` are valid; future `.py` hooks are
  also valid. No conversion happens during migration.
- Resolve `<adapt:NAME>` markers as a final build step under
  `make build-self` only — the one authorised mode that runs marker
  resolution per the distribution-adapters spec's Acceptance Criterion
  for `make build-self` (the AC pinning that `--self` writes to the
  tree, resolves markers, refuses dirty trees without `--force`, and
  honours on-conflict policy). The resolver itself belongs to the
  `adapt-to-project` skill (deferred); for self-host, materialize a
  repo-local `.adapt-discovery.toml` with this repo's concrete values
  and apply it. All other build modes copy markers through unchanged.
- Compare projected output against on-disk content as bytes. *(Phase 2)*
  Strengthen the comparison to byte-for-byte after CRLF→LF normalisation,
  with file mode bits compared for regular files and symlink targets
  compared via `lstat` (never follow symlinks). Phase 1's
  `diff_against_working_tree` uses `read_bytes()` equality — sufficient
  for the adapter-driven primitives the gate covers today; the
  LF-normalising / mode-aware / lstat path lands alongside seed
  projection in Phase 2.
- *(Phase 2)* Enumerate candidate paths from the git-tracked +
  untracked-but-not-ignored set, so editor scratch and gitignored
  build outputs do not surface in either the comparison or the
  unclassified-path report. Phase 1 walks only the shadow projection
  (every path emitted by the adapters), which is a strict subset of
  the eventual git-enumeration set and never produces false positives
  on uncategorised paths.
- *(Phase 2)* Emit `[info]` lines to stderr for on-disk paths that fall
  in neither the *Projected* nor *Excluded* categories. Info-level
  messages do not fail the build; they surface omissions so the next
  PR can classify them. Phase 1 ships without the unclassified-path
  enumeration because seed paths aren't yet projected — almost every
  `docs/` path would surface as `[info]` and bury real signal.
- *(Phase 2)* On drift, name the source path and the regeneration
  command in the failure message (`Edit <source>; run: make build-self`).
  Phase 1 emits `drift: <projected-path>` only; mapping projected→source
  requires a reverse-index across pack `.apm/` directories that's
  cheapest to build alongside Phase-2 seed projection.
- Refuse `make build-self` on a dirty working tree unless `FORCE=1` is
  passed. `FORCE=1` bypasses only the dirty-tree refusal. The
  byte-equality gate runs under `make build-check` and
  `make build-self DRY_RUN=1` regardless of `FORCE=1`; the real-write
  path (`make build-self` without `DRY_RUN=1`) does not run a
  post-write comparison — the gate is `make build-check`, intended to
  run in CI against the resulting commit.
- Update `docs/CONVENTIONS.md` in the same migration PR to record the
  pack source-of-truth split as a convention. The literal markdown
  heading is `## Pack source-of-truth split` (no `§` in the heading
  itself; `§` elsewhere in this spec is shorthand for "section"). Its
  minimum claims are: names `packs/*/.apm/` and `packs/*/seeds/` as the
  upstream for every projected path; cites RFC-0002; cites
  `make build-check` as the gate that enforces the split. RFC-0002
  authorises this amendment; no separate RFC is needed.

### Ask first

- Reclassifying any path between *Source*, *Projected*, and *Excluded*
  beyond what RFC-0002's tables specify. Edits to the *Projected* table
  itself need human sign-off (and may need an RFC if structural).
- Introducing a new `[recipe.*]` section type beyond the enumerated
  six-recipe set defined in the distribution-adapters spec
  (`per-pack-claude-plugin`, `per-pack-apm-package`, `marketplace`,
  `per-pack-overlay`, `composite-agents-md`, `composite-marketplace`).
  The sibling spec pins this set in its dedicated enumerated-set
  Acceptance Criterion under § *Recipe set*. New section types require
  an RFC and a coordinated update to the distribution-adapters spec;
  they affect the recipe schema shared across the bundle.
- Treating a file-level collision between two packs' `seeds/` trees as
  anything other than a build-time error. RFC-0002 mandates surfacing
  these for human resolution by rename or consolidation.
- Any deviation from byte-for-byte equality as the comparison standard
  (e.g. ignore-whitespace, ignore-ordering). The comparison standard is
  the gate's load-bearing property.

### Never do

- **Direct edits to any *Projected* path post-cutover.** After step 3 of
  the migration plan, every change to a projected path flows through
  `packs/*/`. The CI gate enforces this; no local override exists.
- **New top-level directories outside the RFC-0001 / RFC-0002 layout.**
  Top-level structure is governed by RFC; new top-level entries need
  their own RFC, not a self-host change.
- **Local hooks that enforce the gate.** Enforcement is CI-only by
  design. No `pre-commit`, no `pre-push`, no `Stop` hook that runs
  `make build-check`. The maintainer-side ergonomics rely on the gate
  being a CI signal, not a local interruption.
- **Retroactive re-attribution of past commits to pack-side paths.**
  Migration is forward-only per RFC-0002's *Migration plan* step 3. The
  one-shot cutover commit records that projected content matches source;
  history before that commit is not rewritten.
- **Bypassing the comparison gate via `FORCE=1`.** `FORCE=1` is scoped
  to the dirty-tree refusal. `make build-check` and `DRY_RUN=1` run the
  byte-equality comparison regardless of `FORCE=1`; there is no
  flag-or-variable that turns the comparison off.
- **Adapters or recipes beyond the enumerated set.** `make build-self`
  uses only the `claude-code` adapter in Phase 1 (per the *Always do*
  allow-list) and `claude-code` + `codex` in Phase 2 once the Codex
  multi-pack aggregation gap closes. The six enumerated projection
  recipes from the distribution-adapters spec
  (`per-pack-claude-plugin`, `per-pack-apm-package`, `marketplace`,
  `per-pack-overlay`, `composite-agents-md`, `composite-marketplace`)
  stay as the enumerated set; the three composite types are
  metadata-only today and gain runtime in Phase 2. New adapters or
  recipes beyond this enumeration require an RFC.

### Excluded paths

The full *Excluded* table (paths that live on disk but are not derived
from `packs/*/`) is defined in RFC-0002's *What stays out* table and
referenced here without copy. The gate emits neither drift nor `[info]`
for these paths. The classes are: per-instance state
(`AGENTS.local.md`, `.claude/settings.local.json`,
`.claude-plugin/marketplace.json` when not generated, `dist/`,
`.adapt-discovery.toml`), governance under `docs/rfc/`, `docs/adr/`,
`docs/specs/`, `docs/architecture/overview.md`, the migration commit
metadata, and `packs/*/` themselves (sources, not projections). New
classifications go through RFC-0002 amendment.

## Testing Strategy

Each user-visible outcome from the Objective pairs with a verification
mode below. Modes align with the work-loop skill's three (TDD,
goal-based check, visual / manual QA).

- **`make build-check` gate behaviour** — TDD plus goal-based. Unit
  tests cover the comparison rules (LF normalisation, mode-bit
  comparison, symlink-target comparison via `lstat`, missing-counterpart
  drift, info-level unclassified-path reporting, file-collision error).
  This spec owns these unit tests; the distribution-adapters spec's T7
  imports them as a regression gate rather than re-implementing them.
  The comparison rules are properties of the gate, which this spec
  delivers. Why TDD: each rule is a compressible invariant
  with named inputs and outputs. A construction test verifies the gate
  *enforces*, not just runs: make a one-character edit to a projected
  path (not its source), run `make build-check`, assert non-zero exit
  and a `[drift]` line. A regression test asserts `--force` and any
  flag combination never bypass the comparison gate (a fixture injects
  drift; `make build-check` exits non-zero regardless of flags). A
  CI-side static check greps build code for `skip|bypass|SKIP_` exit
  branches and fails if any are introduced. A CRLF/`core.autocrlf` test
  asserts that a CRLF-on-disk file passes the gate (because the gate
  normalises CRLF→LF before comparison) but still produces a `git
  status` change (because `git status` does not). A goal-based check
  asserts the workflow file exists and runs `make build-check`.
- **Branch-protection required-status registration** — manual QA. The
  required-status registration is a GitHub setting, not a repo file;
  capture `gh api
  repos/{owner}/{repo}/branches/main/protection` output (or a
  screenshot) showing `make build-check` listed under
  `required_status_checks.contexts`. Recorded as the artifact for
  Acceptance Criterion 1b.
- **`make build-self` is a no-op on a clean checkout** — goal-based.
  The one-liner: on `main` after cutover, `make build-self` produces
  zero changes to the working tree (`git status --porcelain` emits no
  lines). Why goal-based: the outcome is observable as a single
  filesystem condition; an extra unit test asserting the same thing
  would mirror the implementation.
- **Dirty-tree refusal and `--force` semantics** — TDD. Unit tests for
  the CLI surface: dirty tree without `--force` exits non-zero with a
  named reason; dirty tree with `--force` proceeds but the resulting
  build still runs the comparison gate. Why TDD: small invariant,
  state-machine shape (clean/dirty × with-force/without-force).
- **`AGENTS.md` composition (body + footer)** — goal-based. After
  `make build-self` on a clean checkout, the projected root
  `AGENTS.md` consists of `packs/core/seeds/AGENTS.md` (the body)
  followed by `packs/core/seeds/_agents-footer.md` (the pointer
  footer), composed by the `composite-agents-md` recipe per the
  distribution-adapters spec. Two one-liners verify: (1) the head of
  the projected `AGENTS.md` matches the body source; (2) the tail of
  the projected `AGENTS.md` equals the contents of the footer source
  (after the same LF normalisation the gate uses).
- **First real pack-side edit lands through the pipeline** — manual QA.
  After cutover, a maintainer makes a small, observable edit to a
  projected path's source (e.g. a one-sentence addition in
  `packs/core/seeds/docs/CHARTER.md` or a typo fix in
  `packs/core/.apm/skills/work-loop/SKILL.md`), runs `make build
  --self`, commits the resulting diff, opens a PR, and observes that
  `make build-check` is green. The PR description records that the
  edit was made pack-side, not at the projected path. This QA gesture
  closes Acceptance Criterion 3; the recorded PR URL is the artifact.
- **CONVENTIONS.md amendment** — goal-based. The migration PR contains
  a `docs/CONVENTIONS.md` diff adding a `§ Pack source-of-truth split`
  section. A `grep` against the post-merge file verifies the section
  heading exists, that it names both `packs/*/.apm/` and `packs/*/seeds/`
  as the upstream for projected paths, that it cites RFC-0002, and that
  it cites `make build-check` as the enforcing gate. Each claim is a
  separate grep one-liner.

Tests for the build pipeline's projection logic itself (path
iteration, file copy semantics, `[recipe.per-pack-overlay]` /
`[recipe.composite-agents-md]` / `[recipe.composite-marketplace]`
expansion) live with the sibling distribution-adapters spec, which
owns the pipeline implementation. This spec consumes the pipeline; it
verifies the self-host shape on top. The unit tests for the
comparison rules themselves (LF normalisation, mode-bit comparison,
symlink-via-`lstat`) are owned by this spec, as noted above; the
distribution-adapters spec's T7 imports them as a regression gate.

## Acceptance Criteria

Each AC below is tagged **Phase 1** (closed by this PR) or **Phase 2**
(deferred per § *Phased rollout*). Phase-2 ACs ship in a follow-up PR
once seed-projection, AGENTS.md composition, marketplace aggregation,
and the Codex multi-pack aggregation fix land.

- [x] **AC1a (workflow) — Phase 1.** `.github/workflows/build-check.yml` runs
  `make build-check` on PRs targeting `main` and exits 0 when the
  Phase-1 projection is up-to-date. Verified goal-based by T4.
- [ ] **AC1b (branch protection) — Phase 1, post-merge.** GitHub branch
  protection on `main` lists `make build-check` (the workflow's job
  name) as a required status check. Verified manually; the recorded
  artifact is the output of `gh api repos/{owner}/{repo}/branches/main/protection`
  showing the job under `required_status_checks.contexts` (or an
  equivalent screenshot). Captured *after* this PR merges.
- [x] **AC2 (no-op build) — Phase 1.** `make build-self` on a clean
  checkout of `main` produces no on-disk change. `git status
  --porcelain` emits zero lines. Verified locally on the
  pre-cutover branch and re-verified post-merge.
- [ ] **AC3 (first real edit) — Phase 1, post-merge.** At least one real
  pack-side edit has landed on `main` via the pipeline: the merged
  commit modifies both a `packs/*/` source path and its corresponding
  *Projected* path. A linked PR URL records the manual-QA gesture.
- [x] **AC4 (dirty-tree refusal) — Phase 1.** `make build-self` refuses
  on a dirty working tree with a named reason (non-zero exit; stderr
  contains the dirty-tree refusal message). `FORCE=1` bypasses the
  dirty-tree refusal only. Under `make build-check` and
  `make build-self DRY_RUN=1`, the byte-equality comparison runs
  regardless of `FORCE=1`; the real-write path (`make build-self`
  without `DRY_RUN=1`) writes the projection and exits — the gate is
  `make build-check`, intended to run against the resulting commit.
- [x] **AC5 (CONVENTIONS amendment) — Phase 1.** The migration PR contains
  a `docs/CONVENTIONS.md` amendment whose literal markdown heading is
  `## Pack source-of-truth split`. The section names `packs/*/.apm/`
  and `packs/*/seeds/` as the upstream for every projected path,
  cites RFC-0002 as the authority, and cites `make build-check` as
  the enforcing gate.
- [ ] **AC6 (info-level unclassified) — Phase 2.** On-disk paths that
  fall in neither *Projected* nor *Excluded* surface as `[info]` lines
  on stderr during `make build-check`, without failing the build.
  Deferred until the gate's enumeration walks the git-tracked +
  untracked-but-not-ignored set (the current implementation only
  walks shadow output).
- [ ] **AC7 (seed collisions) — Phase 2.** File-level collisions across
  packs' `seeds/` trees (same target path, different content) cause
  `make build-self` to exit non-zero with a named error identifying
  the colliding source files. Deferred — seed projection lands in
  Phase 2; until then no seed is projected and the collision check
  has nothing to enforce.
- [ ] **AC8 (AGENTS.md composition) — Phase 2.** The projected root
  `AGENTS.md` is composed from BOTH `packs/core/seeds/AGENTS.md` (the
  body) AND `packs/core/seeds/_agents-footer.md` (the pointer footer,
  appended after the body). The composition is performed by the
  `composite-agents-md` recipe; T2 tests verify both the body match
  and the footer append. Deferred — Codex adapter's last-pack-wins
  multi-pack aggregation must be fixed first.
- [ ] **AC9 (seed READMEs) — Phase 2.** Seed READMEs under
  `docs/architecture/`, `docs/specs/`, `docs/knowledge/`,
  `docs/product/`, `docs/guides/`, `docs/rfc/`, `docs/adr/`,
  `docs/_templates/`, and `packages/` are *Projected*; the gate
  enforces byte-equality with their pack-side sources. Deferred —
  seed projection lands in Phase 2.
- [x] **AC10 (commands) — Phase 1.** `.claude/commands/<name>.md` is
  *Projected* from `packs/*/.apm/commands/<name>.md` per the Claude
  Code adapter's `command` primitive projection. The gate enforces
  byte-equality; any direct edit to `.claude/commands/<name>.md` drifts.
- [x] **AC11 (hook-wiring) — Phase 1.** The `hooks` key of
  `.claude/settings.local.json` is *Projected* from
  `packs/*/.apm/hook-wiring/<name>.toml` via the Claude Code adapter's
  `merge-json` projection. Other keys in `.claude/settings.local.json`
  remain per-instance state and are *Excluded*. The gate compares the
  `hooks` key only. (Today the repo ships no hook-wiring TOMLs; the
  projection is a no-op until packs author one.)
- [x] **AC12 (marker resolution) — Phase 1.** `make build-self` resolves
  `<adapt:NAME>` markers under the adapter-target subtree to concrete
  values from `.adapt-discovery.toml` as the final build step before
  writing. The repo ships `.adapt-discovery.toml` at the repo root with
  this repo's concretes.
- [x] **AC13 (markers preserved in dist) — Phase 1.** `make build`
  without `--self` copies `<adapt:NAME>` markers through unchanged; no
  resolution runs (delivered by sibling distribution-adapters spec).
- [ ] **AC14 (missing-config fail-fast) — Phase 2.** Missing
  `.adapt-discovery.toml` under `make build-self` causes fail-fast with
  a named stderr message in the form
  `missing .adapt-discovery.toml required by --self`. Deferred — today
  a missing discovery file is a silent no-op rather than fail-fast;
  Phase 2 adds the fail-fast guard.
