# Verification ledger — ci-gate-main-carve-out-sibling

Mechanical evidence for the carve-out's acceptance criteria. Each entry
names its method, its input revisions, and its result. The standing
control for everything here is the posture test's dispatch-body pin
(`PINNED_DISPATCH_BODY`): any change to the invocation set reddens
`tools/test-build-check-workflow.py` in the same commit, by design.

## AC-0001: command-set preservation (one-to-one invocation match)

- **Method.** A throwaway script (never committed) extracted the two
  moved steps' `run` bodies from the base commit
  (`5499ff9d9:.github/workflows/build-check.yml`) and the dispatch
  body's invocations from the post-change working tree, joining
  backslash continuations the same way bash does. Compared as multisets
  (the shard rebalance deliberately reorders invocations across
  branches; AC-0001 pins presence and count, not sequence).
- **Input revisions.** Before: `6dc12944e` (the plan-approval commit and
  review base — its `.github/workflows/build-check.yml` is byte-identical
  to the originally extracted before-state `5499ff9d9`, a commit that became
  unreachable after the run was re-admitted; the comparison is reproduced
  against the reachable base). After: the delivered T1 commit `3c690bcc6`.
  Both revisions are branch-reachable.
- **Result.** BEFORE: 17 invocations. AFTER: 17 invocations.
  Multiset one-to-one: **true** — zero missing, zero added. The
  27-file tools group extracts as one continuation-joined statement on
  both sides (one pytest process, ADR-0101 discipline preserved).

### The closed set (before = after, 17 invocations)

| # | Invocation (truncated at 72 chars) |
| --- | --- |
| 1 | `python tools/lint-conformance-portability.py --root .` |
| 2 | `python tools/lint-direct-code-table.py --root .` |
| 3 | `python -m pytest tests/ -q` |
| 4 | `python -m pytest packs/architect/tests/pack/ -q` |
| 5 | `python -m pytest packs/architect/tests/skills/architect-assess/ -q` |
| 6 | `python -m pytest packs/architect/tests/skills/architect-design/ -q` |
| 7 | `python -m pytest packs/core/tests/pack/ -q` |
| 8 | `python -m pytest packs/core/tests/skills/workspace-status/ -q` |
| 9 | `python -m pytest packs/credential-brokers/tests/pack/ -q` |
| 10 | `python -m pytest packs/atlassian/tests/pack/ -q` |
| 11 | `python -m pytest packs/atlassian/tests/skills/flow-metrics/ -q` |
| 12 | `python -m pytest packs/atlassian/tests/skills/jira-epic-outcome-view/ -q` |
| 13 | `python -m pytest packs/product-engineering/tests/pack/ -q` |
| 14 | `python -c "import httpx"` |
| 15 | `python -m pytest packs/linear/tests/skills/linear/ -q` |
| 16 | `python -m pytest tools/test_lint_agents_md_diataxis_block.py … (27 files, one statement) … tools/test_check_release_gate.py -q` |
| 17 | `python -m pytest tools/test_local_ci_shared_test_deduplication.py -q` |

### Shard placement (after)

- **shard-1** (~93 s by the WEIGHTS table): #1, #2, #3, #14.
- **shard-2** (~71 s): #4–#9, #16.
- **shard-3** (~69 s, dedup guard ~65 s dominant): #10–#13, #15, #17.

The heaviest single invocation (`pytest tests/`, ~90 s) sets shard-1's
floor; the split is weight-balanced from `tools/shard_test_roster.py`'s
WEIGHTS plus the dedup guard's measured ~65 s.

## Provisioning discovery (spec Assumptions, skip-aware procedure)

- **Method.** Static scan (complete enumeration of every
  `skipif`/`pytest.skip`/`importorskip` site across the moved suites:
  46 sites) plus runtime corroboration in a fresh Python 3.11 venv
  holding exactly the candidate set (pytest,
  `tools/requirements.txt`, editable agentbundle) with `-rs` skip
  reporting. The runtime environment's PATH resolved `python3` to the
  venv (a first attempt resolving to the host's Python 3.15 hung on
  `tools/lint-agents-md.py` — a local artifact, not a CI provisioning
  gap; gate-main runs the same suite green on 3.11).
- **Runtime corroboration.** All 11 pack suites, the dedup guard
  (51 passed), both linters, and the httpx import: green, zero
  provisioning-caused skips. `pytest tests/` ran locally to 23% (local
  macOS subprocess/git overhead makes the full run ~30× its ~90 s CI
  weight) with the only skips being the platform set below; the full
  suite's authoritative run is the sibling's own CI (T4).
- **Provisioning-relevant skip sites found (static, complete):**
  `httpx` (importorskip, test_linear_refresh_processor),
  `jsonschema` (test_containment_attestation_parity), `git` +
  full history (baseline-commit and merge-base probes),
  `node` (ECMA-262 engine check, test_delivery_contract_bundle),
  `sh`/`cat`/`grep` (promotion-drain and shell probes),
  `make` (the dedup guard's `make -n` expansions).
- **Probe set (discovered):** modules `yaml, jsonschema, tomlkit,
  httpx`; executables `git, sh, make, node, cat, grep` (cat/grep added
  by the T6 repair: the ledger's own static scan had recorded the
  promotion-drain skip sites, and the probe must cover every recorded
  executable — review finding R2-001). Pinned verbatim by
  `PINNED_PROBE_BODY` in the posture test.
- **Deliberately not probed, stated honestly:**
  - Platform skips (symlinks, junctions, Windows-only cases) —
    environmental on every runner, not provisioning.
  - `dist/apm/` — probed after the round-1 review repair (T5): the
    discovery environment held dist/ from local runs, so its skip-audit
    could not see the projected-variant cases' dependency on it, and the
    original entry here wrongly claimed gate-main skipped those cases too —
    inside gate-main `make build-check` had materialized `dist/` before the
    carve-out step ran. The sibling now materializes the catalogue
    projection in its own step and the probe fails closed when `dist/apm/`
    is absent (finding R1-001, repaired in T5).

## T1 red proof (red-green, never committed red)

Against the unmodified workflow, after extending the tools and before
the workflow edit:

- `python3 tools/test-build-check-workflow.py` — self-test green
  (baseline clean, every mutation caught), then **9 posture
  violations**: `job-id-set[gate-catalogue-tests]`,
  `job-name-written[gate-catalogue-tests]`, `work-jobs-floor`,
  `sibling-matrix-shards`, `sibling-fail-fast`,
  `sibling-dispatch-body-exact`, `sibling-probe-body-exact`,
  `sibling-probe-before-dispatch`, `moved-steps-left-gate-main`.
- `python3 tools/lint-ci-parity.py` — **49 parity violations**: the 42
  repointed `PR_GATED` where strings name a step the workflow does not
  carry, plus dead roster entries for the sibling's steps.

After the single workflow edit (the delivered T1 commit `3c690bcc6`, whose
workflow is byte-identical to the originally extracted `a0ac3a36d` state):
posture test exits 0 (208 mutations, 93 assertion families, all caught);
lint exits 0 (182 steps dispositioned, 258 targets corroborated); lint
self-test 220 cases pass.

## T6: round-2 review repairs (red-green, never committed red)

Round-2 findings (see
`.context/reviews/run-3a659195cba798ec/`):

- **R2-001 (probe executable set incomplete).** The probe's executable
  loop gains `cat grep` (the promotion-drain skip sites the ledger's
  own static scan had recorded); all are coreutils on every runner
  image, so the fail-closed check has no false-positive risk.
- **R2-002 (ledger T1 citation unreachable).** The T1 section above now
  cites the delivered T1 commit `3c690bcc6` (byte-identical workflow).
- **SEC-R3-001 (SHARD env value unpinned).** New posture check
  `sibling-dispatch-env-value-exact` pins the dispatch step's env
  mapping to exactly `SHARD: ${{ matrix.shard }}`; a constant or
  conditional value that silently routes every replica to one branch
  reddens (verified red before the pin landed: both mutations left the
  prior posture test green).
- **SEC-R3-002 (probe conditionality unpinned).** New posture check
  `sibling-no-step-if` rejects any step-level `if:` on any sibling step
  (verified red before: `if: ${{ false }}` on the probe left every gate
  green).
- **QE-R2-001 (release-guide doc drift).**
  `docs/guides/how-to/cut-a-package-release.md` now attributes the
  roster collection to the sibling's shard-1.

Red proof before the workflow edit: `sibling-probe-body-exact` red
against the unmodified workflow; the new guard checks prove via their
mutations (a constant SHARD, a conditional SHARD, a probe `if:`, a
cat/grep drop each redden). Green after: 215 mutations, 97 assertion
families, all caught; `make build-check` green end-to-end at this tree
(all 93 chain steps, SAST delegated; ~75 min local wall-clock).

## T7: round-3 review repairs (red-green via the mutation matrix)

Round-3 findings (see `.context/reviews/run-3a659195cba798ec/`):

- **R3-001 (working-directory dimension unpinned).** The three pinned
  sibling steps (install, materialize, probe, dispatch) join `_NO_CWD_STEPS`,
  so a `working-directory:` key added to any of them reddens
  `no-working-directory[gate-catalogue-tests/<step>]`. Four mutations prove
  it, one per step.
- **SEC-R4-001 (matrix exclude unpinned).** New check
  `sibling-matrix-no-exclude` read the matrix block's keys with a regex
  restricted to the bare spelling at exactly 8 spaces. Mutation: an
  adjacent bare `exclude:` dropping shard-2 reddened the check (the
  declared shard list still satisfies both cross-pins, which is why a
  dedicated check was needed).
  **Correction (round 4, finding QE-R4-002):** the check's original
  record here overclaimed — "any `exclude:`/`include:` entry reddens"
  held only for the bare adjacent spelling. The same run's round-4
  reviews falsified it three ways (quoted `'exclude':`, duplicate
  `matrix:` blocks, blank-line separation), all controller-verified
  against the shipped workflow; see the T8 section for the class-closing
  repair that replaced the check.
- **SEC-R4-002 (install body unpinned).** New `PINNED_INSTALL_BODY` and check
  `sibling-install-body-exact` pin the sibling's dependency-install body by
  equality, closing the addition and re-point directions the probe cannot
  see (it verifies availability, not provenance). Two mutations: a prepended
  `curl … | sh` line and a re-pointed requirements source.

Red proof: unlike T5/T6 (which reddened against the workflow), the T7
assertions pass against an already-correct workflow — the defect was the
MISSING check, so the red is the mutation matrix: all seven new mutations
(each a one-line workflow edit of exactly the shape each finding named)
reddened their families, and the self-test reported 222 mutations,
99 assertion families, all caught, with every pre-existing family still
green. **Scope of that proof (round 4, finding QE-R4-002):** a caught
mutation proves only the mutated spelling — the matrix check's mutation
proved the adjacent bare `exclude:` and nothing else; it did not prove
the quoted, duplicate-block, or blank-line spellings, which the same
run's round-4 reviews then exercised. `make lint-ruff lint-mypy` clean;
lint-ci-parity ok (183 steps, 258
targets); lint self-test 220 cases pass. The full chain re-run at this
tree is recorded in the T4 section's log (controller-recorded; lands as
controller history the owner adopts).

## T8: round-4 review repairs (the matrix pin closed as a class)

Round-4 findings (see `.context/reviews/run-3a659195cba798ec/`):

- **SEC-R5-001, SEC-R5-002, SEC-R6-001 (the matrix check bypassable three
  ways).** The T7 regex matrix model is REPLACED, not patched:
  `PINNED_STRATEGY_BODY` pins the sibling's entire `strategy:` section by
  equality (comment-stripped, blank-line-free), and exactly-one key counts
  (`sibling-strategy-single`, `sibling-matrix-single`) close the
  duplicate-key class directly. Controller verification against the
  shipped workflow: all seven recorded shapes redden — bare `exclude:`,
  quoted `'exclude':`, quoted flow `"exclude": [{…}]`, blank-line-separated
  `exclude:`, duplicate `matrix:` with `exclude:`, duplicate `matrix:` with
  `shard: [shard-1]` (each reddening the strategy pin, the duplicates also
  the count check). A seventh shape — a duplicate `strategy:` binding — is
  carried by the mutation matrix and caught by the count checks alone
  (`sibling-strategy-single`, with `sibling-matrix-single` and
  `sibling-fail-fast` reddening too); the strategy pin itself stays green
  for it, because its extractor reads only the first `strategy:` block —
  the count checks are load-bearing, not redundant with the pin
  (attribution corrected per round-5 finding QE-R5-001).
- **SEC-R6-002 (job-level defaults channel).** New check
  `no-job-defaults-block` rejects a `defaults:` key at job indent in every
  job, closing the `run: working-directory:` channel the step-level
  `_NO_CWD_STEPS` pins cannot see. Controller verification: a job-level
  `defaults: run: working-directory: tools` on the sibling reddens it.
- **QE-R4-001 (the modeling approach was the defect).** The repair follows
  the file's own pin-the-whole-set doctrine — one equality pin plus counts
  instead of another regex arm; the removed check is not kept alongside a
  replacement (a check that can be bypassed records a held dimension that
  is not held).
- **QE-R4-002 (ledger overclaim).** The T7 section above now records what
  was actually proven and cites this section for the falsified spellings
  (corrected in this same commit).

Red proof: the mutation matrix carries all five new bypass mutations
(quoted exclude, blank-line exclude, duplicate matrix, duplicate strategy,
job-level defaults) plus the original bare exclude, now targeting the
strategy pin — 227 mutations, 102 assertion families, all caught, every
pre-existing family still green. Posture OK against the shipped workflow;
lint-ci-parity ok; lint self-test 220 cases; ruff and mypy clean.
(controller-recorded; lands as controller history the owner adopts.)

## T9: round-5 review repairs (anchor/alias/merge syntax rejected)

Round-5 findings (see `.context/reviews/run-3a659195cba798ec/`):

- **R5-001 (merge-key delivery).** New check `no-anchor-alias-merge`
  rejects YAML `&anchor` definitions, `*alias` references, and `<<:` merge
  keys anywhere in the workflow — the declared-canonical-subset doctrine
  (fail closed on every unmodelled form) rather than modeling merge
  semantics. Controller verification against the shipped workflow: the
  reviewer's exact shapes — an anchor block plus a `<<: *anchor` merge line
  under the sibling job and under the aggregator job, each carrying a live
  job-level `defaults: run: shell: 'true {0}'` (PyYAML resolves it) — now
  redden. Four mutations: the two merge-key shapes, an `*alias` value
  reference, and an `&anchor` definition on the job id.
- **QE-R5-001 (ledger count and attribution).** The T8 section's shape
  count now matches its enumeration (six listed), the seventh shape
  (duplicate `strategy:`) is enumerated with its correct attribution (the
  count checks, not the strategy pin), and the pinned-constant comment no
  longer overclaims ("every structural edit inside the block").

Red proof: the mutation matrix carries all four new mutations — 231
mutations, 103 assertion families, all caught, every pre-existing family
still green. Posture OK against the shipped workflow; lint-ci-parity ok;
lint self-test 220 cases; ruff and mypy clean. (controller-recorded; lands
as controller history the owner adopts.)

## T4: runtime verification

- [x] `python -m pytest tools/test_local_ci_shared_test_deduplication.py -q`
      local run (moved dedup guard against the unchanged Makefile):
      **51 passed, 99.36 s**.
- [x] `make lint-ruff lint-mypy` (local gate pair): **green** (ruff clean;
      mypy: no issues in 158 source files).
- [x] `make build-check` end-to-end (chains the posture test and
      lint-ci-parity; the PR's own gate is the integration proof):
      **green** — all 93 chain steps, SAST/SCA delegated as gate-main runs
      it; ~85 min wall-clock locally (macOS subprocess overhead; CI runs
      the same chain in minutes). Re-run green after the T5 repair at the
      same tree (~50 min).
- [ ] Post-merge: gate-main docs-only median vs the ≤ 600 s target
      (the intent's success metric; the rebalance path is a deliberate
      pinned edit if three shards under-deliver).

## T5: round-1 review repairs (red-green, never committed red)

Round-1 adversarial findings R1-001…R1-005 (see
`.context/reviews/run-3a659195cba798ec/1-adversarial-reviewer-raw.md`):

- **R1-001 (six projected-variant cases would silently skip in the
  sibling).** Repaired: the sibling gains a `Materialize catalogue
  projections (gate-catalogue-tests)` step (the same catalogue-build
  invocation gate-main's `make build-check` chain runs) and the probe
  gains a fail-closed `dist/apm/` check. Red proof before the workflow
  edit: `sibling-probe-body-exact`, `sibling-materialize-body-exact`,
  `sibling-materialize-before-probe` each red against the unmodified
  workflow. Green after: 212 mutations, 95 assertion families, all
  caught; four new mutations (step removed, body emptied, step moved
  after the probe, probe dist-check dropped) each redden.
- **R1-002 / SEC-001 (stray root `uv.lock`).** Deleted; nothing consumes
  it (no uv invocation in Makefile or workflows; the root pyproject is
  tooling-only).
- **R1-003 (24 stale gate-main placement comments).** All reworded for
  the two-job layout: the broad `pytest tests/ -q` run they referenced
  now lives in the sibling's shard-1 (a parallel job), so the named
  gate-main steps are what attribute failures precisely.
- **R1-004 (T4 section unchecked).** Completed above.
- **R1-005 (ledger cited unreachable revisions).** Input-revision record
  corrected above.
