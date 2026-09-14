# Spec: Record-index merge driver

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0112
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

A maintainer merging or rebasing locally in a clone that has run `make
bootstrap-git` never resolves a conflict in `docs/adr/README.md` or
`docs/rfc/README.md`: git settles those two paths without halting, and
`index-records.py` regenerates each from the records in its own directory. A web
merge and an unbootstrapped clone keep the ordinary conflicting behaviour, for
the reasons recorded below. Which side git keeps does not matter and is not
specified: the content is regenerated either way. The records themselves —
`docs/adr/NNNN-*.md` and `docs/rfc/NNNN-*.md` — still conflict normally,
because those carry the decisions a human has to make.

Each index table is a function of the records beside it and of the repository
history that dates them: a record supplies its own `**Date:**`, and where that
field is absent or still a placeholder, `index-records.py` resolves the date
from the record's add-commit. Both inputs are present in any merged tree, and
neither depends on which side of the merge survived in the table, so
regeneration converges from the merged tree. A textual merge of the table is
meaningless regardless: two branches each adding a record produce a table whose
rows git interleaves at the wrong ordinal, and the only correct resolution is
to regenerate.

Correctness does not rest on the merge result. `gate-main` already refuses a
stale index through `check-adr-index` and `check-rfc-index`, both of which run
`index-records.py --check` inside `make build-check`. The driver removes a
pointless conflict; the gate remains the guarantee.

This spec owns the eligibility rule for the whole `merge=regen` set, in place
of acceptance criterion 1 of
[`docs/specs/self-host-projection-merge-driver/spec.md`](../self-host-projection-merge-driver/spec.md).
That spec's remaining criteria still own what the driver does to a real merge
and a real rebase for every declared path, so membership is what this spec
decides.

[ADR-0112](../../adr/0112-index-tables-are-generated-or-absent.md) governs how
these two files are maintained and rejects a `merge=union` driver on them. That
rejection weighs `union`, which is not what this change declares, and the claim
here is only that — not that ADR-0112 decided `union` wrongly.

ADR-0112 rejects `union` on two grounds, and they land differently. Its
correctness ground is that union keeps both sides of a mutated row, so the file
parses cleanly and is wrong; `regen` keeps one side and leaves the file stale,
and a stale table is what `check-adr-index` and `check-rfc-index` already
refuse. Its second ground — neither GitHub nor GitLab honours a merge driver in
a web merge — applies to `regen` unchanged, and is a limit on reach rather than
on safety: a web merge of these paths conflicts normally, the same degraded
fallback a clone that never ran `make bootstrap-git` gets, and the gate still
refuses a stale table either way. The driver helps a maintainer merging
locally and does nothing in the web UI.

The rule itself is the reason the covered set is derived rather than listed: a
path may carry the driver only where a required `gate-main` check would catch a
bad regeneration, because the driver discards one merge side and the gate is
the only thing that notices. Admitting a second generator's rail therefore
widens what the gates cover, never what a maintainer may declare by hand.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — the eligibility rule at its point of use names one generator, one oracle, and three ineligible paths, and this change falsifies all three | `.gitattributes` comment header | Repository maintainers | The header states the covered set as the union over required `gate-main` generator rails, names both oracles (the mutated scratch tree and the gate chain's step list), and lists the current ineligible-but-eligible-looking paths, recording that `docs/specs/README.md` has no generator because ADR-0112 retired its index table, not that it awaits gate coverage | Header names both oracles, still names `tools/test_gitattributes_merge_driver.py` as the enforcing suite, and its `docs/specs/README.md` entry cites ADR-0112 as the reason no generator exists |
| Current architecture | Applicable — the suite that enforces the equality names only the superseded spec | `tools/test_gitattributes_merge_driver.py` module docstring | Repository maintainers | The docstring states that the covered set is the union over required `gate-main` generator rails, cites this spec as the owner of that equality, and cites the superseded spec | Both spec paths appear in the docstring and the equality it describes matches the assertion below it |
| Current architecture | Applicable — the behaviour suite's docstring names only the superseded spec, and after this change "AC4" resolves to two different criteria inside it | `tools/test_merge_driver_behaviour.py` module docstring | Repository maintainers | Every spec-AC label in the suite names its owning spec, so neither the two AC4s nor the two AC5s collide | No bare `ACn` label remains in the suite or its gate-main comment |
| Current architecture | Applicable — the CI comment introducing both merge-driver steps cites the superseded spec's AC1 and calls the set a projection set | `.github/workflows/build-check.yml` comment above the merge-driver steps | Repository maintainers | The comment names this spec and the union rule | Comment names this spec; the two step-name strings are unchanged, so `tools/lint-ci-parity.py`'s pinned keys still resolve |
| Current architecture | Applicable — the `bootstrap-git` recipe comment, its help text, the `merge.regen.name` description, and the completion echo all scope the driver to self-host projections, and that description calls `make build-self` the regenerator | `Makefile` `bootstrap-git` target | Repository maintainers | All four strings describe a driver covering more than one generator, without naming a single regenerator | None of the four names `make build-self` as the sole regenerator, the driver is still named `regen`, and `tools/test_merge_driver_behaviour.py` still derives the driver from the recipe |
| Maintainer procedure | Applicable — § Worktree bootstrap states that without `make bootstrap-git` merges of projections conflict normally, which is false for the two index READMEs | `AGENTS.local.md` § Worktree bootstrap | Repository maintainers | The sentence describes the widened set rather than projections alone | Sentence no longer scopes the consequence to projections |
| Maintainer procedure | Applicable — the section scopes the driver to self-host projections in its sentence beginning "Self-host projections carry `merge=regen`", and names one regeneration command | `AGENTS.local.md` § Landing changes | Repository maintainers | That sentence describes the widened set rather than self-host projections alone, and the section carries both regeneration commands in a form that runs from the repository root with no variable set; `plan.md` names the two literal commands | That sentence covers both generators; each command runs to exit 0 when pasted from the repository root; the file is at or under its 60-line cap |
| Decision rationale | Not applicable | — | — | — | ADR-0112 already governs these paths; the Objective records why `regen` is outside its rejection of `union`, so no new decision is taken; owner confirmation 2026-09-13 |
| Interface compatibility | Not applicable | — | — | — | No published interface changes; `.gitattributes` is Manual and is not seeded to adopters |
| Release history | Not applicable | — | — | — | No pack content changes: nothing under `packs/*/seeds/**` or `packs/*/.apm/**` is touched, so no pack version is bumped and no changelog entry is owed |
| User-facing promise | Not applicable | — | — | — | Adopters do not inherit this change; there is no `packs/*/seeds/.gitattributes` |

## Boundaries

### Always do

- Settle the eligibility question from the gates, never from a second
  hand-maintained list.
- Keep a chain-derived rail's membership dependent on the gate step that
  justifies it, so renaming or removing that step removes its paths from the
  covered set.
- Keep the equality a single set equality over the whole declared set. Two
  equalities over two subsets need a hand-maintained partition to decide which
  one owns a path, and a path in neither subset then satisfies both.
- Prove a rail can report clean before using its red as evidence that it covers
  a path.

### Ask first

- Adding a `merge=regen` pattern for any path the rail check in AC1 does not
  already cover.
- Admitting a generator whose staleness report has to be parsed out of prose
  rather than read from an exit code.
- Changing what any generator writes in order to make a path eligible.

### Never do

- Add a merge driver to a decision record or any other hand-authored file.
  Their content is not recoverable by regeneration.
- Write an unanchored `.gitattributes` pattern. A pattern with no leading slash
  and no directory separator matches at every depth, which is how `AGENT_RULES.md`
  silently caught `packs/core/seeds/AGENT_RULES.md`.
- Introduce a new module, package, top-level directory, test suite, or
  third-party dependency. This change is two `.gitattributes` lines, an
  extension to one existing suite, and prose.

## Testing Strategy

- **Driver scope (AC1): TDD.** Whether a path is covered by a required
  `gate-main` check is a compressible invariant with a mechanical oracle, and
  the criterion is a set equality over that oracle, so a pattern that reaches
  too far and a rail output the block forgot both red on the same assertion.
  The existing AC1 suite already runs in `gate-main`, so the widened equality
  inherits its enforcement rather than needing a new gate.
- **Rail derivation (AC2): TDD.** The criterion is about what happens to the
  covered set when a gate step changes, which is only observable by feeding the
  derivation a step list that differs from the real one. The test therefore
  drives the derivation from constructed step lists as well as the real chain.
- **Rail can-fail control (AC3): TDD.** The criterion asserts both directions of
  a check, so a fixture that can only produce one of them fails to establish it.
  The fixture is synthetic for the reason recorded in Assumptions, and the test
  pins the generated date cell so the fixture cannot silently degrade into the
  state that made a copied directory unusable.
- **Driver attribution (AC4): TDD, exercised as an integration test.** The
  criterion is differential because the driver's effect is an absence — a merge
  that does not halt — and an absence cannot be distinguished from a merge that
  never needed resolving. Observing only the driver-set run admits a fast-forward
  and admits a divergence git settles textually, in both of which the criterion
  holds with the driver deleted. Running the same starting state both ways is
  what makes the criterion false when the driver is absent or irrelevant.
- **Convergence (AC5): TDD, exercised as an integration test on the same
  fixture.** The falsifier is a row the surviving side never had. AC4's halting
  half is what guarantees that row exists: a merge that halts without the driver
  is one where the two sides' rows genuinely collide, so the driver's resolution
  discards one. The criterion reads the regenerated table rather than re-running
  `--check` against it, because re-running the generator and comparing to what
  it just wrote is self-comparing.

## Acceptance Criteria

- [ ] The set of tracked regular-file paths for which `git check-attr merge`
      resolves `regen` is exactly the union, over every required `gate-main`
      generator rail, of the tracked regular-file paths that rail covers.
      Symlinks are outside the equality on both sides, because git applies no
      content merge driver to a symlink blob, so declaring one would report an
      attribute that never takes effect.
- [ ] The record-index rail's covered set changes with the `build-check` chain's
      steps: a chain carrying no `index-records.py --check` step contributes no
      path to the covered set, and a chain carrying such a step for a record
      directory contributes that directory's `README.md` and nothing else.
- [ ] `index-records.py --check <dir>` exits zero against a record directory
      whose `README.md` matches its records, and exits non-zero naming
      `<dir>/README.md` when that file is changed and nothing else is.
- [ ] A `git merge` in which each side has added a distinct record to
      `docs/adr` and regenerated `docs/adr/README.md` halts on that path when
      `merge.regen.driver` is unset, and the same merge from the same starting
      state completes without halting, leaving a commit with two parents, when
      it is set.
- [ ] After the driver-resolved merge, `index-records.py docs/adr` exits zero
      and `docs/adr/README.md` then carries a row for each side's record.

## Follow-ons

- Repository maintainers: separate spec — fragment `docs/product/changelog.md`
  into per-entry files so two branches adding entries never collide.

## Assumptions

- Technical: the required `gate-main` generator rails are, as of 2026-09-13,
  the `make build-check` self-host drift comparison, its adapter-root-bins and
  user-libs drift rails, its packaged-runtime byte-identity check, and its
  record-index checks. This is a dated snapshot for orientation; the criterion
  quantifies over what the suite measures, not over this list (source:
  `rail_set` in `tools/test_gitattributes_merge_driver.py` plus the two
  `index-records.py` steps this change adds)
- Technical: the differential in AC4 is observable, and AC5's falsifier really
  exists. In a scratch repository where two branches each add a record and
  regenerate the index, `git merge` with `merge.regen.driver` unset exits 1 and
  stages a conflict on the index; with the driver set the same merge exits 0 and
  leaves a two-parent commit whose table has lost one side's row; running
  `index-records.py` restores it — two rows before, three after (source:
  scratch-repository probe, 2026-09-13)
- Technical: only the record-index rail derives its membership from the gate
  chain. The self-host, adapter/user-libs and packaged-runtime rails are
  measured behaviourally from the pipeline — `rail_set` shells `agentbundle
  catalogue self-host --check` and imports `_self_host_projection_paths` and
  `_runtime_projections`, none of which reads `build_gate_chain.py` — so
  removing one of their gate steps would not shrink the covered set. That is an
  inherited gap this change neither creates nor closes, and it is why the
  Boundaries bullet is scoped to chain-derived rails (source: `rail_set` in
  `tools/test_gitattributes_merge_driver.py`)
- Technical: the `docs/rfc` half of AC4 and AC5 rests on AC2 and AC3 rather
  than on its own instantiation: AC2 fixes that the rail contributes
  `<dir>/README.md` for every record-index gate step, and AC3's contract is
  stated over an arbitrary `<dir>`, so a fixture proving the `docs/adr` half
  proves the mechanism both halves share (source: those two criteria)
- Technical: `check-adr-index` and `check-rfc-index` run `index-records.py
  --check` against `docs/adr` and `docs/rfc` inside `make build-check` (source:
  `tools/repo/build_gate_chain.py:274-283`; collecting the chain's argv under a
  faked `subprocess.run` returns exactly those two invocations, 2026-09-13)
- Technical: `make build-check` is the required PR check — `.github/workflows/
  build-check.yml:72` defines the job `gate-main`, whose chain step is
  `build_gate_chain.py build-check` (source: `Makefile:161`)
- Technical: `index-records.py --check` exits 0 when the README matches its
  records and exits 1 naming `<dir>/README.md` when it does not (source:
  synthetic single-record probe with an explicit `Date` field, 2026-09-13 —
  exit 0 clean, then exit 1 with `differs in length (6 vs 5 lines)` after one
  appended line)
- Technical: no required check already asserts the join AC3 states. The
  `index-records.py` exit-code contract is owned by
  `tests/roster/test_index_records.py`, whose `--check` cases assert the exit
  code and the differing-line message but never that the named file is
  `<dir>/README.md`; that suite runs in the dispatch-only `test-roster.yml`
  workflow rather than in `gate-main` (source: those cases, and the roster
  suite's absence from `.github/workflows/build-check.yml`)
- Technical: `index-records.py` resolves a record's `Date` from its
  `**Date:**` field, falling back to the record's add-commit via `git log
  --diff-filter=A` when the field is absent or still a placeholder. Two
  consequences: a record directory copied outside the repository loses that
  fallback and reds regardless of its README, so it cannot serve as a fixture;
  and a fixture whose records carry no `Date` renders an empty date cell on
  both sides of a generate-then-check, so it cannot detect the fallback either
  (source: the date-resolution path in
  `.claude/skills/new-adr/scripts/index-records.py`; `cp -R docs/adr <scratch>`
  then `--check <scratch>` returned exit 1 with `no Date field and no git
  history` on an unmutated copy, 2026-09-13)
- Technical: the AC1 suite already runs inside `gate-main` and already carries a
  CI-parity disposition, so the widened equality needs no new suite and no
  `run-test-suite` or pinned-digest change (source:
  `.github/workflows/build-check.yml:288-289` runs
  `tools/test_gitattributes_merge_driver.py`; `tools/lint-ci-parity.py:377`
  holds `LOCAL("test-after-build-check")` for that step at `:378-379`). The same holds for
  `tools/test_merge_driver_behaviour.py`, which T4 extends:
  `.github/workflows/build-check.yml:298-299` runs it and
  `tools/lint-ci-parity.py:380-381` disposes it. Both step-name strings are pinned
  as literal dict keys at `tools/lint-ci-parity.py:378-381`, so this change
  corrects the comments above them and leaves the names alone. Neither suite is
  covered by `PROVEN_COMPATIBLE_NODE_HASH`, whose scope is
  `PROVEN_COMPATIBLE_FILES`, so adding a case to either needs no hash bump
  (source: those symbols in
  `tools/test_local_ci_shared_test_deduplication.py`).
- Technical: both index READMEs are invisible to the self-host rail, so they
  cannot enter the superseded criterion's covered set at all —
  `_is_excluded(Path("docs/adr/README.md"))` and its `docs/rfc` counterpart both
  return `True` (source: those calls against
  `packages/agentbundle/agentbundle/build/self_host.py`, 2026-09-13)
- Technical: `.gitattributes` is never overwritten by self-host, so an appended
  block survives (source: `_is_excluded` returns `True` for it)
- Technical: `docs/specs/README.md` is tracked but no `build-check` chain step
  generates it, so the rule excludes it (source: no `index-records.py` step
  names `docs/specs` in the collected chain argv)
- Technical: `web/src/lib/now-highlights.generated.json` is tracked and
  generated but carries no required-check coverage, so it stays out of the
  driver. It was untracked by `da10ba428` and re-added by `081c26209` (PR
  #1292). Its ignore entry is still listed at `.gitignore:146` and is inert only
  because the path is tracked again, so the earlier reason for excluding it —
  that an untracked file cannot conflict — no longer holds. The reason that does
  hold is the rule itself: no required check compares the committed bytes to a
  regeneration. `tools/test_build_site_routing.py` is in `gate-main`
  (`build-check.yml:339`), but every one of its `now_highlights` cases calls
  `build_site.project_now_highlights(text)` on inline fixtures and never reads
  the committed file; `tools/build-site.py` writes it and has no `--check` mode;
  and the only other readers are `web/src/pages/now/index.astro`, which consumes
  it at build time, and `web/src/test/rendered-output.test.ts`, a web vitest
  suite `build-check.yml` does not run. Exercising the generator is not the same
  as gating its output, so nothing would red if a merge left the file stale and
  the driver would discard a real edit unnoticed (source: those files, and
  `grep -rn now-highlights.generated tools/`, 2026-09-13)
- Process: the superseded spec's body is frozen and takes no amendment — a
  supersession Status pointer must cite an ADR, not a spec (source:
  `docs/CONVENTIONS.md:162-163` rule 2, and rule 4 at `:171-176`). The owner ruled on
  2026-09-13 that this spec owns the widened equality and that the suite
  docstring and the `.gitattributes` header carry the pointer, with no ADR and
  no frozen-body edit.
- Process: this change takes a spec with no ADR or RFC, because it extends the
  existing "regenerate, do not merge" convention to a second generator rather
  than establishing a new one (source: user confirmation 2026-09-13)
- Process: the record-index rail is derived from `index-records.py --check`
  steps only, so another generator needs its own rail and its own review rather
  than a generic parse of every `--check` step in the chain (source: user
  confirmation 2026-09-13)
- Product: the people this serves are the maintainers working across this
  repository's parallel worktrees, the same population the superseded spec
  names (source: user confirmation 2026-09-13)
- Product: adopters do not inherit this change — there is no
  `packs/*/seeds/.gitattributes`, and `.gitattributes` is Manual/adopter-owned
  (source: `git ls-files 'packs/*/seeds/.gitattributes'` returned empty)
