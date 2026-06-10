# Spec: self-hosting

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md), [RFC-0002](../../rfc/0002-self-hosting.md)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Post-ship amendments:** the spec body has been amended post-ship; see
> [Changelog](#changelog).

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
> the `.agentbundle-state.toml` schema, and the `.upstream.<ext>` semantics.
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

- **Phase 1 (this PR).** Adapter-driven `.apm/` primitives projected via
  the Claude Code adapter, plus the seed-projection / marketplace-
  aggregation / CLAUDE.md-symlink / missing-discovery fail-fast /
  drift-source-naming / info-line classification additions landed
  during the EXECUTE fix-pass. The *Projected* set covers:
  - Claude Code adapter's five direct outputs: `.claude/skills/<name>/`,
    `.claude/agents/<name>.md`, `.claude/commands/<name>.md`,
    `tools/hooks/<name>.<ext>`, and the `hooks` key of
    `.claude/settings.local.json`.
  - Seed-projected paths: `docs/CONVENTIONS.md`. (Narrowed by the
    2026-05-25 amendment — see [Changelog](#changelog); 19 paths
    previously in this set were reclassified Projected → Manual and
    now ship as placeholder seeds with adopters' on-disk content
    owned post-install. `docs/APPROACH.md` was retired in the same
    amendment.)
  - Aggregated: `.claude-plugin/marketplace.json` from
    `packs/*/.claude-plugin/plugin.json`.
  - Recreated: `CLAUDE.md → AGENTS.md` symlink.
  Phase 1 also ships packs/* sources, the recipe TOMLs,
  `.adapt-discovery.toml`, the `make build-check` workflow, and the
  CONVENTIONS amendment.
- **Phase 2 (closed).** AGENTS.md body+footer composition, Codex
  multi-pack managed-block aggregation, and the comparison-rule
  strengthening (LF normalisation, file-mode bits, symlink-target
  comparison via `lstat`) all landed. See Changelog.

Every *Always do*, *Ask first*, *Never do*, Acceptance Criterion, and
test below carries an implicit "Phase 1 only" unless it names Phase 2
explicitly. Phase-2-deferred items are tagged `(Phase 2)`.

### Always do

- Read source-of-truth from `packs/*/.apm/` (including
  `packs/<pack>/.apm/skills/`, `packs/<pack>/.apm/agents/`,
  `packs/<pack>/.apm/hooks/`, `packs/<pack>/.apm/commands/`, and
  `packs/<pack>/.apm/hook-wiring/`), `packs/*/seeds/`, the adapter
  contract at `docs/contracts/`, and the build pipeline at
  `packages/agentbundle/agentbundle/build/` (with a thin shim at
  `tools/build/build.py`; the user-facing entry points are still
  `make build-self` and `make build-check`). In Phase 1, project the
  five Claude Code adapter outputs plus the seed-projected paths
  enumerated in § *Phased rollout*; aggregate
  `.claude-plugin/marketplace.json` and recreate the CLAUDE.md symlink.
- Run the `claude-code` and `codex` adapters under self-host. The other
  contract-declared adapters (`kiro`, `copilot`) remain in the contract
  for distribution builds but stay excluded from `SELF_HOST_ADAPTERS`, so
  projections into `.kiro/` and `.github/instructions/` do not fire under
  `make build-self`.
- Compose root `AGENTS.md` from BOTH `packs/core/seeds/AGENTS.md`
  (the body) AND `packs/core/seeds/_agents-footer.md` (the pointer
  footer, appended after the body, LF-normalised). The
  `composite-agents-md` recipe defined in the distribution-adapters
  spec drives this composition.
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
- Compare projected output against on-disk content with three rules,
  all landed in Phase 2: byte-for-byte after CRLF→LF normalisation
  for text-like files (UTF-8-decodable inputs only — binaries that
  happen to contain a 0x0D 0x0A pair are compared raw); file-mode
  permission-bit comparison for regular files (low 9 bits); and
  symlink-target comparison via `lstat` — the gate never follows a
  symlink. Implementation: `diff_against_working_tree` in
  `agentbundle.build.self_host`.
- Enumerate candidate paths from the git-tracked + untracked-but-not-
  ignored set (`git ls-files --cached --others --exclude-standard`), so
  editor scratch and gitignored build outputs do not surface in either
  the comparison or the unclassified-path report.
- Emit `[info]` lines to stderr for on-disk paths that fall in neither
  the *Projected* nor *Excluded* categories. Info-level messages do
  not fail the build; they surface omissions so the next PR can
  classify them. Excluded patterns are enumerated in
  `agentbundle.build.self_host.EXCLUDED_PATTERNS`; extend that
  constant when an RFC authorises a new excluded class. Phase-1
  Projected paths that would otherwise match an excluded glob (the
  seed READMEs under `docs/architecture/`, `docs/product/`,
  `docs/knowledge/`, `docs/guides/`) are listed in
  `PROJECTED_README_OVERRIDES`.
- On drift, name the source path and the regeneration command in the
  failure message: `[drift] <projected>: edit <source>; run: make
  build-self`. The projected→source map is built per dry-run from
  `packs/*/.apm/` (via the Claude Code adapter's contract projections)
  and `packs/*/seeds/`; directory-level mappings are walked to find
  the file-level source.
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
  uses only the `claude-code` and `codex` adapters. The six enumerated
  projection recipes from the distribution-adapters spec
  (`per-pack-claude-plugin`, `per-pack-apm-package`, `marketplace`,
  `per-pack-overlay`, `composite-agents-md`, `composite-marketplace`)
  stay as the enumerated set. New adapters or recipes beyond this
  enumeration require an RFC.

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
- [x] **AC1b (branch protection) — Phase 1, post-merge.** GitHub branch
  protection on `main` lists `make build-check` (the workflow's job
  name) as a required status check. Configured 2026-05-22 via
  `gh api -X PUT repos/eugenelim/agent-ready-repo/branches/main/protection`
  with `strict: true` (PRs must be up-to-date with main) and
  `enforce_admins: false` (admins retain a hotfix escape hatch).
  Artifact at
  [`notes/ac1b-branch-protection.json`](notes/ac1b-branch-protection.json)
  — the captured `gh api .../branches/main/protection` output showing
  `make build-check` under `required_status_checks.contexts`.
- [x] **AC2 (no-op build) — Phase 1.** `make build-self` on a clean
  checkout of `main` produces no on-disk change. `git status
  --porcelain` emits zero lines. Verified locally on the
  pre-cutover branch and re-verified post-merge.
- [x] **AC3 (first real edit) — Phase 1, post-merge.** At least one real
  pack-side edit has landed on `main` via the pipeline: the merged
  commit modifies both a `packs/*/` source path and its corresponding
  *Projected* path. Closed by
  [PR #20](https://github.com/eugenelim/agent-ready-repo/pull/20)
  (merge commit `92735a1`), which edited
  `packs/core/seeds/docs/architecture/README.md` and re-projected to
  `docs/architecture/README.md` via `make build-self`. The
  required-status-check gate (`make build-check`) ran green on the
  PR — meta-verifying both the source-of-truth split *and* the gate
  enforcement configured under AC1b.
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
- [x] **AC6 (info-level unclassified) — Phase 1.** On-disk paths that
  fall in neither *Projected* nor *Excluded* surface as `[info]` lines
  on stderr during `make build-check`, without failing the build.
  Implemented via `_emit_info_for_unclassified` (enumerates via
  `git ls-files --cached --others --exclude-standard`); excluded
  patterns enumerated in `EXCLUDED_PATTERNS`.
- [x] **AC7 (seed collisions) — Phase 1.** File-level collisions across
  packs' `seeds/` trees (same target path, different content) cause
  `make build-self` to exit non-zero (exit code 4) with a named error
  identifying both colliding source paths. Implemented in
  `_project_seeds`; tested by
  `SeedProjectionTests::test_collision_with_different_content_raises`.
- [x] **AC8 (AGENTS.md composition) — Phase 2.** The projected root
  `AGENTS.md` is composed from BOTH `packs/core/seeds/AGENTS.md` (the
  body) AND `packs/core/seeds/_agents-footer.md` (the pointer footer,
  appended after the body). The composition is performed by the
  `composite-agents-md` recipe; tests verify the body match, the
  multi-pack Codex-managed block, and the footer append. Closed by the
  Codex multi-pack aggregation fix and self-host composition runtime.
- [x] **AC9 (seed READMEs) — Phase 1, superseded by 2026-05-25 amendment.**
  ~~Seed READMEs under `docs/architecture/`, `docs/specs/`,
  `docs/knowledge/`, `docs/product/`, `docs/guides/`, `docs/rfc/`,
  `docs/adr/`, and `packages/` are *Projected*; the gate enforces
  byte-equality with their pack-side sources.~~ **Superseded:** the
  2026-05-25 amendment (RFC-0002 § Amendments § 2026-05-25)
  reclassified these paths Projected → Manual. The gate no longer
  enforces byte-equality on them; the pack-side seed is a placeholder
  template adopters receive via brownfield rules
  (`safety.write_companion`) on first install. See AC18-AC23 for the
  new contracts. The collision check from AC7 remains in effect for
  the one path that stays Projected (`docs/CONVENTIONS.md`) and any
  future composite seeds.
  (`docs/_templates/` was in this enumeration when this AC was first
  written; the directory was retired 2026-05-24 when its contents
  moved to per-skill `assets/` folders — see Changelog.)
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
  this repo's concretes. (Today no pack source carries `<adapt:NAME>`
  markers; the resolver path is verified by fixture tests in
  `test_self_host_check.py` and runs as a vacuous no-op against the
  live repo until a pack authors a marker — matching AC11's no-op
  posture for hook-wiring.)
- [x] **AC13 (markers preserved in dist) — Phase 1.** `make build`
  without `--self` copies `<adapt:NAME>` markers through unchanged; no
  resolution runs (delivered by sibling distribution-adapters spec).
- [x] **AC14 (missing-config fail-fast) — Phase 1.** Missing
  `.adapt-discovery.toml` under `make build-self` causes fail-fast with
  a named stderr message in the form
  `missing .adapt-discovery.toml required by --self` (exit code 3).
  Implemented in `run_self_host`; tested by
  `MissingDiscoveryFailFastTests`.
- [x] **AC15 (CLAUDE.md symlink) — Phase 1.** `make build-self`
  recreates the `CLAUDE.md → AGENTS.md` symlink at the repo root.
  Idempotent (a correctly-pointing symlink is left alone); a
  wrong-target symlink or regular file at `CLAUDE.md` is replaced.
  Implemented by `_recreate_claude_symlink`; tested by
  `ClaudeSymlinkTests`.
- [x] **AC15b (CLAUDE.md cross-shape equivalence) — Phase-2
  amendment.** The drift detector treats three on-disk shapes of
  the repo-root `CLAUDE.md` as equivalent: (a) a symlink whose
  target is `"AGENTS.md"`; (b) a regular file whose content is
  byte-equal (after LF normalisation) to the disk-side
  `AGENTS.md`; (c) a regular file whose stripped content is
  `"AGENTS.md"` — the form Git for Windows materialises when
  `core.symlinks=false`. Clause (c)'s trailing-whitespace
  tolerance (CRLF, LF, none) mirrors `lint-agents-md.py` check
  #2's `.strip() == "AGENTS.md"` semantics, so an adopter that
  passes the lint also passes the drift gate. Cross-shape
  pairings (e.g., symlink shadow vs. materialised-symlink disk on
  a Windows runner) no longer drift. Tampering (any other
  content) still drifts. The rule is scoped to
  `relative == Path("CLAUDE.md")` only; every other file keeps
  the strict symlink/regular distinction Phase 2 introduced.
  Implemented by `_is_equivalent_claude_md_shape`; tested by
  `ClaudeMdEquivalenceTests`.
- [x] **AC16 (marketplace aggregation) — Phase 1.**
  `.claude-plugin/marketplace.json` at the repo root is aggregated
  from every `packs/<pack>/.claude-plugin/plugin.json` so this repo is
  itself a usable marketplace at HEAD. JSON serialised with
  `sort_keys=True` for byte-determinism. Implemented by
  `_aggregate_marketplace`; tested by `MarketplaceAggregationTests`.
- [x] **AC17 (drift source-naming) — Phase 1.** Drift messages take
  the form `[drift] <projected>: edit <source>; run: make build-self`,
  naming both the projected path and the pack-side source for direct
  navigation. Implemented by `_build_projected_to_source_map` +
  `_lookup_source` in `diff_against_working_tree`; tested by
  `DriftSourceNamingTests`.
- [x] **AC18 (seed scrub) — 2026-05-25 amendment.** The five leaking
  seeds enumerated in RFC-0002 § Amendments § 2026-05-25
  (`packs/core/seeds/docs/architecture/overview.md`,
  `packs/core/seeds/docs/specs/README.md`,
  `packs/core/seeds/docs/knowledge/patterns.jsonl`,
  `packs/governance-extras/seeds/docs/rfc/README.md`,
  `packs/governance-extras/seeds/docs/adr/README.md`) are scrubbed
  to placeholder-only shape: empty tables, `<theme>` /
  `<list your packs and packages>` placeholders, no agent-ready-repo
  identifiers. The other 14 reclassified-Projected → Manual paths
  were already placeholder-shaped and need no scrubbing; the
  `tools/lint-seeds.py` lint (AC21) verifies the placeholder shape
  across all 19. Goal-based verification via grep + lint.
- [x] **AC19 (CONVENTIONS seed RFC scrub) — 2026-05-25 amendment.**
  The eight inline RFC-NNNN cross-references in
  `packs/core/seeds/docs/CONVENTIONS.md` (1× RFC-0002 at line 378,
  1× RFC-0004 at line 392, 6× RFC-0006 across lines 792-889) are
  dropped or inlined per the per-ref disposition table in the
  amendment plan: 8 drops in this PR, no relocations needed since
  surrounding prose stood on its own once links were removed. The
  seed-projected enumeration in CONVENTIONS § "Pack source-of-truth
  split" was simultaneously narrowed to list only `docs/CONVENTIONS.md`
  (the post-shrink Projected set) and the "RFC-0002 is the authority"
  paragraph was rewritten to remove the authority-attribution framing.
  Goal-based verification: `grep -c RFC-000
  packs/core/seeds/docs/CONVENTIONS.md` returns 0.
- [x] **AC20 (override shrink) — 2026-05-25 amendment.**
  `PROJECTED_README_OVERRIDES` in
  `packages/agentbundle/agentbundle/build/self_host.py:329` shrinks
  from 20 entries to 1 (only `docs/CONVENTIONS.md` remains). The 19
  removed entries fall through to `EXCLUDED_PATTERNS`: 11 covered by
  the existing patterns (`docs/architecture/*.md`,
  `docs/product/*.md`, `docs/knowledge/*.md`,
  `docs/guides/**/*.md`); 8 added explicitly in the same edit
  (`docs/CHARTER.md`, `docs/knowledge/patterns.jsonl`,
  `docs/rfc/README.md`, `docs/adr/README.md`, `docs/specs/README.md`,
  `packages/README.md`, `packages/_example/README.md`,
  `packages/_example/AGENTS.md`). Includes the CHARTER odd-status
  clause: `docs/CHARTER.md` was historically in the override despite
  being conceptually Manual; this amendment regularises that — the
  on-disk `docs/CHARTER.md` retains its filled-in content post-build.
  TDD verification: `test_post_2026_05_25_shrink_leaves_only_conventions`
  in `test_self_host_check.py` asserts (a) 19 paths land in Excluded
  post-shrink, (b) `docs/CONVENTIONS.md` stays in the override,
  (c) a hypothetical `docs/architecture/data-pipeline.md` stays
  Excluded (regression guard), (d) the added literals are anchored
  (`packages/_example/README.md` matches but
  `packages/foo/_example/README.md` does not).
- [x] **AC21 (seed-content lint) — 2026-05-25 amendment.**
  `tools/lint-seeds.py` ships a stdlib-only lint that asserts every
  seed under `packs/*/seeds/` (a) carries required placeholder tokens
  (per-file hardcoded expectations in
  `lint-seeds.py:REQUIRED_PLACEHOLDERS`; fail-loud on unknown seed
  files — every new seed must declare its expected shape), (b)
  contains no catalogue-specific strings (the same blocklist the
  snapshot test in AC22 uses). The lint honours a single-line
  sentinel `<!-- seed-content-lint-ignore: <reason> -->` that
  exempts the next non-empty non-comment line. Stacked sentinels
  are an error; trailing sentinel is an error; sentinels inside
  fenced ``` blocks are ignored. The sentinel mechanism ships
  carrying no live exemptions — the catalogue-attribution footer
  formerly at `packs/core/seeds/AGENTS.md` was removed in the same
  PR (per direction during EXECUTE) along with the corresponding
  line in the projected root `AGENTS.md`. Wired into
  `tools/hooks/pre-pr.py` and the `.github/workflows/docs.yml`
  `lint-seeds` job.
- [x] **AC22 (first-install snapshot test) — 2026-05-25 amendment;
  rescoped 2026-05-25 (same day; see Changelog ordering).**
  `packages/agentbundle/tests/integration/test_install_snapshot.py`
  parameterises over the four packs with seeds (`core`,
  `governance-extras`, `user-guide-diataxis`, `monorepo-extras`).
  *Naming note*: the test exercises `agentbundle scaffold`, not
  `agentbundle install` — `install` projects adapter-route content
  (`.claude/`, `apm/`) but does not project seeds. Seed projection
  is **route-agnostic** by construction: `agentbundle scaffold` is
  the only function that drops `packs/<pack>/seeds/` into an
  adopter tree, and neither the Claude-plugins build recipe
  (`per-pack-claude-plugin`) nor the APM build recipe
  (`per-pack-apm-package`) produces a `dist/<route>/<pack>/seeds/`
  subtree — verified by `make build` against all four packs at
  rescope time. The install→adapt chain (`agentbundle install` →
  in-process `agentbundle adapt`) does not invoke `scaffold` either.
  The cross-route invariant is therefore enforced at the **source**
  (`packs/*/seeds/`) by AC21's `tools/lint-seeds.py`, not at the
  per-route projection.
  *No continuous gate on the rescope premise.* The `dist/<route>/<pack>/`
  absence claim is a snapshot, not a CI-asserted invariant: `make
  build-check` enforces byte-equality of paths *that are projected*,
  not the *non-existence* of `seeds/` under those paths. A future PR
  that introduces per-route seed projection (e.g. landing the
  hypothetical RFC named below) would silently void this AC's rescope
  premise without tripping any existing gate. The defence is review
  discipline: any PR that adds a `dist/<route>/<pack>/seeds/` target
  must re-evaluate AC22 in the same change.
  For each pack, runs `agentbundle scaffold` into a fresh tempdir
  and asserts (i) the sorted list of scaffolded paths matches a
  checked-in golden at
  `packages/agentbundle/tests/fixtures/install_snapshot/<pack>.paths.txt`,
  (ii) the scaffolded content has no catalogue-specific leaks per
  the AC21 blocklist (sentinel-aware). Set `UPDATE_GOLDEN=1` to
  regenerate goldens when seed structure legitimately changes.
  *Scope history.* The 2026-05-25 amendment originally framed AC22
  as "per pack per install route" with Claude-plugins / APM route
  coverage deferred to a ROADMAP follow-on. That framing assumed a
  per-adapter seed-projection path that does not exist in the
  build pipeline today; the rescope (this revision) closes the
  follow-on as moot rather than building one. If a future RFC
  wires seed projection into the Claude-plugins or APM routes, AC22
  becomes a candidate for re-extension at that point — not before.
- [x] **AC23 (APPROACH→CHARTER fold-in) — 2026-05-25 amendment.**
  `docs/APPROACH.md`'s content folded into `docs/CHARTER.md` (Mission
  from "the wager" ¶1, Scope from "the wager" ¶2 + "what we left out",
  Principles verbatim from "the four principles"; "What's inside (and
  why)" and "Why this shape rather than the alternatives" sections
  dropped). Both `docs/APPROACH.md` (on-disk) and
  `packs/core/seeds/docs/APPROACH.md` (seed) are removed. CHARTER's
  Manual classification (per AC20) is what enables the fold-in
  without round-tripping the catalogue's mission into the seed.
  References to `docs/APPROACH.md` removed from
  `packs/core/seeds/docs/CONVENTIONS.md` (line 366 area, paired with
  AC19's broader rewrite) and `docs/specs/self-hosting/spec.md`
  (Phase-1 enumeration). Goal-based verification: both APPROACH paths
  absent; `docs/CHARTER.md` carries filled mission/scope/principles.

## Changelog

- 2026-06-10: restored Codex repo projection under self-host after the
  native-skills migration temporarily narrowed the allow-list. `make
  build-self` and `make build-check` again run both `claude-code` and
  `codex`, with Codex output enforced under `.agents/skills/`,
  `.codex/agents/`, and `.codex/hooks.json`.
- 2026-05-25: AC22 rescoped from "per pack per install route" to
  single-route (chronologically follows the same-day scaffold-leak
  closure entry below). The original 2026-05-25
  amendment named Claude-plugins and APM as deferred routes,
  tracking the gap in `docs/backlog.md`'s "AC22 install-route
  coverage extension" follow-on. Investigation against `make
  build` output confirmed no per-adapter seed-projection path
  exists today — `dist/claude-plugins/<pack>/` and
  `dist/apm/<pack>/` contain only the projected primitives
  (`.claude/`, `.apm/`, hook scripts, `pack.toml`, plugin/package
  manifests), no `seeds/` subtree; the install→adapt chain reads
  marker files but never invokes `scaffold`. Seed projection is
  route-agnostic by construction (only `agentbundle scaffold`
  drops `packs/<pack>/seeds/`), so per-route snapshots would have
  been performative — three runners ending at the same code path
  against the same source tree. AC22 wording rescoped to remove
  the "per install route" framing; the ROADMAP follow-on closed
  as moot in the same PR. A future RFC that wires seed projection
  into the Claude-plugins or APM routes would re-open AC22's route
  axis at that point. No production code touched.
- 2026-05-25: scaffold-leak closure (RFC-0002 § Amendments § 2026-05-25).
  Six items (a-f) executed in a single PR with the ordering DAG
  `(a) → (b) → (f); (a)(c) → (d)(e)`: (a) scrubbed 5 leaking seeds
  to placeholder shape; (b) shrank `PROJECTED_README_OVERRIDES`
  from 20 to 1 entry and added 8 explicit `EXCLUDED_PATTERNS`
  entries; (c) dropped 8 RFC-NNNN cross-references from
  `packs/core/seeds/docs/CONVENTIONS.md`; (d) shipped
  `tools/lint-seeds.py` with sentinel mechanism and per-file
  placeholder expectations; (e) shipped
  `tests/integration/test_install_snapshot.py` covering 4 packs ×
  `agentbundle scaffold` CLI route; (f) folded
  `docs/APPROACH.md` into `docs/CHARTER.md` and deleted both
  APPROACH copies. AC9 (seed READMEs are Projected) superseded;
  AC18-AC23 added covering the new contracts. The Phase-1
  enumeration in § *Phased rollout* was narrowed to list only
  `docs/CONVENTIONS.md` as a seed-projected path.
- 2026-05-24: AC15b added as a Phase-2 amendment — CLAUDE.md
  cross-shape equivalence in the drift detector. The three on-disk
  shapes (symlink → AGENTS.md, content-copy of AGENTS.md, regular
  file whose stripped content is `"AGENTS.md"`) are accepted as
  equivalent for the repo-root CLAUDE.md row only. Closes the
  cross-OS asymmetry the Windows CI matrix (PR #77) surfaced:
  macOS/Linux contributors keep the auto-following symlink
  ergonomics; Windows contributors run `make build-self` (or check
  out with Git for Windows in either symlink mode, including
  `core.autocrlf=true` which writes the materialised stub as
  `AGENTS.md\r\n`) without the drift gate failing on the alias
  shape. The amendment tightens parity with `lint-agents-md.py`
  check #2 — both now accept the same set of CLAUDE.md shapes via
  the same `strip()`-based literal-string test. Implementation in
  `self_host.py:_is_equivalent_claude_md_shape`; eight test cases
  under `ClaudeMdEquivalenceTests` cover the six shape pairings
  (symlink/copy shadow × symlink/copy/materialised disk) plus the
  tampering, missing-CLAUDE.md, and CRLF regression cases. The
  pre-existing `SymlinkTargetTests.test_matching_symlinks_no_drift`
  was retargeted from CLAUDE.md to a non-CLAUDE.md filename so it
  exercises the Phase-2 strict path rather than the new
  short-circuit (which would mask a future regression).
- 2026-05-24: `docs/_templates/` directory retired. Templates
  (`spec.md`, `plan.md`, `adr.md`, `rfc.md`, `state.json`, plus the
  directory's `README.md`) moved into the `assets/` folder of the
  skill that creates instances of each — `new-spec`, `new-adr`,
  `new-rfc`, `work-loop`. This complies with the agentskills.io
  spec's skill-layout convention (skills are self-contained units
  with `references/` for read-on-demand material and `assets/` for
  material the skill copies elsewhere). AC9's seed-README
  enumeration was edited to remove `docs/_templates/`; the
  byte-equality gate it describes is unchanged in semantics.
- 2026-05-23: Phase-2 AC8 closed. Codex now aggregates skill
  descriptions across every discovered pack before splicing the
  `AGENTS.md` managed block, self-host runs both `claude-code` and
  `codex`, and `make build-self` composes root `AGENTS.md` from
  `packs/core/seeds/AGENTS.md`, the Codex-managed block, and
  `packs/core/seeds/_agents-footer.md`. Focused unit tests and
  `make build-check` passed. Comparison-rule strengthening remains
  open.
- 2026-05-22: typo-class amendment after Phase 1 ship — adapter
  contract files relocated from `docs/specs/adapter-contract/` to
  `docs/contracts/` (path-only; field semantics and acceptance
  criteria unchanged). See
  [RFC-0001 § Amendments](../../rfc/0001-bundle-distribution-by-adapter-spec.md#amendments)
  for the full rationale and the `CONVENTIONS.md:80` exception note.
- 2026-05-23: AC12 implementation migrates from reading [adapt] to reading [markers] per docs/specs/adapt-to-project/spec.md; AC12 contract unchanged.
- 2026-05-23: Phase 2 closed. `diff_against_working_tree` strengthens
  the comparison along the three rules the spec named: CRLF→LF
  normalisation for text-like files (UTF-8-decodable inputs only),
  file-mode permission-bit comparison for regular files (low 9 bits;
  setuid/setgid/sticky out of scope), and symlink-target comparison
  via `lstat` — never following the link. Implementation in
  `packages/agentbundle/agentbundle/build/self_host.py`; per-rule
  unit tests + one integration test pairing each rule with the
  regression it was added to catch live in `tests/test_self_host_check.py`
  under `CrlfNormalisationTests`, `FileModeBitsTests`,
  `SymlinkTargetTests`, and `StrengthenedDiffRegressionIntegrationTests`.
  Status flips to Shipped — no Phase 3.
