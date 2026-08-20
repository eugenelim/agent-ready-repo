# Plan: ci-gate-parallelization

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done (2026-08-17)

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (`docs/CONVENTIONS.md` § Document lifecycle).

## Approach

Extract the two floor-setting steps — the SAST/SCA leg and the export-boundary
gate — into their own jobs, leaving everything else in `gate-main` with today's
install set. Three work jobs plus an aggregator. **No figures appear in this
document:** job estimates live in spec AC1's table, targets in AC11.

**The method is empirical for the coupling graph and specified for the fail-open
guards** — spec § *How this spec is scoped* records the division and, importantly,
*why it is safe*: every work job's severable coupling lands on an existing
fail-closed guard, so CI reports the loud class correctly in minutes. The partition
breaks in exactly two places, both named ACs: the aggregator (AC13) and the two
gates whose fail-open is silent rather than loud (AC14).

Order: T2 (banner, so the delegated state is understood before the workflow
produces it) → T3 (the split, iterated against CI) → T4 (aggregator + posture
test) → T5 (dispositions, which need final names). T1 and T6 are independent.

The riskiest part is the aggregator (T4): it wears the required-check name, its
guard must run *inside* it, and that guard must be pure-stdlib so there is no
import for anyone to guard away under pressure.

**Files:** `.github/workflows/build-check.yml`,
`.github/workflows/catalogue-tooling-ci-gates.yml`, `Makefile`,
`tools/lint-ci-parity.py`, `tools/test-lint-ci-parity.py`,
`tools/test-build-check-workflow.py` and `tools/fixtures/build-check-good.yml`
*(both written — see T4)*, a new
chain-assertion script, `tools/repo/build_gate_chain.py`,
**`tools/test_build_gate_chain.py`** (two holds: `EXPECTED_SCRIPT_STEPS` exact
equality + pinned count, *and* a textual assertion that the agentbundle+pytest
install precedes `Run make build-check` in the workflow file),
`docs/adr/0085-*.md`, `docs/adr/0017-*.md`, `docs/specs/local-gate-ci-parity/`
(Status lines only), `workspace.toml`.

## Constraints

### Governance

- **ADR-0017** — CI-chaining sub-decision partially superseded (T6); rest binding.
- **ADR-0083** — npm SCA; inside `make sast`, travels with `gate-sast`.
- **ADR-0084** — precedent for the annotation shape: `Supersedes:` names only an
  ADR; the spec end is a Status annotation.
- **RFC-0082** — export-boundary's internal budget; why `timeout-minutes` travels
  with `gate-export-boundary`.
- **`docs/specs/local-gate-ci-parity/`** — gains Status annotations on both
  `spec.md` and `plan.md` (AC9), and pins `build_gate_chain.py` as the **make-free**
  Windows entry point, which is why T2's chain assertion skips when `make` is
  absent.
- **`CONVENTIONS.md`** § *Superseding a frozen document*, § *A spec directory
  freezes as a unit*, and § *Stub → EXECUTE handoff* (TDD tasks carry compilable red
  stubs with `# STUB: AC<n>` markers and `stub: true`).
- **`AGENTS.md`** — stdlib-Python tool scripts; no new top-level directory without
  an RFC; prefer the established helper.

### Discovered invariants

- **The workflow's steps are the outer layer.** `make build-check` runs
  `build_gate_chain.py` → ~40 further gates, **at least three failing open on
  missing history**: `lint-catalogue-curation-guard.py`, `lint-build.py`'s top-level
  audit (which enforces this spec's own `Never do`), and `lint-spec-status.py`'s
  base-ref resolution.
- **`lint-nosec-form` degrades to exit 0 without bandit** — it sets a caveat string
  and drops its unknown-ID check. It runs in `gate-main`'s chain while the SAST
  install moves away, so `gate-main` needs an unconditional bandit install (AC14).
  Already tracked as `build-check-installs-bandit-unconditionally`, scoped to
  `SKIP_SAST` PRs; this change would widen it, and fixing it closes the entry.
- **The export-boundary suite skips on tree shape** — all three real-artifact tests
  are `skipif(not (REPO_ROOT / "packages" / "agentbundle").is_dir())`, so a narrowed
  checkout makes the gate exit 0 verifying nothing. Module probes cannot see it.
- **The export-boundary gate declares its own deps** —
  `_DEPENDENCY_IMPORTS = ("pytest", "yaml", "jsonschema", "credbroker")` in
  `tools/check-artifact-contents.py`, checked via `find_spec` from `check_sdist()`
  and **raising** on a miss, so the module direction is already fail-closed.
- **Two `steps.changes` readers**, not one: `Run make build-check`'s `${{ }}` read
  and the `if:` on `Install SAST/SCA tools`. A cross-job `steps.*` reference does not
  error — it evaluates empty, so `'' != 'true'` is **true**.
- **`make sast` needs its scanners installed** or it exits 1 at `command -v bandit`.
- **`$(origin VAR)`** returns `command line` vs `environment` — verified by
  execution — and is the only provenance discriminator not forgeable from the
  environment. Textual substitution cannot express it, so T2's harness must invoke
  real `make`.
- **Make executes rather than prints `$(MAKE)` lines under `-n`**, and exports
  command-line overrides to children via `MAKEFLAGS`/`MAKEOVERRIDES`.
- **The wired posture-test precedent is pure stdlib**
  (`tools/test-build-check-windows-workflow.py`); the one PyYAML-importing posture
  test is invoked nowhere.
- **Reuse, don't rebuild:** the aggregator shape in `build-check-windows.yml`;
  `lint-ci-parity.py`'s already-present, already-self-tested cross-job duplicate
  step-name check.

## Construction tests

**Red stubs (materialised at PLAN):**
- `tools/test-build-check-workflow.py` — **written**, `# STUB: AC13`, pure stdlib.
  Controls are matched as shell **command words**, not substrings: comments are
  stripped to the first unquoted `#`, guard statements are checked for their
  *consequent*, and `set +e` / un-`pipefail`'d pipelines are rejected. Proven three
  ways, with **no count restated here** — `--self-test` prints the canonical figures:
  a clean baseline with every mutation caught; a coverage check, computed from the
  populated baseline rather than an empty input, that rejects any assertion *family*
  without a mutation; and a replay of every documented bypass of its two earlier
  drafts, all now blocked.
- T2's verdict cases — stub markers `# STUB: AC5b` / `# STUB: AC5c`, added to
  `tools/test-lint-ci-parity.py`'s polarity table.

**Integration tests:** the authoritative signal is a real Actions run — per AC15 the
run *is* the discovery instrument for the coupling graph.

**Manual verification:** AC2's pre-merge branch-protection query (PR description);
AC11's post-merge measurement and AC15's non-relevant-diff run (backlog entry).

## Design (LLD)

### Design decisions

- **Extract only the two floor-setting steps.** Further splitting chases
  single-digit seconds while adding extraction boundaries, and every boundary is a
  place a coupling gets severed silently. Traces to: AC1.
- **Empirical completion of the provisioning set.** Derivation failed four times
  against an undocumented dependency graph; CI reports it correctly. The fail-open
  class stays specified because CI cannot surface it. Traces to: AC15.
- **The aggregator is the CI analogue of `make ci`.** Traces to: AC2, AC3.
- **The posture test is pure stdlib and runs in the aggregator.** Stdlib because a
  test that can fail on a missing import is a test someone will import-guard, and an
  import-guarded posture test is vacuous; in the aggregator because a guard on the
  far side of the edge it protects dies with that edge. Traces to: AC13.
- **Derived set-equality *and* a literal floor.** Derivation catches added-and-
  unwired; the floor catches deleted-entirely. Traces to: AC13.
- **Explicit env-var transform** (`upper()`, `-`→`_`), because the literal
  `$GATE-MAIN_RESULT` is POSIX default-value syntax and would leave the aggregator
  permanently red. Traces to: AC3.
- **`$(origin SAST_DELEGATED)` as the provenance test**, gating both the quiet
  banner and the `$(MAKE) sast` short-circuit. Every environment variable is
  forgeable by the threat model it defends against. Traces to: AC5b, AC5c.
- **Scanners installed unconditionally in `gate-sast`**, so the predicate has one
  consumer. Traces to: AC4.
- **Bandit installed unconditionally in `gate-main`**, because `lint-nosec-form`
  fails open without it. Traces to: AC14.
- **No composite action.** New top-level directory; `lint-build.py`'s audit and
  `lint-ci-parity.py` both react to it. Traces to: Boundaries § Never do.
- **Require the three work jobs in branch protection (AC2), and accept one-to-many
  local parity (AC16).** These are the two decisions that came from the human rather
  than from review, and they are paired: requiring the jobs directly is what demotes
  the aggregator from sole-guard to summary, which is why eight rounds of
  aggregator-wiring bypasses stop being the load-bearing risk. The verifier's
  remaining scope is the *inside* of jobs, which is what it can plausibly assert.
  Traces to: AC2, AC3, AC13, AC16.

### Failure, edge cases & resilience

- Any work job failed or cancelled → aggregator fails.
- No job may be `skipped` — AC4 removes the only conditional job, and AC13 asserts
  no work job carries a `needs:` key, which would reintroduce one.
- Dependency dropped from `needs:` → three-way binding fails. Job added and never
  wired → derived set-equality fails. Job deleted entirely → the literal floor fails.
- The aggregator's guard runs inside it, so unwiring an edge fails the required
  check on its own evidence.
- **Partial re-run** — the `needs` payload's reported results for non-re-run
  dependencies are unverified. T4 establishes the shape and records it; "full re-run
  only" is an acceptable answer, silence is not.

## Tasks

### T1: Gate A's two suites run as two jobs, and the ubuntu pack suite runs once

**Depends on:** none · **Touches:** .github/workflows/catalogue-tooling-ci-gates.yml

**Verification mode:** goal-based check. **Tests:** no stub (goal-based).

**Approach:**
- `Gate A-tests`: `Run full agentbundle test suite (Linux)` (full matrix) +
  `Run agentbundle test suite (Windows — curated portable subset)`.
- `Gate A-packs`: `Run repo/pack hook suites (Linux)` + `Run pack hook suites
  (Windows — curated portable subset)`, keeping a `windows-latest / py3.11` matrix
  entry beside its ubuntu/py3.12 one. Named `-tests`/`-packs` rather than A1/A2
  because "A1" collides with assumption A1 (AC7).
- Scope `Gate A-packs`' **ubuntu** leg to py3.12 only, reason at the matrix
  declaration.
- **Update the header legend** — it declares "Nine gates" and `A: agentbundle-tests`
  with A–I allocated.
- **Apportion installs by verified consumer.** The `jsonschema` step's annotation
  points at work-intake oracles, but its real consumers are agentbundle schema
  suites that `pytest.skip` when it is absent — a `Gate A-tests` concern.
- **No `permissions` / `persist-credentials` change here** — deferred to
  `catalogue-tooling-workflow-hardening`. Seven gates, two of which move artifacts,
  none reviewed by this spec; not the mechanical ride-along the carve-out admits.

**Done when:** a run shows both jobs, both Windows curated steps execute, the ubuntu
pack suite appears once, the legend matches, Gate A's ubuntu path meets AC11's
target, and **the skip check passes** — `pytest -rs` plus a grep for
`not installed|no module named|importorskip` (plain `-q` prints no skip reasons, so
`-rs` is required or the check observes nothing).

### T2: no banner or echo claims more than the run performed

**Depends on:** none · **Touches:** Makefile, tools/test-lint-ci-parity.py,
tools/repo/build_gate_chain.py, tools/test_build_gate_chain.py, new chain-assertion
script

**Verification mode:** TDD. **`stub: true`** — markers `# STUB: AC5b`,
`# STUB: AC5c`.

**Tests:**
- **Harness first.** `_run_verdict` substitutes `$(SKIP_SAST)` textually before
  handing the recipe to `sh`, and textual substitution **cannot express `$(origin)`**
  — so the AC5b/AC5c cases must invoke **real `make`**. Without that the branch is
  never taken and a passing test exercises the wrong one.
- `delegated-command-line` (`make … SAST_DELEGATED=1`) → AC5a's wording, quiet.
  Forbidden: `INCOMPLETE`, `complete for this diff`, any claim a scan ran.
- `delegated-ambient` (`SAST_DELEGATED=1 make …`, i.e. `environment` origin) →
  `make sast` **is** invoked (AC5c), so the verdict is the unchanged
  `complete — every leg … SAST/SCA included`. Assert the **absence** of AC5a's quiet
  wording; do **not** assert `INCOMPLETE`, which would be false about a run whose
  SAST leg ran and whose `SKIP_SAST` is unset.
- `delegated-argument-quiet` (`make … SAST_DELEGATED=1`, i.e. `command line`
  origin) → AC5a's quiet wording, `make sast` **not** invoked. This is AC5b's
  accepted residual, and the only form that reaches the quiet state.
- `local-skip` and `full-run` unchanged; the `ci-skip` case deleted (AC5f).
- Extend the ambient-env scrub to include `SAST_DELEGATED`.
- **AC10 chain assertion**, a standalone script: scrub `MAKEFLAGS`, `MAKEOVERRIDES`,
  `SAST_DELEGATED`, `SKIP_SAST` from the child env; **skip cleanly when `make` is
  absent** (the make-free Windows path is a shipped AC); key on a marker unique to
  the `sast` recipe's expansion, since Make executes rather than prints `$(MAKE)`
  lines under `-n`. Assert reachability, not text presence.
- **Mutations:** "runs in a sibling job" wording fails `delegated-command-line`;
  making the ambient case quiet fails `delegated-ambient`; neutering the `sast`
  branch fails the chain assertion **with the parent environment present**.

**Approach:** add AC5a's state gated on `$(origin SAST_DELEGATED)` = `command line`;
widen the `$(MAKE) sast` condition with the same gate (AC5c); fix the mid-run echo
(AC5d); rewrite the stale prose at AC5e's enumerated sites; retire the `ci-skip`
branch (AC5f). Wire the chain assertion into `build_gate_chain.py` and update
`EXPECTED_SCRIPT_STEPS` **and** the pinned count in `test_build_gate_chain.py` in the
same commit.

**Done when:** both test files pass, the chain assertion runs in the chain and skips
without `make`, and each mutation fails only its named case.

### T3: build-check.yml runs three work jobs — iterated against CI

**Depends on:** T2 · **Touches:** .github/workflows/build-check.yml, workspace.toml,
tools/repo/build_gate_chain.py

**Verification mode:** goal-based check, **driven by real CI runs** (AC15).

**Tests:** no stub. The run is the instrument; the guards are AC12/13/14.

**Approach:**
- `gate-main` keeps its steps, checkout and install set unchanged, minus the two
  extracted groups, **plus an unconditional bandit install** (AC14) — and correct
  `build_gate_chain.py`'s comment claiming that leg needs no scanner.
- **Close the backlog entry this satisfies.** AC14 states the unconditional bandit
  install closes `build-check-installs-bandit-unconditionally` in
  `workspace.toml [backlog].open`; remove it here. Without this the PR ships an AC
  the register contradicts, and T7 — the only other task naming `workspace.toml` — is
  post-merge and out of the PR.
- `gate-sast`: the detect step + `make sast` + `tools/requirements-sast.txt`
  **unconditionally** (AC4, so the predicate has one consumer — the `make sast`
  step, whose `if:` travels with it). Convert the detect step's
  `${{ github.event.pull_request.base.sha }}` / `.head.sha` to `env: BASE_SHA` /
  `HEAD_SHA`. Preserve the predicate's fail-closed guards verbatim.
- `gate-export-boundary`: the export-boundary step, `tools/requirements.txt`,
  `pytest`, `'packages/credbroker[crypto]'` (matching today's environment), the
  tree-shape assertion `test -d packages/agentbundle`, and `pytest -rs` with a skip
  check (AC14). **No `sparse-checkout`.**
- `gate-main` runs `make build-check PACKS_DIR=packs SAST_DELEGATED=1`.
- **Per AC12:** `fetch-depth: 0` on the three work jobs (the aggregator is exempt —
  see AC12), `persist-credentials: false` everywhere, `python-version: "3.11"` on all
  four, explicit `timeout-minutes` per job with RFC-0082's comment onto
  `gate-export-boundary`, top-level `permissions: contents: read`, and AC12's literal
  `concurrency` expression.
- **AC16's addressability comment block.** Add, beside the job definitions, the
  per-job local reproduction table from AC16 — including the label that
  `make build-check SAST_DELEGATED=1` is CI-equivalence only and **not** the pre-push
  command, and that `make ci` is the only job-level claim. A contributor debugging one
  job should not have to derive the command, and should not be nudged toward the
  invocation that skips SAST.
- **Enumerate the suffixed step names literally as they are created**, so T5's delta
  is checkable. Starting set: the two extracted jobs' `Set up Python`, their
  provisioning installs, and the AC14 probe — extended by what CI reports.
- **Check `test_build_gate_chain.py`'s second hold:** it textually pins that the
  agentbundle+pytest install precedes `Run make build-check`. Preserve that order or
  rewrite the assertion to be job-scoped.
- **Iterate:** push, read failures, add the missing provisioning to the job *and to
  AC1's table*, repeat.

**Done when** (AC15's bar): every job green on the SAST-relevant class;
export-boundary tests **executed not skipped**, proven by the `-rs` check rather than
a log read; `actionlint` and `zizmor --min-severity high` green; no gate script's
dependency declarations edited and no posture assertion weakened; AC1's provisioning
column updated to what CI actually required; and
`build-check-installs-bandit-unconditionally` removed from `[backlog].open`.

### T4: the aggregator, guarded from inside itself

**Depends on:** T3 · **Touches:** .github/workflows/build-check.yml,
tools/test-build-check-workflow.py, tools/repo/build_gate_chain.py,
tools/test_build_gate_chain.py

**Verification mode:** TDD. **`stub: true`** — `tools/test-build-check-workflow.py`
carries `# STUB: AC13`, is pure stdlib, compiles, and is red against the current
workflow.

**Tests:** the stub asserts everything in AC13 — derived set-equality **plus** the
literal floor, each work job's three-way binding via AC3's explicit transform,
exactly one job named `make build-check`, `if: ${{ always() }}`, no work job with a
`needs:` key, AC12's per-job settings and literal `concurrency`, the `make sast`
step's `if:` polarity, `gate-main`'s anchor step and bandit install, and
`gate-export-boundary`'s tree probe, skip check and absence of `sparse-checkout`.
- **Mutations run by `--self-test`, each required to produce a specific violation
  id.** Written and passing; `--self-test`'s output is the only place the count
  appears. They cover: unwiring a dependency; deleting a
  work job and its binding; rebinding one env var to another job's result; dropping a
  comparison; dropping `if: always()`; `permissions: write`; a job-level
  `permissions:`; adding `needs:` to a work job; dropping `fetch-depth: 0`; a
  `github.head_ref` concurrency key; `continue-on-error`; commenting out the anchor
  step; passing `SAST_DELEGATED` as a prefix instead of an argument; dropping it
  entirely; commenting out the bandit install; putting the `if:` back on the scanner
  install; dropping the `make sast` `if:`; neutering the tree probe with `|| true`;
  dropping the skip grep; neutering the pytest line; sparse-checking-out
  `gate-export-boundary`; and **removing the guard from the aggregator**.
- The self-test also asserts **no assertion lacks a mutation case**, because
  aggregate redness is not validation — a stub can be red overall while individual
  assertions pass for the wrong reason, which is how the first draft shipped four
  vacuous checks.

**Approach:**
- Aggregator: id `build-check`, `name: make build-check`, `if: ${{ always() }}`, one
  `env:` var per dependency named by AC3's transform, one literal
  `[ "$<VAR>" != "success" ]` each, a diagnostic naming the failure.
- **It runs the posture test itself** — a checkout plus `python-version` per AC12,
  and no `fetch-depth: 0` (AC12 exempts it: one stdlib script, one file, no history).
  The `build_gate_chain.py` invocation is retained as the local-parity path, which is
  why T5 dispositions the step `LOCAL`.
- Update `EXPECTED_SCRIPT_STEPS` and the pinned count for the new chain step.
- **Establish the partial-re-run `needs` payload shape**; record it in AC3.
- **Re-query the branch-protection API pre-merge** and record the result as a line in
  the PR description (AC2).
- **Do NOT add the three job names to the required set in this PR** (AC2's
  sequencing): a required check that no run produces leaves every PR pending forever.
  The PR lands with the required set unchanged; adding `gate-main`, `gate-sast` and
  `gate-export-boundary` is a **post-merge admin action**, tracked in the AC11 backlog
  entry beside the measurement. Note in the PR description that every open PR must
  rebase when it happens.

**Done when:** `--self-test` exits 0, the API result is
recorded, `test_build_gate_chain.py` is green, and a run with a deliberately failed
work job shows the aggregator red.

### T5: lint-ci-parity is green, with the disposition delta enumerated

**Depends on:** T3, T4 · **Touches:** tools/lint-ci-parity.py

**Verification mode:** goal-based check. **Tests:** no stub — it is the gate. **No new
uniqueness check** is written (AC6).

**Approach:** work AC6's delta against T3's literal suffix list — **three** new
`<unnamed step in gate-*>` keys; `<unnamed step in build-check>` **retained** (the
aggregator keeps that job id) with its reason rewritten to describe the aggregator's
checkout; the suffixed provisioning steps; the new `make sast` step; the AC14 probe;
the posture-test step dispositioned **`LOCAL("build-check")`**, not `CI_ONLY`, since
AC13 retains the local chain invocation; and — per AC6 and AC16 — the
`Run make build-check` anchor **reclassified from `CI_ONLY` to
`LOCAL("build-check")`**, with the minus-SAST divergence in its reason string, because
a `CI_ONLY` entry that asserts local coverage is the false roster statement AC6
rejects. The `Run make build-check` anchor's
reason is rewritten. `WORKFLOW_SCOPE` unchanged. **The chain assertion produces no
disposition** — it is wired into `build_gate_chain.py`, not the workflow, so it adds
no workflow step.

**Done when:** `python3 tools/lint-ci-parity.py` exits 0 and the `STEP_DISPOSITION`
diff matches the enumerated list with no unexplained entries.

### T6: governance records, pointing only in allowed directions

**Depends on:** none · **Touches:** docs/adr/0085-*.md, docs/adr/0017-*.md,
docs/specs/local-gate-ci-parity/{spec,plan}.md *(Status lines only)*

**Verification mode:** goal-based check. **Tests:** no stub.

**Approach:**
- Write `docs/adr/0086-split-the-sast-gate-into-its-own-ci-job.md`. `Supersedes:`
  names **only ADR-0017**.
- **Carry as an explicit decision, not a consequence:** "provenance is
  `$(origin SAST_DELEGATED)`, not any environment variable." CONVENTIONS rule 2
  requires `local-gate-ci-parity`'s pointer to land on the ADR carrying the
  reasoning, and that spec's AC3a is the decision being reversed.
- Record accepted consequences: the SAST leg is now the critical path, so additions
  translate 1:1 into PR latency; the pre-existing head-commit self-certification;
  that a green aggregator does not prove a scan executed, naming the
  pinned-ref-ruleset mechanism and its backlog entry rather than calling it inherent;
  the banner case-set change; and that `ci-security.yml` / `codeql.yml` carry the
  refuted `cancel-in-progress` belief, so their group shape is not a pattern to copy.
- Update ADR-0017's `Status` line only, and decide and record whether its existing
  non-conforming ADR-0084 clause is normalized in the same edit. Carry a `Related:`
  field per precedent.
- **Status annotations on both** `docs/specs/local-gate-ci-parity/spec.md`
  (`Status: Shipped …`) and `plan.md` (`Status: Done …`), naming **AC3, AC3a and
  AC3b's verdict case-set**.
- **Record as a decision, not a gap:** `docs/specs/windows-ci-bundler/` and
  `docs/specs/build-check-windows/` phrase their boundary as "the Linux
  `build-check.yml` job (the required status check)"; AC2 preserves the intent, so
  neither needs annotation.
- Stamp `docs/specs/sast-sca-tooling/` only if it *teaches* the CI-chaining rule.

**Done when:** ADR-0086 exists with pointers in allowed directions only and the
`$(origin)` provenance decision in its decision section; ADR-0017's body is
byte-identical apart from its Status line; both `local-gate-ci-parity` files carry
their annotation; and every decision above is written down with reasoning.

### T7: the metrics are measured — **out of this PR**

**Depends on:** T1-T6 · **Touches:** workspace.toml *(post-merge only)*

**Verification mode:** visual / manual QA. Not part of the shipping diff and does not
gate the PR — owned by the backlog entry, so `plan.md` can reach `Done` and freeze
with the spec.

**Approach:** after merge, read a real run of both in-scope workflows; record per-job
durations against AC11's ceilings; report the repo-wide figure for information. Also
capture the **non-relevant-diff run** AC15 defers here, since only a post-merge
`docs/**`-only PR can produce it. A miss inside AC11's noise band is re-measured before any
conclusion; a larger miss is diagnosed.

**Done when:** the backlog entry carries the measurement, the non-relevant-class run
URL, and any diagnosis.

## Rollout

- **Delivery:** single PR by explicit decision. Reversible — `git revert` restores the
  prior job. Nothing migrated, published, or destroyed.
- **Infrastructure:** none provisioned; net runner-seconds down.
- **External-system integration:** branch protection; AC2 means no change, verified
  pre-merge.
- **Deployment sequencing:** T2 → T3 → T4 → T5; T4 complete before merge. T7 is
  post-merge and out of the PR.
- **Irreversible:** nothing.

## Risks

- **Aggregator correctness (T4)** — wears the required-check name. Mitigated by the
  three-way binding with an explicit transform, derivation *plus* a literal floor, a
  pure-stdlib guard running inside the aggregator, and its mutation matrix.
- **A silent fail-open loses its prerequisite** — bandit for `lint-nosec-form`, tree
  shape for the export-boundary suite, history for the three transitive gates. The
  class AC15 does *not* delegate to CI.
- **The tempting wrong fixes**, named because they will look reasonable under
  pressure: dropping an entry from `_DEPENDENCY_IMPORTS`; import-guarding or
  `sys.exit(0)`-ing the posture test; narrowing `SAST_CONFIG` to reach AC15's
  unreachable diff class. All three are Boundaries violations.
- **`test_build_gate_chain.py`'s two holds** both trip on this change.
- **The SAST floor keeps rising.**

## Changelog

- 2026-08-17 — initial draft.
- 2026-08-17 — **revision 2** after round 1 (8 blockers): step-level predicate inside
  an always-running `gate-sast`; AC11 deferred; missing template sections added.
- 2026-08-17 — **revision 3** after round 2 (7 blockers) plus a step inventory:
  aggregator reuses `build-check-windows.yml`'s pattern; `concurrency`,
  `permissions`, `persist-credentials` added; objective restated around
  `strict: true` with no merge queue.
- 2026-08-17 — **revision 4** after round 3 (9 blockers) plus a gate-chain traversal:
  residual job no longer split; blanket `fetch-depth: 0`.
- 2026-08-17 — **revision 5** after round 4 (11 blockers). Method change: the
  coupling graph is completed empirically (AC15) while the fail-open class stays
  specified. `$(origin SAST_DELEGATED)` named as the provenance test; the posture
  test moved into the aggregator; supersession pointer corrected.
- 2026-08-17 — **revision 6** after round 5 (8 blockers — the first fall in the
  trend, and the first round whose findings were mostly self-contradictions rather
  than misunderstood system behaviour). A **consolidation rewrite**, because four
  contradictions were artifacts of layered editing: a count that disagreed with its
  own labels, two ACs disagreeing on the aggregator's Python, a disposition key
  claimed retired that is retained, and a rationale naming the wrong job. Substantive
  fixes: `gate-main` gains an unconditional bandit install, because
  `lint-nosec-form` exits 0 without it and the SAST install was moving away —
  widening a fail-open the repo already tracks; the posture test is **pure stdlib**
  (the wired precedent is, the unwired one is not) so it has no import to guard away,
  and its red stub is now written, compiling and failing with 12 violations; derived
  set-equality gains a **literal floor**, since derivation alone lets a whole job be
  deleted green; AC3's env-var transform is pinned because `$GATE-MAIN_RESULT` is
  POSIX default-value syntax; the export-boundary suite's tree-shape skipifs get an
  assertion and an `-rs` skip check while the redundant module probe is dropped
  (`_preflight_dependencies` already raises); AC15's non-relevant-diff class moves
  post-merge because `SAST_CONFIG` makes it unreachable from this branch, with
  narrowing those lists forbidden outright; the Gate A jobs are renamed to stop "A1"
  colliding with assumption A1; and the aggregator is exempted from `fetch-depth: 0`
  with a stated reason rather than inheriting a blanket rule that does not reach it.
- 2026-08-17 — **revision 7** after round 6 (9 blockers, verdict "landable: no").
  Six were self-contradictions or vacuous assertions I had introduced, which is the
  reason this revision's centre of gravity moved from prose to a **proven artifact**.
  The posture-test stub was demonstrated to print `✓ posture OK` against a four-job
  workflow that verified nothing — every required substring supplied by a YAML
  comment — reproducing the antipattern this repo recorded a day earlier. Validating
  it by aggregate redness was the error: a stub can be red overall while individual
  assertions pass for the wrong reason. It is rewritten line-anchored and
  comment-stripped, with a mutation matrix, a coverage check that no
  assertion lacks a mutation, and an assertion that the guard runs **in the
  aggregator** so its placement is self-enforcing. Spec fixes: AC5b no longer routes
  the ambient case to `INCOMPLETE` (which AC5c made false, and AC10 authorized no
  rewording of); AC5b's accepted residual now names `make ci SAST_DELEGATED=1` rather
  than the ambient form, correcting an inversion of the rule stated two lines above
  it; AC1 says shallow checkout for the aggregator, matching AC12; `continue-on-error`
  is forbidden outright as a one-line total bypass; the argument-vs-prefix position of
  `SAST_DELEGATED` is asserted, since the whole `$(origin)` design rests on it and a
  prefix would silently run the SAST leg twice; and T3 now closes the
  `build-check-installs-bandit-unconditionally` entry AC14 claims it closes.
