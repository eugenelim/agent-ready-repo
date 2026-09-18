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
