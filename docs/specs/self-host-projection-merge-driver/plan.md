# Plan: Self-host projection merge driver

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/CONVENTIONS.md` § Pack source-of-truth split
  (the authoritative Projected-path list); in
  `packages/agentbundle/agentbundle/build/self_host.py` — `TARGET_PATHS`,
  `EXCLUDED_PATTERNS`, `_is_excluded`, `PROJECTED_README_OVERRIDES`,
  `_runtime_projections`, `_compose_agents_md`, `diff_against_working_tree`,
  `_self_host_projection_paths`, `_self_host_projection_drifts`,
  `_is_equivalent_claude_md_shape`;
  `SHIM_COMPANION_BASENAME` in `build/adapter_root_bins.py`;
  `target_resolver.py`; `.github/workflows/build-check.yml` `gate-main` (the
  only place a repo-level pytest is reachable). Analogous implementations
  inspected: `tools/test_build_gate_chain.py` and
  `tools/test_build_site_sidebar.py`, both repo-root-relative suites wired as
  explicit `gate-main` steps.

## Approach

Three independent pieces that share one oracle.

The **oracle** is the self-host pipeline itself. A path is eligible exactly
when mutating it makes a required gate fail, so the guard computes eligibility
rather than comparing against a second hand-maintained list. That is what keeps
the change from decaying: adding an adapter that projects a new tree does not
silently widen the driver, and removing one does not leave a dead pattern that
swallows a real edit. The guard is stated as an equality between the attribute
set and the rail set, so a fixture that degenerates — reporting everything, or
nothing — fails rather than passes.

The **driver** is `.gitattributes` plus two `git config` keys. The config keys
cannot travel in `.gitattributes`, so a clone without them gets ordinary
conflicts — degraded, never wrong.

The **workflow** is prose, because nothing mechanical can force a maintainer to
run `make build-self` after a merge. It does not need to: the drift gate
already refuses the push.

## Constraints

- `make build-check` runs no pytest. A new test file that is not added as an
  explicit step in `.github/workflows/build-check.yml`'s `gate-main` job runs
  nowhere, in CI or locally. Both new suites must be wired in the same PR that
  creates them.
- Editing `tools/repo/build_gate_chain.py` reds Gate F while `make build-check`
  stays green. This plan does not touch the gate chain; if a task turns out to
  need it, run the Gate F pytest pair before pushing.
- `make build-self` refuses a dirty tree (`is_dirty_tree` is fail-closed:
  missing git, non-repo, and failed calls all count as dirty). Tests operate on
  a scratch copy, never the working tree, and never pass `FORCE=1`.
- `.gitattributes` is excluded from projection, so the new block needs no
  `make build-self` run to land.
- `docs/CONVENTIONS.md` is projected. Its edit goes to
  `packs/core/seeds/docs/CONVENTIONS.md` followed by `make build-self`.

## Construction tests

Two new suites, both under `tools/` to match the 63 existing repo-root-relative
suites there, both wired into `gate-main`:

- `tools/test_gitattributes_merge_driver.py` — the driver-set equality. Owns AC1.
- `tools/test_merge_driver_behaviour.py` — merge, rebase, source-conflict, and
  convergence. Owns AC2, AC3 and AC4.

## Durable-output map

| Spec durable output | Task | Evidence |
| --- | --- | --- |
| `AGENTS.local.md` § Landing changes | T4 | Section names the merge → regenerate → amend sequence |
| `AGENTS.local.md` § Worktree bootstrap | T3 | Section names `make bootstrap-git` and its per-clone scope |
| `docs/CONVENTIONS.md` § Pack source-of-truth split | T4 | Seed edited, `make build-self` run, seed and projection byte-identical |

## Design (LLD)

Shape is `integration`: the change wires git's merge machinery to the existing
self-host pipeline. `## Data & schema` and `## Component decomposition` are
omitted because no schema or module boundary changes.

### Design decisions

**The guard is a set equality, not a pair of one-way checks.** A test
asserting `.gitattributes` matched a hardcoded expected set would pass forever
while the projection set moved beneath it, which is the decay this change has
to avoid. Both one-way alternatives fail too: quantifying only over
`merge=regen` matches lets a block containing one pattern pass while every
other projection keeps conflicting, and a negative control drawn from an
excluded path is a tautology, because `_is_excluded` rejects by path before any
content is compared. Comparing the two sets computed from the same oracle
catches over-scope and under-scope on one assertion and needs no control.

**Three rails, not one.** Eligibility is not a single predicate. Most projected
paths are covered by `diff_against_working_tree`; `.agentbundle/` is
additionally covered by `_adapter_root_bins_check_drift` and
`_user_libs_check_drift`; the five `_runtime_projections` pairs are skipped by
`diff_against_working_tree` — `_is_excluded` returns `True` for
`packages/**` — and are covered instead by the packaged-runtime byte-identity
check. A guard that consulted only the first rail would wrongly reject all five.

**`tools/hooks/*.py` is excluded despite being a projection.** `_is_excluded`
gates the drift comparison as well as seed projection, and `tools/**` is an
excluded pattern that `PROJECTED_README_OVERRIDES` does not rescue. Those three
files therefore have no rail, and keep conflicting normally. This is the
accepted coverage gap. It also means those paths belong to neither side of
AC1's equality: they are absent from the rail set because no gate sees them,
and absent from the attribute set because the block does not list them.

**A `true` driver rather than a regenerating one.** Git runs a merge driver
once per conflicted file, mid-merge, with the tree in an indeterminate state.
Regenerating from inside a per-file driver would run self-host hundreds of
times against a half-merged tree. Keeping one side and regenerating once
afterwards is cheaper and is the only ordering that sees merged sources.

**The contract never names a surviving side.** Under `git merge` the driver
keeps the local side; under `git rebase` ours and theirs invert, so it keeps
upstream — and when the replayed commit touched only projections, the patch
becomes empty and git drops the commit outright. For regenerable content that
is harmless, but it makes any side-pinned criterion wrong for half the cases.
AC2 asserts only that the operation does not halt and leaves no marker; AC4
carries the correctness half. AC4 is stated as a fixed point rather than a
no-op: `make build-self` is *expected* to write after a merge that kept one
side's projection, which is exactly why the documented workflow ends in
`commit --amend`. What must hold afterwards is that the drift checks report
nothing, not that the tree was already clean.

### Interfaces & contracts

`merge.regen` is a git config namespace, not a published interface. The name is
local to this repository; adopters inherit nothing.

### Failure, edge cases & resilience

- **Unregistered clone.** Git reports `Unknown merge driver: regen` and falls
  back to the default merge, so the path conflicts normally. Degraded, not wrong.
- **Stale projection reaching a push.** Blocked by the drift gate.
- **A path listed but no longer projected.** AC1 reds while the path is still
  tracked. A pattern matching no tracked file leaves both sets unchanged and is
  inert rather than caught — dead configuration, not lost protection.
- **A path projected but not listed.** AC1 reds: the rail set has a member the
  attribute set does not.
- **A projection-only commit vanishing under rebase.** Expected; the content is
  regenerated from source and AC4 covers the result.

### Dependencies & integration

No new dependency. Git 2.50.1 is the probed floor; `merge.<driver>.driver`
predates every version in use.

## Tasks

### T1: Driver-set equality guard and the `.gitattributes` block

**Depends on:** none

**Tests:**
- `tools/test_gitattributes_merge_driver.py` (AC1). Builds two sets over the
  tracked file list and asserts equality. The attribute set comes from
  `git check-attr merge -- <paths>`, so the test observes what git resolves
  rather than reimplementing gitattributes precedence. The rail set is the
  union of three sources: the non-excluded paths `diff_against_working_tree`
  walks, the paths the adapter-root-bins and user-libs rails own, and the
  `_runtime_projections` pairs. Assert set equality, then assert each side is
  non-empty so a pair of empty sets cannot pass.
- The failure report prints both differences by name — attribute-only paths are
  over-scope, rail-only paths are a projection the block forgot.
- `stub: true`: the set-equality assertion is a grounded, callable seam over
  `git check-attr` and the rail helpers, and carries a compilable red before
  the block exists.

**Approach:**
- Derive the rail set from `_self_host_projection_paths`, the
  `_runtime_projections` pairs, and the non-excluded paths the dry run walks —
  never a literal list — so an added or removed adapter moves the expectation
  automatically. `run_self_host(dry_run=True)` already computes this union.
- Drop non-regular entries from **both** sides before comparing — `git ls-files
  -s` mode `120000`, or `lstat` plus `stat.S_ISLNK`. This is the mechanization
  of AC1's regular-file clause. Without it the rail set contains `CLAUDE.md`,
  which `_is_excluded` does not exclude, and the equality reds with a rail-only
  member on its first run.
- Generate the `.gitattributes` block from one dry run rather than typing it.
  The set it emits is wider than the adapter trees alone: besides `.claude/**`,
  `.agents/**`, `.codex/**`, `.claude-plugin/marketplace.json`,
  `.agentbundle/bin/**`, `.agentbundle/lib/**` and `docs/CONVENTIONS.md`, it
  carries the seed-projected `AGENT_RULES.md`, `docs/AGENTS.md` and
  `governance/manifest.example.yaml`, plus the five `_runtime_projections`
  files named individually — never a `_data/*.py` glob, which would swallow 22
  hand-authored siblings. `CLAUDE.md` is gate-covered but excluded by AC1's
  regular-file restriction.
- Append the block at end of file, not after the `* text=auto eol=lf` line. The
  `binary` macro expands to `-diff -merge -text`, so any path matching
  `*.png` and its seven siblings would have `merge` unset by a later line. No
  tracked projection carries those extensions today; placing the block last
  means the day one does, AC1 does not red for a reason nobody would guess.
- Resolve attributes with `git check-attr merge --stdin`: the tracked list is
  far past the argv limit.
- Wire the suite as a `gate-main` step.

**Done when:** `python -m pytest tools/test_gitattributes_merge_driver.py`
passes and the suite appears as a `gate-main` step.

### T2: Merge, rebase, source-conflict and convergence behaviour

**Depends on:** T1

**Tests:**
- `tools/test_merge_driver_behaviour.py` (AC2, AC3, AC4).
- Fixture for AC2 and AC3: a synthetic scratch repository carrying the
  repository's real `.gitattributes`, the registered driver, and two files — a
  `merge=regen` path and a `packs/**/.apm/` path. It drives a real merge and a
  real rebase and asserts non-halting on the first path, halting on the second,
  and no conflict-marker line in the first afterwards. Synthetic is sufficient
  here because only git's resolution is under test.
- Fixture for AC4: a `git clone` of the working tree into the scratch
  directory, because `make build-self` needs the `Makefile`, the whole `packs/`
  tree, and a resolvable `agentbundle` — none of which a synthetic repo has.
  Three things the clone needs that a bare `git clone` does not give it:
  the `.gitattributes` block must be **committed** on the branch the fixture
  clones, since a clone carries HEAD and not the working tree; the driver must
  be registered inside the clone, because git config is per-clone; and the
  assertion must reach both halves of AC4 without calling
  `run_build_check_drift_gates`. Run `catalogue self-host --check` against the
  clone — equivalently `run_self_host(dry_run=True)`, the only route to the
  self-host drift comparison — and assert zero drift; then compare the
  `_runtime_projections(clone_root)` pairs directly for the byte-identity half.
  Neither needs `dist/`. Two independent reasons rule the aggregate call out:
  its first gate resolves `dist/` and hard-fails when absent, and its
  packaged-runtime gate iterates `_runtime_projections(REPO_ROOT)` rather than
  the output root, so it would measure this repository instead of the clone
  even with `dist/` present.
  Run `make build-self` with no `FORCE=1`; the clone is clean, so the
  fail-closed dirty-tree refusal does not fire.
- AC4 asserts the drift checks report nothing. It does not assert a clean
  `git status`: `make build-self` is expected to write here.

**Approach:**
- Reuse the merge shape validated during authoring: auto-resolved with zero
  markers while a `packs/` path reported `CONFLICT (content)`.
- Do **not** reuse the rebase shape from that probe. It reported
  `dropping <sha> ... patch contents already upstream`, which means the patch
  was empty and no merge ran — so the assertion would hold identically with the
  driver unregistered and with no `.gitattributes` block at all. Pin the
  replayed commit to also touch a path outside the driver set — edited on the
  replayed side only, so it cannot itself conflict — making the patch non-empty
  so a real three-way merge runs on the `merge=regen` path. Assert the replayed
  commit is present on the rebased branch; that is the post-condition which
  makes the non-halting claim non-vacuous.
- Assert non-halting rather than a surviving side, for the reason in
  § Design decisions.
- Wire the suite as a `gate-main` step.

**Done when:** `python -m pytest tools/test_merge_driver_behaviour.py` passes
and the suite appears as a `gate-main` step.

### T3: `make bootstrap-git`

**Depends on:** none

**Tests:**
- TDD (AC5), in `tools/test_merge_driver_behaviour.py`: read the `git config`
  commands out of the `bootstrap-git` recipe and run them twice against a
  scratch repository, then assert the driver key holds the recipe's value and a
  second run did not change it. Invoking `make bootstrap-git` directly is the
  one thing the test must not do — it writes the developer's real git config.
  Reading the recipe rather than restating it is the join: nothing else ties
  that recipe to the driver name `.gitattributes` declares.

**Approach:**
- Add the target beside the existing `bootstrap-*` family in the `Makefile`.
- Record the step in `AGENTS.local.md` § Worktree bootstrap, noting that git
  config is shared across linked worktrees but not across clones.

**Done when:** `python -m pytest tools/test_merge_driver_behaviour.py -k
bootstrap` passes and `AGENTS.local.md` § Worktree bootstrap names the target.

### T4: Durable outputs

**Depends on:** T1, T3

**Tests:**
- Goal-based: `make build-self` leaves the tree clean after the CONVENTIONS
  seed edit, proving seed and projection agree.
- Goal-based: `lint-spec-status.py --root .` reports no hard violation. This
  proves spec metadata shape — status vocabulary, criterion notation, deferral
  anchors — and not that the prose is accurate; a wrong sentence in
  `AGENTS.local.md` passes it, which is why Done-when names the destinations
  rather than resting on the lint.

**Approach:**
- `AGENTS.local.md` § Landing changes: add the merge → `make build-self` →
  `commit --amend` sequence and the never-`FORCE=1` rule, beside the existing
  branches-must-be-current statement.
- `packs/core/seeds/docs/CONVENTIONS.md` § Pack source-of-truth split: three
  edits. Note that the Projected paths carry `merge=regen`; correct the
  `tools/hooks/<name>.<ext>` entry, which is listed as gate-covered and is not;
  and correct the claim that the non-`CONVENTIONS.md` seed-projected paths
  "were reclassified as *Manual* with placeholder seeds", which is wrong for
  `AGENT_RULES.md`, `docs/AGENTS.md` and `governance/manifest.example.yaml`.
  Then `make build-self`.
- `docs/product/changelog.md`: the seed edit is shipped pack content, so
  `packs/core` bumps and that bump is a released artifact owing a free-standing
  `## [core][<version>]` entry with `Highlights` — an adopter's installed
  conventions now say something different. Derive the version from the current
  `origin/main`, never from the branch's base: `origin/main` may already have
  published the next number.

**Done when:** `AGENTS.local.md` § Landing changes states the regeneration
sequence, `AGENTS.local.md` § Worktree bootstrap names `make bootstrap-git`,
`docs/CONVENTIONS.md` § Pack source-of-truth split records the `merge=regen`
status of the projected paths, corrects its `tools/hooks/<name>.<ext>` entry to
state that no drift gate covers it, and corrects its Manual-reclassification
claim for the three seed-projected paths that are still gate-covered, and
`make build-check` passes.

## Rollout

- **Delivery:** big bang, single PR. Reversible by deleting the
  `.gitattributes` block; the config keys become inert with no pattern to match.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T1 and T3 are independent. T2 needs T1's block.
  T4 documents what the others built.

Review shape: all four tasks sit far below 2,000 reviewable behavior and test
lines, so no WIDE/MIXED/DEEP decomposition applies.

## Risks

- **The driver is local-only.** Git config cannot ship in `.gitattributes`, and
  GitHub's servers do not honour custom merge drivers. This makes strict-rebase
  cheaper and does nothing inside a GitHub merge queue; if the repository later
  adopts one, these paths conflict server-side again and the queue cannot run
  `make build-self` to fix them. Recorded here because it is the fact a future
  maintainer is least able to reconstruct from `.gitattributes`, and the
  governance route for this change is spec-only.
- **Over-scoping is silently destructive.** A pattern matching a
  non-regenerated path discards a real edit with no gate behind it. AC1 is the
  control and AC2 is the control on the control.
- **Byte-identity is not gate coverage.** The two claims came apart once
  already during authoring: `tools/hooks/*.py` is byte-identical to its pack
  source and is covered by no rail. Any future addition to the driver list is
  decided by `_is_excluded` and the rails, never by `cmp`.

## Changelog

- 2026-09-13: Approved shape. The contract is five criteria resting on one
  oracle: an equality between the paths declaring `merge=regen` and the paths a
  required gate covers, computed from the pipeline rather than enumerated.
  Three review rounds moved it here; the reasoning that survives — why set
  equality rather than a one-way check plus a control, why no criterion names a
  surviving side, why `tools/hooks/*.py` is excluded — lives in
  § Design decisions.
