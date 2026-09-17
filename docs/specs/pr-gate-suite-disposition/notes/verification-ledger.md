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

## T2 — the roster and its check arm (2026-09-16)

Implemented in `tools/lint-ci-parity.py`: the three constructors, `suite_lines`,
`line_targets`, `pr_gate_sources`, `SUITE_DISPOSITION`, and `check_suites` called
from `main()`. 866 added lines, one file.

Gates: `lint-ci-parity` 0, `lint-ruff` 0, `lint-mypy` 0,
`test-lint-ci-parity` 0 (143 cases). `tools/test_local_ci_shared_test_deduplication.py`
51 passed in 53.9s, confirming a tools-only change moves neither plan digest.

The roster carries 118 keys: 114 target paths plus 4 literal-substring keys for
the lines with no path operand. Split: **56 PR_GATED, 6 PR_GATED_IF, 56 with no
pull-request gate** (52 targets and the 4 substring keys). `main()` now prints
both rosters' counts, so a green run states which checks ran — a silently deleted
arm would otherwise leave the output unchanged.

### Void-probe matrix

Each row mutates the tree, runs `python3 tools/lint-ci-parity.py --root .`, and
restores. A control that cannot fail proves nothing, so every arm was probed.

| Probe | Mutation | Exit | Verdict |
| --- | --- | ---: | --- |
| A | `check_suites` call removed from `main()` | 0 | **open — T3/AC-0008 owns it** |
| B | new suite appended to the 19-target `tools/` batch line | 1 | closes the defect class |
| C | a truly gated suite re-declared `NO_PR_GATE` | 1 | closed |
| D | suite behind an `@`-prefixed guard on one line | 1 | closed |
| E | suite inside a Make-expanded recipe comment | 1 | closed |
| F | inert prose comment naming a path | 0 | no false alarm |
| G | `PR_GATED` naming a `paths`-filtered workflow | 1 | closed |

Probe B is the one that matters most: `tools/test_brand_new_suite.py` appended
beside nineteen siblings on a single continued line is caught and named. That is
the recorded defect — a new suite landing PR-ungated in silence — demonstrated
closed rather than described.

### Three defects found by probing, not by reading

**1. The completeness arm required *any* target, not every target.** The first
implementation resolved a line if one of its targets carried an entry. Deleting
`packs/desk-research/tests/pack/`, which shares a line with five siblings, left
the line resolved and the lint green. With nineteen modules on the `tools/` batch
line, a twentieth would have inherited its siblings' dispositions and demanded
none of its own. Now every target of a line must carry an entry, and the
violation names the missing ones.

**Deviation from the plan's `## Design (LLD)`, recorded here rather than
amended.** That section says "Every surviving line must resolve to at least one
`SUITE_DISPOSITION` entry", which is the weaker rule the first implementation
matched. The implemented rule is stronger and still satisfies AC-0001, which
requires the lint to fire when a line resolves to no entry; firing *also* on a
partially dispositioned line exceeds the criterion rather than contradicting it.
`## Design (LLD)` is working material under the plan's own tier declaration, and
the lifecycle reference puts a deviation from a task row's literal method in this
ledger, so no contract amendment is owed.

**2. Unanchored substring matching was a false pass.** The fallback for a line
with no path operand matched *any* roster key as a substring. The repo-root key
`tests/` is a substring of nearly every test path, so
`# $(shell $(PYTHON) -m pytest packs/sneaky/tests/ -q)` resolved against it and
passed — the comment-expansion hatch reopened through a different door. Only the
four keys in `_SUBSTRING_KEYS` are now eligible for substring matching.

**3. Wrapping a source string corrupted a load-bearing identifier.** Generating
the roster with `textwrap.wrap` at its defaults split
`windows-build-gate-chain` into `windows-build-gate- chain`, because
`break_on_hyphens` is true by default. The corroboration arm caught it
immediately — a `PR_GATED` source naming no real step — which is the inversion
working as designed. Fixed with `break_on_hyphens=False, break_long_words=False`;
verified zero literals split at a hyphen before re-splicing.

### T2's standing cases, and the two defects writing them found

`tools/test-lint-ci-parity.py` goes from 143 to **166 cases**. Each new case
supplies its own Makefile text, roster and source map as keyword arguments, so
none touches module state.

Writing them surfaced two defects the probe matrix had not, both in
`PR_GATED_IF`, and both of the same shape — a check that could not fail:

**1. `PR_GATED_IF` collapsed `where` and `condition` into one string.**
`("pr-gated-if", f"{where} — {condition}")` broke both checks that read the
entry. Corroboration compares a source's `where` for equality, and a joined
value never matches one, so **every conditional claim went entirely
unverified** — an entry could name a workflow or step that does not exist. The
empty-reason check read the same joined value, which a blank condition leaves
non-empty, so it could not fire either. The constructor now returns
`("pr-gated-if", where, condition)`, `SUITE_DISPOSITION` is typed
`dict[str, tuple[str, ...]]`, and a conditional claim is corroborated in both
directions: the named source must exist, and it must actually be filtered or
conditional.

**2. One defect emitted two messages.** A `PR_GATED` entry naming a filtered
source produced the specific diagnosis *and* the generic "does not reach it",
which is the same failure at two resolutions. The branch is now mutually
exclusive.

### Mutation proof — every arm reddens a named case

Each row deletes or neutralises one arm of `tools/lint-ci-parity.py`, runs
`python3 tools/test-lint-ci-parity.py`, records which named case failed, and
restores. An arm whose removal left the suite green would be a control that
cannot fail.

| Arm removed | Exit | Case that reddened |
| --- | ---: | --- |
| all-targets completeness | 1 | `suites-partial-line-fires-on-the-missing-target` |
| no-path-operand completeness | 1 | `suites-no-path-operand-line-needs-a-substring-key` |
| dead entry | 1 | `suites-dead-entry-fires` |
| `PR_GATED` on a filtered source | 1 | `suites-pr-gated-naming-a-filtered-workflow-fires` |
| `PR_GATED` on a conditional source | 1 | `suites-pr-gated-naming-a-conditional-step-fires` |
| `PR_GATED` uncorroborated | 1 | `suites-pr-gated-with-no-covering-step-fires` |
| stale `NO_PR_GATE` | 1 | `suites-no-pr-gate-contradicted-by-a-covering-step-fires` |
| empty `NO_PR_GATE` reason | 1 | `suites-no-pr-gate-empty-reason-fires` |
| `PR_GATED_IF` uncorroborated | 1 | `suites-pr-gated-if-with-no-source-fires` |
| `PR_GATED_IF` empty condition | 1 | `suites-pr-gated-if-empty-condition-fires` |
| `suite_lines` keeping `@`-prefixed lines | 1 | `suite-lines-keeps-an-at-prefixed-command` |
| `suite_lines` keeping expanding comments | 1 | `suite-lines-keeps-a-comment-carrying-an-expansion` |

Twelve for twelve. The one hole that remains is the wiring itself: every case
above passes its own tables, so all of them stay green if `check_suites` is never
called from `main()`. `suites-shipped-roster-is-complete-in-both-directions`
reads the shipped roster but calls `check_suites` directly, so it does not close
that hole either — it exists to say so. AC-0008 and T3 own it.

### Suites referencing the edited files

Anchor-test sweep found no hash or count pin on either edited file, but nine
files reference them. All run green:

- `tools/test_check_artifact_contents.py`, `tools/test_build_gate_chain.py`,
  `tools/test_catalogue_tooling_rewire.py`, `tools/test_gate_enumeration.py` —
  **154 passed, 28 subtests, 620s**.
- the four standalone hyphenated entry points a directory sweep never collects —
  `test-build-check-workflow.py`, `test-pages-workflow.py`,
  `test-pages-concurrency.py`, `test-lint-ci-parity.py` — each exit 0.
- `tools/test_local_ci_shared_test_deduplication.py` — **51 passed, 59s**,
  confirming a tools-only change moves neither plan digest.
