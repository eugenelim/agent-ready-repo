# Spec: local-gate-ci-parity

- **Status:** Shipped (superseded in part by [ADR-0085](../../adr/0085-split-the-sast-gate-into-its-own-ci-job.md) — **AC3, AC3a and AC3b's verdict case set**: the `GITHUB_WORKFLOW`-keyed CI-intentional branch is retired and provenance becomes `$(origin SAST_DELEGATED)`, so the three-distinct-lines requirement now describes a different three; everything else stands) <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0017, RFC-0059, ADR-0052

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Two defects, one concern: **the repo's local test signal does not mean what a
reader takes it to mean.**

**1 — `make ci` claims to mirror CI and does not.** Its comment says it
"mirrors build-check.yml + docs.yml on Linux/macOS". Two gates reached CI red
past a green local run during PR #872:

- `tools/lint-catalogue-curation-guard.py` — the RFC-0059 D6 path-gate that
  requires an `Engine-Change-RFC:` trailer for a changeset touching
  `packages/agentbundle/**` outside a `tests/` path. It appears in
  `build-check.yml` and in **no** local chain: not the `Makefile`, not
  `tools/repo/build_gate_chain.py`, not `tools/catalogue/pre_pr_catalogue.py`.
  A CI-only gate with no local equivalent at all.
- **The SAST/SCA leg.** `make ci` reaches it, but `SKIP_SAST=1` is the
  documented fast path and the skip is a single mid-run `echo`. A green
  `SKIP_SAST=1 make build-check` is textually indistinguishable from a green
  real one, so the skipped leg is invisible at exactly the moment a reader
  concludes "green, ship it".

The deeper defect is not the two missing gates — it is that **nothing detects
the divergence.** Any future CI step can be added with no local counterpart and
no signal. Wiring today's two holes shut without closing that would put the
repo back in the same position on the next PR.

**2 — `tools/test-all.py` has exited non-zero for weeks and nobody noticed.**
`TESTS` names `tools/test-check-xd-chain.py` and
`tools/test-llm-judge-cross-pack-eval.py`. Neither exists in the tree, and
neither was ever *deleted* from `main`: `git log --diff-filter=D` finds nothing
because the files were never on `main` at all. They were added on PRs #673 /
#684, which the 2026-07-24 history rewrite left unreachable; the rewritten
commit `96232e62` carried the `TESTS` entries into a tree that never held the
scripts. So the umbrella runner reports `test-all: 2 of 9 failed` — a message
about two tests that ran and failed, when in fact two entries never resolved to
a file. A runner that mis-describes what it checked is worse than one that
doesn't run: it is trusted.

## Acceptance Criteria

### Workstream A — local gate ↔ CI parity

- [x] **AC1:** `tools/lint-catalogue-curation-guard.py` runs from a local gate
      chain reachable via `make build-check` (hence `make ci`), together with
      its self-test `tools/test-lint-catalogue-curation-guard.py`. Windows
      *contributors* reach it through
      `python tools/repo/build_gate_chain.py build-check`; Windows *CI* does not
      — `build-check-windows.yml` drives `agentbundle catalogue self-host
      --check --windows`, which never invokes the chain.
- [x] **AC2:** A commit touching `packages/agentbundle/**` outside a `tests/`
      path and lacking the `Engine-Change-RFC:` trailer fails the local chain.
      Demonstrated by construction against a scratch commit, not by reading.
- [x] **AC3:** A local run that skipped the SAST/SCA leg ends with a terminal
      banner naming the skipped leg and stating the run is **INCOMPLETE**; a run
      that did not skip ends with a distinct completion line. `make build-check`
      and `make ci` both emit one. A CI run that skipped the leg gets a third,
      distinct line — the workflow sets `SKIP_SAST=1` itself whenever the diff
      touches nothing scannable, and shouting INCOMPLETE inside a green required
      check on most PRs would train readers to ignore the banner. Demonstrated
      by construction: all three final lines differ.
- [x] **AC3a:** The CI-intentional branch keys on `GITHUB_WORKFLOW`, not on
      `GITHUB_ACTIONS` alone. That line asserts a specific provenance, and any
      process can export `GITHUB_ACTIONS` — `act`, a devcontainer, a developer
      exercising the branch — which would hand them a claim untrue of their run.
- [x] **AC3b:** The verdict's wiring and *polarity* are asserted, not observed
      once. A manual-QA demonstration is a one-time fact; a later edit dropping
      `$(call gate_verdict,…)`, commenting it out, or inverting the
      `GITHUB_WORKFLOW` test would silently restore the "green, ship it"
      ambiguity. `tools/test-lint-ci-parity.py` asserts both recipes still call
      the macro (reading the recipe as its contiguous non-comment tab block, so a
      commented-out call fails) and asserts each of the three verdicts by
      **executing** the macro body under `sh` for the three environments —
      grepping for `GITHUB_WORKFLOW` survives inverting the condition, which is
      the exact false assurance AC3a removes.
- [x] **AC4:** `tools/lint-ci-parity.py` derives, from
      `.github/workflows/build-check.yml`, the set of gate targets that workflow
      exercises, and fails when any target is neither reachable from `make ci`
      nor carried by an explicit exemption with a stated reason.
      **The property this delivers, stated exactly:** the gate holds a
      **disposition per step** (`STEP_DISPOSITION`) — each `run:`/`uses:` step
      declares either the `make` target covering it locally or why no local gate
      can. A step cannot be added, renamed, or removed without a human
      dispositioning it, and that check reads no shell commands, so no shell shape
      defeats it. Extraction is retained only to *corroborate* a `LOCAL` claim, so
      an extractor bug raises a false alarm rather than granting a false pass —
      the inversion that matters, since four review rounds each defeated the
      extractor a different way. It is **not** a proof that the two environments
      verify the same things, and it does not catch a gate added *inside* an
      already-dispositioned step; no per-step scheme does. The linter's § What it
      does not prove is canonical, and
      `workspace.toml [backlog].open`
      `ci-parity-hidden-gate-in-dispositioned-step` records the residual with the
      options for closing it.
- [x] **AC4a:** Local coverage is computed from **invocation positions only** —
      the recipe lines of Makefile targets `make ci` transitively reaches, the
      gate chain's `_script_step` calls, and the pre-PR aggregators' `_run`
      argv. Never a variable assignment (`SAST_DIRS := tools packs packages`
      would otherwise make every path in the repo covered), never prose, never a
      Makefile target `make ci` does not reach, and never
      `tools/test-all.py` (which nothing invokes, so it cannot certify parity).
      The value of a value-taking pytest flag is never a target either:
      `--ignore packs/converters/` names an *excluded* tree, and reading it as
      coverage would retire every exemption beneath it.
- [x] **AC4b:** A step from which no gate target can be extracted fails the
      linter unless it is enumerated with a reason. That covers three shapes, all
      of which are ordinary Actions idiom and all of which would otherwise be
      invisible to the very linter this spec adds: an inline-shell `run:` step
      (the `rg` scrubs, the evals-disposition loop); a step carrying `uses:` and
      no `run:` (a gate added as a composite or third-party action); and a job
      whose whole body is a reusable-workflow `uses:`. The table is for steps
      with *nothing to declare* — a gate whose target exists but the extractor
      cannot parse belongs in the exemption list, keyed on its real path, or the
      drift merely relocates.
- [x] **AC4c:** Every file in `.github/workflows/` must be classified in-scope or
      out-of-scope-with-a-reason; an unclassified new workflow fails the linter.
      Otherwise "parity" quietly means "parity with the one workflow we picked".
- [x] **AC4d:** The reachable-target set is **derived from the `Makefile`**, not
      declared — `ci`'s prerequisites walked transitively plus `$(MAKE) <target>`
      calls in reached recipes. A hand-written list would be a fourth
      declaration table, and the one no staleness check can police: widening it
      is precisely the "silence a parity failure by widening" move § Never do
      bans. Removing a prerequisite from `ci:` must collapse coverage, and the
      self-test asserts it does.
- [x] **AC4e:** A step name appearing twice in an in-scope workflow fails the
      linter. The untargeted table is keyed by step name for readability, so
      duplicate names would let one entry silence two steps.
- [x] **AC5:** Each of the three declaration tables is self-maintaining: every
      entry states a non-empty reason, and an entry that no longer corresponds
      to reality is itself a failure — a target no in-scope workflow runs, a step
      name that is no longer untargeted, a workflow file that was deleted. Both
      staleness *directions* count: an exemption whose target `make ci` now
      covers reports as **redundant**, or it keeps asserting "a local gate cannot
      run this" after that stops being true (which is where the
      `gate-chain-step-vocabulary` backlog item will take it).
- [x] **AC6:** `tools/lint-ci-parity.py` runs from the same local chain as AC1,
      so a CI step added without a local counterpart or a declared exemption
      fails the gate that a contributor runs.
- [x] **AC7:** A self-test `tools/test-lint-ci-parity.py` proves the linter's
      pure functions, including the three cases that keep it from being
      vacuously clean: bare Makefile variables are not coverage, a script named
      only by a non-`ci` Makefile target is not coverage, and prose is not
      coverage. It also proves the wiring is **load-bearing** — stripping the
      newly-wired lints from the chain source must make their CI targets read as
      uncovered again.
- [x] **AC8:** The `make ci` comment states what the target actually covers and
      what it does not, replacing the "mirrors build-check.yml + docs.yml"
      claim, without enumerating workflows by name (that list drifts too).
- [x] **AC8a:** `tools/hooks/README.md` § CI parity carries the same
      "the catalogue gate and CI run the same checks" claim and is corrected in
      the same change. Fixing one and leaving the other moves the lie.

### Workstream B — umbrella runner honesty

- [x] **AC9:** `tools/test-all.py` validates every `TESTS` entry's `.py`/`.sh`
      target token at startup, before running anything, and on a missing target
      prints a block that names each offending entry and exits **2** — distinct
      from exit 1 (a test ran and failed) and 0 (all passed). An entry from
      which no target token can be extracted is a manifest error too, so a bare
      `-m pytest` cannot preflight clean while verifying nothing. The exit-code
      contract is documented in the module docstring.
- [x] **AC10:** The `check-xd-chain` entry is **dropped**, with the reason
      recorded in the file: the checker and its `xd-chain-gate.yml` workflow are
      absent from `main`, and the chain map they enforced is readable only from
      the unreachable commit `321c825c`, so it cannot be verified against `main`
      at all. Two of the five skills that map named no longer exist under those
      names — `design-system-foundations` → `design-system` (ADR-0052), and
      `design-token-taxonomy`, RFC-0071's intended new name for `design-system`,
      is nowhere in the tree. (`design-principles` is a separate new skill from
      RFC-0066 D3, not a rename of either; an earlier draft of this AC said
      otherwise.) Of its five invariants, description-length is covered by
      `agentbundle catalogue lint` and Digital-Experience-Contract copy parity
      by `tools/catalogue/check_contract_parity.py`.
- [x] **AC11:** The `llm-judge-cross-pack-eval` entry is **dropped**, with the
      reason recorded in the file: the judge moved into
      `packages/agentbundle/agentbundle/commands/pack_evals.py`, and its
      self-test is `tools/test-run-pack-evals.py`
      (`build_judge_prompt` / `parse_judge_verdict` / `get_judge` /
      `load_judge_config` / `grade_judge`), which
      `tools/catalogue/pre_pr_catalogue.py` already runs — so the check is
      gated, not lost.
- [x] **AC12:** Every residual this change knowingly leaves open is on the
      register in `workspace.toml [backlog].open`, and the resolved
      `test-all-dangling-entries` entry is removed from it. The residuals:
      `xd-chain-structural-invariants-uncovered` (the three invariants with no
      successor), `ci-parity-docs-yml-out-of-scope`,
      `gate-chain-step-vocabulary` (the chain cannot express a
      `working-directory` step, which is why several pure-stdlib CI suites are
      exempted rather than wired), and `curation-guard-silent-base-skip`.
- [x] **AC13:** `tools/test-all.py`'s docstring stops claiming it runs "every
      self-test in `tools/`". The replacement wording carries no count — the
      list and the population both change, and a number in prose is a third
      thing to keep in sync.
- [x] **AC14:** `python3 tools/test-all.py` exits 0 on the merged tree, **and**
      its manifest is gated: `tools/test-test-all.py` runs in the `build-check`
      chain and fails if any `TESTS` entry stops resolving. AC14 without this is
      a one-time observation about a runner nothing invokes — which is exactly
      how the two dangling entries survived.

## Boundaries

### Always do

- Read the workflow; never restate it. `build-check.yml` stays the authority
  and this change does not edit it — the parity linter's input must be a file
  the change does not control, or the check is circular.
- Keep every new gate zero-argument and dependency-free beyond
  `tools/requirements.txt`, so it composes into `build_gate_chain.py`'s
  `[sys.executable, <script>]` step contract. "Stdlib plus
  `tools/requirements.txt`" is the real repo rail — `tools/build-site.py` and
  `tools/validate_guides.py` already import `yaml`. No new dependency.
- Compare *gate targets* (script and pytest paths), not arbitrary shell. A
  linter that tries to interpret GitHub Actions expressions will be wrong.

### Ask first

- Removing the now-duplicated curation-guard / experience-agnostic steps from
  `build-check.yml`. Deduplicating CI is a CI-structure change; the redundant
  seconds are cheap and the workflow is the parity linter's input.

### Never do

- Make `SKIP_SAST=1` exit non-zero. It is a legitimate fast path and CI itself
  sets it for diffs with nothing to scan. The fix is legibility, not refusal.
- Generate the `Makefile` from `build-check.yml`. Several steps
  (`apt-get install`, `sudo`, pinned `pip install`, `github.event`
  conditionals) have no local expression; a generator would need a skip-list,
  and the skip-list is where the drift would move.
- Silence a parity failure by widening an exemption class. An exemption names
  one target and states why.
- Reimplement a CI check locally in a second language or a second script. Two
  implementations of one gate is the drift this spec exists to end.

## Assumptions

- `pyyaml` is available to the parity linter. It is already in
  `tools/requirements.txt`, which `build-check.yml` installs before `make
  build-check` and which `AGENTS.md` names as one-time local setup.
- Being reachable from the local chain is sufficient parity for a gate target.
  Verifying that a locally-run gate *passes for the same reason* CI's does is
  out of scope; the defect is absence, not disagreement.
- The curation guard's `{base}...HEAD` diff semantics are correct to preserve
  locally. It gates committed changesets, not the working tree, exactly as in
  CI. Uncommitted work being ungated is the existing contract, not a regression
  introduced here.
- **Bound on AC2, stated plainly, in both directions.** The guard's path-gate
  returns "skipped, not failed" and exits 0 when git or the `--base` ref is
  unavailable, so AC2 holds for a fetched branch ahead of `main` — the shape of
  every real PR — and the guard is a no-op on a branch with no commits. A **stale**
  base is worse than an absent one: it does not merely widen the changeset, it can
  *silence* the gate. `git diff {base}...HEAD` widens to the older merge-base, and
  because the exemption is changeset-scoped (`has_exemption` reads the whole
  `git log {base}..HEAD` message blob), an already-merged commit carrying
  `Engine-Change-RFC:` inside that range exempts the current untrailered
  changeset. CI is unaffected (`fetch-depth: 0` plus an explicit
  `--base origin/main`), so both directions are local-only. That silent skip is
  the same class of defect AC3 fixes for `SKIP_SAST`; closing it changes a gate CI
  shares, so it is recorded as `curation-guard-silent-base-skip` rather than
  folded in here.

## Testing strategy

- **AC1, AC6** — goal-based: `python tools/repo/build_gate_chain.py
  build-check` names both new steps and exits 0; `tools/test_build_gate_chain.py`
  pins the chain's exact ordered step list, so the additions are asserted, not
  incidental.
- **AC3a, AC3b** — TDD: `tools/test-lint-ci-parity.py` executes the
  `gate_verdict` macro body under `sh` for all three environment combinations and
  asserts which message appears, and asserts both recipes still call the macro.
  Grepping for `GITHUB_WORKFLOW` would survive inverting the test, which is
  precisely the false-assurance AC3a removes.
- **AC4d, AC4e** — TDD: the same suite's `dropped-prereq-loses-coverage`,
  `prose-not-coverage[makefile-*]`, `sub-make-target`, and
  `check-duplicate-step-name-fails` cases.
- **AC2, AC3** — manual QA by construction on a scratch commit: create a commit
  touching `packages/agentbundle/` outside `tests/` with no trailer, run the
  local chain, record the observed failure; add the trailer, record the pass.
  Record both final banner lines for the SAST-skipped and SAST-run cases.
- **AC4, AC5, AC7** — TDD: the extraction / coverage / exemption logic is pure,
  so `tools/test-lint-ci-parity.py` drives it with synthetic workflow dicts
  plus a live assertion that the real repo is parity-clean.
- **AC9–AC11, AC13** — TDD in `tools/test-all.py`'s own preflight: a synthetic
  `TESTS` list with a missing target must yield exit 2 and name the entry.
- **AC14** — goal-based: `python3 tools/test-all.py` exits 0.
