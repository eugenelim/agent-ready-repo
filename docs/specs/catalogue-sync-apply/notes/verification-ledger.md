# Verification ledger — catalogue sync, the apply path and the scoping flags

Execution observations, one section per wave. The plan contract sends them here
rather than into the plan, which is hash-pinned from `plan-locked` onward.

## Shaping — grounding derivations

- **Date:** 2026-09-22

Four read-only probes under
[`grounding/`](grounding/) established the facts the contract rests on. The
plan's § Grounding table holds each invocation; this section holds what each
one printed.

| Derivation | Printed |
| --- | --- |
| `probe-scope-subtrees.py` | `--package credbroker` → `packages/credbroker/`, gated on the `credential-brokers` pack; `--package agentbundle` → `.agentbundle/tooling/agentbundle/`, gated on vendored tooling. `collect_fields` replaces the recorded recipe when `cfg.packs` is not `None`; `_plan_stale_owned_paths`'s `current_paths` is the keep-set |
| `probe-pin-ref.py` | `resolve_catalogue` returns a `Path` only; `_resolve_https` parses the ref from the URI and defaults it to `main`, never resolving it to a commit SHA; the pattern is the module-level `_HTTPS_RE` |
| `probe-jailed-write-admits-planned-paths.py` | external 1,907 planned paths, vendored 2,147; zero rejected as a direct write and zero as a companion write in both modes |
| `probe-rollback-snapshot-bound.py` | external 13.7 MiB, vendored 17.3 MiB of replayed bytes; largest single file 0.2 MiB; worst-case peak 34.5 MiB for replay plus a full-run snapshot |

### Residuals reported

- The architecture's § Granularity calls both `--package` targets "`packages/`
  subtrees". Only `credbroker` is one; the vendored `agentbundle` lands under
  `.agentbundle/tooling/`. AC-0053 corrects it.

## Execution — wave 1

Grounding re-run 2026-09-23 against the rebased base: all ten derivations
reproduce. Two figures the contract leans on hardest were confirmed
unchanged — `write_jailed` 16 call sites across 10 modules against
`write_companion` 4 across 4, and the link publish leaving `st_nlink=2` with
staged residue until the unlink, which the confined reader refuses.

### T1 — the `git+https://` ref helper

`resolve_git_ref` exported from `catalogue.py`; `_resolve_https` delegates and
no longer defaults the ref itself. Gates: lint exit 0, pytest exit 0 over 197
tests. This repository's pytest prints dots and no summary line, so every
count in this ledger is a dot count against an exit code, never a parsed
"N passed".

### T2 — the scope predicate

`select_write_set` plus three private helpers. Gates: lint exit 0, pytest exit
0 over 106 tests.

**Mutation proof.** The `--pack core` / `packs/core-extras/` trap is the case
the task says no other case distinguishes. Dropping the trailing separator
from `f"packs/{name}/"` turns the suite red and restoring it turns it green,
so that guard fails when broken rather than merely passing.

**Observation — the replay the fixture uses.** T2's `Done when` requires the
predicate be tested "against the planned-path set of a real replay, not a
hand-written list". A live-repository replay costs roughly 75 s per
invocation, so the fixture is a small on-disk source driven through a genuine
`replay_derivation()` call rather than the monorepo itself. The clause's
intent holds — no hand-written path list — and the fixture reproduces every
shape the task names, including paths under
`.agentbundle/tooling/packs/catalogue-curation/`, which are exactly what a
narrow reading of clause 5 admits.

### T3 — the state merge and the pin

`build_pin` and `merge_ownership_state`, both pure. Gates: lint exit 0, pytest
exit 0 over 121 tests.

**Observation — AC-0059's absolute clauses do not bind this function.** T3's
first draft asserted that a Tier-3 path and a companion path were absent from
the merged set while supplying neither in any input, so both assertions held
whatever the implementation did. Measured 2026-09-23: feeding
`packs/alpha/README.upstream.md` and an adopter-only path in through the
pre-run `recorded` mapping leaves both in the merged set, so the exclusion was
never a property of `merge_ownership_state`.

Owner decision 2026-09-23, the contribution reading: AC-0059's "a path **the
run classified** Tier-3" binds what this run contributes, and this run
classifies nothing arriving through `recorded`. The two dead assertions were
deleted rather than made fail-able. A suffix filter in the merge would be
wrong outright — AC-0071 establishes that a source may legitimately ship
`x.upstream.md`, refusing only on collision with a Tier-2 `x.md`.

**Obligation handed forward.** The clauses bind the caller, which is the only
seam that knows which paths were companion destinations. **T4 and T6 must
assert that no companion destination ever enters `written`.** Without it,
AC-0059's two absolute clauses have no fail-able check anywhere in the
delivery.

## Execution — wave 2

### T4 — the write sequence

`safety.py` gains the `Publish` selector (`REPLACE` default, `NEVER_REPLACE`,
`REPLACE_IF_UNCHANGED`) and `DestinationDivergedError`, spending this
delivery's second and last out-of-module edit. `catalogue_sync.py` gains the
rollback snapshot, write ordering, both AC-0077 rechecks, companion
admission/collision classification, coverage-scoped removal, the at-unlink
confinement recheck and `apply_write_sequence`. Gates: lint exit 0, full
`packages/agentbundle/tests/unit` suite exit 0 over 3,213 tests.

The primitive deliberately does **not** classify a link failure as occupancy.
§ Grounding's publish probe measured that `os.link` reports `EEXIST` for an
occupant but `EPERM`/`EOPNOTSUPP` where the filesystem has no hard links, so
a primitive that read any link failure as occupancy would misreport a dropped
companion as a preserved one. Classification stays at the caller's
admission-time check.

**Mutation proof, three guards.**

| Mutation | Result |
| --- | --- |
| `Publish` default flipped to `NEVER_REPLACE` | `test_safety.py` red and full suite red — AC-0052's two pins fire |
| `_in_coverage` always `True` | suite red — the 240-path deletion on a vendored-derived tree is guarded |
| keep-set narrowed to the scope before the shipped guard | **survived** — see below |

### Defect found by mutation: AC-0035's keep-set was asserted one level too high

The third mutation is the plan's § Never do violation exactly: narrowing the
keep-set handed to `_plan_stale_owned_paths`. It left the suite green.

Two reasons, both worth recording. On an **unscoped** run `_in_scope` admits
everything, so the narrowing is a no-op — and an unscoped fixture is what the
shipped AC-0035 test drove. On a **scoped** run the narrowing is real, but
`select_removal_set`'s downstream coverage filter removes the same paths
again and masks the difference in behaviour.

The shipped test spied `select_removal_set` and read its third positional
argument. AC-0035 constrains the keep-set handed to the **shipped guard**,
and the narrowing happens *inside* `select_removal_set`, so that spy sits one
level above the thing the criterion names. Instrumented 2026-09-23: the spy
reports 9 paths while `_plan_stale_owned_paths` is handed 3.

Repaired by `test_apply_keep_set_handed_to_the_shipped_guard_is_full_replayed`,
which spies `_plan_stale_owned_paths` itself and drives a scoped run. It
carries an explicit teeth assertion — the in-scope subset must be a proper
subset — so it cannot pass on a fixture where narrowing would be a no-op.
Re-run against the same mutation: the suite is now red, and that test is the
one that fails.

**Generalisation for the remaining tasks.** A spy proves the call it watches,
not the call downstream of it. When a criterion names an argument to a
specific function, spy that function — not a wrapper that happens to take a
similarly-shaped argument.

## Execution — wave 3

### T6 — `_run_apply` and the exit rows

Every apply row of AC-0039's table is driven to its code by its own test; 33
new tests. Gates: lint exit 0, full `packages/agentbundle/tests/unit` suite
exit 0 over 3,246 tests.

**Mutation proof.** Disabling `_narrow_replayed_paths` — so the replay's
possibly-widened `file_bytes` passes through unnarrowed, which is the
AC-0068 defect stated exactly — turns the suite red across several tests.
§ Grounding's widening derivation is why this guard exists: 28 of 32 recorded
selection values widen to the source's full contents with no refusal, across
both `packs` and `profiles`, and only a valid non-empty list of shipped names
narrows.

### Three deviations, recorded because two are more than they look

**1. `apply_write_sequence` was split.** T6 divided T4's landed function into
`plan_write_set` (read-only classification) and `execute_write_sequence`
(gate recheck onward), keeping `apply_write_sequence` as a thin composition of
both. This was structurally necessary, not cosmetic: `_run_apply` must insert
the consent prompt between the snapshot build and the gate recheck, which is
the ordering AC-0039's trailing note fixes — AC-0076 builds the snapshot
before the prompt, and the gate row sits below the consent rows. T4's single
call shape did not expose that seam. Every T4 test passes unchanged, which is
the behaviour-preserving evidence.

**2. An unauthorised ride-along that qualifies on its merits.** T6 extracted
`_managed_paths_container_is_array` out of `_run_dry_run`'s inline block so
the apply path reuses it rather than carrying a second copy. Its report says
"Bundled fixes: none", which is inaccurate — this is a ride-along edit to
phase-2 shipped code.

Judged against the carve-out's four clauses it passes all of them: it fires no
risk trigger standalone, changes no behaviour and resolves no design call, is
verifiable as a literal extraction with the suite green, and touches no file
defining what an agent may do. The fault is mine, not the implementer's: the
dispatch brief must explicitly authorise the carve-out in supervisor mode and
mine did not. Kept, because reverting it would restore the duplication
AGENTS.md's Cut-before-adding ladder exists to remove. **Remaining briefs
should state whether the carve-out is authorised.**

**3. One `except Exception` added**, on the apply path's `replay_derivation`
call, mirroring `run()`'s existing resolver handling. AC-0040 requires every
failure to reach a named row rather than an uncaught traceback setting the
exit status, so a bare catch is the criterion's own demand here rather than a
smell. `_run_dry_run`'s narrower catch is untouched.

### Gap carried forward to T7

`_run_dry_run` and `--check` do not yet apply AC-0068's per-field validation
or accept the scoping flags, so AC-0039's "or `--dry-run`" half of rows 4 and
5 is currently exercised only through the apply path. T7 owns the preview half
of AC-0043 and AC-0030's `--check` clause. T7's `Touches:` names `cli.py`
only, so if wiring those genuinely needs a `catalogue_sync.py` change, that is
a plan error to surface rather than an edit to make quietly.
`_resolve_effective_selection` and `_narrow_replayed_paths` were written to be
reusable from the parser side without a second edit here.

## Execution — wave 4

### T7 — the parser admits an apply run

`cli.py` relaxes the `--dry-run`/`--check` group so a bare invocation reaches
`_run_apply`, adds `--yes` to that group, registers the three scoping flags,
sets `allow_abbrev=False` on the `sync` subparser, and drops the
read-only claim from the help text. `catalogue_sync.py` narrows `_run_dry_run`
by the CLI scope and refuses a scoping flag alongside `--check`. Gates: lint
exit 0, full suite exit 0 over 3,257 tests.

**Mutation proof.** Neutering the `--check`-with-a-scoping-flag refusal turns
the suite red, so AC-0030's `--check` clause has a check that fails when
broken.

### `Touches:` is not an authorization boundary — resolved, no amendment

T7 stopped rather than edit `commands/catalogue_sync.py`, which its `Touches:`
omits, and asked. That was the right instinct and the answer is that the field
does not gate edits. `Touches:` is read in exactly one place —
`loop-cohort.py:1546`, the wave disjointness screen, labelled in the tool's own
output "serialize-only, never a greenlight". What governs the edit budget is
plan.md § Constraints: "The apply path extends `commands/catalogue_sync.py`.
Outside it and `cli.py` there are exactly two edits" — so both of those files
are freely editable and the budget binds only outside them. T7's `Touches:`
under-named its file set. Metadata inaccuracy, not a plan error; no controlled
amendment owed.

### A defect T7 found in its own first attempt

Filtering `planned_paths` BEFORE classification, rather than filtering the
classified `verdict_rows` after, corrupts stale-removal detection: every
recorded path outside the scope is then miscounted as `would-remove`. This is
the same class as the delivery's first feared defect — narrowing an input that
the removal logic reads as its keep-set — arriving on the preview path instead
of the apply path. Caught by a real failing test, then fixed by mirroring
`_apply_acted_rows`'s post-classification filter.

### Observation carried to post-GATES review: AC-0039 row order vs evaluation order

AC-0039 lists, in order: `source could not be resolved or its integrity could
not be verified` (3), then `a --pack or --profile name the resolved source
does not ship` (2), then `a recorded selection field is present and invalid`
(3). `_run_apply` and now `_run_dry_run` evaluate `_underivable_condition` and
`_resolve_effective_selection` BEFORE `replay_derivation`, so for an input
matching both the source row and the invalid-selection row the code reports the
selection row, where the table's first match is the source row.

No exit-code contract is violated: both rows carry `3 — cannot-answer`, and
AC-0039 governs the code. The unshipped-name row at code 2 cannot be reached
out of order, because the table's own note fixes that whether a source ships a
name "is not decidable until the source resolves".

What made it visible was a phase-2 test asserting the refusal MESSAGE: it
expected `source could not be verified` and got `the recorded packs selection
is invalid`. T7 adjusted that fixture so the test still exercises the row its
comment names. That is a legitimate fixture repair, but it does mean the
ordering discrepancy is now unobserved by any test. **Recorded here for the
post-GATES adversarial reviewer to judge** rather than repaired against a
frozen plan, since the remedy is a row-order question and AC-0039 is § Ask
first territory.

## Execution — wave 5

### T8 — the walk covers both trees

Test-only, as the task predicted: `SYNC_TREE_WALK_CASES` is untouched and a
second registry `SYNC_TREE_WALK_PERMITTED_DIFFERENCE_CASES` carries the four
apply rows with their own parametrised test. Folding them into the existing
unconditional `after == before` test would have forced that assertion to
weaken for every row it already holds. Declined and refused stay on the
unchanged-tree rail — four rows, not five; matching arity is not
correspondence. Gates: lint exit 0, full suite exit 0 over 3,261 tests.

**Mutation proof — because the agent's own non-vacuity check was removed.**
T8 verified its four cases produce non-empty diffs with a scratch assertion
and then deleted it, so that proof no longer lived in the tree. Re-established
independently:

| Mutation | Result |
| --- | --- |
| `write_merged_state` becomes a no-op | red, and the failing case is `sync-apply-0-success` — the row whose expected diff names the state file |
| `_confined_unlink` reports success and unlinks nothing | red |

A walk-comparison test over a fixture where nothing changed passes against any
implementation, so this was the task most exposed to a vacuous pass in the
whole delivery. It is not vacuous.

### T9 — the durable outputs

Eight files: the architecture doc, phase 2's frozen spec, the guide and its
projection, and the five release surfaces. Gates: lint exit 0, full unit suite
exit 0 over 3,261 tests, `lint-spec-status` clean,
`lint-contract-item-alignment` 0 findings, the entry-link gate exit 0, and
`make site-link-check` clean at 94,865 links across 481 pages.

**The release surface is derived, and I re-derived it.** All five read
`0.49.0` and the derivation reports agreement. Before the change all five read
`0.48.0` and agreed, so the bump moved the whole closed set rather than a
hand-listed subset. The derivation supplies that set from the version-bump
rule plus the package's declared readme, so a surface added upstream would
appear rather than be silently omitted.

**The frozen spec took exactly one line.** `catalogue-sync-dry-run/spec.md` is
`Status: Shipped`, and the diff is its Status line alone, carrying a
supersession pointer that names AC-0013's "neither or both" malformed row for
the "neither" case and AC-0015's no-write walk coverage of the bare
invocation. Body, criteria and everything below the preamble untouched —
which is the only edit shape a frozen spec accepts.

**AC-0061's oracle is resolution, so each citation was opened.** All four in
the edited architecture file resolve to the construct the prose names:
`initialise_self_hosted.py:1611` is the `CONFLICT`-abort `return _fail(...)`;
`:1623` is `atomic_write(dest, content)`; `commands/_common.py:225` is
`pack_major = _major(declared)`, inside `check_spec_version_gate` which is
defined at line 203, exactly as the prose claims; `catalogue_init.py:202` is
`source=Path(source_raw).resolve()`. An absence check would have passed a
wrong re-pin just as readily.

**The projection is a gitignored build artifact.** T9 reported regenerating
the guide's projected copy and `git status` shows no such file, which looks
like a discrepancy and is not: `docs-site/src/content/docs/guides/...` is
ignored and rebuilt by `tools/build-site.py`. Both copies carry the new
section, and the rendered-link gate ran against the regenerated tree.

`npm ci` was run for `docs-site/` and `web/` to make the site gate runnable.
Both `node_modules/` trees are gitignored, and no untracked file reached the
working tree.

**Changelog placement follows the repo's ordering.** `0.49.0` is topmost in
`packages/agentbundle/CHANGELOG.md`. In `docs/product/changelog.md` the order
is `[Unreleased]`, then the `core` entry adjacent to it, then
`[agentbundle][0.49.0]` below — the pack entry sits under core, not above it.

## Execution — wave 6

### T10 — an adopter's apply run, exercised end to end

Visual / manual QA, run by the controller against the real built artifact.
AC-0056 requires the ledger to record **the comparison**, not only the
observed output, so the comparison is below.

**The invocation had to be pinned, and this is the finding worth keeping.**
A bare `python3 -m agentbundle.cli` from this worktree resolves to
`/Users/eu.gene.lim/orca/agent-ready-repo/packages/agentbundle/` — the primary
checkout — because that is where the editable install points. The first
invocation reported `agentbundle 0.48.0` and a `sync` help string still
reading "Read-only: writes nothing.", both of which this delivery had already
changed. A manual QA run taken at face value would have exercised the wrong
code and reported a false pass.

The unit suite is unaffected: pytest inserts the worktree's package path ahead
of the install, verified directly — `agentbundle.__file__` under pytest
resolves inside this worktree and `select_write_set`, `apply_write_sequence`
and `safety.Publish` are all present. Every gate run in this ledger is
therefore against this worktree's code. Manual invocation needs
`PYTHONPATH=<worktree>/packages/agentbundle`, which reports `0.49.0` and the
new help text.

**The run.** A 650-file tree derived by `catalogue init --preset self-hosted`
from a 3,387-file source (`--pack core --guides selected --tooling external
--attribution white-label`), edited at one recorded path
(`guides/_shared/README.md`), then synced from a source **moved** to a
different path than init used. Dry-run first: it classified the edited path
`would-companion` and everything else `would-update`. Apply run: exit 0,
`would-update=648 would-companion=1 would-remove=0 deferred-package=0`.

| AC-0056 condition | Result | Evidence |
| --- | --- | --- |
| Run exits 0 | PASS | observed exit status |
| Companion beside the edited file carries the source bytes | PASS | `guides/_shared/README.upstream.md`, bytes equal to the source file, `st_nlink=1`, no staged residue |
| The adopter's file's digest is unchanged | PASS | `584dfa97c13da1bc650b6cd7` before and after; the `<!-- ADOPTER EDIT` marker is still in the file |
| No path outside the printed plan is altered | PASS | 650 paths changed, plan 651, **0 outside** |

`st_nlink=1` with no staged residue is the post-publish state AC-0070's third
outcome requires, measured on the real artifact rather than a fixture. A link
publish that skipped its unlink would read 2 here, and § Grounding's publish
probe established that this repository's own confined reader refuses a link
count above one.

**A harness defect I made, and corrected.** The first run took its before-walk
*before* the adopter edit, so condition 3 compared a pre-edit digest against a
post-sync one and reported FAIL. The product was correct throughout — the
after-digest equalled the post-edit digest exactly. The whole experiment was
re-run with the baseline taken after the edit and immediately before the sync,
which is what AC-0056's "unchanged" actually quantifies over. Recorded because
a mis-timed baseline is the one way this manual check fails against working
code, and the next person to run it should take the baseline at the same
moment.

## Post-GATES review — round 1

Three reviewers over the merged diff, each adjudicated by a separate neutral
adjudicator. 22 raw findings, **19 sustained**, 3 refuted. Three distinct
Blockers, two of them found by two lanes independently.

The pre-EXECUTE rounds could only audit the contract. All three Blockers were
implementation gaps no amount of spec review would have reached, and every
gate was green when they were found: lint 0, 3,261 tests, and a manual
end-to-end that passed all four AC-0056 conditions on a real tree.

### The three Blockers

**An admitted write path with neither AC-0077 recheck.** `execute_write_sequence`
built its gate map only from `would_update_admitted`, so a path admitted by
AC-0033 clause 3's introduced-pack branch fell to a bare `write_jailed` at
`Publish.REPLACE`. Any `--pack <new-name>` run over a tree where the adopter
already held that path overwrote it — no recheck, no companion — while the
printed plan showed the row as `untouched`.

**`--package` was never registered.** Measured: `catalogue sync --package
credbroker` died in argparse as an unrecognized argument, so AC-0047's
cannot-answer row was unreachable. Both tests passed only by setting
`args.package` on a hand-built namespace, which AC-0030's oracle forbids.
After the fix, measured again: both recognised names exit 3 naming the package
on apply, `--dry-run` and `--check`; an unrecognised name is malformed at 2.

**A deletion the printed plan never named.** The removal set was computed
before the prompt for display and recomputed inside the write sequence after
consent, so a recorded path that appeared during the prompt was deleted having
never been printed — § Never do's phase delta verbatim. Now computed once and
passed through.

### Two relayed remedies were wrong, and driving the test caught both

The adjudicators were reliable about every defect and wrong about two fixes.
Both were caught the same way: by driving the required test first.

**Blocker 1's formula.** The adjudicators proposed taking each expectation
from the snapshot — digest when `kind == "file"`, else `None` — applied
uniformly, and the controller relayed it. `classify` never reads an
introduced-pack destination, so a snapshot-derived expectation is whatever the
adopter already has there, and it passes its own recheck unchanged. The fix
is an unconditional `None` for that row class. Confirmed by mutation: the
relayed formula turns the test red, as does the pre-repair scope.

**P3's restore scope.** The brief said to include a failed companion
destination in `restore_scope` unconditionally. Applied literally it broke an
already-green test by deleting another writer's raced-in file when the LINK
itself failed rather than the unlink. The implementer drove that test, saw the
regression, and guarded on content instead: restore only when the destination
holds the exact bytes this run tried to publish.

**Standing lesson, now in every repair brief.** A reviewer's remedy is a
hypothesis, not a work order. Drive the test first; if the prescribed fix does
not make it pass, say so with evidence rather than substituting quietly.

### Five more checks that could not fail

The class this delivery has now hit eight times. Two were verified by the
controller directly rather than taken on the adjudicator's word:

`issubclass(WriteError, FileExistsError)` is `False` — measured. So
`assert not isinstance(exc_info.value, FileExistsError)` was `True` for every
error `write_jailed` can raise, and the property it existed to pin — that an
`EPERM` from a link-less filesystem is not misread as occupancy, the exact
residual § Grounding's publish probe flagged — was unguarded. Now asserted
through the raised error's `__cause__.errno`.

Its sibling, `assert dest.is_symlink() or dest.exists()`, passed for any
implementation leaving anything at the destination, including one that
overwrote a regular occupant's bytes and then raised. Now a full pre/post walk
tuple.

The third gate case was worse than reported: the `__qualname__` guard meant to
select it was dead code, because a lambda's `__qualname__` never carries the
`ids=` label. All three cases asserted the same changed-digest shape.

### Mutation proof for the repairs

| Mutation | Result |
| --- | --- |
| gate expectation reverted to `would_update_admitted` only | red |
| introduced rows expect the live snapshot (the relayed formula) | red |
| snapshot lstat errors collapsed back into "absent" | red |
| post-write receipt call removed | red |

Final gates after all 19: lint exit 0, full unit suite exit 0 over 3,275
tests — up from 3,261, so the repairs added net new covering tests rather than
relaxing existing ones.
