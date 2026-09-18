# Verification ledger — catalogue sync, dry-run and check

Execution observations, one section per wave. The plan contract sends them here
rather than into the plan, which is hash-pinned from `plan-locked` onward.

## Wave 0 — T0: the grounding derivations exist and the marker conflict is resolved at its owner

- **Date:** 2026-09-17
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`, cycle `:17`
- **Worker:** headless Codex (`gpt-5.6-terra`, medium reasoning), supervised.
  188,453 tokens. Codex owns repository reasoning and implementation; the
  supervisor owns scheduling, git, gates, and verification.

### What was built

Nine derivation scripts plus a shared `_common.py` under
`docs/specs/catalogue-sync-dry-run/notes/grounding/`, and `decisions.md` as the
discovery channel's append-only record. `packages/AGENTS.local.md` already
carried the criterion-ordinal exemption from the spec-drafting work, so it was
verified rather than rewritten.

### Derived values, as the scripts printed them

| Script | Derived |
| --- | --- |
| `probe-sink-class.py` | 12 sink-class members admitted, hostile variants and non-strings rejected; length bound 4096, exact |
| `probe-tier.py` | `unrecorded=tier-3, absent=tier-1, matching=tier-1, changed=tier-2, present_null_sha=tier-2` |
| `probe-mypy-scope.py` | three typed package directories, none under `docs/**`; `no_strict_optional: True` |
| `derive-decline-branches.py` | 6 decline branches; reason-emitting at lines 1073, 1084, 1096 |
| `probe-digest-provenance.py` | `archive+https` digest adopter-supplied from the URI fragment; `catalogue+https` digest is the descriptor's `sha256` from the same origin |
| `derive-subcommands.py` | 9 direct children of `catalogue` |
| `derive-citations.py` | `derived-catalogue.md:1145`, `upstream-sync.md:1145` |
| `derive-site-gates.py` | entry-link gate reads authored guides; rendered-link gate reads the generated tree |
| `derive-release-surfaces.py` | `version.py`, package `pyproject.toml`, package and product changelogs, PyPI README |

### Residuals reported

- Decline guard: 3 silent branches, at lines 1066, 1080, 1094.
- Subcommands: `contracts` carries 3 nested verbs — `list`, `show`, `export`.
- Citations: `:1137` references in both architecture documents are unresolvable
  by the derivation; § Follow-ons owns that residual and T10 does the re-pinning.
- Release surfaces: unclassified candidates are new-command documentation and
  release-automation tag assertions.
- The sink-class, Tier, mypy, digest and site-gate probes each reported no
  residual.

### Kill condition

Did not fire. Every enumerated member of AC-0012's declared sink class was
admitted, and the exact length boundary held.

### Supervisor verification — independent of the worker's report

- All nine § Grounding commands re-run from the repository root: **exit 0**.
- `make lint-ruff`: **All checks passed**.
- `lint-spec-status.py --root .`: **clean metadata**.
- `lint-contract-item-alignment.py`: **0 findings**.
- Criterion-ordinal labels under `packages/agentbundle/tests/`: 6 labels across
  3 files, every one bare — no path and no section reference (AC-0028, AC-0029).
- `derive-decline-branches.py` derives via `ast.walk` over
  `_remove_stale_owned_paths`, not a hand count.
- `derive-release-surfaces.py` derives from the version-bump rule text and the
  release-coupling definition, and fails closed when that rule is absent. It
  does not enumerate by searching for the current version string, which is the
  self-selection defect a round-1 finding sustained against the earlier draft.
- **`probe-tier.py` was proved able to fail.** Its expected verdicts are `Tier`
  enum members written independently of `classify`, so the comparison is not
  sourced from the table under test. Flipping the `changed` expectation to
  `TIER_1` in place produced `Tier classifier differs for changed`, exit 1;
  the file was restored from a pre-mutation copy and its SHA-256 re-verified as
  `0f575e4bc9408eb2a89e22067ad90d3113dfabf36260cb40d40a22430ebb328f`. A first
  attempt at this mutation, run from a scratch directory, failed on `REPO_ROOT`
  resolution instead of on the comparison — a wrong-reason failure that proved
  nothing, which is why the probe was driven through its real invocation path.
- `__pycache__/` under the new directory is ignored by `.gitignore:75` and does
  not enter the staged set.

### Notes

Nothing in T0's contract went unsatisfied. Amendment 001 had already resolved
the script-location question before T0 began, so the discovery channel made no
refinement of its own; `decisions.md` records that and stands ready for later
entries.

## Wave 1 — T1 and T2

- **Date:** 2026-09-17
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`
- **Worker:** headless Codex (`gpt-5.6-terra`, medium reasoning), supervised
  across four dispatches — T1, T2, T2's two repairs, and T2's roster move.
- **Amendments consumed:** 002 (T2's `Touches` gains the decline-branch
  derivation) and 003 (T2's `Touches` gains the roster test and its three
  wiring files).

### T1 — the shared fixture set

Four fixtures in a new `packages/agentbundle/tests/unit/conftest.py`:
`self_hosted_source`, `upstream`, `derived_tree` (schema-3 state, full recipe,
`pin.archive_sha256: null`) and `upstream_with_bumped_pack` (`alpha` 1.0.0 →
1.1.0). The throwaway consumer is
`test_catalogue_sync_fixture_set.py::test_catalogue_sync_fixture_set_composes`,
which asserts the one-pack source, the schema-3 recipe and null digest, and that
the bumped version strictly exceeds the derived one — real assertions, not a
setup smoke test.

No existing fixture was changed or shadowed; the unit `conftest.py` did not
previously exist and the parent `tests/conftest.py` is untouched.

**Fixture fidelity checked against production:** `initialise_self_hosted.py:325`
declares `schema_version: str = "3"` and the fixture writes the string `"3"`, so
the fixture uses production's shape rather than a plausible-looking variant.

### T2 — the removal guard

`_plan_stale_owned_paths(target, old_state, current_paths) -> (removable,
reasons)` in recorded-state order, with `_remove_stale_owned_paths` reduced to
planning then unlinking. Decline branches **6 → 7**, measured by the § Grounding
derivation; all three previously silent branches now emit reasons, and the
derivation reports `residual silent lines: none`.

The seven reasons and their partition, exactly two undecided per the settled
owner decision:

| Reason | Classification |
| --- | --- |
| `malformed-recorded-path` | decided |
| `path-remains-current` | decided |
| `path-confinement-refused` | **undecided** |
| `recorded-path-absent` | decided |
| `missing-recorded-sha256` | decided |
| `recorded-sha256-mismatch` | decided |
| `recorded-entry-unreadable` | **undecided** |

Confinement is driven through `validate_confined_directory` and
`sha256_confined_regular_file` against a real hard link, a real FIFO, and a
symlink. **Platform limit, stated rather than papered over:** macOS has no
native Windows reparse point, so that third condition in AC-0020's wording
cannot be demonstrated on this host; the symlink is the available analogue.

### Two defects found in T2's own verification, and repaired

1. **The undecided partition could not fail for one member.** The assertion read
   `{...} == {undecided fixtures} | {"recorded-entry-unreadable"}`, and the
   fixture table held one undecided entry, so the second member was supplied by
   the union literal rather than observed. Reclassifying it would have left the
   test passing while AC-0013's "could not be compared" condition reads that
   set. Repaired: all seven reasons now carry their classification in one table
   compared against a named `_UNDECIDED_STALE_DECLINE_REASONS` constant, and the
   unexplained `+ 1` count offset is gone. Proved by mutation — flipping
   `recorded-entry-unreadable` to decided fails the test.
2. **The count check shipped broken.** It read the § Grounding derivation
   repo-relatively from `packages/agentbundle/tests/`, which is a *published*
   tree that `gate-export-boundary` runs inside an sdist with no `docs/`.
   Demonstrated by holding the derivation aside: `assert 2 == 0`,
   `[Errno 2] No such file or directory`. Repaired under amendment 003 by
   moving only that check to `tests/roster/test_catalogue_sync_decline_branch_alignment.py`,
   which imports the fixture table and the undecided constant from the unit
   module rather than copying them.

### Supervisor verification — independent of the worker's report

- `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py`
  → **425 passed, 0 failed** in 32s. Codex reported 43–44 failures on each of
  three dispatches; every one was the sandbox's `TemporaryDirectory` cleanup
  `PermissionError` on generated `profiles/` paths, and none reproduced outside
  it.
- **The shipping property, proved on the whole file rather than a subset.** With
  `derive-decline-branches.py` held aside — the sdist's condition — the full unit
  file still reports **425 passed**. The worker had only run 12 of its tests for
  this proof.
- `tests/roster/test_catalogue_sync_decline_branch_alignment.py` → 1 passed.
- `ruff check .` → All checks passed. `tests/AGENTS.md` requires this after a
  move because the repository lint targets do not cover orphaned imports.
- `make lint-ruff` → All checks passed.
- `python3 tools/lint-ci-parity.py` → ok, 91 steps, all dispositioned.
- `tests/roster/test_two_sided_prune_closure_invariant.py` → 47 passed, both
  before and after correcting the entry's alphabetical position.
- The three wiring diffs total **5 inserted lines and 0 deletions** across
  `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py` and
  `.workspace-prune-protected.toml`, each matching its adjacent roster entry.
  The supervisor corrected one cosmetic ordering slip: the prune entry had been
  placed between `caf` and `canonical`.
- A 36 MB `.pytest-tmp-t1/` directory left by the T1 dispatch had poisoned
  `make lint-ruff` with 38 errors from generated Python; it was untracked with
  zero tracked files and was removed. Later dispatches were told not to set a
  worktree-local `TMPDIR`, and none did.

## Wave 2 — T3

- **Date:** 2026-09-17
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`, cycle `:33`
- **Worker:** the `implementer` subagent, running in the supervisor's
  environment rather than a sandbox. This removed the recurring 43-failure
  temp-cleanup artefact that every Codex dispatch had reported.

### What was built

`collect_fields(cfg, source_meta, recipe=None, *, interactive=True)` plus one
local helper `_resolve_field(prompt_text, default, *, interactive)`. All five
`_prompt` call sites — `name`, `display_name`, `description`, `owner_name`,
`owner_email` — route through it, and it returns the default unprompted when
`interactive=False`. The remaining config fields never called `_prompt` and are
unchanged.

`_is_attributed` was not touched and remains the sole attribution gate.

### Supervisor verification

- `pytest …/test_catalogue_tooling_self_hosted_init.py` → **426 passed** in 29s
  (baseline 425; +1 for the stub).
- `make lint-ruff` → All checks passed. `make lint-mypy` → Success, 149 files.
- The test file's diff is **30 insertions, 0 deletions**, so T3's "no assertion
  edited" condition holds mechanically rather than by assertion.

### A verification-depth limit, found by mutation and recorded rather than hidden

T3's stub asserts the right outcome but **cannot fail for its criterion in one
step.** Mutating `collect_fields` to prefer a recorded attribution left the test
passing, because `_SelfHostRecipeInput` carries nine fields and no mode, so the
attribute does not exist and the read falls through. `_load_self_host_recipe`
drops the recorded modes before `collect_fields` is reached, so that dataclass —
not `collect_fields` — is what enforces "the modes never come from state".

AC-0003's own text describes a **`--dry-run` invocation**, and a search of the
plan found AC-0003 named in exactly two places, both inside T3. No task drove
the invocation the criterion describes. The contract-alignment lint could not
see this, because it checks only that some task names each criterion, not that
the naming task's seam can express the violation.

Amendment 004 adds the end-to-end case to T5, where the verb first exists.

### Process note

One mutation attempt here was invalid: a script asserted out before applying its
edit, and the test command chained after it still printed `1 passed`, which
evidenced nothing. The file's SHA-256 was confirmed unchanged at
`546ce645c24dda76da934b44b32e0eebae9a612465de3221f6e7c98b6aa06ba7`. A failable
edit must not be chained with the step that reads its result.

## Wave 3 — T4

- **Date:** 2026-09-17
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`, cycle `:41`
- **Worker:** the `implementer` subagent.

### What was built

`replay_derivation(cfg, *, interactive=True) -> DerivationReplay` lifts steps
1–9 out of `init_self_hosted`, which is now its caller plus steps 10–14 reading
everything through `replay.*`.

### Deviations from the task's `Approach`, recorded here because the plan is pinned

The plan's contract block makes `Approach` working material "corrected in place
as the work teaches", but `plan.md` is hash-pinned from `plan-locked` onward, so
these are recorded in the ledger — which that same contract names as the home
for execution observations — rather than by editing a frozen plan.

1. **`DerivationReplay` carries 14 fields, not the 8 the `Approach` names.** The
   extra six — `source_meta`, `source`, `old_state`, `field_collection_mode`,
   `recorded_recipe`, and the split of "selections" into `pack_names` and
   `profile_names` — all existed in the original function body between steps 1
   and 9 and are read by steps 10–14. Without them `init_self_hosted` cannot
   keep working unchanged, which is T4's `Done when`.
2. **A new `ReplayError(cfg, messages)`** carries the steps 1–6 precondition
   failures, since `replay_derivation`'s contract is to return a
   `DerivationReplay` and those are hard stops before one exists.
   `init_self_hosted` catches it and rebuilds the identical
   `SelfHostedInitResult`.
3. **`leak_scan_result` is not carried** on the replay; it is derivable from
   `violations`, and `init_self_hosted` still builds it locally as before.

### The phase-3 boundary — verified, not taken on report

The two constructs reserved for phase 3 are **untouched**, confirmed by grepping
the diff rather than by reading the worker's claim:

- the `CONFLICT` abort, now at `:1608-1611`;
- the unconditional overwrite, now at `:1618-1638`.

`git diff -U0` over `initialise_self_hosted.py` contains **no** line mentioning
`CONFLICT`, `conflict_plans`, `commit_files` or `owned_planned`. Both constructs
have now moved twice across T2 and T4, which is why they are named semantically
in every brief instead of by the line numbers the original constraint used.

### The whole-tree walk helper

`walk_target_tree(root)` in `test_catalogue_tooling_self_hosted_init.py:2514`.
Verified non-dereferencing: `os.walk(..., followlinks=False)` with
`entry.lstat()`, recording per relative path the entry kind, `stat.S_IMODE`, the
symlink target via `os.readlink`, and bytes for regular files only. No
timestamp, hard-link count or extended attribute is recorded, matching AC-0015's
stated exclusions.

Parametrised through a `TREE_WALK_CASES` registry over the three AC-0013 rows
T4 can reach without a CLI: `replay-success`,
`replay-identity-leak-violation`, and `replay-source-validation-failure`. Later
tasks import the helper and add their own rows rather than copying a walk.

### Supervisor verification

- `pytest …/test_catalogue_tooling_self_hosted_init.py` → **432 passed** in 32s
  (426 + 6 new), and **zero skipped** under `-rs`. That last check matters
  because the suite carries a POSIX-only `st_nlink` skip guard for T2's
  hard-link confinement case; it does not fire on this platform, so AC-0020's
  oracle really runs.
- `pytest …/test_catalogue_init_cli_self_hosted.py` → **16 passed**, untouched
  by the diff.
- `make lint-ruff` → All checks passed. `make lint-mypy` → Success, 149 files.
- Test-file diff is **188 insertions, 0 deletions**, so "no assertion edited"
  holds mechanically.

### Note carried forward to T5

The AC-0015 stub calls `replay_derivation(cfg)` and therefore runs with
`interactive=True`; it passes because the test environment is not a TTY, so the
prompt path resolves to defaults anyway. Nothing yet exercises
`interactive=False` through the replay. T5's command module is what must pass
`interactive=False`, and T5's own AC-0003 case is what will observe it.

## Wave 4 — T5

- **Date:** 2026-09-18
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`, cycle `:43`
- **Worker:** the `implementer` subagent.

### What was built

`agentbundle catalogue sync [TARGET] --source <uri>` registered in `cli.py`
beside `init`, implemented in the new `commands/catalogue_sync.py`, with 17
tests in the new `test_catalogue_sync.py`. The command calls
`replay_derivation(cfg, interactive=False)` — always explicitly, never the
default — so a TTY cannot seed a prompt from this read-only path. The extracted
directory of a digest-bearing fetch is cleaned in a `finally:` block, so it goes
on the success path, on a `ReplayError` refusal, and on any other exception
alike.

The four source forms and their fidelity tokens:

| `--source` form | dispatch | token |
| --- | --- | --- |
| local filesystem path | `resolve_catalogue` | `local-path` |
| `git+https://` | `resolve_catalogue` | `git-tls` |
| `archive+https://…#sha256=<64hex>` | `fetch_catalogue_archive_with_provenance` | `digest-adopter-pinned` |
| `catalogue+https://` | `fetch_catalogue_archive_with_provenance` | `digest-publisher-asserted` |

The two digest forms carry distinct tokens because the digest's provenance
differs: the adopter supplies it in the URI fragment, versus the publisher
asserting it in a descriptor the same origin serves.

`--dry-run` and `--check` are an argparse mutually exclusive group with
`required=True`, and `--source` is `required=True`, so "neither or both" and an
omitted source are parser-level refusals rather than hand-written checks.

### AC-0003's end-to-end case is load-bearing — proved by mutation

`test_sync_dry_run_replays_flag_modes_not_recorded_ones` writes
`attribution="attributed"`, `tooling="vendored"`, `guides="none"` into the
derived tree's state, invokes the real parser with none of the three mode flags,
and asserts the printed plan shows `white-label`, `external`, `selected`.

Mutating `run()` to fall back to a recorded mode produced the red the criterion
needs:

```
AssertionError: assert 'white-label' in 'fidelity: local-path
modes: attribution=attributed tooling=external guides=selected …'
```

This is what T3's seam could not do, and it is the reason amendment 004 put the
case here.

### A real defect the identity leak check caught, reproduced by the supervisor

The `--source` help text first read "**Upstream catalogue** URI: …", which
collided case-insensitively with a fixture's `display_name = "Upstream
Catalogue"` in three unrelated `vendored`-mode tests. Those fixtures copy the
whole live `agentbundle/` tree — `cli.py` included — into a derived catalogue and
run the real leak check over it, so a help string became a reported identity
leak.

Reproduced deliberately rather than taken on report: reinstating the wording
gives **3 failed, 429 passed**; the reworded text gives **432 passed**. The
three casualties name nothing the change touched —
`test_init_self_hosted_vendored_copies_tooling`,
`test_self_hosted_init_cli_materialises_runnable_conformance[vendored]`, and
`test_credbroker_source_travels_in_both_tooling_modes[vendored]` — so without
the mechanism the failure reads as a regression in the copy machinery. No test
was edited to make it pass; the wording changed.

**Carried forward:** any new help text, prose default, epilog or error message
in `cli.py` or a command module can trip this. T6, T7 and T9 all add rendered
output, so each brief must say so.

### Two deviations, disclosed

1. **`--check` is registered and parses, but `run()` answers it with a fixed
   cannot-answer and an explicit reason** rather than a real comparison. The
   ordered, total exit table is T8's declared work, and implementing it here
   would duplicate that task. Verified safe for T8: **no test asserts the
   placeholder text, and no test asserts `--check` behaviour at all**, so T8 can
   implement the real table without editing an assertion.
2. The `--dry-run` identity-leak row's wiring (`violations` → difference code)
   is present because the replay already computes it, though T5's own bullets do
   not exercise it at the CLI level — § Testing Strategy assigns AC-0004 and
   AC-0005 to the callable.

### Supervisor verification

- `pytest …/test_catalogue_sync.py` → **17 passed**.
- `pytest …/test_catalogue_tooling_self_hosted_init.py` → **432 passed**,
  baseline unchanged. `…/test_catalogue_init_cli_self_hosted.py` → **16 passed**.
- `make lint-ruff` → All checks passed. `make lint-mypy` → Success, **150**
  source files, up from 149 with the new module.
- `derive-subcommands.py` → 10 direct subcommands including `sync`, against the
  recorded pre-change baseline of 9. § Grounding said T5 was expected to add
  one, and an unchanged count would have been the failure.
- Tree-walk rows added: `sync-dry-run-success` and `sync-resolution-refusal`,
  both asserting the target is byte-identical before and after, including an
  adopter-owned file already present. The helper is imported from T4's module
  rather than copied.

## Wave 5 — T6

- **Date:** 2026-09-18
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`, cycle `:45`
- **Worker:** the `implementer` subagent.

### What was built

`catalogue_sync.py` gained the AC-0009 underivable-selection guard
(`_underivable_condition`, checked **before** `replay_derivation` so a discarded
or absent selection can never widen to "every pack"), the Tier-verdict and
seven-count reconciliation (`_classify_planned_paths`, built on `safety.State`
plus `classify`, reusing T2's `_plan_stale_owned_paths` for the removal side),
and `packs`/`profiles`/`summary`/`verdicts` rendering on both the table and JSON
surfaces.

### The count identity, and the evidence it can fail

The denominator is `old_state["managed_paths"]` read **raw and unfiltered**.
Entries `_migrate_managed_paths` drops contribute `len(raw) - len(migrated)` to
`uncompared`; survivors failing `_is_safe_recipe_text`, or duplicating a seen
path, also land there. `path-confinement-refused` and
`recorded-entry-unreadable` stay `uncompared` per AC-0017's undecided partition.
`untouched` is counted over planned paths that are not recorded at all, outside
the identity's denominator.

Proved failable by mutation: dropping the `uncompared` increment on the
malformed branch produced `assert (2 + 1) == (2 + 2)` — the identity failing by
exactly the dropped entry — then restored to 35/35 and 432/432.

**Supervisor check on non-triviality:** the T1 fixture records more than zero
`managed_paths`, so `compared + uncompared == 0` cannot satisfy the identity.
That matters because the plan names the identity as this task's inline proof,
and an identity over an empty denominator proves nothing.

### The five path states, decided by the real classifier

Driven through one `derived_tree` run, each landing in exactly one bucket:

| path | recorded state | verdict |
| --- | --- | --- |
| `packs/alpha/pack.toml` | present, sha matches | Tier-1 → `would-update` |
| `packs/alpha/README.md` | present, sha differs | Tier-2 → `would-companion` |
| `packs/alpha/extra.md` | present, `sha256: null` | Tier-2 → `schema-1-inert` |
| `catalogue.toml` | not recorded | Tier-3 → `untouched` |
| `packs/alpha/stale.md` | recorded, dropped by source | → `would-remove` |

The companion path is asserted against `safety.companion_path(...)`'s own
output rather than a locally assembled string — verified in the test source.

### AC-0009: every loader failure, not three of them

All six `_load_ownership_state` `None` returns were driven — confinement
refusal via a symlinked state file, invalid UTF-8, invalid JSON, a non-object
document, an I/O error, and recursion exhaustion — each reporting "the
ownership-state loader could not return a state object" and exiting 3. Plus no
state file, no `recipe` key, a non-object recipe, a recipe with neither `packs`
nor `profiles`, and a discarded selection.

### Two deviations, both examined

1. **The AC-0016 stub's literal `== 1` was not kept.** T1's committed
   `derived_tree` records two `managed_paths` entries, not one, so the literal
   was an artefact of a one-entry scratch fixture. The test now reads the
   denominator from the state document on disk. **No amendment is owed:** the
   pinned contract states the identity as `compared + uncompared ==
   len(raw managed_paths)` (`spec.md:348`), and reading the real length conforms
   to that more closely than the literal did. The comparison stays independent —
   the length is read from the document, not from the command's output.
2. **`_sync_dry_run_success_row`'s setup gained a minimal derivable state.**
   T6's own AC-0009 guard makes "no state file" a cannot-answer, and T5's
   success row predated that guard; without the fix the row would have regressed
   from 0 to 3. Same test file, inside T6's `Touches`.

### Supervisor verification

- `pytest …/test_catalogue_sync.py` → **35 passed** (baseline 17).
- `pytest …/test_catalogue_tooling_self_hosted_init.py` → **432 passed**, no
  regression.
- `make lint-ruff` → All checks passed. `make lint-mypy` → Success, 150 files.
- Tree-walk rows added: `sync-dry-run-would-companion`,
  `sync-dry-run-would-remove`, `sync-dry-run-underivable-selection`. The
  registry was restructured to `(setup, invoke)` pairs so per-row fixtures land
  before the "before" snapshot — without which the new stateful rows were
  failing the no-write assertion for the wrong reason.

### Noted, not fixed

A recorded path appearing twice is counted as a second `uncompared` entry, since
no unique verdict exists per duplicate raw entry. AC-0016's text does not
require this and it is not separately tested; the implementation fails closed
rather than under- or over-counting.

## Wave 5 — T9

- **Date:** 2026-09-18
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`, cycle `:45`
- **Worker:** the `implementer` subagent, over two passes.

### What was built

Four warn-only compatibility signals rendered as advisory rows that never change
the exit code (AC-0018), plus `check_spec_version_gate` reused verbatim for the
adapter-contract-major refusal (AC-0019). New in `catalogue_sync.py`:
`compatibility_warnings`, `check_adapter_contract_gate`, `_pack_toml_from_replay`
and `_read_baseline_pack_toml`. A fixture pack declaring adapter-contract major
`1` lives at
`packages/agentbundle/tests/fixtures/catalogue_sync/adapter_contract_major_mismatch/pack.toml`,
because every pack shipped in this repository declares major 0 — without it the
refusal could not fail.

### The four signals, each with both arms

| Signal | Marker | Absent arm | Present arm |
| --- | --- | --- | --- |
| `pack-version-changed` | `pack version` | 0 (constant pin) | 0 |
| `adapter-contract-version-changed` | `adapter-contract version` | 0 | 0 |
| `required-dependency-unmet` | `required dependency` | 0 | 0 |
| `conflicts-dependency-violated` | `conflict with` | 0 | 0 |

Each pair asserts `exit_absent == 0` and then `exit_present == exit_absent`, so
the pair cannot both drift to the same wrong value. The present arm's
adapter-contract version declares major 0, so AC-0019's gate does not also fire
and contaminate the warn-only observation.

### Refusing the "shared code path" argument found dead code

The first pass parametrised only two of the four signals, on the grounds that
adapter-contract-version "shares the same comparison code path as pack-version,
so a third arm would test the same branch shape rather than a new one."

That was refused: AC-0018 pins the property **per signal** — "one advisory row
per signal" — not per code path, and a shared path is where divergence hides
because the two signals read different manifest keys.

Sending it back established the signal **could never fire**. The comparison
required *both* sides to declare a version string, and `derived_tree`'s baseline
declares no `[pack.adapter-contract]` table at all, so the branch was
unreachable. The missing test arm was concealing dead production code, and the
"same branch shape" claim was false — the branch was never entered. The
comparison now fires whenever either side declares, showing `absent` for the
missing side. No advisory template's wording changed.

### The AC-0020 oracle has the right pass direction

The derived-tree baseline read goes through the declared helper:

```python
baseline_bytes = read_confined_regular_file(target, baseline_path)
```

`test_sync_reads_derived_tree_baseline_through_the_confinement_helper`
monkeypatches that exact name on `catalogue_sync` to raise `UnsafeContentError`
and asserts the pack-version signal disappears. An inline lexical-prefix check
would not observe the patch, so the test fails a mutation an inline substitute
would pass — which is the distinction AC-0020 exists to draw.

### Supervisor verification

- `pytest …/test_catalogue_sync.py` → **43 passed** (35 → 41 → 43 across the two
  passes). The four compatibility arms pass under `-k compatibility_signal`.
- `pytest …/test_catalogue_tooling_self_hosted_init.py` → **432 passed**, no
  regression and no identity-leak trip from the new advisory strings.
- `make lint-ruff` → All checks passed. `make lint-mypy` → Success, 150 files.
- Tree-walk row added: `sync-dry-run-adapter-contract-refusal`, proving the
  target is byte-identical across a refusal as well as a success.
- **Sdist boundary re-checked.** `packages/AGENTS.md` warns that a test in this
  published tree reading a repository path "passes locally and fails the sdist
  artifact gate". Three tasks have added tests here since T2's roster move, so
  the suite, the unit conftest and the fixture-set test were swept: no `docs/`
  read, no repository-root walk, and the new fixture resolves inside the package
  tree.

### Noted, not fixed

`commands/verify.py`'s dependency-graph walk and `install.py`'s
`validate_dependencies_required` each re-parse `pack.toml` per pack rather than
sharing one confined-read seam. Outside T9's `Touches`.
