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
  httpx`; executables `git, sh, make, node`. Pinned verbatim by
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

After the single workflow edit (commit `a0ac3a36d`): posture test
exits 0 (208 mutations, 93 assertion families, all caught); lint
exits 0 (182 steps dispositioned, 258 targets corroborated); lint
self-test 220 cases pass.

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
