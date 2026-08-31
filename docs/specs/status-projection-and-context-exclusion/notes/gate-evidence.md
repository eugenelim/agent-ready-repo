# Gate and mutation evidence — RFC-0096 Wave 6

Recorded during EXECUTE. Every mutation was applied by editing the source,
verified to redden its named test, and restored with the target file's digest
re-asserted afterwards.

## Mutation proofs

A harness ran each case with three preconditions, because prose warnings had
already failed three times in this repository: the target must have no
uncommitted changes (`git checkout --` restores HEAD, so on uncommitted work it
destroys what you are proving), the anchor must occur an exact expected number
of times, and the file digest must match its pre-run value after every restore.

### T1 — 6/6 killed

| Mutation | Reddens |
| --- | --- |
| delete the `is_symlink()` refusal | AC10 |
| delete the lifecycle-directory `relative_to` check | AC9 |
| drop the `(disposition, post_closeout_result)` predicate | AC3 |
| store raw locator strings instead of resolved paths | AC12 |
| drop candidate 3's `relative_to` | AC40 |
| ship only `cooling.py` in `_runtime_projections` | AC37 |

Three of these initially **survived** and the tests were repaired, not the
mutations weakened:

- **AC10** asserted only that a symlinked record yields
  `invalid_lifecycle_record`, which `file_safety`'s own `O_NOFOLLOW` produces one
  layer down with the same code. The engine's guard uniquely refuses *before*
  handing the path to the reader, so the test now probes the reader and asserts
  the symlink never reaches it.
- **AC12** resolved the alias itself before comparing, so it held whether or not
  the implementation resolved anything. The record now names the artifact
  *through* the alias and the assertion is on the real path.
- **AC37** compared bytes already on disk, which a shrunk projection list cannot
  disturb until the next clean checkout silently loses the closure. It now also
  parses `_runtime_projections` and asserts all three names are declared.

### T2 — 9/9 killed

| Mutation | Reddens |
| --- | --- |
| Type 1 filter moved below the counter increment | AC16 (AC15 must still pass) |
| predicate matches every spec | AC16 |
| aliases dropped from the cooled set | AC2 |
| `analyze_bounded` stops resolving | AC21, AC22 |
| spec dependency short-circuit removed | AC13 |
| cooled dependency reported `missing_dependency` | AC14 |
| short-circuit moved above the `structurally_blocked_paths` guard | AC55 |
| defect branch stops suppressing its probe | the defect read guard |
| raw `dep.path` compared instead of the resolved path | the alias dependency guard |

### T3 — 8/8 killed

| Mutation | Reddens |
| --- | --- |
| `isinstance` guard deleted alongside the raise | AC44 |
| visibility flag hard-coded `True` | AC33's false half |
| visibility flag hard-coded `False` | AC33's true half |
| dueness hard-coded `True` | AC23 |
| UTC date compare instead of the recorded zone | AC42 |
| boundary clock made naive | AC43 |
| mode gate removed | AC35 |
| `Retired` allowed into the due list | AC28 |

### T4 — 3/3 killed

Removing any one of the three wave-boundary statements from
`docs/architecture/work-intake-and-artifact-routing.md` reddens
`tests/roster/test_wave4_durable_outputs_and_release.py::test_wave4_docs_keep_the_remaining_wave_boundary`.

## Retracted: the `dep.kind == "spec"` restriction

This section previously recorded that the restriction had no observable removal
and was correct defence-in-depth. **Both claims were wrong, and the restriction
was a defect (A1), repaired in `fix(core)!: decide a cooled dependency before
any probe is built`.**

The measurement was wrong in two independent ways, and each alone invalidates
it:

- **It used the one kind that structurally cannot reproduce the defect.**
  `brief` is constrained by `_is_canonical_local_brief_path`, so a `brief`-kind
  dependency is refused by `_dependency_metadata_safety_finding` before the
  probe matters. `intent`, `research`, and `design` are not so constrained, and
  those are the kinds that fell through and opened the cooled body.
- **It observed the wrong thing.** `ready == []` is a dispatch outcome. Whether
  the artifact body was *read* is a different question, and a refusal downstream
  of the read says nothing about it. The repair is verified instead by a
  sentinel planted in the cooled body and asserted absent from the emitted JSON,
  and by a probe recording entry to the reader.

**The generalizing lesson:** a sample drawn from the one member that cannot
exhibit the behaviour proves nothing about the others, and an observable one
layer downstream of the property under test cannot decide it. This is the same
defect class as the guards that "passed for the wrong reason" — it simply
appeared in the justification for skipping a guard rather than in a guard.

## Gate results

| Gate | Result |
| --- | --- |
| `make lint-ruff` | clean |
| `lint-spec-status.py --root .` | exit 0 |
| `tests/roster/test_status_projection_and_context_exclusion.py` | 57 passed |

| `tools/test_workspace_status_cli.py` | 158 passed, 19 subtests |
| `tools/test_workspace_status.py` | 86 passed |
| `tests/roster/test_workspace_status_projection.py` | 26 passed, 12 subtests |
| `tests/roster/test_wave4_durable_outputs_and_release.py` | 6 passed |
| `packs/core/tests/skills/close-work/` | 96 passed |
| `packs/core/tests/skills/workspace-status/` | 90 passed, 1 skipped |
| `packages/agentbundle/tests/test_workspace_mcp_tools.py` | 20 passed, 5 skipped |
| `build-site.py` → `web` build → `docs-site` build | exit 0 each, in order |
| `npm test --prefix web` | 18 files, 129 tests passed |

Counts above are the post-GATES figures. The repair rounds that followed the
review added criteria and controls, so the suite counts are re-measured at
closeout rather than carried forward from this table.

## Two failures worth recording, because their surface pointed away from the cause

1. **`configuration_mismatch` on every `repair-plan` invocation** was a swallowed
   `TypeError`: the CLI called `analyze(..., cooling_enabled=False)` and the
   engine did not accept that parameter, so a generic handler converted an
   arity error into a plausible-looking finding and exit 2. It reddened 47 of the
   CLI contract suite's 158 tests while `reconcile` stayed green.
2. **`CAT-V-014 missing generated output`** for four `.pyc` files was a `dist/`
   tree contaminated by an earlier `pytest` run: the manifest had recorded
   bytecode as legitimate build output. The repair is a clean `dist/` rebuild,
   not satisfying the manifest.

## Release version collision, 2026-08-31

`plan.md:657` instructs a bump to Core 2.17.0. That number no longer names this
wave: main released `[core][2.17.0]` on 2026-08-31 while this branch was in
review, so the reserved version now names someone else's code. This wave ships
**2.18.0** instead.

`plan.md` is hash-pinned by `approve-plan` and is not edited, so its
instruction stands as written and is superseded here rather than corrected in
place. The obligation the plan step actually carries — one identical version
across `pack.toml`, `plugin.json`, and a topmost dated `[core]` changelog
heading — is met at 2.18.0, and AC53 states the requirement as a floor
(`strictly greater than (2, 16, 1)`) rather than a literal, so no criterion
had to change.

A reserved version behaves like a reserved RFC ordinal: it is not held until
it is pushed. The check that catches it is diffing `origin/main:pack.toml`
immediately before committing a release surface, not at the time the number is
chosen.
