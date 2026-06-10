# Plan: self-hosting

- **Spec:** [`spec.md`](spec.md)
- **Status:** Shipped

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

> **Phase-1 / Phase-2 reading guide (EXECUTE-time amendment, updated
> in the easy-Phase-2-lift fix-pass).** Task bodies below (T1–T7) were
> authored pre-EXECUTE against the original spec scope. The
> 2026-05-22 (EXECUTE) and 2026-05-22 (EXECUTE fix-pass) changelog
> entries partition the scope. When reading T1–T7:
>
> - **In Phase 1** (this PR): adapter-driven `.apm/` primitive
>   projection (skills, agents, commands, hooks, hook-wiring via the
>   Claude Code adapter), seed projection (`packs/*/seeds/**` →
>   repo root, with file-level collision detection), root
>   marketplace aggregation
>   (`.claude-plugin/marketplace.json`), `CLAUDE.md → AGENTS.md`
>   symlink recreation, missing-discovery-file fail-fast,
>   drift-message source-path + regen-command naming,
>   `[info]` lines for unclassified paths, and `.adapt-discovery.toml`
>   marker resolution across the widened scope.
> - **Phase 2 (closed):** AGENTS.md body+footer composition + Codex
>   multi-pack managed-block splice closed by the 2026-05-23 AC8
>   pass; comparison-rule strengthening (LF normalisation, file-mode
>   bits, symlink-target via `lstat`) closed by the 2026-05-23 final
>   pass per the Changelog. No Phase 3.
> - CLI surface in task bodies uses RFC-0002's flag form (`--self`,
>   `--force`, `--dry-run`). The on-disk Makefile equivalents are
>   `make build-self`, `make build-self FORCE=1`, and
>   `make build-self DRY_RUN=1` per spec drafting-drift note item 5.
>
> Spec § Phased rollout names the partition; this plan reading guide
> applies it to the task-body details so the plan tracks reality
> without re-writing every bullet.

## Approach

The plan executes RFC-0002's four-step migration on top of RFC-0001's
build pipeline. **T1 cannot start until the sibling distribution-adapters
spec lands its enumerated-set Acceptance Criterion under § *Recipe set*
(pinning the six recipe types including the three composite types this
spec needs) and its Tier-1/2/3 contract definition in this same
coordinated update.** Sibling AC numbers may shift across reviewer
passes; this plan cites by description rather than number, and the
orchestrator reconciles after both fix-passes merge.
The build pipeline lives at `packages/agentbundle/agentbundle/build/`
with a thin shim at `tools/build/build.py`; user-facing entry points
are `make build-self` and `make build-check`. Once the sibling
amendments and pipeline machinery exist, the self-host work is:
(1) author the four packs, (2) write the `self-host.toml` recipe using
the three composite section types defined in the distribution-adapters
spec, (3) author `.adapt-discovery.toml` so `make build-self` can
resolve this repo's `<adapt:NAME>` markers as the final build step,
(4) reconcile pack-side sources until `make build-self DRY_RUN=1` is
a byte-identical no-op, (5) flip the cutover commit, then (6) wire
`make build-check` as a required CI status and amend
`docs/CONVENTIONS.md`. The riskiest piece is the reconcile loop —
every inadvertent whitespace, line-ending, or ordering delta between
the current hand-maintained projection and the pack-side source
surfaces as drift. The migration PR pays that cost once.

## Constraints

- [RFC-0002](../../rfc/0002-self-hosting.md) — source-of-truth split,
  the `--self` flag's semantics, the `make build-check` CI gate, the
  `self-host.toml` recipe shape, and the migration plan. RFC-0002's
  *Projected* and *Excluded* tables are the load-bearing list this plan
  implements.
- [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md) — the
  adapter contract and build pipeline this plan depends on. The
  distribution-adapters sibling spec at
  [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  defines `pack.toml`, `.claude-plugin/plugin.json`, and the recipe
  schema. This plan references those without redefining them.
- [`docs/CONVENTIONS.md`](../../CONVENTIONS.md) — the pack source-of-truth
  split lands as an amendment in the migration PR (T6 below); RFC-0002
  authorises this without a separate RFC.

**Cross-spec dependency:** tasks below cite distribution-adapters task
IDs directly. The sibling spec's tasks are: T1a (adapter contract +
schemas), T1b (`pack.toml` schema), T1c (`plugin.json` schema), T2
(Claude Code adapter), T3 (Kiro adapter), T4 (Copilot adapter), T5
(Codex adapter), T6 (build pipeline + recipe dispatch covering all
six recipe types), T7 (`make build-self DRY_RUN=1` + comparison
gate machinery), T8 (Makefile surface + `make build-check`), T9
(stdlib-only + no-new-top-level audit). The minimum dependency set
for each self-hosting task is named under its `Depends on:` field.

## Construction tests

Most construction tests live under each Task's `Tests:` subsection.
The cross-cutting ones:

**Integration tests:**

- End-to-end self-host smoke: from a clean checkout post-cutover,
  `make build-self` exits 0 with `git status --porcelain` empty.
- End-to-end drift detection: introduce a one-character edit to a
  projected path (e.g. `.claude/skills/work-loop/SKILL.md`), run `make
  build --check`, assert non-zero exit and a `[drift]` line naming the
  pack-side source.
- End-to-end forward-flow: introduce a one-character edit to the
  pack-side source for the same file, run `make build-self`, assert
  the projected path is updated to match, assert `make build-check`
  is then clean.

**Manual verification:**

- Acceptance Criterion 3's first-real-edit gesture (recorded PR URL in
  the spec's manual-QA artifact list).
- Visual inspection of the migration PR's `docs/CONVENTIONS.md` diff.

## Tasks

### T1: Pack sources authored under `packs/*/`

**Depends on:** `distribution-adapters` T1a (adapter contract +
schemas), T1b (`pack.toml` schema), T1c (`plugin.json` schema).

**Tests:**

- Per-pack: `pack.toml` parses against the adapter contract's schema
  (goal-based, invokes the sibling spec's validator from F-spec).
- Per-pack: `.claude-plugin/plugin.json` parses against the schema
  defined in the sibling spec (goal-based).
- Hand-extracted skill / agent / hook files retain their existing test
  coverage (TDD, unchanged tests still green post-move).
- Verifies Acceptance Criterion: pre-requisite for the no-op build.

**Approach:**

- For each pack (`core`, `governance-extras`, `user-guide-diataxis`,
  `monorepo-extras`), per RFC-0002's *Migration plan* step 1:
  - Move skills into `packs/<pack>/.apm/skills/<name>/`.
  - Move agents into `packs/<pack>/.apm/agents/<name>.md`.
  - Move hook bodies into `packs/<pack>/.apm/hooks/<name>.<ext>`
    preserving today's source extension. Today's hooks ship as `.sh`
    under `tools/hooks/`; they move as `.sh`. The `[primitive.hook-body]`
    projection in the distribution-adapters spec preserves the source
    extension, so future `.py` hooks are equally valid. No conversion
    happens in this migration.
  - Move commands: `.claude/commands/<name>.md` →
    `packs/<pack>/.apm/commands/<name>.md` (RFC-0002 *Migration plan*
    step 1 calls out `.claude/commands/conventions-check.md` →
    `packs/core/.apm/commands/conventions-check.md` explicitly).
    The sibling spec defines `command` as a first-class primitive
    with a Claude Code projection back to `.claude/commands/`.
  - Move hook wiring: each entry under the `hooks` key of
    `.claude/settings.local.json` →
    `packs/<pack>/.apm/hook-wiring/<name>.toml` (one TOML per hook).
    The sibling spec defines `hook-wiring` as a first-class primitive;
    the Claude Code adapter projects these back via `merge-json` into
    the `hooks` key of `.claude/settings.local.json`. Per-instance
    keys in `.claude/settings.local.json` (everything outside the
    `hooks` key) remain Source category.
  - Move seed content (`AGENTS.md`, `docs/CHARTER.md`,
    `docs/CONVENTIONS.md`, template files, seed READMEs) into
    `packs/<pack>/seeds/...`. Seed paths use the repo's singular
    convention: `docs/rfc/` and `docs/adr/`, not `docs/rfcs/` or
    `docs/adrs/`. Normalise any drafting-drift names from RFC-0002
    during the move; T5 verifies no plural paths remain under
    `packs/*/seeds/`.
  - Write `pack.toml` with `[pack.metadata]`, `[pack.adaptation]`, and
    `recommends` per RFC-0002's enumeration.
  - Write `.claude-plugin/plugin.json` per the sibling spec's schema.
- Write `packs/core/seeds/_agents-footer.md` containing the
  `AGENTS.local.md` pointer line (the working assumption in RFC-0002's
  *Unresolved questions* #1, adopted as the spec's commitment).
- Move repo-specific contributor paragraphs out of the current
  `AGENTS.md` into a new root `AGENTS.local.md` (Source category).

**Done when:** every pack directory under `packs/` has its `pack.toml`,
`.claude-plugin/plugin.json`, and the `.apm/` + `seeds/` content
RFC-0002 enumerates. `AGENTS.local.md` exists at the repo root.

### T2: `self-host.toml` recipe authored against distribution-adapters' six-recipe set

**Depends on:** T1, `distribution-adapters` T1c (`plugin.json` schema —
T2 below loads and aggregates `plugin.json` files), T2 (Claude Code
adapter), T5 (Codex adapter), T6 (recipe loader + dispatch covering
all six recipe types per the sibling spec's enumerated-set Acceptance
Criterion under § *Recipe set*).

**Tests:**

- TDD: `[recipe.per-pack-overlay]` iterates `packs/*/`, copies
  `.apm/skills/`, `.apm/agents/`, `.apm/hooks/` to the configured
  targets; copies `seeds/**` to the repo root at seed-relative paths.
- TDD: file-level collision between two packs' `seeds/` trees (same
  target path, different content) produces a non-zero exit with both
  source paths named. Verifies Acceptance Criterion 7.
- TDD: `[recipe.composite-agents-md]` composes the projected root
  `AGENTS.md` from BOTH `packs/core/seeds/AGENTS.md` (body) AND
  `packs/core/seeds/_agents-footer.md` (footer, appended after body),
  invokes the Codex adapter for the managed block where the contract
  declares one, writes the assembled file to the configured output
  path. Two assertions: (a) the head of the projected file matches the
  body source; (b) the tail of the projected file matches the footer
  source byte-for-byte after LF normalisation. Verifies Acceptance
  Criterion 8.
- TDD: `[recipe.composite-marketplace]` reads
  `packs/*/.claude-plugin/plugin.json` and emits
  `.claude-plugin/marketplace.json` with the aggregated entries and the
  configured `owner` block.
- TDD: section execution order follows source order in the recipe TOML.

**Approach:**

- Author `packages/agentbundle/agentbundle/build/recipes/self-host.toml`
  per RFC-0002's *The self-build command* section, verbatim shape.
- The distribution-adapters spec's enumerated-set Acceptance
  Criterion under § *Recipe set* pins all six recipe types (the three
  RFC-0001 types plus the three composite types this recipe uses);
  the pipeline implementation recognises them per that spec's T6.
  No extension point is needed on this side.
- Wire the Claude Code adapter (for `.claude/` projection) and the
  Codex adapter (for `AGENTS.md`'s managed block) per
  `[recipe.adapters].targets`.

**Done when:** unit tests above are green. The build pipeline accepts
`self-host.toml` and produces output into a temp directory without
error against the T1 pack sources.

### T3: `--self` CLI flag, dirty-tree refusal, `--force` semantics, `.adapt-discovery.toml`

**Depends on:** T2, `distribution-adapters` T7 (`--self --dry-run`
machinery), T8 (Makefile + `--check` surface).

**Tests:**

- TDD: `make build-self` on clean tree exits 0; output root is the
  repo (not `dist/`); recipe selection is implicit (`self-host.toml`).
- TDD: `make build-self` on dirty tree exits non-zero with a stderr
  line containing the named dirty-tree refusal reason. Verifies
  Acceptance Criterion 4.
- TDD: `make build-self FORCE=1` on dirty tree proceeds; the
  byte-equality comparison still runs (no bypass). Verifies Acceptance
  Criterion 4.
- TDD: `make build` without `--self` writes to `dist/` (the existing
  distribution build is preserved).
- TDD: with `.adapt-discovery.toml` present, `make build-self`
  resolves every `<adapt:NAME>` marker in source to its repo-local
  concrete value as the final build step (per the distribution-adapters
  spec's Acceptance Criterion for `make build-self`, which pins that
  `--self` writes to the tree, resolves markers, refuses dirty trees
  without `--force`, and honours on-conflict). Without the file, the
  build fails fast with a stderr message in the form
  `missing .adapt-discovery.toml required by --self`.
- TDD: marker resolution runs only under `--self`. `make build` (no
  `--self`) copies `<adapt:NAME>` markers through unchanged.

**Approach:**

- The `--self` flag, dirty-tree refusal, and `--force` semantics are
  implemented in `distribution-adapters` T7 / T8. This task verifies
  the behaviour from the self-host vantage and pins the
  `.adapt-discovery.toml` exception for this repo.
- Author `.adapt-discovery.toml` at the repo root with the concrete
  values for every `<adapt:NAME>` marker that appears in
  `packs/*/seeds/` (project name, repo URL, owner, etc.). The resolver
  itself belongs to the deferred `adapt-to-project` skill; here we
  materialize the config.
- `--force` flag toggles only the dirty-tree refusal; the comparison
  gate is unconditional.

**Done when:** the unit tests above are green; the existing
distribution build (no `--self`) continues to write into `dist/`;
`<adapt:NAME>` markers in source resolve to repo-local values only
under `--self`.

### T4: `make build-check` gate behaviour

**Depends on:** T2, `distribution-adapters` T7 (`--check` command),
T8 (Makefile surface).

**Tests:**

- TDD: byte-equality after LF normalisation — a file with CRLF on disk
  and LF in source produces no drift; same content with extra trailing
  space drifts.
- TDD: CRLF + `git status` interaction — a CRLF-on-disk file passes
  the gate (the gate normalises before comparison) but produces a
  `git status` line because `git status` does not normalise. Documents
  the `core.autocrlf` expectation for contributors on Windows.
- TDD: file mode comparison for regular files — `0755` on disk vs
  `0644` projected drifts.
- TDD: symlink target comparison via `lstat` — `CLAUDE.md → AGENTS.md`
  on disk vs `CLAUDE.md → README.md` projected drifts; the gate never
  follows the link.
- TDD: missing-on-disk drift — a *Projected* path with no on-disk
  counterpart produces drift labelled "expected projected output, none
  on disk".
- TDD: enumeration uses `git ls-files --cached --others
  --exclude-standard`; gitignored editor scratch in the worktree does
  not surface.
- TDD: unclassified paths (neither *Projected* nor *Excluded*) emit
  `[info]` lines on stderr and do not fail the build. Verifies
  Acceptance Criterion 6.
- TDD: drift failure message names the source path and the
  regeneration command, per the example in RFC-0002 § Round-trip
  safety.
- TDD (regression): a fixture injects drift on a projected path;
  `make build-check` exits non-zero regardless of `--force` or any
  other flag combination. The gate has no bypass surface.
- Goal-based (CI lint): `grep -E 'skip|bypass|SKIP_'` over the build
  code under `packages/agentbundle/agentbundle/build/` fails CI if any
  unguarded exit branch with those tokens is introduced.
- Goal-based: `.github/workflows/build-check.yml` exists and runs
  `make build-check` on PRs targeting `main`; the workflow exits 0
  when the projection is up-to-date. Verifies Acceptance Criterion 1a.

**Approach:**

- Implement `make build-check` as a separate sub-command (or as
  `make build-check` — settle in T3's CLI design, but the
  externally-named contract is `make build-check`). The
  implementation lives in `packages/agentbundle/agentbundle/build/`;
  `tools/build/build.py` is a thin shim.
- Implementation: project into a temp directory, walk the *Projected*
  table, compare per the rules above. Failure path emits one `[drift]`
  block per drifting path, naming source and re-run command.
- Wire into `.github/workflows/build-check.yml`. Registering the
  workflow as a required status check on `main` is Acceptance
  Criterion 1b and is recorded by manual QA in T6.

**Done when:** unit tests above are green; a deliberately-introduced
drift on a feature branch produces a red CI status (covers Acceptance
Criterion 1a); the `--force` regression test and the `grep` lint both
fail CI when violated.

### T5: Reconcile pack-side sources until `make build-self DRY_RUN=1` is a byte-identical no-op

**Depends on:** T1, T2, T3, T4 (no additional sibling-spec deps
beyond those carried by T1–T4).

**Tests:**

- Goal-based: `make build-self DRY_RUN=1` on the feature branch
  exits 0 and reports zero would-be-changed paths.
- Goal-based: integration test under *Construction tests* above
  (drift introduction + forward-flow) passes locally.
- Goal-based (path-normalisation): no `docs/rfcs/` or `docs/adrs/`
  paths remain under `packs/*/seeds/` (covering the singular/plural
  drafting drift in RFC-0002). Verified by a `find packs -path
  '*seeds*' \( -path '*/docs/rfcs/*' -o -path '*/docs/adrs/*' \)`
  one-liner returning empty.

**Approach:**

- Per RFC-0002's *Migration plan* step 2: iterate edit-projection-diff
  on `packs/*/.apm/` and `packs/*/seeds/` until projected output
  matches on-disk content under LF-normalised byte rule.
- Expected delta sources: trailing whitespace, line endings, list
  ordering, header capitalisation, missing front-matter, missing
  `_agents-footer.md` content. Each is paid once.
- The repo's own RFC/ADR/spec entries (e.g. this spec) stay Manual at
  the projected paths; do not migrate them into `packs/`. Confirm by
  enumerating `docs/rfc/NNNN-*.md`, `docs/adr/NNNN-*.md`,
  `docs/specs/<feature>/*` against the *Excluded* table.

**Done when:** `make build-self DRY_RUN=1` reports zero changes;
`git diff` against base shows only `packs/`,
`packages/agentbundle/agentbundle/build/` (and the `tools/build/`
shim), and adapter-contract edits.

### T6: Cutover commit, `docs/CONVENTIONS.md` amendment, CI gate required

**Depends on:** T5.

**Tests:**

- Goal-based: post-merge, `make build-self` on `main` exits 0 with
  `git status --porcelain` empty. Verifies Acceptance Criterion 2.
- Manual QA: post-merge, `make build-check` is registered as a
  required status check on branch protection for `main`. Artifact: the
  output of `gh api repos/{owner}/{repo}/branches/main/protection`
  showing the workflow's job under
  `required_status_checks.contexts` (or a screenshot). Verifies
  Acceptance Criterion 1b.
- Goal-based: `docs/CONVENTIONS.md` contains a section heading
  `§ Pack source-of-truth split`; the section text mentions both
  `packs/*/.apm/` and `packs/*/seeds/` as upstream sources for
  projected paths; it cites RFC-0002 as the authority; it cites
  `make build-check` as the enforcing gate. Each claim is verified
  by a separate `grep` one-liner. Verifies Acceptance Criterion 5.
- Goal-based: the projected root `AGENTS.md` is composed from BOTH
  `packs/core/seeds/AGENTS.md` (head matches body source) AND
  `packs/core/seeds/_agents-footer.md` (tail matches footer source,
  appended after the body, after LF normalisation). Verifies
  Acceptance Criterion 8.
- Goal-based: every seed README path under `docs/architecture/`,
  `docs/specs/`, `docs/knowledge/`, `docs/product/`, `docs/guides/`,
  `docs/rfc/`, `docs/adr/`, and `packages/` listed in RFC-0002's
  *Projected* table exists on disk and matches its pack-side source
  under the gate's comparison rules. Verifies Acceptance Criterion 9.

**Approach:**

- Per RFC-0002's *Migration plan* step 3: run `make build-self` for
  real; commit the result. The commit records that projected content
  matches source.
- Amend `docs/CONVENTIONS.md` to describe the pack source-of-truth
  split (a new sub-section under § *Document hierarchy* or a sibling
  section, whichever the reviewer prefers). Cite RFC-0002.
- Per RFC-0002's *Migration plan* step 4: flip `make build-check`
  to *required* in branch protection for `main`. **PR ordering is
  pinned:** T6's main PR closes Acceptance Criterion 1a (the workflow
  file exists and runs green); Acceptance Criterion 1b's branch-
  protection artifact (the `gh api
  repos/<repo>/branches/main/protection` output showing `make build
  --check` under `required_status_checks.contexts`) is captured
  *after merge* during the Rollout step and recorded against this
  plan's Changelog — it is not part of T6's PR diff, because branch
  protection cannot be configured by a PR that hasn't merged yet.
- Update `docs/specs/README.md` to mark this spec as Implementing
  (then Shipped after T7).

**Done when:** the post-merge `make build-self` no-op check passes
on `main`; the `docs/CONVENTIONS.md` amendment is present with all
four claims; the `AGENTS.md` composition check passes; the seed
README byte-equality check passes. Acceptance Criterion 1a is
closed by this task's PR; Acceptance Criterion 1b's artifact is
recorded in the post-merge Rollout step.

### T7: First real pack-side edit lands through the pipeline

**Depends on:** T6.

**Tests:**

- Manual QA: per the spec's *Testing Strategy*, make a small
  observable edit to a `packs/*/` source, run `make build-self`,
  commit, open PR, verify `make build-check` green, merge. Record
  the PR URL in this plan's changelog and in the spec's Acceptance
  Criterion 3 artifact.
- Construction (direct-edit-bounces): on a feature branch, make a
  one-character edit to a *Projected* path (not its source); run
  `make build-check`; assert non-zero exit and a `[drift]` line.
  Verifies the gate *enforces*, not merely *runs*. Pair with the
  forward-flow integration test in *Construction tests* above to
  confirm round-trip safety end-to-end on the real repo.

**Approach:**

- Pick a low-stakes edit. Candidates: a one-sentence addition to
  `packs/core/seeds/docs/CHARTER.md`'s principles, a typo fix in
  `packs/core/.apm/skills/work-loop/SKILL.md`, a clarification in a
  seed README.
- The point is not the edit's content; it's that the muscle-memory
  works end-to-end and the CI gate is observed green on a real PR.

**Done when:** PR is merged to `main` and its URL is recorded under
*Changelog* below and in spec.md's Acceptance Criterion 3 artifact
list.

## Rollout

One-shot, forward-only. RFC-0002's *Migration plan* step 3 is the
cutover; there is no grace period. After T6, all bundle changes flow
through `packs/*/`; the CI gate enforces this. Reversal would mean
re-vendoring the hand-maintained projections as canonical (which loses
the structural property RFC-0002 exists to gain) or accepting
build-derived output as the new floor. Plan for forward only.

CI workflow flips to *required* in branch protection at T6. Until
that flip, the gate runs but does not block — informational only.
The flip is the moment self-hosting becomes load-bearing. The flip
itself is configured against the merged `main` branch through the
GitHub repo settings UI (or `gh api ... -X PATCH`); the artifact
that closes Acceptance Criterion 1b is the output of
`gh api repos/<repo>/branches/main/protection` showing
`make build-check` under `required_status_checks.contexts`,
captured after the flip and recorded in this plan's Changelog and
in spec.md's Acceptance Criterion 1b artifact field. This step is
explicitly post-merge — Acceptance Criterion 1b is not closed by
T6's PR diff.

## Risks

- **Reconciliation effort exceeds estimate.** RFC-0002 estimates a
  half-day for T5's reconcile loop. Whitespace / line-ending / list-
  ordering deltas may compound across the four packs. Mitigation: if
  T5 stretches past two days of triage, stop and split — land the
  least-divergent pack first (likely `monorepo-extras` since it's
  smallest), then the others in subsequent PRs.
- **Recipe-schema bikeshed.** The six-recipe set is enumerated in the
  distribution-adapters spec, but exact field shapes inside
  `[recipe.composite-agents-md]` and `[recipe.composite-marketplace]`
  may shift during T2 as the recipe is exercised against real pack
  sources. Mitigation: track shape changes in the
  distribution-adapters spec; this spec consumes whatever shape lands
  and adjusts `self-host.toml` accordingly. No new section types
  introduced here.
- **CI gate latency.** Re-running the build pipeline and walking every
  projected path adds seconds to every PR. Implementation cost
  negligible per RFC-0002 § *Drawbacks*; if it grows past ~30s,
  cache the temp-directory projection across CI runs.
- **`.adapt-discovery.toml` correctness.** `make build-self`
  resolves `<adapt:NAME>` markers using this file; if a marker in
  source has no entry, the build fails fast (T3 test). Risk is human:
  someone introduces a new marker in `packs/*/seeds/` without updating
  `.adapt-discovery.toml`. Mitigation: T3's missing-config test catches
  this on PR; reviewers add the corresponding entry in the same PR.

## Changelog

- 2026-06-10: restored the Codex side of self-host projection as a
  follow-up to the native-skills migration. `SELF_HOST_ADAPTERS` again
  contains `claude-code` and `codex`; the dry-run clone surface now
  includes `.codex/` and `.agents/`; tests pin `.agents/skills/`,
  `.codex/agents/`, and `.codex/hooks.json` as drift-gated outputs.
- 2026-05-23: Phase 2 closed. Comparison-rule strengthening landed:
  CRLF→LF normalisation for text-like files, file-mode permission-bit
  comparison for regular files, and symlink-target comparison via
  `lstat` (never following). Implementation in
  `agentbundle/build/self_host.py::diff_against_working_tree`; per-rule
  unit tests (`CrlfNormalisationTests`, `FileModeBitsTests`,
  `SymlinkTargetTests`) plus one integration test
  (`StrengthenedDiffRegressionIntegrationTests`) pairing each rule
  with the regression it was added to catch. All 40
  `test_self_host_check.py` cases green; `make build-check` clean.
  Plan status flips to Shipped.
- 2026-05-23: executed the Codex-dependent Phase-2 slice for AC8.
  Added Codex multi-pack aggregation before managed-block splicing,
  widened `SELF_HOST_ADAPTERS` to `claude-code` + `codex`, materialised
  `packs/core/seeds/AGENTS.md`, and wired self-host `AGENTS.md`
  composition as body + Codex-managed skills block + footer. Focused
  unit tests and `make build-check` passed. The comparison-rule
  strengthening task remained open at the time and was closed in the
  follow-up entry above.
- 2026-05-22: initial plan.
- 2026-05-22: applied cross-cutting decisions CC1–CC6 (canonical
  spec directory `docs/specs/self-hosting/`; singular `docs/rfc/` /
  `docs/adr/` paths; the literal CONVENTIONS heading is
  `## Pack source-of-truth split`; recipes live under
  `packages/agentbundle/agentbundle/build/recipes/`; hook source
  extensions `.sh` and `.py` both valid; `<adapt:NAME>` resolution
  scoped to `make build-self`). Applied adversarial-reviewer
  pass-1 findings (T1 hook-extension preservation, T3
  `.adapt-discovery.toml` and missing-config failure semantics, T6
  branch-protection artifact, composite-recipe field flux risk).
  Applied adversarial-reviewer pass-2 findings (cite sibling ACs
  by description rather than number; add `command` and
  `hook-wiring` primitives to T1 migration; add T1c to T2's
  Depends-on; pin AC1a/AC1b PR ordering with the branch-protection
  artifact captured post-merge in Rollout; extend the
  drafting-drift note to cover stale recipe path and `.py`-only
  hook references in RFC-0002; add ACs anchoring marker
  resolution under `--self` with the stderr failure message
  format).
- 2026-05-22 (post-merge, AC3): first real pack-side edit landed
  through the pipeline.
  [PR #20](https://github.com/eugenelim/agent-ready-repo/pull/20)
  (merge commit `92735a1`) edited
  `packs/core/seeds/docs/architecture/README.md` (a one-paragraph
  pointer to the source-of-truth split convention) and re-projected
  to `docs/architecture/README.md` via `make build-self`. The
  required `make build-check` gate ran green on the PR before merge.
  AC3 closed.
- 2026-05-22 (post-merge, AC1b): registered `make build-check` as a
  required status check on `main` via
  `gh api -X PUT repos/eugenelim/agent-ready-repo/branches/main/protection`.
  Config: `required_status_checks.strict = true`,
  `required_status_checks.contexts = ["make build-check"]`,
  `enforce_admins = false`, no required PR reviews, no push
  restrictions. Artifact captured at
  `docs/specs/self-hosting/notes/ac1b-branch-protection.json`. AC1b
  closed.
- 2026-05-22 (EXECUTE fix-pass): user requested follow-up additions to
  the same PR. Lifted from Phase 2 to Phase 1: seed projection
  (`_project_seeds` with collision check), marketplace aggregation
  (`_aggregate_marketplace`), CLAUDE.md symlink recreation
  (`_recreate_claude_symlink`), missing-discovery-file fail-fast (exit
  3), drift-message source-naming
  (`_build_projected_to_source_map` + `_lookup_source`), and `[info]`
  lines for unclassified paths (git-tracked + untracked-not-ignored
  enumeration). ACs 6, 7, 9, 14 → Phase 1; new ACs 15
  (CLAUDE.md), 16 (marketplace), 17 (drift source-naming) added.
  AC8 (AGENTS.md composition — needs Codex multi-pack fix) and the
  comparison-rule strengthening (LF norm / mode / lstat) stay
  Phase 2. Authored missing seed READMEs
  (`docs/architecture/README.md`, `docs/_templates/README.md`,
  `packages/README.md`) and `_agents-footer.md`. Real-write created
  `.claude-plugin/marketplace.json` and `CLAUDE.md` symlink at the
  repo root. 131/131 tests pass (+12 new); dry-run + build-check
  exit 0 against the live repo's `packs/`.
- 2026-05-22 (EXECUTE): discovered that the sibling
  distribution-adapters spec landed the three composite recipe types
  (`per-pack-overlay`, `composite-agents-md`, `composite-marketplace`)
  as metadata-only TOMLs without runtime; that the Codex adapter's
  managed-block splice is last-pack-wins across multiple packs (so a
  multi-pack AGENTS.md projection is incorrect today); and that seed
  projection / root marketplace aggregation / CLAUDE.md symlink
  recreation are not implemented in `self_host.py`. Spec amended to
  partition into **Phase 1** (adapter-driven `.apm/` primitives only;
  closed by this PR) and **Phase 2** (seed projection, AGENTS.md
  composition, marketplace, symlink — follow-up PR). Tasks: T1–T6
  closed at Phase-1 scope in this PR; T5 reconciles trivially because
  the only adapter that fires is `claude-code` and packs/ was
  scaffolded as literal copies. AC6/7/8/9/14 tagged Phase 2 with the
  reason inlined under each. Makefile target form (`make build-self`,
  `make build-check`) replaces RFC-0002's `make build --self` /
  `make build --check` references (item 5 in the spec's drafting-drift
  note); `FORCE=1` and `DRY_RUN=1` are the variable equivalents of
  the original `--force` / `--dry-run` flags.
- 2026-05-22: adapter contract files moved from
  `docs/specs/adapter-contract/` to `docs/contracts/` (flat layout,
  `<name>.schema.json` suffix). Spec line 120 updated; field
  semantics unchanged. See
  [RFC-0001 § Amendments](../../rfc/0001-bundle-distribution-by-adapter-spec.md#amendments).
