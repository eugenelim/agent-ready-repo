# Spec: Self-host projection merge driver

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material.

## Objective

A maintainer merging or rebasing one branch onto another never resolves a
conflict in a file the self-host pipeline generates. Git settles those paths
without halting and without emitting conflict markers, and `make build-self`
regenerates them from the merged pack sources. Which side git keeps does not
matter and is not specified: the content is regenerated either way, so the
contract rests on convergence after regeneration rather than on a surviving
side. Conflicts in pack sources under `packs/**/.apm/` and `packs/**/seeds/`
still surface normally, because those carry the decisions a human has to make.

The people this serves are the maintainers working across this repository's
parallel worktrees. One edit to a core-pack skill currently lands as three or
four committed copies under `.claude/`, `.agents/`, and `packs/core/.apm/`, so
two branches touching the same skill conflict in every copy. The textual merge
is meaningless there: the copies are a pure function of their source, so the
only correct resolution is to regenerate them.

Correctness does not rest on the merge result. `make build-check` already
refuses a stale projection through its self-host drift check and its
packaged-runtime byte-identity check, both required inside `gate-main`. The
driver removes a pointless conflict; the gate remains the guarantee.

A path is eligible only where one of those gates covers it, so the eligible
set is smaller than the projected set. `tools/hooks/*.py` is a genuine
projection that no gate covers; those three files stay out and keep conflicting
normally. Accepting that lowered coverage is deliberate — closing it means
editing the exclusion list in `agentbundle` build code, a larger change than
this one. The repo-root `CLAUDE.md` symlink stays out for an unrelated reason:
git applies no content merge driver to a symlink blob, so declaring one would
have no effect.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the merge-then-regenerate workflow is a new maintainer obligation | `AGENTS.local.md` § Landing changes | Repository maintainers | The section states the `merge → make build-self → commit --amend` sequence and that automation never passes `FORCE=1` | Section names the sequence and the dirty-tree refusal |
| Maintainer procedure | Applicable — a new clone must register the driver before the driver has any effect | `AGENTS.local.md` § Worktree bootstrap | Repository maintainers | The section names `make bootstrap-git` and states that git config is shared across worktrees but not across clones | Section names the target and the per-clone scope |
| Current architecture | Applicable — the projected-path list gains a second consumer, and two of its entries are wrong | `docs/CONVENTIONS.md` § Pack source-of-truth split, edited via `packs/core/seeds/docs/CONVENTIONS.md` | Repository maintainers | The Projected-paths list notes which paths carry `merge=regen`; corrects the `tools/hooks/<name>.<ext>` entry to record that no drift gate covers it; and corrects the claim that the non-`CONVENTIONS.md` seed-projected paths were reclassified Manual, which is wrong for `AGENT_RULES.md`, `docs/AGENTS.md` and `governance/manifest.example.yaml` | All three edits present, and source seed and projection byte-identical after `make build-self` |
| Release history | Applicable — correcting the seed changes shipped pack content, which bumps `packs/core` and makes that bump a released artifact | `docs/product/changelog.md`, a free-standing `## [core][<version>]` section | Repository maintainers | The entry exists at top level beneath `[Unreleased]`, with a `Highlights` block, because the correction changes what an adopter's installed conventions tell them | Entry present at the released version, and the version matches `packs/core/pack.toml` |
| Decision rationale | Not applicable | — | — | — | The driver mechanically enforces the existing "edit sources, not projections" convention rather than establishing a new one; confirmed with the owner 2026-09-12 |
| Interface compatibility | Not applicable | — | — | — | No published interface changes; `.gitattributes` is Manual and is not seeded to adopters |

## Boundaries

### Always do

- Settle the eligibility question from the gates, never from a second
  hand-maintained list.
- Keep pack sources under `packs/**/.apm/` and `packs/**/seeds/` out of the
  driver so their conflicts still surface.
- Run `make build-self` after any merge that the driver auto-resolved, and
  before committing.

### Ask first

- Adding a `merge=regen` pattern for any path the rail check in AC1 does not
  already cover.
- Registering the driver by any route that writes to a projected file, since
  that converts this change into a pack-source change.
- Changing what `make build-self` writes in order to make a path eligible.

### Never do

- Pass `FORCE=1` or `--force` to `make build-self` from automation. The
  dirty-tree refusal is fail-closed by design.
- Add a merge driver to `docs/product/changelog.md`, `workspace.toml`, any
  `pack.toml`, or any other hand-authored file. Their content is not
  recoverable by regeneration.
- Introduce a new module, package, top-level directory, or third-party
  dependency. This change is configuration, a Makefile target, and prose.

## Testing Strategy

- **Driver scope (AC1): TDD.** Whether a path is covered by a gate is a
  compressible invariant with a mechanical oracle, and the criterion is a set
  equality over that oracle, so a pattern that reaches too far and a projection
  the block forgot both red on the same assertion.
- **Merge, rebase and source behaviour (AC2, AC3, AC4): TDD, exercised as
  integration tests.** These properties live across a boundary — git's merge
  machinery, this repository's `.gitattributes`, and the self-host pipeline — so
  the tests drive real git operations against a real tree rather than asserting
  on the attributes file.
- **Bootstrap target (AC5): TDD.** Invoking `make bootstrap-git` directly would
  write into the developer's real git config, so the test reads the recipe's
  own `git config` commands out of the `Makefile` and runs them twice against a
  scratch repository. Reading them rather than restating them is the point: it
  is the only thing joining the recipe to the driver name `.gitattributes`
  declares, and without that join a typo in the recipe leaves every behaviour
  test green while every real merge falls back to conflicting.

## Acceptance Criteria

- [x] The set of tracked regular-file paths for which `git check-attr merge`
      resolves `regen` is exactly the set of tracked regular-file paths covered
      by a required `gate-main` check — the `make build-check` self-host drift
      comparison, its adapter-root-bins and user-libs drift rails, and its
      packaged-runtime byte-identity check. Symlinks are outside the equality
      on both sides, because git applies no content merge driver to a symlink
      blob, so declaring one would report an attribute that never takes effect.
- [x] A `git merge` and a `git rebase` that each bring divergent edits to the
      same `merge=regen` path complete without halting on that path, and that
      path contains no conflict-marker line afterwards. The rebase replays its
      commit rather than dropping it as already-upstream, so the driver is
      exercised rather than bypassed.
- [x] A `git merge` that brings divergent edits to the same path under
      `packs/**/.apm/` or `packs/**/seeds/` halts on that path.
- [x] After a `git merge` that auto-resolved at least one `merge=regen` path,
      `make build-self` exits zero and the self-host drift comparison and
      packaged-runtime byte-identity check then report no drift.
- [x] `make bootstrap-git` sets `merge.regen.driver` to `true`, and a second
      consecutive run leaves that value unchanged.

## Follow-ons

- Repository maintainers: separate spec — generate `docs/specs/README.md` and
  `docs/adr/README.md` from their directories instead of maintaining the index
  tables by hand.
- Repository maintainers: separate spec — fragment `docs/product/changelog.md`
  into per-entry files so two branches adding entries never collide.

## Assumptions

- Technical: a merge driver whose command is `true` settles a matching path
  without halting and emits no conflict markers, while non-matching paths
  conflict normally (source: scratch-repository probe, git 2.50.1, 2026-09-12 —
  a `.claude/**` path auto-merged with zero markers while a `packs/` path
  reported `CONFLICT (content)`)
- Technical: under `git rebase` the driver keeps the upstream side, which can
  make a projection-only commit empty and cause git to drop it — `dropping
  <sha> ... patch contents already upstream` (source: scratch-repository probe,
  2026-09-12). The contract therefore specifies convergence after
  regeneration, never a surviving side.
- Technical: self-host projections are a pure function of pack sources (source:
  `python -m agentbundle catalogue self-host --root . --check` returned
  `catalogue self-host --check: ok` on a clean tree and left it clean)
- Technical: `_is_excluded` gates the drift comparison in
  `diff_against_working_tree`, not only seed projection, and rescues exactly
  one path — `PROJECTED_README_OVERRIDES` contains `docs/CONVENTIONS.md` alone
  (source: those three symbols in
  `packages/agentbundle/agentbundle/build/self_host.py`)
- Technical: `tools/**` is in `EXCLUDED_PATTERNS`, so no gate covers
  `tools/hooks/*.py`, and the owner accepted that gap rather than adding those
  paths to `PROJECTED_README_OVERRIDES`. Byte-identity with a pack source
  establishes only that the files agree today, never that a mutation would be
  caught (source: `_is_excluded(Path("tools/hooks/pre-pr.py"))` returns `True`;
  those paths are absent from `_runtime_projections`; user confirmation
  2026-09-12)
- Technical: the eligible set is covered by three rails — the
  `diff_against_working_tree` comparison for every non-excluded projected path,
  `_adapter_root_bins_check_drift` and `_user_libs_check_drift` for
  `.agentbundle/`, and the packaged-runtime byte-identity check for the five
  `_runtime_projections` pairs, which `_is_excluded` skips (source: those
  symbols in `self_host.py`; `_is_excluded` evaluated against each candidate
  path, 2026-09-12)
- Technical: all ten tracked `.agentbundle/` files are projections and are
  byte-identical to sources in `packs/credential-brokers/.apm/` — three from
  `adapter-root-bins/`, six from `user-libs/credbroker/`, plus
  `credentials_shim.py` from `shared-libs/` as a shim companion (source: `cmp` against each source;
  `SHIM_COMPANION_BASENAME` in
  `packages/agentbundle/agentbundle/build/adapter_root_bins.py`)
- Technical: `CLAUDE.md` is a projected symlink that a required gate does
  cover — `_is_excluded` returns `False` for it and `diff_against_working_tree`
  carries a dedicated row for it — so it is not out of scope in the sense of
  being ungated. It falls outside AC1 because AC1 quantifies over regular files
  only: git applies no content merge driver to a symlink blob, so
  `merge=regen` on that path would declare an attribute that never takes
  effect (source: `_is_excluded`, `_recreate_claude_symlink` and
  `_is_equivalent_claude_md_shape` in `self_host.py`; `docs/CONVENTIONS.md`
  § Pack source-of-truth split lists it under Recreated)
- Technical: `.gitattributes` is in `EXCLUDED_PATTERNS`, so self-host never
  overwrites the block this spec adds (source: `_is_excluded` returns `True`
  for it)
- Technical: `extensions.worktreeConfig` is unset, so one `git config`
  invocation covers every linked worktree, while a fresh clone needs its own
  (source: `git config --get extensions.worktreeConfig` returned empty)
- Technical: `AGENTS.md` is never written by self-host — `_compose_agents_md`
  returns `None` when the file exists, because `AGENTS.md` is in
  `EXCLUDED_PATTERNS`; its presence in `TARGET_PATHS` is the dry-run
  shadow-clone list, not the write list (source: those symbols in
  `self_host.py`)
- Process: this change takes a spec with no ADR or RFC, because the driver
  mechanically enforces the existing "edit sources, not projections" convention
  rather than establishing a new one (source: user confirmation 2026-09-12)
- Process: the driver is registered by a new `make bootstrap-git` target rather
  than by a session hook, keeping the change out of pack sources (source: user
  confirmation 2026-09-12)
- Product: `docs/CONVENTIONS.md` is in scope for the driver despite being a
  heavily read human document, because it is genuinely projected and is the
  sole path rescued from exclusion by `PROJECTED_README_OVERRIDES` (source:
  user confirmation 2026-09-12)
- Technical: three further seed-projected paths are gate-covered and belong in
  the driver set — `AGENT_RULES.md`, `docs/AGENTS.md` and
  `governance/manifest.example.yaml`. `docs/CONVENTIONS.md` § Pack
  source-of-truth split states that the other seed-projected paths "were
  reclassified as *Manual* with placeholder seeds", which is wrong for these
  three; the spec's own boundary makes the gates authoritative (source:
  `_is_excluded` returns `False` for each, each is tracked, and each is
  byte-identical to its seed under `packs/core/seeds/` or
  `packs/governance-extras/seeds/`; `governance-extras` is in
  `[recipe.packs] include` in
  `packages/agentbundle/agentbundle/build/recipes/self-host.toml`, which that
  file marks as the authoritative source for `SELF_HOST_PACKS` —
  `_DEFAULT_SELF_HOST_PACKS` is only the import-time fallback and already
  differs from it)
- Product: adopters do not inherit this change — there is no
  `packs/*/seeds/.gitattributes`, and `.gitattributes` is Manual/adopter-owned
  (source: `git ls-files 'packs/*/seeds/.gitattributes'` returned empty)
