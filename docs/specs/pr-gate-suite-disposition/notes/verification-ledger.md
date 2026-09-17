# Verification ledger: pr-gate-suite-disposition

Execution observations for this delivery. Not hash-pinned, so an observation
recorded here needs no contract amendment; a genuine specification error does,
and one is recorded below.

## T1 — enumeration and corroboration probe (2026-09-16)

Throwaway probe, not committed, run through `tools/lint-ci-parity.py`'s own
parsers via `tools/selftest_harness.py`'s loader so the measurement uses the
declared instrument rather than a second implementation.

### Baseline: the disposition split

The define expands, at `test-unleased`'s call site, to **114 distinct gate
targets**:

| Disposition | Count |
| --- | ---: |
| `PR_GATED` — reached by a workflow whose `pull_request` trigger carries no path filter | 56 |
| `PR_GATED_IF` — reached only conditionally | 6 |
| `NO_PR_GATE` — reached by no pull-request workflow | 52 |

The 6 conditional targets and their routes: `packages/agentbundle/tests/`,
`packs/core/tests/hooks/`, `tools/test_catalogue_tooling_rewire.py` and
`tools/test_catalogue_tooling_docs.py` behind `catalogue-tooling-ci-gates.yml`'s
`paths-ignore`; `tools/test_coordination_lease.py` behind
`build-check-windows.yml`'s `paths-ignore`; `tools/lint-pack-test-boundary.py` behind
`docs.yml`'s `paths`.

Of 17 workflow files, only `build-check.yml` and `ci-security.yml` carry an
unfiltered `pull_request` trigger. 11 carry a filtered one — 6 `paths`, 5
`paths-ignore` — and 4 have no pull-request trigger. An earlier reading of this
table mislabelled `build-check-windows.yml` and `codeql.yml` as `paths`; both are
`paths-ignore`. No classification moves, because the amended AC-0005 treats both
filter kinds as conditional; only the prose was wrong.

### Enforcement shapes, measured

No job or step of any workflow carries `continue-on-error`. The `if:` conditions
that exist sit on `gate-sast`'s two steps and the `build-check` aggregator job
(`always()`), on `build-check-windows`'s job, on four `catalogue-tooling-ci-gates`
matrix steps, on `docs.yml`'s `check-adr-immutability` job, on `pages.yml`'s
upload-on-failure step and `deploy` job, and on the three release workflows' tag
guards. **None is on `gate-main`**, which is where every script-invocation and
pytest-operand `PR_GATED` route runs, so AC-0004's arm rejects no current entry.

Exactly one step invokes `make build-check` and so pulls in the whole gate chain:
`gate-main / Run make build-check`.

### Lines with no extractable target: four, not three

The plan predicted the enumeration would find lines carrying no path operand and
needing a substring key. It finds exactly four:

    @command -v npm >/dev/null 2>&1 || { echo "make test: npm not found ..." }
    @test -d docs-site/node_modules || { echo "make test: docs-site deps missing ..." }
    npm run test:plugins --prefix docs-site
    $(PYTHON) -c "import httpx"

`$(3)` is not among them, which confirms the plan's call-site decision: the
enumeration reads the define as `test-unleased` expands it, so the two suites
arriving through the third macro argument — `tools/test_workspace_status.py` and
`tools/test_workspace_status_cli.py` — receive real keys instead of hiding behind
an unexpanded placeholder.

### The gate-chain union is load-bearing

Those same two suites are reached on a pull request only through
`make build-check` → `tools/repo/build_gate_chain.py` (its `_script_step` calls at
lines 311-317), never through a literal `pytest` line in any workflow. Dropping
`script_step_targets` from the coverage union moves both from `PR_GATED` to
`NO_PR_GATE`, so the union changes the answer rather than decorating it.

### `extract_ci_targets` over eleven newly-read workflow files

The plan named one uncertainty: the extractor was written against
`build-check.yml` and is now read over eleven more files. **Closed.** Exactly one
shape misreports, in one file:

- `release-agentbundle.yml`, step "Assert tag matches pyproject version", yields
  `agentbundle/version.py`. The path does not exist at that location; the token
  comes from **prose inside a heredoc body** — a `::error::` message and a source
  comment, neither a command. This is the declared false-positive residual, now
  with a measured instance.

It cannot reach a `PR_GATED` claim: `release-agentbundle.yml` is `paths`-filtered,
and neither unfiltered pull-request workflow contains a heredoc at all. Verified
by scanning both for heredoc openers.

A second flagged token was a false alarm of the probe, not the extractor:
`.claude/skills/work-loop/scripts/lint-knowledge.py` in `docs.yml` is a real
invocation of a real file; the probe's own root-allowlist was too narrow.

### Specification error found — AC-0005 omits a coverage shape

**This is a contract defect, not an observation, and it follows the controlled
amendment procedure.**

AC-0005 defines what it means for a step to "reach" a suite as two shapes: a
pytest operand of that step, and any target `build_gate_chain.py` runs when the
step invokes `make build-check`. Corroboration can recognise a **third**: a script
invoked at a command position. Five `run-test-suite` targets are gated exclusively
that way:

| Target | Gating step | Invocation |
| --- | --- | --- |
| `tools/lint-conformance-portability.py` | pytest catalogue-test carve-out destinations (RFC-0082) | `build-check.yml:425` |
| `tools/lint-direct-code-table.py` | pytest catalogue-test carve-out destinations (RFC-0082) | `build-check.yml:426` |
| `tools/check-docs-contrast.py` | docs palette contrast gate | `build-check.yml:366` |
| `tools/test-pages-workflow.py` | pages.yml deploy-gate posture | `build-check.yml:374` |
| `tools/test-pages-concurrency.py` | pages.yml concurrency posture | `build-check.yml:379` |

None is a pytest operand; each is `python3 tools/<name>.py` at a command
position. Implementing AC-0005 literally rejects all five correct `PR_GATED`
entries, which then makes AC-0013 — the lint exits 0 against the repository —
unsatisfiable. The two criteria contradict each other as frozen.

The omission is in the criterion's enumeration, not in the module: the forward
gate already reads non-pytest gates at invocation positions, which is how the
existing `STEP_DISPOSITION` corroboration covers the same five scripts locally.

Verified after amending: under the three-shape definition all five classify
`PR_GATED` and the 56/6/52 split is unchanged, so AC-0013 is reachable.

### A fourth shape exists, and is deliberately unread

Review of the amendment found that `build-check.yml:827`'s `run_with_floor` shell
function takes a suite directory as an argument, `cd`s into it and runs bare
`python -m pytest`. The suite is neither a pytest operand nor a script at a command
position, and no `make build-check` is involved. Its two directories —
`packs/catalogue-curation/tests/skills/assimilate-primitive` and
`.../assimilate-repo` — are not `run-test-suite` targets, so no roster entry
depends on it.

The criterion therefore states three *recognised* shapes rather than an exhaustive
three. The direction is safe: an unrecognised shape makes corroboration fail a true
`PR_GATED` claim, a false alarm, never a false pass.
