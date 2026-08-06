# Plan: local-gate-ci-parity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

### The option decision (spec Objective ¶4)

Three options were on the table for closing the local↔CI gap:

| | Option | Stays true? | Cost |
|---|---|---|---|
| (a) | Wire the missing gates into `make ci` | No — the next CI step drifts identically | Low |
| (b) | Generate the local target from the workflow | Yes, in principle | High, and partly impossible |
| (c) | `make ci-strict` running the exact CI job set; `make ci` stays fast | No — hand-maintained, drifts the same way | Medium |

**Chosen: (b), inverted — assert the correspondence instead of generating it.**

Generating a local runner from `build-check.yml` requires interpreting a subset
of GitHub Actions: `working-directory`, `env`, `if:` on `github.event`,
`apt-get`/`sudo`, and pinned `pip install` steps that mutate the ambient
interpreter. Several of those steps have no local expression at all, so a
generator needs a skip-list — and the skip-list is exactly where the drift
would reappear, now one layer less visible.

Inverting it keeps (b)'s property at (a)'s cost. `tools/lint-ci-parity.py`
reads `build-check.yml`, extracts the **gate targets** each step exercises
(script paths and pytest paths, `working-directory`-prefixed), and asserts each
is either reachable from `make ci` or carries a one-line exemption naming why.
Adding a CI step with neither fails the gate a contributor already runs. The
three declaration tables become the repo's first honest inventory of what CI
verifies and a laptop cannot — and because a stale entry in any of them also
fails, the inventory cannot rot into a rubber stamp.

The linter reads a file this change does not edit. That direction is
load-bearing: a parity check whose subject it also authors proves nothing.

The failure mode to design against is not a false alarm but a **vacuous pass**:
over-extraction on the CI side is safe, over-broad coverage on the local side is
fatal and silent. That asymmetry drives every design choice below — the full
argument lives in `tools/lint-ci-parity.py`'s docstring rather than being
restated here, so the two cannot drift apart.

### Sequencing

`build-check.yml` runs ~33 steps beyond `make ci`. Most are not divergence:
CI names `packages/agentbundle/tests/unit/test_version.py` explicitly while
`make test` runs `packages/agentbundle/tests/` wholesale — the same coverage,
spelled differently. Prefix-based coverage collapses those. What remains after
that is roughly a dozen real divergences, and they split cleanly:

- **Free to wire locally** (zero-argument, no cwd): the curation-guard pair and
  the experience-agnosticism pair. Wired in T2 — leaving a wire-able gate
  exempted would make the allowlist a lie on day one.
- **Genuinely CI-only**: skill-script suites needing unvendored third-party
  libraries (`python-pptx`, `docxtpl`, `openpyxl`, `pypdf`, `olefile`,
  `httpx`), the `ripgrep` scrub steps, the inline-shell steps with no repo
  script to call, and the pure-stdlib suites that need a `working-directory` the
  chain cannot express. Exempted per T3's mechanical criterion, each with its own
  reason.

T1 (SAST loudness) is independent. T3 (the linter) must land after T2 or it
fails on gates this change is about to wire. T4 (workstream B) is independent of
all of them; T3a wires T4's manifest check into T2's chain. T6 proves T1–T3.

## Constraints

- Every step added to `tools/repo/build_gate_chain.py` must be invocable as
  `[sys.executable, path]` with **no extra argv** —
  `test_build_gate_chain.py::test_script_steps_are_windows_clean` asserts
  `len(argv) == 2`. Every new lint defaults its flags (`--root .`, and for the
  guard `--base origin/main`), so zero-arg invocation is correct. The corollary
  bites: a CI step needing `working-directory` has no home in this chain, which
  is why several pure-stdlib CI suites end up exempted rather than wired
  (backlog `gate-chain-step-vocabulary`).
- **Three** anchor tests in `tools/test_build_gate_chain.py` pin the chain, not
  two: `test_spawned_script_paths_in_order` (the ordered path list),
  `test_script_steps_are_windows_clean` (`len(argv) == 2`), and
  `test_full_step_sequence` (a hardcoded `len(order) == 11`). Hoist the pinned
  list to a module constant and derive the count from it — a literal count drifts
  out of step with the list it describes.
- The parity linter is scoped to `build-check.yml`; every other workflow is
  classified out-of-scope with a reason in its `WORKFLOW_SCOPE` map. `make ci`'s
  comment must say so — and must not enumerate workflows by name, since that
  list drifts exactly like the claim it replaces.
- `SKIP_SAST=1` must keep exiting 0. CI sets it itself for diffs with nothing to
  scan — which also means the INCOMPLETE banner needs a third, quieter form
  under `GITHUB_ACTIONS`, or it cries wolf on most green PRs.
- `build-check-windows.yml` runs `agentbundle catalogue self-host --check
  --windows`, **not** this chain. Wiring a gate here reaches Windows
  contributors, not Windows CI.

## Tasks

### T1 — Make a skipped SAST leg unmistakable

**Depends on:** none.
**Verification mode:** manual QA (the artifact is terminal output; the test is
reading it).
**Tests:** no stub (manual QA). `Done when:` `SKIP_SAST=1 make build-check` and
`make build-check` end with different, self-describing final lines, and
`make ci` does the same.

**Approach:** a `gate_verdict` Make macro, called as the last recipe line of
both `build-check` and `ci`. Skipped → a bordered `*** INCOMPLETE ***` block
naming the leg, the `SAST_DIRS`/`SAST_CONFIG` scope CI applies it to, and the
instruction to re-run without the flag. Not skipped → a single-line completion
statement. The point is that the **last** line differs: a mid-run `echo`
scrolls away, and a reader who scrolls to the bottom is the reader who is about
to conclude "green".

`ci` currently has no recipe (pure prerequisite list); it gains one line.

### T2 — Wire the two CI-only lint pairs into the local chain

**Depends on:** none.
**Verification mode:** goal-based.
**Tests:** `tools/test_build_gate_chain.py` (existing anchor test, extended).
`Done when:` `python -m pytest tools/test_build_gate_chain.py` passes with the
four new paths in the pinned list, and
`python tools/repo/build_gate_chain.py build-check` runs them.

**Approach:** four `_script_step` entries appended after the existing
workspace-status steps — self-test before lint for each pair, matching the
workflow's own order and the chain's existing `test-lint-* → lint-*` idiom:

1. `tools/test-lint-catalogue-curation-guard.py`
2. `tools/lint-catalogue-curation-guard.py`
3. `tools/test-lint-experience-agnostic.py`
4. `tools/lint-experience-agnostic.py`

`build_gate_chain.py` rather than `pre_pr_catalogue.py`: the guard's own
docstring rules out the projected `pre-pr.py`, and the chain is what `make
build-check` and a Windows *contributor's* `python tools/repo/build_gate_chain.py
build-check` share, so one wiring serves both invocations. It does **not** reach
Windows CI — `build-check-windows.yml` drives `agentbundle catalogue self-host
--check --windows`, which never touches the chain. (That entrypoint,
`self_host_windows.py`, already runs the experience-agnostic pair itself; it is
deliberately not counted as local coverage by T3's linter, since a Windows-only
invocation must not certify a macOS `make ci` run.)

Update all three anchor tests in the same commit — see § Constraints.

### T3 — `tools/lint-ci-parity.py` + self-test

**Depends on:** T2 (the linter fails on gates T2 is about to wire).
**Verification mode:** TDD.
**Tests:** `tools/test-lint-ci-parity.py`. Beyond the mechanical cases, these
exist specifically to stop the gate being *vacuously* clean — the way this kind
of linter fails in practice — and each one corresponds to a hole a review pass
actually constructed:

- `makefile-vars-not-coverage` — bare tokens from a `:=` assignment must not
  enter the local set; they are directory prefixes of nearly everything.
- `makefile-unreachable-target` — a script named only by a target `make ci` does
  not reach is not coverage.
- `makefile-ignore-value-not-coverage` — `--ignore <dir>` names an *excluded*
  tree; reading it as coverage would retire every exemption beneath it.
- `dropped-prereq-loses-coverage` — deleting a prerequisite from `ci:` must
  collapse the derived reachable set, not be silently ignored.
- `prose-not-coverage` — a script named in a docstring is not coverage.
- `classify-untargeted` / `classify-reusable-workflow-job` — a gate added as a
  composite action or a reusable workflow must be classified, not skipped.
- `load-bearing-wired` / `load-bearing-unwired` — the A/B pair: with T2's lints
  in the chain their targets read covered, with the chain text stripped they read
  uncovered. Both sides go through the linter's own `local_targets()` so the case
  cannot drift from what `main()` computes.
- `verdict-wired` — the Makefile's terminal verdict is still called from both
  recipes and still has all three branches.

**Approach:** pure functions plus a thin I/O shell, matching the other
`tools/lint-*.py` (stdlib + `yaml`, `--root` flagged, exit 0/1/2):

- `extract_ci_targets(workflow, name)` — walk `jobs.*.steps`, collect `*.py` /
  `*.sh` tokens and `pytest` path arguments per shell *segment*, prefix each with
  the step's (or the job's `defaults.run`) `working-directory`. Returns targets
  attributed to `<workflow> step '<name>'`, the steps that yielded none, and any
  duplicate step names.
- Local coverage from **invocation positions only**, narrow extractors rather
  than one broad token scan: `makefile_recipe_targets` over the *derived*
  reachable set (`derive_reachable_targets` walks `ci`'s prerequisites plus
  `$(MAKE) <target>` in reached recipes), `script_step_targets`
  (`_script_step("label", *parts)`, joined), and `run_call_targets` (`_run(...)`
  argv in the two pre-PR aggregators). `tools/test-all.py` is **not** a source:
  nothing invokes it, so it cannot certify parity — the first draft's mistake.
  All of it composes in one place, `local_targets()`, so the self-test's A/B
  cannot diverge from `main()`.
- `is_covered(target, local)` — exact match, or any local token that is a
  directory prefix of the target (this is what makes `make test`'s
  `packages/agentbundle/tests/` cover CI's per-file spellings).
- Three declaration tables, all in-file so there is no third source of truth,
  all failing when stale in both directions: `EXEMPTIONS` (target → reason),
  `UNTARGETED_STEPS` (step name → why it has nothing to declare), and
  `WORKFLOW_SCOPE` (workflow file → in-scope, or out with a reason). They are
  keyword parameters of `check()` defaulting to the globals, so each self-test
  case supplies its own instead of mutating shared state.

**Exemption criterion, applied mechanically** — a target is exempt only if it
needs a dependency outside `tools/requirements.txt` plus the two editable
installs `AGENTS.md` prescribes, **or** it needs a `working-directory` the
chain's step contract cannot express. Everything else gets wired. The second
clause is a real limitation, not a loophole: it is why the pure-stdlib
catalogue-curation and credential-setup suites stay CI-only, and it is on the
register as `gate-chain-step-vocabulary`.

Then wire the pair into the T2 chain (self-test, then lint).

### T3a — Gate the umbrella's manifest

**Depends on:** T4.
**Verification mode:** goal-based.
**Tests:** covered by `tools/test_build_gate_chain.py`'s pinned list.
`Done when:` `tools/test-test-all.py` appears in the chain and runs.

**Approach:** `tools/test-all.py` is hand-run and nothing invokes it, so
"exits 0 on the merged tree" is a one-time observation and the next dangling
entry rots identically. Wire T4's `tools/test-test-all.py` into the chain: its
live case asserts every `TESTS` entry resolves to a file, which gates the cheap
half of the umbrella without paying for the multi-minute suite.

### T4 — Umbrella-runner honesty

**Depends on:** none.
**Verification mode:** TDD for the preflight, goal-based for the run.
**Tests:** `tools/test-test-all.py` (named for its subject, per the
`test-<tool>` convention) drives `_missing_targets` with synthetic `TESTS`
lists, plus a real-invocation case in an empty `git init` tree. `Done when:` a
planted missing entry yields exit 2 with the entry named and no `✓` line
printed; `python3 tools/test-all.py` exits 0.

**Approach:**

- `_entry_targets(cmd)` — the argv tokens that name a file (`.py`/`.sh`,
  excluding `sys.executable`).
- `_missing_targets(tests, root)` — pure; returns `[(label, problem)]`. An entry
  yielding *no* target is a problem too, so a bare `-m pytest` cannot preflight
  clean while verifying nothing.
- `main()` calls it first. Non-empty → print a `BROKEN MANIFEST` block naming
  each offending entry and return **2**, before running a single test. Document
  0/1/2 in the docstring.
- Drop the two dangling entries with the coverage reason in a comment above
  `TESTS` (spec AC10/AC11). Cite ADR-0052 for the one real rename; the chain map
  itself is only readable from the unreachable commit `321c825c`, so say that
  rather than assert what it contained.
- Correct the docstring's "every self-test in `tools/`" claim — count-free
  wording, since both the list and the population change.
- Correct the same claim in `tools/hooks/README.md` § CI parity, which asserts
  "the catalogue gate and CI run the same checks". Fixing one and leaving the
  other moves the lie.

### T5 — Bookkeeping and the honest comment

**Depends on:** T3, T4 (records their residuals).
**Verification mode:** goal-based.
**Tests:** no stub (mode). `Done when:` `python3 -c "import tomllib, pathlib;
tomllib.loads(pathlib.Path('workspace.toml').read_text())"` parses, and
`.claude/skills/work-loop/scripts/lint-spec-status.py --root .` is clean.

**Approach:** remove the resolved `test-all-dangling-entries` entry from
`[backlog].open`; add the four residuals this change knowingly leaves open —
`xd-chain-structural-invariants-uncovered`, `ci-parity-docs-yml-out-of-scope`,
`gate-chain-step-vocabulary`, `curation-guard-silent-base-skip`. Rewrite the
`make ci` comment per spec AC8.

### T6 — Prove workstream A by construction

**Depends on:** T1, T2, T3.
**Verification mode:** manual QA.
**Tests:** no stub (mode). `Done when:` the observed output of each run below is
recorded in this plan's changelog and in the PR description.

1. Scratch commit touching `packages/agentbundle/agentbundle/version.py` with no
   `Engine-Change-RFC:` trailer → the wired `lint-catalogue-curation-guard` step
   must fail naming the path. Amend in the trailer → must pass. Drop the scratch
   commit. Note the precondition from spec § Assumptions: the branch must be
   fetched and ahead of `origin/main`, or the guard's path-gate no-ops.
2. Remove the wired guard step from the chain and re-run the same scratch commit
   → the local gate must go green, which is what "CI-only gate" meant before
   this change. This is the half that proves the wiring is the fix rather than
   the commit being innocuous.
3. `SKIP_SAST=1 make build-check` vs `make build-check` vs
   `SKIP_SAST=1 GITHUB_WORKFLOW=build-check make build-check` — all three final
   lines recorded, all three distinct. Plus `GITHUB_ACTIONS=true` alone, which
   must still get the INCOMPLETE banner (AC3a).

## Assumption trio

- **Files touched:** `Makefile`; `tools/repo/build_gate_chain.py`;
  `tools/test_build_gate_chain.py`; new `tools/lint-ci-parity.py`,
  `tools/test-lint-ci-parity.py`, `tools/test-test-all.py`;
  `tools/test-all.py`; `tools/hooks/README.md`; `workspace.toml`;
  `docs/specs/README.md` (index row); `docs/knowledge/patterns.jsonl` (three
  entries from § Capture learnings); this spec and plan.
- **Tests that demonstrate done:** `tools/test-lint-ci-parity.py`,
  `tools/test-test-all.py`, `tools/test_build_gate_chain.py`, plus
  `make ci` with no `SKIP_SAST`, `tools/lint-catalogue-curation-guard.py --root
  . --base origin/main`, and `tools/test-all.py` — and the T6 scratch-commit
  runs, without which AC2/AC3 are unproven.
- **Not changing:** `.github/workflows/**` (the parity linter's input must not
  be authored by this change); `packages/agentbundle/**` (so no
  `Engine-Change-RFC:` trailer, no version bump, no `CHANGELOG.md` entry is
  owed); the shipped `tools/hooks/pre-pr.py` (deliberately runs no repo
  linters); `SKIP_SAST`'s exit code.

## Declined patterns

- **A `make ci-strict` target.** Tempting because it is the smallest edit that
  answers "run what CI runs". Declined: hand-maintained, so it drifts exactly
  as `make ci` did, and it splits the gate a contributor runs from the gate that
  gates them.
- **Generating the `Makefile` from `build-check.yml`.** Declined in the option
  table above: needs a skip-list, and the skip-list is the new drift surface.
- **Reason-*class* exemptions (`third-party-libs`, `ci-only-env`) instead of
  per-target reasons.** Tempting because ~a dozen entries share a cause.
  Declined: a class is a bucket things get dropped into without being read,
  which is how the two dangling `test-all.py` entries survived.
- **Removing the now-duplicated steps from `build-check.yml`.** Tempting for
  tidiness. Declined: CI-structure change, out of the spec's boundary, and the
  workflow is the linter's input.
- **Making `SKIP_SAST=1` exit non-zero.** Tempting as the strongest possible
  signal. Declined for the reason in spec § Never do — CI sets the flag itself.
- **Extending the parity linter to `docs.yml` and `ci-security.yml` now.**
  Tempting while the extraction code is open. Declined: the brief's evidence is
  about `build-check.yml`; a second workflow's exemption inventory is a second
  research task. Recorded as backlog, not silently omitted.
- **Fixing the curation guard's silent base-ref skip in this PR.** Tempting
  because it is the same defect class as the `SKIP_SAST` fix, found while wiring
  the guard. Declined: the guard is shared with CI, so changing its exit
  semantics is a deliberate CI-behaviour change, not a ride-along. Recorded as
  `curation-guard-silent-base-skip`.
- **A cwd-aware chain step so the pure-stdlib CI suites could be wired.**
  Tempting because the exemption criterion's second clause exists only because
  the chain lacks the vocabulary. Declined: it relaxes an argv-shape assertion
  three tests depend on, which is its own change. Recorded as
  `gate-chain-step-vocabulary`.
- **Adding `tools/test-run-pack-evals.py` to `test-all.py` to "replace" the
  dropped judge entry.** Declined: `pre_pr_catalogue.py` already runs it, so
  the entry would duplicate a gated check and make `test-all.py` look more
  authoritative than it is.

## Risks

- **The parity linter's extraction is heuristic.** A CI step could exercise
  something the regex does not see, and the linter would report clean. Mitigated
  by scope, not by cleverness: it is a *drift detector for newly-added steps*,
  and the honest bound belongs in its docstring. Over-extraction is the safe
  failure (a spurious target forces a human to write an exemption); silent
  under-extraction is the dangerous one and is what the docstring must name.
- **`make ci` without `SKIP_SAST` is slow** (CI budgets 15 minutes). Accepted:
  the spec's gate list requires the real run, and T1 exists so a reader knows
  which one they got.
- **The T6 scratch commit touches `packages/agentbundle/**`.** It must be
  dropped before the PR, or the change ships owing a trailer and a release. The
  task ends with the drop, and `git log origin/main..HEAD` confirms it.

## T6 evidence (observed output)

**AC2 — the guard now fires locally.** Scratch commit appending a comment to
`packages/agentbundle/agentbundle/version.py`, no trailer.
`python tools/repo/build_gate_chain.py build-check`:

```
test-lint-catalogue-curation-guard: all cases passed.
lint-catalogue-curation-guard: path-gate: changeset touches a protected tree without the 'Engine-Change-RFC:' exemption trailer:
lint-catalogue-curation-guard:     packages/agentbundle/agentbundle/version.py
build chain: ✖ lint-catalogue-curation-guard failed (exit 1)
```

Amending `Engine-Change-RFC: n/a — …` into the commit message →
`lint-catalogue-curation-guard: ok`, exit 0. Scratch commit dropped
(`git log origin/main..HEAD` shows only the real commit).

**AC2, counterfactual — it was genuinely CI-only before.** At base commit
`c2acf82e`, grep for `curation-guard` in each local gate source:

```
Makefile                                 hits=0
tools/repo/build_gate_chain.py           hits=0
tools/catalogue/pre_pr_catalogue.py      hits=0
tools/hooks/pre-pr.py                    hits=0
```

**AC4/AC6 — the drift detector is load-bearing.** Removing the two guard steps
from the chain (same commit, nothing else changed):

```
lint-ci-parity: ✖ tools/lint-catalogue-curation-guard.py — run by build-check.yml step
  'catalogue-curation guard lint + self-test (RFC-0059 D6)'; not reachable from `make ci`
  and not in EXEMPTIONS. …
lint-ci-parity: ✖ tools/test-lint-catalogue-curation-guard.py — … 
lint-ci-parity: 2 parity violation(s).
```

Chain restored → `lint-ci-parity: ok`. The same property is pinned as a
`load-bearing` case in `tools/test-lint-ci-parity.py`, so it is asserted on
every run, not only in this transcript.

**AC3 / AC3a — three distinct terminal verdicts.** Re-captured after the AC3a
change (the earlier transcript recorded `SKIP_SAST=1 GITHUB_ACTIONS=true`, which
now correctly yields the INCOMPLETE banner — only `GITHUB_WORKFLOW=build-check`
reaches the benign branch). Actual bytes:

```
$ SKIP_SAST=1 make build-check                     # local shortcut
*************************************************************
*** make build-check: INCOMPLETE — this is NOT a full pass.
*** The SAST/SCA leg was SKIPPED (SKIP_SAST is set).
*** CI runs that leg on any diff touching: tools packs packages
*** or: bandit.yaml .snyk Makefile .github/workflows/build-check.yml .github/workflows/codeql.yml
*** Re-run without SKIP_SAST before treating this as green.
*************************************************************

$ SKIP_SAST=1 GITHUB_WORKFLOW=build-check make build-check    # CI's own skip
make build-check: complete for this diff — SAST/SCA skipped by build-check.yml because the diff touches nothing scannable.

$ SKIP_SAST=1 GITHUB_ACTIONS=true make build-check    # spoofable env alone
*************************************************************      ← INCOMPLETE, correctly

$ make build-check                                  # full run
make build-check: complete — every leg of this target was invoked, SAST/SCA included.
```

"was invoked", not "ran": make sees each leg's exit code, and a leg can exit 0
having gated nothing — the wired curation guard skips its path-gate on a missing
or stale base (`curation-guard-silent-base-skip`). The banner should not claim
more than make can observe.

## Bundled: knowledge-file encoding normalization

`docs/knowledge/patterns.jsonl` carried a mix of `\uXXXX` escapes and raw UTF-8 —
entries written with `json.dumps(..., ensure_ascii=True)` sat beside ones written
without it, so `—` appeared as `\u2014` on some lines and literally on others.
Rewritten once with `ensure_ascii=False`, so every entry is raw UTF-8 and a future
append cannot make the file inconsistent again by picking the other default.

This touches 19 lines this change did not author, which is why it is called out
rather than buried: **no entry's data changed.** Verified by parsing both versions
and comparing the decoded objects — every id present on `main` is equal as data;
only the escape representation differs. `lint-knowledge.py` passes on 24 entries.

## Changelog

- 2026-08-06: Authored. Option (b)-inverted chosen over (a)/(c); reasoning in
  § Approach.
- 2026-08-06: Reworked after the pre-EXECUTE adversarial pass. Six substantive
  corrections, all of which would have shipped a gate that reported clean
  without checking anything:
  (1) local coverage now reads **invocation positions only** — the first draft's
  token scan pulled `tools` / `packs` / `packages` out of `SAST_DIRS :=` and
  those are directory prefixes of nearly every gate target, so the linter would
  have been permanently green;
  (2) `tools/test-all.py` dropped as a coverage source — nothing invokes it, so
  it cannot certify parity;
  (3) added `UNTARGETED_STEPS`, because seven of `build-check.yml`'s gates are
  inline shell and a new gate in that house style was invisible;
  (4) added `WORKFLOW_SCOPE`, because a gate in a *new* workflow file was
  undetected;
  (5) the SKIP_SAST banner gained a third CI-intentional form — CI sets the flag
  itself on most PRs, and crying wolf in a green required check is how the
  previous notice got ignored;
  (6) AC10's rename provenance was wrong (ADR-0052 renamed
  `design-system-foundations`; `design-principles` is a new RFC-0066 D3 skill,
  not a rename) and the error was already in a code comment.
  Also: three anchor tests pin the chain, not two; Windows CI does not run the
  chain; `tools/hooks/README.md` carried the same false parity claim; and
  `test-all.py`'s manifest is now gated (T3a) rather than merely observed once.
- 2026-08-06: Recovery note — a concurrent Conductor workspace popped this
  workspace's `git stash` mid-run (the stash stack is shared across workspaces on
  one repo). Work was recovered from the re-stashed commit. Park WIP with a local
  commit here, never `git stash`.
- 2026-08-06: Second review round (adversarial + quality + security, post-GATES).
  Three independent passes converged on the same shape of defect — the gate
  reporting clean while checking less than it claimed — and each found a distinct
  instance:
  (1) the reachable-target set was a *fourth* declaration table with no staleness
  check, and dropping `test` from `ci:` left the linter clean while 46 of 70
  targets lost their coverage. Now derived from the `Makefile` (AC4d).
  (2) `--ignore packs/converters/` in a reachable recipe would have entered the
  local set, marking an *excluded* tree covered and silently retiring 11 of the
  18 exemptions. Value-taking pytest flags now consume their value (AC4a).
  (3) a step carrying `uses:` and no `run:` — how a gate added as a composite or
  third-party action looks — was neither extracted nor classified. Now classified
  (AC4b), along with reusable-workflow jobs.
  Also: per-segment provisioning classification (`pip install x && python3
  tools/gate.py` no longer loses the gate); duplicate step names fail (AC4e);
  redundant exemptions fail (AC5); `WORKFLOW_SCOPE` joins the non-empty-reason
  check; `cd x && pytest` resolves to a real target, which moved two entries out
  of the untargeted table and into exemptions where they belong; the verdict
  banner keys on `GITHUB_WORKFLOW` (AC3a) and its wiring is asserted (AC3b); and
  `test-all.py` reports a wrong repository root as such rather than advising
  someone to delete a correct manifest.
- 2026-08-06: Third review round. Three more fatal-direction holes, all in the
  lexical-extraction layer, all found by construction rather than by reading:
  (1) **Makefile recipe comments were read as commands.** A tab-indented
  `# … pytest packs/ …` inside a reachable recipe put `packs/` into the coverage
  set, and because coverage is prefix-based that one comment marked every
  `packs/**` gate covered; `# historically: $(MAKE) zipapp` pulled an unreachable
  target in. The live `build-check` and `sast` recipes already carry such lines.
  Fixed by making `iter_makefile_rules()` the single parser both walks consume —
  one place to get comments, `\` continuations, and multi-target rules right,
  rather than two that must agree.
  (2) **`\bpytest\b` matched inside a path.** `bash tools/run-pytest-suite.sh`
  read as a bare pytest invocation, and the bare-pytest branch then skipped the
  path scan entirely — with a `working-directory` that resolved to a covered
  directory the step reported *covered* while its real gate went unchecked.
  `pytest` now has to sit at a command position, and the working-directory
  substitution happens only when a segment names no path at all.
  (3) **AC3b's own assertion passed with the verdict call commented out** — the
  recipe-span regex did not stop at `#`, so it swallowed the SAST comment block.
  The recipe is now the contiguous tab-indented non-comment block, and polarity is
  asserted by *executing* the macro under `sh` for three environments: grepping
  for `GITHUB_WORKFLOW` survived inverting the test, which would have printed the
  reassuring CI line on a laptop.
  Also: the recorded T6 evidence had gone stale against the macro it documents and
  was re-captured; `run_call_targets` strips comments (the adopter stub in
  `pre-pr.py` ships commented `_run` examples by design); `wd` persists across
  lines of one `run:` body; the linter's exit 1 and exit 2 are now pinned by
  subprocess cases in a temp tree, which a `return 1` → `return 0` mutant had
  survived; and the three new scripts carry the Windows UTF-8 stream guard the
  rest of `tools/` has.

- 2026-08-06: Fourth review round — **the loop's termination rule fired.** Three
  more fatal-direction holes, each constructed and run, and one of them was
  *introduced by round 3's own fix*:
  (1) **Indirect coverage sources were not gated on reachability.** `local_targets`
  unioned the gate chain and both aggregators unconditionally, so dropping
  `build-check` from `ci:` — which removes `catalogue verify`, the entire gate
  chain including this linter, and the SAST leg — left the coverage set
  byte-identical. AC4d was true only of the prerequisites whose coverage happens
  to come from a recipe line. Each indirect source is now conditional on its own
  path being in the Makefile-derived set, and the self-test drops each of the four
  prerequisites in turn.
  (2) **A subshell `cd` was treated as persistent.** Round 3 made `wd` carry
  across lines, which is right for a plain `cd` and wrong for `(cd x && …)` — the
  form `build-check.yml:495` already uses. A new gate on the following line became
  `packages/credbroker/tools/lint-new-gate.py`, which `make test`'s
  `packages/credbroker/` prefix covered. Now a parenthesised `cd` prefixes its own
  line only, and `cd -` / `cd ~` / absolute paths clear rather than compose.
  (3) **Inline trailing recipe comments** still granted coverage; round 3 closed
  only the whole-line form. One `@true  # see also tools/lint-x.py` could cover a
  gate deleted from the chain.

  **Termination and the decision it forces.** Work-loop § Termination stops the
  loop when findings keep coming while the diff shrinks — and rule 3's real test,
  "spot-fixing without addressing root cause", is now met: four rounds, four
  distinct lexical classes, and a fix in one round creating a defect in the next.
  The root cause is not any single regex. It is that **extraction of gate targets
  from shell text has no completeness bound**, so no number of pins closes the
  class.

  What was done, rather than a fifth patch round on the extractor:
  - The three Blockers above are fixed and pinned.
  - **The trust anchor moved.** `STEP_DISPOSITION` is now a roster with one entry
    per `run:`/`uses:` step — 50 of them, up from the 37 the two old tables
    covered — declaring either `LOCAL("<make target>")` or `CI_ONLY("<reason>")`.
    Every step must appear and every entry must name a real step; both directions
    fail. That check reads no shell commands, so no shell shape defeats it.
    `EXEMPTIONS` and `UNTARGETED_STEPS` are gone: their reasons are preserved,
    re-keyed from paths onto the steps that own them.
  - **Extraction is demoted to corroboration.** For a `LOCAL` step, every target
    the extractor sees must be covered. Since the roster already carries
    completeness, an extractor bug can now only raise a false alarm — never grant
    a false pass. Previously the extractor decided *whether a step needed a
    declaration at all*, which is why every one of its misses was silent.
  - The roster was authored from what the gate already concluded, then reviewed —
    not 50 hand judgements. No step was unresolvable, and no step had mixed
    coverage, so the corroboration check could be made strict without loss.

  **Measured, not assumed.** A new step whose only extracted target
  phantom-prefixes a covered directory (round 4's Blocker-2 shape) landed
  *silently* under the extraction-only design and now fails; both are asserted
  (`roster-catches-phantom-covered-new-step`). And the residual is asserted too:
  a gate added *inside* an already-dispositioned step is **not** caught, by either
  design — a second command on a later line changes nothing a per-step scheme sees.
  The reviewer's pitch called the declaration form "complete by construction";
  that was wrong, and the backlog entry now says so with the options
  (`ci-parity-hidden-gate-in-dispositioned-step`). Closing it needs a per-step
  content hash, or executing each command.
