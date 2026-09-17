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

## T3 — the entry-point case (2026-09-17)

`suites-arm-is-wired-into-main-*` drives the command entry point against a
fixture whose define carries an undispositioned line. Void-probed: deleting the
`check_suites(...)` call from `main()` reddens
`suites-arm-is-wired-into-main-reports-the-suite` and
`...-names-the-roster`, closing probe A.

**The exit-code assertion alone would not have closed it.** A fixture root also
fails the forward gate — its workflows are unclassified — so `exit 1` holds
whether or not the suite arm ran. `suites-arm-is-wired-into-main-exit` stayed
green under the mutation; only the two content assertions caught it. That is why
the case asserts the suite-specific message rather than the status.

169 cases.

## T5 — the two suites are PR-gated (2026-09-17)

Two `gate-main` steps added, each with a `STEP_DISPOSITION` entry as
`LOCAL("test-after-build-check")`, and both `SUITE_DISPOSITION` entries flipped
to `PR_GATED` naming their step. The roster now reads **58 PR-gated, 6
conditionally gated, 54 with no pull-request gate**.

### A parent directory matches neither direction

The pack step first read `python -m pytest packs/frontend-engineering/tests/ -q`,
which collects the same 337 tests as the deeper path. The lint refused it twice:
the forward arm because `make ci` reaches
`packs/frontend-engineering/tests/skills/frontend-engineering/` and not its
parent, and the suite arm because it looks a target up by key and the parent is a
different key. Both directions compare *written* paths, so the step now spells
the path exactly as the define spells it. Recorded because the failure mode is
invisible from either surface alone: the shorter path runs the same tests and
reports a real gate as absent.

### Both steps are load-bearing

| Step removed | Exit | Entry that reddened |
| --- | ---: | --- |
| `pytest frontend-engineering pack suite` | 1 | `packs/frontend-engineering/tests/skills/frontend-engineering/` |
| `pytest shared-test dedup guard` | 1 | `tools/test_local_ci_shared_test_deduplication.py` |

### No plan digest moved

`tools/test_local_ci_shared_test_deduplication.py`: **51 passed, 60.8s** after
the workflow edit, so the plan's claim holds — the digests are taken over the
Makefile, which this change does not touch, and no re-pin is owed.
`tools/test-build-check-workflow.py` exits 0.

## T6 — the obligation pair (2026-09-17)

`tools/AGENTS.md` now states both directions as one pair rather than a second
caveat: a new `build-check.yml` step owes a `STEP_DISPOSITION` entry, and a new
or moved `run-test-suite` line owes a `SUITE_DISPOSITION` entry per target. It
also carries the path-spelling rule T5 discovered, and states that reasons are
checked for presence and not for truth. The four `lint_agents_md_*` suites stay
green (16 passed, 10 subtests).

## T4 — the docstring states both rosters and five residuals (2026-09-17)

The module docstring gains a second-roster section and a *What the suite roster
does not prove* block naming five limits, each verified present by reading
`__doc__`: corroboration is best-effort in **both** directions unlike the forward
gate's one-way claim; it proves a step *names* a suite, not that it runs it;
`PR_GATED_IF` records a condition nobody evaluates; the `run_with_floor` fourth
shape is deliberately unread; and a reason is checked for presence, never truth.
The exit-code note now covers the Makefile as a readable source. It also carries
the path-spelling rule, since both directions compare written paths.

## T7 — every arm reddens a named case, on the finished tree (2026-09-17)

Re-run after T3–T6 landed, because a mutation record goes stale when the code it
cites moves. Each row neutralises one arm, runs
`python3 tools/test-lint-ci-parity.py`, and restores.

| Arm removed | Exit | First case to redden |
| --- | ---: | --- |
| completeness: all targets of a line | 1 | `suites-partial-line-fires-on-the-missing-target` |
| completeness: no-path-operand line | 1 | `suites-no-path-operand-line-needs-a-substring-key` |
| completeness: dead entry | 1 | `suites-dead-entry-fires` |
| `PR_GATED` on a filtered source | 1 | `suites-pr-gated-naming-a-filtered-workflow-fires` |
| `PR_GATED` on a conditional source | 1 | `suites-pr-gated-naming-a-conditional-step-fires` |
| `PR_GATED` uncorroborated | 1 | `suites-pr-gated-with-no-covering-step-fires` |
| stale `NO_PR_GATE` | 1 | `suites-no-pr-gate-contradicted-by-a-covering-step-fires` |
| empty `NO_PR_GATE` reason | 1 | `suites-no-pr-gate-empty-reason-fires` |
| `PR_GATED_IF` uncorroborated | 1 | `suites-pr-gated-if-with-no-source-fires` |
| `PR_GATED_IF` empty condition | 1 | `suites-pr-gated-if-empty-condition-fires` |
| `suite_lines` `@`-strip | 1 | `suite-lines-keeps-an-at-prefixed-command` |
| `suite_lines` comment rule | 1 | `suite-lines-keeps-a-comment-carrying-an-expansion` |
| `check_suites` call in `main()` | 1 | `suites-arm-is-wired-into-main-reports-the-suite` |

**Thirteen for thirteen**, including the wiring, which the earlier matrix left
open. No arm survives its own deletion.

## T8 — the register entry is retired (2026-09-17)

Moved from `[backlog].open` to `[backlog].closed`. The comment records that the
fix did **not** land in the entry's own `path` — `tools/repo/build_gate_chain.py`
is untouched, and the mechanism is in `tools/lint-ci-parity.py`, chosen because
that module is already run by a required pull-request check, so the new check
could not itself land PR-ungated.

It also records two corrections to what the entry claimed: one instance versus a
measured 52 of 114, and the declined "derive" instruction. And it names the
second instance the entry did not know about, `tools/test_local_ci_shared_test_deduplication.py`,
whose pins were red on `main` from PR #1313 to PR #1339.

Verification: `workspace.toml` parses; the entry appears **once**, under
`closed`; no `[backlog].open` entry restates it; the `source.ref` it names still
resolves. `test_workspace_status.py` and `test_workspace_status_cli.py` exit 0
individually and **252 passed, 22 subtests** under pytest.

Four-revision resurrection check, per the known trap that a merge can restore a
retired entry: the entry was present exactly once in `HEAD`, `HEAD~1`,
`origin/main` and `origin/main~1` before this change, so it was not already
mid-retirement anywhere.

## The gate caught an independent change, unprompted (2026-09-17)

The strongest evidence in this delivery is not a probe. While the work was in
flight, a peer merged **PR #1342, "fold the gate-enumeration guard into the final
tools batch, so it gates a PR"** — by hand, for one suite, with no knowledge of
this spec. It moved `tools/test_gate_enumeration.py` out of its own
`run-test-suite` line into the batched line and named it in
`build-check.yml`'s catalogue-test carve-out step.

Rebasing onto it made this roster stale, and the lint said so before any human
looked:

```
lint-ci-parity: ✖ suite 'tools/test_gate_enumeration.py' — NO_PR_GATE is
  contradicted by covering step 'build-check.yml / gate-main / pytest
  catalogue-test carve-out destinations (RFC-0082)'. Change it to PR_GATED.
lint-ci-parity: 1 parity violation(s).
```

Three things this establishes that a synthetic probe cannot:

1. **The stale-declaration arm fires on real repository movement**, not only on
   a mutation authored to trip it.
2. **Completeness survived a line relocation.** #1342 moved the target between
   recipe lines; the key still resolved, and only the *disposition* went stale.
   That is the anchor behaving as designed — keyed on lines for completeness,
   on targets for corroboration.
3. **The manual practice the roster replaces was already happening.** A
   maintainer was hand-auditing one suite's PR coverage and hand-fixing it. That
   is the recall this defect asked to eliminate, observed in the wild mid-delivery.

Entry corrected to `PR_GATED` naming the covering step. The roster now reads
**59 PR-gated, 6 conditionally gated, 53 with no pull-request gate**, and the
`run-test-suite` target count rises to 115 with #1342's relocation.

Re-run on the rebased tree: `lint-ruff` 0, `lint-mypy` 0, `lint-ci-parity` 0,
`test-lint-ci-parity` 0 (169 cases), and the dedup guard green against #1342's
own re-pinned digests.

## Post-gates review round 1 — seven findings, all sustained (2026-09-17)

The adversarial round on the finished diff returned seven findings. Six were
confirmed by direct test against the code, not by reading; the seventh is a
contract reading. **None was refuted.**

### Finding 1 was the serious one, and its cause was my method

`catalogue-tooling-ci-gates.yml` lists 24 suite paths literally inside
`for d in <paths>; do python -m pytest "$d" -q; done`. The extractor sees
`pytest "$d"` — no literal operand — so `pr_gate_sources` recorded nothing for
them. **21 of the 24 therefore carried a `NO_PR_GATE` reason asserting that no
workflow named them, while that workflow ran every one.**

The cause is not a typo. The roster was authored *from* `pr_gate_sources`, so
wherever the extractor is blind the roster is confidently wrong in exactly those
places. The comment above the loop even says it is statically unresolvable and
that `lint-pack-test-boundary.py` carries a declared exception for it; that file
had been read during shaping. The "then reviewed" half of *authored from
measurement, then reviewed* was performed thematically — checking that reasons
read sensibly by category — not per entry against the workflows, which is the
only reading that could have caught this.

A second half of the same finding: the stale-declaration arm ignored
**conditional** sources, so even a correct source map would not have contradicted
those 21. `NO_PR_GATE` now means "no pull-request check reaches this at all", and
any source contradicts it — `PR_GATED_IF` is what the conditional case is for.
The self-test case that asserted the opposite,
`suites-no-pr-gate-not-contradicted-by-a-conditional-source`, encoded the wrong
assumption and is inverted.

Corrected split: **59 PR-gated, 27 conditionally gated, 32 with no pull-request
gate.** The figure the delivery reported before this round, 59 / 6 / 53, was
wrong.

### All seven, and how each was confirmed

| # | Defect | Confirmed by |
| --- | --- | --- |
| 1 | 21 false `NO_PR_GATE` entries; shell-loop invocation invisible | measured — exact count, independently and by the lint |
| 2 | `pytest known/tests/ $(EXTRA_SUITE)` — the opaque operand demanded no entry | `line_targets` returned only the literal |
| 3 | `# ${shell … pytest …}` dropped; only `$(` was retained | brace kept `False`, paren kept `True` |
| 4 | `npm run test:plugins-extra` inherited the `npm run test:plugins` entry | 0 violations for a different suite |
| 5 | `if: false` loads as Boolean false, so a step that never runs read unconditional | `bool(False)` is `False` |
| 6 | Duplicate step names cross-credited targets between steps | both steps shared `['a/tests/']` |
| 7 | AC-0001 permits the weaker "at least one" rule | contract reading; owner amended |

Findings 2, 3 and 4 are the original defect class — a suite escaping the roster
silently — arriving through three doors the recipe-line anchor did not close.
Finding 1 is worse: an entry present and false.

### Finding 7 corrects my own earlier reasoning

The T2 ledger recorded the all-targets rule as a deviation needing no amendment,
on the grounds that stronger behaviour satisfies AC-0001. That was right about
**conformance** and wrong about **durability**: nothing stopped a later
implementation restoring the weaker rule while still passing AC-0001 and
AC-0014. The owner authorised a second controlled amendment.

### Mutation proof of the fixes, and three weak cases it exposed

The first pass left three arms with no reddening case — the literal-item guard,
the substring boundary, and the job-level `if` presence. **All three were gaps in
the cases, not the code**, which is the whole purpose of probing rather than
asserting:

- `loop-targets-ignores-a-non-literal-item` used `for d in $(SUITES)`, which the
  path-shape filter excludes for an unrelated reason. `$(SUITE_DIR)/tests/` is
  the discriminating shape, because it contains a slash.
- the substring-boundary probe reported a false negative of its own: the
  mutation's anchor did not match, so it never applied. Re-run by locating the
  guard in the file itself.
- the `if`-presence cases put `if: false` on the step only, leaving the job-level
  branch untested.

After strengthening, every arm reddens a named case:

| Arm removed | Exit | Case |
| --- | ---: | --- |
| loop body must run pytest on `$VAR` | 1 | `loop-targets-ignores-a-loop-that-does-not-run-pytest` |
| loop item must be literal | 1 | `loop-targets-ignores-a-non-literal-item` |
| the loop reader itself | 1 | `live-clean` |
| opaque operand demands a key | 1 | `suites-opaque-operand-demands-its-own-key` |
| brace-form comment retained | 1 | `suite-lines-keeps-a-comment-with-a-brace-expansion` |
| substring boundary | 1 | `substring-key-does-not-match-a-longer-command` |
| job `if` presence | 1 | `job-if-false-is-conditional-by-presence` |
| step `if` presence | 1 | `if-false-is-conditional-by-presence` |
| conditional source contradicts `NO_PR_GATE` | 1 | `suites-no-pr-gate-contradicted-by-a-conditional-source` |

184 cases. Gates: `lint-ci-parity` 0, `lint-ruff` 0, `lint-mypy` 0.

## Post-gates review round 2 — three more, all in my own repairs (2026-09-17)

Round 2 reviewed round 1's repairs and returned three Blockers and two Nits.
Every Blocker was a defect **introduced by a round-1 repair**, and two of the
three were in the direction the design calls consequential.

**1. `loop_targets` accepted non-executing text.** The new loop reader searched
the raw body, so `# python -m pytest "$d"` and `echo "python -m pytest $d"` both
satisfied it and every literal item in the list was reported as real coverage.
Repair 1 had *added* coverage detection, where a false positive grants a false
pass — it could validate a `PR_GATED_IF` claim for a suite nothing runs. The body
is now read as comment-stripped command segments, and a printing command is
excluded.

**2. Quoted and composed expansions escaped AC-0002.**
`_OPAQUE_OPERAND.fullmatch(token)` matched a bare `$(EXTRA)` only, so
`"$(EXTRA)"`, `'${EXTRA}'` and `$(SUITE_DIR)/tests/` all slipped past — the last
being the likeliest shape an author writes. Now the outer quotes are stripped and
the pattern is searched rather than fullmatched.

**3. The opaque-operand remedy was undiscoverable.** The opaque branch tested raw
`key in line`, so a key merely *mentioned* on the line suppressed the violation;
and a key legitimately declared for a mixed literal/opaque line never entered
`resolved`, so it was then reported as a **dead entry** — sending the author to
delete exactly what they had just been told to add.

The reviewer called this self-contradictory. **Partly refuted**: the remedy is
satisfiable, verified by performing it — adding the key to the roster *and* to
`_SUBSTRING_KEYS` yields zero violations. It was undiscoverable, not impossible.
Deriving `_SUBSTRING_KEYS` instead would reintroduce the round-1 boundary defect,
because the repo-root key `tests/` boundary-matches almost every test line
(measured). So the declaration stays and the half-finished state now diagnoses
itself by name instead of reading as a dead entry.

### The probe found an unprobed branch

Mutating the quote-stripping loop left the suite green: `search` already finds an
expansion inside quotes, so stripping changes only the *reported* string, and a
truthiness assertion could not see it. The case now pins the reported value, so
the branch is covered by what it actually buys — a message naming `$(EXTRA)`
rather than `"$(EXTRA)"`. An unprobed branch is a control that cannot fail,
whatever else the suite says.

### Mutation proof, round 2's fixes

| Arm removed | Exit | Case |
| --- | ---: | --- |
| echo/comment exclusion in the loop body | 1 | `loop-targets-ignores-an-echoed-invocation` (both since removed with the reader) |
| loop body read as segments | 1 | `loop-targets-ignores-a-commented-invocation` (ditto) |
| `search` rather than `fullmatch` | 1 | `opaque-operand-detects[…]` |
| quote stripping | 1 | `opaque-operand-detects["$(EXTRA)"]` |
| opaque operand demands a key | 1 | `suites-opaque-operand-demands-its-own-key` |
| half-done remedy diagnosis | 1 | `suites-half-declared-line-key-names-its-own-remedy` |

191 cases. Gates: `lint-ci-parity` 0, `lint-ruff` 0, `lint-mypy` 0.

Two Nits also fixed: the spec's Testing Strategy still assigned the
unresolvable-line case to AC-0001 after the amendment moved it to AC-0002, and
the plan still described the comment guard as retaining `$(` only rather than
any `$`.

## Post-gates review round 3 — the loop reader was the wrong instrument (2026-09-17)

Round 3 returned six findings against round 2's repairs. **All sustained.** Five
shared one cause, and it retires an approach rather than patching it.

### One mistake, five findings

`_segments` and `_strip_inline_comment` are documented single-**line** helpers —
"split a shell line", "truncate *line* at the first unquoted `#`". Round 2's
repair applied both to a multi-line shell body. Measured consequences:

| Loop body | `loop_targets` | Direction |
| --- | --- | --- |
| `# a note` then a real `pytest "$d"` | `[]` | missed gate |
| `echo setup` then a real `pytest "$d"` | `[]` | missed gate |
| `true` then `echo "python -m pytest $d"` | `['packs/a/tests/']` | **phantom coverage** |
| `: "python -m pytest $d"` | `['packs/a/tests/']` | **phantom coverage** |

Phantom coverage is the consequential direction: it silently validates a false
`PR_GATED_IF`, which is the failure this delivery exists to remove.

### The decision was reversed on measured evidence

Defects in the loop reader alone: round 1 → 1, round 2 → 1, round 3 → 5. It
diverged. The owner had chosen to build it over a hand declaration on the
strength of one claim of mine — that being derived, "it cannot go stale". That
claim was false: it is hand-written shell parsing, and this module's docstring
already records that making extraction the trust anchor was defeated four ways,
with a fix in one round causing the next round's defect. The loop reader was that
class a fifth time.

Surfaced to the owner with the measurement, who reversed the decision.
`loop_targets` and `_ECHOES` are **deleted** — about 80 lines of shell parsing —
and `_SUITE_SOURCE_EXCEPTIONS` declares the step and its 24 literal suites with
the reason no static scan can attribute them. This is the mechanism
`tools/lint-pack-test-boundary.py` already uses, keyed the same way, for this
same loop.

The split is unchanged at **59 / 27 / 32**, so the declaration buys the same
answer with none of the parsing.

**Residual, stated rather than parsed.** These suites' coverage now rests on a
hand declaration. A listed path the step stops running is a stale declaration no
check can catch. That cost is real and strictly smaller than a parser that
invents coverage. What *is* checked: every declared path appears verbatim in that
step's own `run`, so the declaration cannot drift from the workflow text without
reddening `suite-source-exception-paths-are-in-the-step`.

### The second independent finding

The half-declared-key diagnosis told an author to add the entry to
`_SUBSTRING_KEYS` — including when the entry was a **path**. Since `tests/`
boundary-matches almost every test line, that recommended precisely the edit that
makes a path key substring-eligible, restoring the broad false pass the hand
declaration prevents. My own stated rule forbade it and my branch violated it.
`_PATH_SHAPED` now keeps a path entry on the dead-entry remedy.

### Mutation proof

| Arm removed | Exit | Case |
| --- | ---: | --- |
| declaration wired into `pr_gate_sources` | 1 | `live-clean` |
| a declared path the step does not run | 1 | `live-clean` |
| `_PATH_SHAPED` guard on the line-key remedy | 1 | `suites-unresolved-path-entry-keeps-the-dead-entry-remedy` |

193 cases. Gates: `lint-ci-parity` 0, `lint-ruff` 0, `lint-mypy` 0.

### Review totals

Three post-gates rounds, **18 findings, every one sustained, none refuted.** Two
of my own claims were refuted by the rounds: that a stronger implementation
needed no amendment, and that the loop reader could not go stale.

## Post-gates review round 4 — three findings on the reversal (2026-09-17)

**1. A duplicate step name regained phantom coverage.** The declaration is keyed
on `(workflow filename, step name)`, so a second step of the same name received
all 24 declared targets although it runs none, and attached its own `if:` state
to them. The cross-crediting fixed in round 1 had returned through the
declaration instead of through `extract_ci_targets`. A declaration now applies
only when that step name is unique in its workflow.

**2. Drift validation checked only one direction.** The case asserted each
*declared* path still appears in the step — which catches a removal and misses an
**addition**. A 25th suite added to the loop is invisible to extraction by
definition, so its entry could sit at `NO_PR_GATE` and pass. The step's `run`
body is now digest-pinned, so any edit to it reddens
`suite-source-exception-step-body-is-pinned` and a human re-checks the
declaration. A pin is the only fail-closed answer available when the invocation
cannot be parsed.

**3. The contract still promised three coverage shapes.** AC-0006 said
corroboration recognises three, and that an unrecognised shape "makes
corroboration fail a true `PR_GATED` claim, which is a false alarm and never a
false pass". The declaration is a fourth source, asserted by hand, and it *can*
grant coverage the workflow does not provide — so both halves were false.

AC-0006 now names four sources and says which three are read from the workflow
and which one is asserted. The declaration's cost is bounded by a new
**AC-0007**: unique step name, every listed suite present in that step's `run`,
and that body pinned. 16 criteria → 17.

This is the *fourth* instance of one class across the delivery — a claim about
what a mechanism proves, stated more strongly than it does. The earlier three
were the one-way-safety claim, `paths-ignore` counted as gating, and "exactly
three shapes". Each was repaired only where it was cited; none of those repairs
prompted a sweep for the next instance.

### Mutation proof

| Arm removed | Exit | Case |
| --- | ---: | --- |
| declaration applies only to a unique step name | 1 | `suite-source-exception-does-not-apply-to-a-duplicated-step` |
| step-body digest pin | 1 | `suite-source-exception-step-body-is-pinned` |
| a 25th path added to the real loop | 1 | `suite-source-exception-step-body-is-pinned` |

196 cases. Gates: `lint-ci-parity` 0, `lint-ruff` 0, `lint-mypy` 0.

### Review totals

Four post-gates rounds, **21 findings, every one sustained.** Three of my own
claims were refuted by them: that a stronger implementation needed no amendment,
that the loop reader could not go stale, and that corroboration recognised every
shape that mattered.

### The class sweep I should have run two rounds earlier

Round 4's third finding was the fourth instance of one class, so the class was
swept directly instead of waiting for round 5 to find instance five. Two results:

**A stale companion the round-4 fix missed.** AC-0006 was corrected in the spec,
but the module docstring's residual list still named five limits and did not
mention `_SUITE_SOURCE_EXCEPTIONS` at all — the very source whose cost the
amendment existed to state. Now six limits, with the declaration named and its
three bounds and its one unbounded part spelled out.

**One surviving overclaim of my own.** The list said "no extraction failure
removes a recipe line from the roster", which is true and was doing duty for a
stronger claim it does not support: completeness is extraction-independent at the
**line** level only. Which *targets* a line carries is read by `line_targets`, so
a pytest operand that is neither a literal path nor a recognised expansion would
escape — caught only by the opaque-operand arm, which is itself extraction. Now
stated at that precision.

One nuance verified rather than assumed: `suite_lines` does interpret Make's
`$(call …)`, and a failed expansion returns the line unchanged, which then
carries no path operand and demands an entry — fail-closed.

**The sweep's own conclusion was an instance of the class it swept for, and round
5 caught it.** It was written as "every other guarantee-shaped claim in the
docstring, spec and plan was checked against the code and holds". Only the
**docstring** was swept. The spec's Objective and its `Always do` boundary still
promised that a command the extractor cannot read cannot escape the roster — the
target-level overclaim the docstring had just been corrected for — and the plan
still described completeness as extraction-independent and listed three coverage
shapes with `run_with_floor` as the fourth, omitting the declaration entirely.

So the sweep found two instances, fixed them in one file, and then asserted a
result over three. That is the fifth instance of this class in the delivery,
committed in the act of sweeping for it, which says something the four earlier
instances did not: the failure is not inattention to a particular claim but a
habit of stating a conclusion at a wider scope than the work performed. A sweep's
conclusion has to name the surface it actually covered.

## Post-gates review round 5 — eight findings, and the sweep's own overclaim

Round 5 reviewed round 4's repairs and the self-initiated class sweep. **Eight
findings, all sustained.** Two were code, six were consistency between the code
and what the delivery says about it.

**The declaration's bounds were pinned to the one exception that exists.** The
path-membership and digest assertions hard-coded the single current key, so a
second `_SUITE_SOURCE_EXCEPTIONS` entry would have taken coverage on the generic
name-uniqueness check alone — no path agreement, no pinned body. The declared
tuple itself was also unpinned, so an entry could gain a path without reddening
anything. Both are now driven from an `_EXCEPTION_PINS` manifest asserted to
cover exactly the declaration's keys, with a pin for the step body *and* for the
declared tuple.

**The uniqueness case duplicated the name inside one job.** The implementation
counts names across the whole workflow, which is right because the key carries no
job name — but a change to per-job counting would have left the case green while
restoring cross-job phantom coverage. The fixture now spans two jobs.

The six consistency findings: the spec still promised target-level extraction
independence in both its Objective and its `Always do` boundary; AC-0006 called
the gate-chain source "read from the workflow" when its membership comes from
`build_gate_chain.py`; the plan still described the superseded mechanism and
counted four and five residuals; the spec's figures still read 114 / 56 / 6 / 52;
the declaration's own comment denied checks that now exist; and the sweep's
conclusion was disproven by the first two.

Figures now stated once and measured: **63 recipe lines, 114 distinct targets,
118 roster keys, 59 / 27 / 32.**

198 cases. Gates: `lint-ci-parity` 0, `lint-ruff` 0, `lint-mypy` 0.

### Review totals

Five post-gates rounds, **29 findings, every one sustained, none refuted.** Four
of my own claims were refuted by them:

1. that a stronger implementation than the criterion needed no amendment;
2. that the derived loop reader could not go stale;
3. that corroboration recognised every shape that mattered;
4. that the class sweep had covered the docstring, spec and plan.

Every one was a claim about scope or guarantee stated wider than the work
supported. The reviews did not find much wrong with the mechanism I built; they
found a great deal wrong with what I said about it.

## Contract bookkeeping: a completed section cannot absorb a later round

`approve-plan` refused the amended baseline with *"completed task section
changed: T2, T3, T5"*. Rounds 4 and 5 had added test cases and renumbered AC
references inside task sections the amendment had already pinned, and the
contract is explicit: a completed task section cannot be edited, and a correction
is a new dependency-ordered task.

Recovery, in the contract's own terms rather than by loosening it:

1. Those three sections were restored byte-for-byte to their pinned content.
   They now read as they did at completion — a record, not a live claim.
2. **T9** carries the delta, and lists T2/T3/T5's files in its own `Touches` so
   the correction reaches their output.
3. Restoring the sections re-orphaned three criteria whose only task reference
   was the pre-amendment number inside them (AC-0010, AC-0014, AC-0015).
   `lint-contract-item-alignment` caught all three; T9 adopts them explicitly and
   says why.

Then a sequencing error of mine: `approve-plan` ran *before* T9 was added, so
`schedule` re-pinned a plan the approval had not seen. The tool's own diagnostic
prescribes the recovery — a cohort-only reset, never an engine reset, since
`plan-locked` is legal only from `SPEC-PLAN-APPROVED` and the engine has no
state-setting verb. Run in the documented order, with both statuses reading
`Approved` first.

That reset **is a re-approval in substance**, and it discarded the cohort's
amendment history, completed-task state and retry counters. The owner had just
approved the amended spec and plan, so the re-approval is substantively
authorised rather than assumed — but the discarded history is a real loss, and
the amendment record survives only here and in `notes/owner-decisions.md`.

## The quality-engineer pass — five Concerns, all applied (2026-09-17)

A separate reviewer on the cost-to-live-with lens, not correctness. Five
Concerns, none refuted.

**A maintenance failure crashed instead of diagnosing.** The per-exception loop
recorded a missing or renamed step and then dereferenced `_named[0]` anyway, and
an unpinned exception reached `_EXCEPTION_PINS[_key]` and raised `KeyError`. Both
now stop after reporting. The digest mismatch also emits the replacement value
*and* names the manifest key and field to set, so a maintainer who trips it does
not have to read the test to act.

**One rename cost 21 synchronised edits.** The Linux pack-hook source string and
its condition were written out in 21 roster entries each. Both are now single
constants. The roster *keys* stay explicit per suite — a roster whose keys were
derived would stop being a declaration, which is the property the design rests
on. Net effect on the module: **−10 lines**, despite adding the constants.

**A filter classification was tested behind the boundary that produces it.** The
filtered-source cases inject `filtered=True` into a source record, which exercises
`check_suites` and not `pr_gate_sources`. Three fixture cases now drive
`pr_gate_sources` over a real `paths` trigger, a real `paths-ignore` trigger and
an unfiltered one. This matters more than it looks: **`paths-ignore` carries all
27 conditional entries**, so reading only `paths` would have reported every one of
them as unconditionally gated. Probed — narrowing the check to `paths` reddens
`pr-gate-sources-reads-a-paths-ignore-filter` by name.

**The success line reported roster keys as recipe lines.** It printed
`len(SUITE_DISPOSITION)` — 118 — labelled "suite line(s)", where there are 63
lines and 114 targets. Another instance of the delivery's recurring class, this
time in the telemetry: a count presented as a different count. It now reports all
three: *63 recipe line(s) … carrying 114 target(s) … across 118 roster key(s)*.

A vacuous case went with it: `len(roster) >= len(lines)` passes with unrelated or
dead entries and added nothing to the behavioural completeness check beside it.

**PyYAML is not stdlib.** A bare top-level `import yaml` in the self-test
contradicted `tools/AGENTS.md`'s stdlib rule for `tools/` additions and turned a
missing dependency into a traceback, bypassing the install hint the linter itself
gives. Now guarded, exiting 2 with the same hint.

200 cases. Gates: `lint-ci-parity` 0, `lint-ruff` 0, `lint-mypy` 0,
`lint-contract-item-alignment` 0, dedup guard 51 passed in 61s.

## Confirmatory round on the quality pass (2026-09-17)

Three findings, all narrow, all applied.

**A pin missing a *field* still crashed.** The guard added one round earlier
handled a wholly absent pin but not a pin present with `step_body` or `declared`
missing — that passed the manifest-coverage check and then raised `KeyError`.
Both now read through `.get` and produce the same diagnosis. The reviewer also
confirmed the two `continue`s added for that repair are safe: each follows an
already-recorded failure and skips only checks dependent on the missing step or
pin, so neither can turn a real failure into a pass.

**The de-duplication comment claimed more than the work did.** `_PACK_HOOK_LINUX`
and `_WHY_FILTERED_AND_CONDITIONAL` had 21 uses each, but `_WHY_PATH_FILTERED`
had **zero** while its text remained duplicated six times under a different line
wrap — and the comment beside it said the de-duplication was done. Fixed: 21, 6
and 21 uses, and the comment now states those counts. The reviewer verified by
sampling that the constants carry byte-identical text to the literals they
replaced, which matters because a silent change to a `PR_GATED_IF` source string
would break corroboration for 21 suites at once.

**The self-test still called itself pure-stdlib** while requiring PyYAML. The
docstring now states the dependency and what a missing install does.

This is the seventh instance in the delivery of a claim stated wider than the
work performed, and the fourth found by a reviewer rather than by me. The pattern
is not carelessness about any one claim: it is that I write the summarising
sentence from the intent of the change rather than from its result, and the two
diverge whenever the change is partial. What catches it is a reviewer re-reading
the claim against the artifact — which is exactly what these rounds did, 32 times.

200 cases. Gates: `lint-ci-parity` 0, `lint-ruff` 0, `lint-mypy` 0.
