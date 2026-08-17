# Spec: ci-gate-parallelization

- **Status:** Implementing
- **Owner:** eugenelim
- **Constrained by:** ADR-0017, ADR-0083, ADR-0084, RFC-0082,
  `docs/CONVENTIONS.md` § *Superseding a frozen document*,
  `docs/specs/local-gate-ci-parity/`
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none — no runtime contract changes. One required status check keeps
  its name but changes from a work job to an aggregator; one ADR sub-decision is
  partially superseded and one shipped spec gains a Status annotation.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Two risk triggers fire: structural change (a single CI job
becomes four, and the required status check changes kind) and a governance
surface (ADR-0017's chaining sub-decision).

Revision 6 is a consolidation rewrite. Revisions 2–5 layered fixes until the
document contradicted itself in four places (a count that disagreed with its own
labels, two ACs disagreeing on the aggregator's Python, a disposition key claimed
retired that is retained, a rationale naming the wrong job). Those were artifacts
of layering, so this revision restates rather than edits. -->

## Approval record

**Approved by the human gate over outstanding reviewer findings.** Eight
pre-EXECUTE review rounds ran (`adversarial-reviewer` + `security-reviewer`);
neither returned `Clean — ready to commit.` The unique-blocker count per round was
8 → 7 → 9 → 11 → 8 → 9 → 12 → 13, and round 8's verdict was "landable: no".

This is recorded, not glossed, because a future reader will otherwise assume the
loop's normal exit condition was met. It was not. What changed to make approval
reasonable was **AC2**: requiring the three work jobs in branch protection
eliminates the aggregator-wiring class that dominated rounds 6–8 by construction,
rather than by another attempt to harden a text-matching verifier. The verifier's
remaining scope — the *inside* of jobs — is pinned by
`tools/test-build-check-workflow.py`, which blocks every documented bypass of its own
earlier drafts — replayed against the shipped file, not asserted — and carries a
mutation matrix whose count and coverage `--self-test` prints. That output is the only
figure worth quoting: an earlier draft of this paragraph cited "24 bypasses", which
nothing in the matrix labelled and no command reported.

**Known-unreviewed at approval:** AC2 and AC16 were written after round 8 and have
had no review pass. The inside-job assertions were rebuilt after round 8 and have
had none either. Treat T3's CI iteration (AC15) as the first real test of both.

## Objective

`build-check.yml` runs 56 steps in a single serial job. It is slow not because the
work is slow but because independent work is sequenced.

**Why this hurts more than the duration suggests.** `make build-check` is the
**sole** required status check on `main` (branch protection and every ruleset
verified), branch protection is **`strict: true`**, and **no merge queue is
enabled**. Every merge to `main` therefore invalidates every other PR's
up-to-date status, forcing a rebase and a *full* re-run. Merge throughput is
bounded by one build-check duration. The serialization, not the raw number, is the
cost.

**Design to the floor.** Two steps are indivisible and set the floor: the SAST/SCA
leg and the export-boundary gate. Extract exactly those two and leave everything
else in one `gate-main` job. Per AC1's estimates the residual and `gate-sast` then
land within measurement noise of each other (AC11 defines the noise band) — so
neither is meaningfully "the floor", and splitting the residual
further would chase single-digit seconds while adding extraction boundaries. Every
boundary is a place a coupling gets severed. **All job estimates live in AC1's
table; all targets live in AC11. No figure appears twice in this document.**

## How this spec is scoped, and why

Four revisions failed to enumerate this job's coupling graph. Each closed its
findings and each severed a new one — a missing `pytest`, a missing scanner
install, a second `steps.changes` reader, a `credbroker` import required by the
gate script rather than the test, a bandit install whose absence silently disarms
a lint. The cause is structural: this is a 56-step sequence with **implicit,
order-dependent provisioning**, built so each step inherits everything before it,
and no manifest exists. Reconstruction by inspection kept missing edges.

So the work is divided by **failure mode**:

| Failure mode | Owner | Why |
| --- | --- | --- |
| Missing install, undefined `steps.*`, wrong order | **CI** (AC15) | Loud red on the first run; CI reports the true graph in minutes where derivation could not |
| **Fail-open** — a gate exiting 0 having verified nothing | **This spec** (AC12, AC13, AC14) | Reports green; no CI iteration surfaces it |

**The division is safe because of a property worth stating:** every work job's
severable coupling lands on an existing fail-closed guard — `make sast`'s four
`command -v … || exit 1`; `_preflight_dependencies` raising on any missing
`_DEPENDENCY_IMPORTS` member; `_check_skip_integrity` refusing every unexpected
skip in the inner sdist run; the in-step `python -c "import …"` probes already in
this workflow; `run_with_floor`'s collection-count floors; named-file pytest
invocations exiting 5 on nothing collected; and `'' != 'true'` evaluating
fail-*safe* for the `make sast` predicate on a missing or skipped detect step.
`lint-ci-parity.py` iterates `jobs:` generically, so a four-job split does not
narrow it.

**The partition breaks in exactly two places, and both are named ACs:** the
aggregator, which has no such guard and wears the required-check name (AC13); and
two gates whose fail-open is *silent* rather than loud — `lint-nosec-form`'s
bandit dependency and the export-boundary suite's tree-shape skipifs (AC14).

AC1's provisioning column is **known-required, not exhaustive**. AC15 makes
completion an empirical result with the fail-open guards as the bar. That is a
deliberate methodology choice, recorded so a reader does not mistake it for an
unfinished enumeration.

## Measured baseline

GitHub Actions, 2026-08-16/17, single samples unless noted. Queue time 0s across
the last eight runs, so this is execution time, not runner contention.

| Workflow / job | Observed | In scope |
| --- | --- | --- |
| `build-check` (SAST-relevant diff) | **430–450s** | **yes** |
| `catalogue-tooling` Gate A ubuntu py3.12 | **253–264s** | **yes** |
| `catalogue-tooling` Gate A ubuntu py3.11 | 232s | **yes** |
| `catalogue-tooling` Gate A windows | 67s warm; **183s** recorded in `docs/specs/test-sandbox-seed-cost/` | **yes** |
| `catalogue-tooling` Gates B–G | 7–20s each | no |
| `docs` | 168–198s | no |
| `codeql` | 77–103s | no |
| `build-check-windows` | 59s warm; **190s** recorded in `docs/specs/test-sandbox-seed-cost/` | no |
| `ci-security` | 11s | no |

**Variance warning.** The Windows figures differ ~3× between this spec's
warm-runner samples and a shipped in-repo record. Cold starts,
`timeout-minutes: 15` on `build-check-windows`, and single sampling all say the
same thing: these numbers bound nothing tightly. AC11 scopes its ceilings to jobs
this change touches for that reason.

Step-level inside the `build-check` job:

| Step | Duration |
| --- | --- |
| `Run make build-check` | 175–182s (≈30s chain + ≈150s SAST/SCA leg) |
| `pytest export-boundary gate` | 123s |
| `pytest catalogue-test carve-out destinations (RFC-0082)` | 33s |
| `pytest credbroker (RFC-0023 Phase 1)` | 27s |
| `Install SAST/SCA tools` | 11s |
| ~35 remaining pytest/lint steps + installs | ≈85s combined |

The SAST leg was re-measured after rebasing (#977 and #980 both added to it in one
day). It is the floor that keeps rising.

## Assumptions

- **A1.** Per-job provisioning costs ≈25s. Derived from the current job's step
  timings, not measured per-job. AC11's measurement tests it.
- **A2.** Durations are single samples — see § Variance warning.
- **A3.** GitHub schedules the four jobs concurrently. Supported by 0s observed
  queue time; AC12's `concurrency` block protects it.
- **A4.** *(Retired.)* Earlier revisions assumed the extracted groups' dependencies
  could be established by reading their suites. That produced four rounds of
  severed couplings and is replaced by AC15's empirical method.

## Non-goals

- Making any individual gate faster; the export-boundary gate's own cost is
  deferred.
- Splitting the residual `gate-main` job further — see § Objective.
- Changing what is verified, or any gate's trigger conditions.
- Changing *what* any gate verifies. (Branch-protection *configuration* **is** in
  scope now — AC2 adds the three work jobs to the required set as a post-merge
  step. Earlier revisions listed this as a non-goal, which is what forced the
  aggregator to be the sole guard and produced eight rounds of bypass findings.)
- Touching `docs.yml`, `codeql.yml`, `ci-security.yml`, `build-check-windows.yml`,
  or Gates B–G of `catalogue-tooling-ci-gates.yml`.

## Boundaries

**Always do**

- Preserve every existing step's behaviour and trigger conditions. A step-level
  `if:` reading `steps.*` travels **with its step** into whichever job hosts it.
- Give every step in an in-scope workflow a name unique across the whole workflow.
- Keep the SAST relevance predicate reading `make -s print-sast-dirs` /
  `print-sast-config`.

**Ask first**

- Any change to what a gate verifies, rather than where it runs.
- Any `Makefile` change beyond AC10's carve-out.
- **Any edit to a gate script's own dependency declarations** — in particular
  `_DEPENDENCY_IMPORTS` in `tools/check-artifact-contents.py`. Dropping an entry to
  make a job pass turns `_check_skip_integrity` vacuous.
- **Any weakening of the aggregator's guard or the posture test's assertions**,
  including making either tolerant of its own missing prerequisites
  (`try/except ImportError`, `sys.exit(0)` on unreadable input, a relaxed
  comparison). These sit on the required check itself, so weakening them is
  strictly more damaging than the `_DEPENDENCY_IMPORTS` case above.

**Never do**

- **No new top-level directory**, specifically **no `.github/actions/`** — needs an
  RFC; `lint-build.py`'s top-level audit enforces it mechanically.
- **No branch-protection edit.**
- **No new dependency**, runtime or CI.
- **No `${{ }}` interpolation inside any `run:` body** this change writes or moves.
- **No `pull_request_target` trigger.**
- **No `continue-on-error`, anywhere in `build-check.yml`.** It is a one-line total
  bypass that looks like ordinary flake management: on `gate-main`'s anchor step it
  reports the job green with the whole ~40-gate chain failed; on the aggregator's
  guard step it greens the required check regardless of every `needs.*.result`. The
  key appears nowhere in this workflow today, and `zizmor --min-severity high` does
  not flag it. AC13 asserts its absence and T4 mutation-proves that assertion.
- **No narrowing of `SAST_CONFIG` or `SAST_DIRS` to manufacture a test case.**
  AC15's non-relevant-diff path is unreachable pre-merge (AC15 says why); narrowing
  the lists to reach it would defeat the property the workflow documents — that a
  PR loosening the gate is scanned by the gate it changes.
- **No edit to any ADR body**, including appends.

## Acceptance Criteria

- [ ] **AC1 — `build-check.yml` runs three work jobs plus an aggregator.** Job
  **ids** are named because `lint-ci-parity.py` keys unnamed steps by job id.

  | Job id | `name:` | Contents | Known-required provisioning | Est. |
  | --- | --- | --- | --- | --- |
  | `gate-main` | gate-main | everything except the two extractions | today's set **plus an unconditional bandit install** (AC14) | ~180s |
  | `gate-sast` | gate-sast | the detect step + `make sast`, **always runs** (AC4) | `tools/requirements-sast.txt`, **unconditionally** (AC4) | ~175s |
  | `gate-export-boundary` | gate-export-boundary | the export-boundary suite | `tools/requirements.txt`, **bare** `pytest`, `'packages/credbroker[crypto]'` (AC14) — an editable `agentbundle` install was tried and proved surplus: the suite builds the package via subprocess, which needs the source tree, not an install | ~150s |
  | `build-check` | **`make build-check`** | aggregator (AC3) + the AC13 posture test | shallow checkout (AC12 exempts it from `fetch-depth: 0`), `python-version` per AC12 | ~15s |

  The provisioning column is **known-required, not exhaustive** — AC15 owns
  completion and adds to this table as CI reports.

  Three entries correct earlier revisions. `gate-sast` needs the scanner install
  (extracting `make sast` without it exits 1 at the `command -v bandit` guard).
  `gate-export-boundary` needs `pytest` and an importable `credbroker`, with the
  `[crypto]` extra to match the environment the step runs in today — narrowing it
  is a derived guess of the kind that caused four rounds of severed couplings, so
  AC15 proves any narrowing rather than assuming it. And `gate-main` needs bandit
  even though SAST moved: see AC14.

- [ ] **AC2 — branch protection requires the three work jobs by name, and the
  aggregator keeps its name.** Today `make build-check` is the sole required check
  (branch-protection API and every ruleset verified). After this change the required
  set is **`gate-main`, `gate-sast`, `gate-export-boundary`, and `make build-check`**.

  **Why, and what it buys.** Eight review rounds found repeated bypasses of the
  aggregator's wiring — a job unwired from `needs:`, a job deleted entirely, an
  `echo`-spoofed comparison, a step-level `always()` relocation. Every one of those
  is a way to make the aggregator green while a gate did not run, and every one is
  **eliminated** by requiring the work jobs directly: GitHub enforces the check set,
  so an unwired or deleted job blocks the PR regardless of what the aggregator says.
  The aggregator remains for the `make ci` parity story (AC3) and as a single
  green/red summary, but it stops being the only thing between a PR and an empty
  gate.

  **What it does not buy, stated so the verifier's remaining job is clear.** Branch
  protection cannot see *inside* a job. A work job that reports success having
  verified nothing — via `continue-on-error`, or via any AC14 fail-open — is still
  green to GitHub. So AC12/AC13/AC14 remain fully load-bearing for the *inside* of
  jobs; only the aggregator-wiring assertions are demoted to belt-and-braces.

  **Sequencing — corrected, and the window is a strict weakening, not a neutral
  wait.** The original rationale ("a required check cannot precede the job that
  reports it") stopped applying the moment this branch's run reported the three
  names, which it now does: `gate-main`, `gate-sast` and `gate-export-boundary` all
  appear as check-runs. The real constraint is *other* open PRs, whose heads predate
  the split and would sit pending on checks they never produce — so this is a
  coordinated maintenance step, not a deferral.

  **Be explicit about the cost of the window.** Before the split, the sole required
  check *was* the job that ran every gate, so greening it meant disabling gates
  inside a ~40-step chain. After the split it is a job that by design runs no gate
  and only reads `needs.*.result` — and nothing outside `build-check.yml` audits
  `build-check.yml`. So during the window a PR can green the sole required check with
  an edit that touches no gate step. **The required set is therefore widened in the
  same maintenance window as the merge**, not as an open-ended follow-up, and the PR
  description states plainly that the PR itself merges under the weakened posture.

  The aggregator's `name:` stays exactly `make build-check`, and AC13 asserts
  **exactly one** job carries it, since two would leave GitHub resolving an ambiguous
  pair. The API is re-queried **pre-merge** and the result recorded in the PR
  description.
  *Status: the query returned HTTP 503 ("No server is currently available") on
  every attempt — a GitHub-side outage, not a skipped step. It is a merge
  precondition and remains outstanding. What IS confirmed from the check-runs API:
  all four job names report on this branch, which is the precondition for widening
  the required set.*

- [ ] **AC3 — the aggregator fails closed, with each dependency bound three ways.**
  It follows the shape already running in `build-check-windows.yml`
  (`runs-on: ubuntu-latest`, short `timeout-minutes`, `if: ${{ always() }}`, one
  `env:` var per dependency, one inline `[ "$X" != "success" ]` test each, a
  diagnostic naming the failure) — adopted per `AGENTS.md`'s established-helper
  rule, with two strengthenings the precedent lacks.

  **Why an aggregator.** `make ci` is the repo's local run-everything target and
  `lint-ci-parity.py`'s premise is one local target per CI step. A CI job requiring
  every leg is its honest counterpart; the preserved required-check name is a
  consequence, not the motive.

  **The env-var transform is `job_id.upper().replace("-", "_") + "_RESULT"`.**
  Stated explicitly because `<J_UPPER>_RESULT` is ambiguous for a hyphenated id:
  written literally, `[ "$GATE-MAIN_RESULT" != "success" ]` is POSIX default-value
  syntax rather than the variable intended, so it never equals `success` and the
  aggregator is permanently red.

  **Strengthening 1 — a per-id three-way binding, not three existence checks.**
  For each work job `J`: an env var named exactly by the transform above, whose
  value is exactly `${{ needs.J.result }}`, **and** a literal
  `[ "$<VAR>" != "success" ]`. Existence checks alone are insufficient: two env
  vars could be declared while the `run:` body compares one of them twice.

  **Strengthening 2 — the guard runs inside the job it guards** (AC13).

  *Value domain:* `!= "success"` fails on `failure`, `cancelled`, `skipped`, and
  any value GitHub adds later. AC4 makes every work job unconditional, so no job
  may legitimately be `skipped`; AC13 asserts no work job carries a `needs:` key,
  which would reintroduce a skip.

  **Residual, now largely bounded by AC2.** `pull_request` evaluates the workflow
  from the PR's own ref, so a coordinated PR editing the workflow, the `env:` block,
  the comparisons **and** the posture test together could make the *aggregator* go
  green. With AC2 requiring the three work jobs directly, that no longer suffices:
  the PR would also have to keep three independently-required checks green, which
  means the gates have to actually run. What remains is the narrower case of a job
  that runs and reports success having verified nothing — which is AC12/AC13/AC14's
  territory, not the aggregator's.

  **Correction — this sentence previously claimed the pinned-ref ruleset and
  `CODEOWNERS` "remain registered as a further bound." Neither exists.** There is no
  `CODEOWNERS` file anywhere in this repository (root, `.github/`, or `docs/`), and
  `main` requires no PR review — `workspace.toml` records both facts accurately, so the
  repo contradicted itself and this document was the wrong half. The drift matters more
  than the wording: **every bypass found in five review rounds — 22 of them — required
  editing `.github/workflows/build-check.yml`.** A `CODEOWNERS` entry on
  `.github/workflows/**` removes the unilateral capability instead of enumerating its
  expressions, needs no API endpoint, and is strictly stronger against this threat model
  than any text matcher can be. It is a *named gap*, not a bound: tracked as
  `ci-gate-parallelization-workflow-codeowners`, and it does not belong to this spec
  because assigning review ownership is a human decision about people, not a CI change.

- [ ] **AC4 — the SAST predicate stays step-level, and has exactly one consumer.**
  A job-level `if:` is evaluated before a runner exists and cannot execute shell,
  so it cannot read a predicate that shells out to `make -s print-sast-dirs`.
  `gate-sast` therefore **always runs** with the predicate as a step inside it. A
  detect job exposing outputs was the alternative: it adds a job, one provisioning
  cost (A1) of critical path ahead of `gate-sast`, and a skip state the aggregator
  would have to interpret.

  **There are two `steps.changes` readers today**, not one: `Run make build-check`'s
  `${{ }}` read, and the `if:` on `Install SAST/SCA tools`. A cross-job `steps.*`
  reference does **not** error — it evaluates empty, so `'' != 'true'` is **true**.
  Resolution: **install the scanners unconditionally in `gate-sast`**, so the
  predicate's only consumer is the `make sast` step, whose `if:` travels with it and
  whose polarity AC13 asserts literally. Delegation removes the other read.

  Behaviour is unchanged both ways: the scan runs on every diff touching
  `SAST_DIRS` or `SAST_CONFIG`, always on push-to-main, and on a non-relevant diff
  `gate-sast` exits `success` having correctly scanned nothing. The predicate's
  existing fail-closed guards are preserved verbatim. `build-check.yml` stays in
  `SAST_CONFIG`, so this PR's own diff runs SAST.

  **Delegation mechanism:** `gate-main` invokes `make build-check PACKS_DIR=packs
  SAST_DELEGATED=1` — never `SKIP_SAST=1`, which would re-enter the CI-intentional
  banner branch and print "complete for this diff … touches nothing scannable" on
  every PR.

- [ ] **AC5 — no banner or echo claims more than the run performed.** **Six**
  changes, each separately authorized, each with a stable label so citations
  survive insertion.

  - **AC5a — a new banner state** for "this target did not invoke the scan". Its
    wording must **not** assert the scan ran anywhere: `gate-sast` may have scanned
    nothing on a non-relevant diff, so "runs in a sibling job" is the same false
    assurance relocated. It states a fact Make can observe about itself.
  - **AC5b — the quiet state is gated on `$(origin SAST_DELEGATED)` being
    `command line`.** No environment variable is sufficient provenance:
    `GITHUB_WORKFLOW`, `CI`, `GITHUB_ACTIONS`, `GITHUB_RUN_ID` and
    `RUNNER_ENVIRONMENT` are all either synthesized by `act` or exportable from a
    devcontainer image or shell profile. `$(origin)` is not an environment value —
    it returns `command line` for `make … SAST_DELEGATED=1` (AC4's invocation) and
    `environment` for an ambient export, **verified by execution**.
  - **AC5c — the `$(MAKE) sast` short-circuit is gated on the same `$(origin)`
    test**, so an ambient export cannot skip the leg at all — strictly stronger than
    banner parity. This composes with AC10's `MAKEFLAGS`/`MAKEOVERRIDES` scrub,
    which exists because command-line origin propagates to child makes.

    **Therefore the ambient case does not take the `INCOMPLETE` branch.** An earlier
    draft said it did, which contradicted this AC: if AC5c means SAST *runs* under
    an ambient export, then the existing `INCOMPLETE` text ("the SAST/SCA leg was
    SKIPPED (SKIP_SAST is set)") would be false about that run, and AC10 authorizes
    no rewording of that branch's body. The ambient case therefore takes the
    **unchanged existing `complete — every leg of this target was invoked, SAST/SCA
    included`** path, which is true: the leg ran. The test asserts the *absence* of
    AC5a's quiet wording plus the presence of `complete`, not `INCOMPLETE`.

    **Accepted residual:** `make ci SAST_DELEGATED=1` — command-line origin, so a
    developer who deliberately passes it as an argument gets the quiet state and
    skips the leg. The *ambient* form `SAST_DELEGATED=1 make ci` does not: it yields
    `environment` origin, so the leg runs. An earlier draft named the ambient form
    here, inverting the rule stated two lines above it.
  - **AC5d — the mid-run echo** at the `SKIP_SAST` branch, which otherwise prints
    "skipping SAST/SCA gate (no SAST-relevant changes to scan)" in the delegated
    case — the same falsehood in the same run.
  - **AC5e — the stale prose, enumerated by site rather than counted:** the
    ~18-line justification block above the `SKIP_SAST` branch (which describes
    `build-check.yml` setting `SKIP_SAST=1` itself, and the `GITHUB_WORKFLOW`-keyed
    CI-intentional branch — both untrue after AC5b and AC5f); the comment asserting
    `make sast` is "chained into build-check above so the repo's single native gate
    runs it locally and in build-check.yml CI"; and the two `build-check.yml`
    comments describing cross-step install and skip coupling.
  - **AC5f — the `ci-skip` branch is retired**, having lost its only producer. This
    changes the verdict case-set that `docs/specs/local-gate-ci-parity/` pins, so it
    needs the annotation in AC9.

  Tests assert every state is distinguishable and that the delegated state never
  claims a scan happened. **Harness first:** `_run_verdict` in
  `tools/test-lint-ci-parity.py` substitutes `$(SKIP_SAST)` textually before handing
  the recipe to `sh`; textual substitution **cannot express `$(origin)`**, so the
  harness must invoke real `make` for the AC5b/AC5c cases. Without that the branch
  is untestable and a passing test would be exercising the wrong one.

- [ ] **AC6 — every disposition `lint-ci-parity.py` needs is present.**
  1. **Unnamed steps are keyed by job id** —
     `label = step.get("name") or f"<unnamed step in {job_id}>"`. The three work
     jobs' unnamed checkouts add **three** keys. `<unnamed step in build-check>` is
     **retained, not retired** — the aggregator keeps that job id — but its
     disposition reason, which today reads "the unnamed first step. Repository
     checkout", must be rewritten to describe the aggregator's checkout.
  2. **Cross-job duplicate step names are a hard violation.** Only the extracted
     jobs need their own provisioning, so the suffixed set is small; the plan lists
     it literally.
  3. **`make sast` is a new step name**, the AC13 posture test's step is new, and
     the `Run make build-check` disposition — the parity anchor — needs a rewritten
     reason — **and it must be reclassified `LOCAL("build-check")`, not left
     `CI_ONLY`.** `CI_ONLY`'s declared contract is "no local gate runs it, and why";
     AC16 requires the reason to state that `make build-check` *does* cover it, so a
     `CI_ONLY` entry asserting local coverage is exactly the false roster statement
     this AC rejects three lines below for the posture-test step. The divergence
     (minus SAST) belongs in the `LOCAL` reason string.

  The posture-test step's disposition is **`LOCAL("build-check")`**, not `CI_ONLY`:
  AC13 retains the `build_gate_chain.py` invocation, so a local target does cover
  it, and claiming otherwise is the false roster statement `local-gate-ci-parity`
  exists to prevent. **No new uniqueness check is written** — `lint-ci-parity.py`
  already reports cross-job duplicates and is already self-tested. No count of
  existing dispositions is asserted anywhere in this spec.

- [ ] **AC7 — Gate A's two suites run as two jobs.** `Run full agentbundle test
  suite (Linux)` and `Run repo/pack hook suites (Linux)` become separate jobs;
  **both Windows curated steps survive**, the agentbundle one with the agentbundle
  job and the pack-hook one with the pack job. The jobs are named **`Gate A-tests`**
  and **`Gate A-packs`** rather than A1/A2, because "A1" collides with assumption
  A1 in this document. The workflow's header legend declares "Nine gates" and
  `A: agentbundle-tests` with letters A–I allocated, so the legend is updated with
  the rename.

- [ ] **AC8 — the ubuntu pack/hook leg runs on one Python version.** Both py3.11
  and py3.12 run the whole pack/hook suite today; those suites exercise skill
  scripts, not `packages/agentbundle`, which is what the matrix exists for. The
  **ubuntu** pack leg runs py3.12 only; the Windows curated leg and the agentbundle
  matrix are unchanged. Reason recorded at the matrix declaration.

  **Gate A's installs are apportioned by verified consumer, not by annotation** —
  the `jsonschema` step is annotated "for the work-intake contract test oracles"
  but its real consumers are agentbundle schema suites that `pytest.skip` when it is
  absent, i.e. a `Gate A-tests` concern. The acceptance signal is a skip check:
  `pytest -rs` plus a grep for `not installed|no module named|importorskip`,
  mirroring `_check_skip_integrity`'s pattern — plain `-q` prints no skip reasons,
  so the check must add `-rs` or it observes nothing.

- [ ] **AC9 — governance records, pointing only in directions CONVENTIONS allows.**
  ADRs are frozen (status mutable, bodies not), so a new ADR-0086 is written — the
  precedent ADR-0084 set against ADR-0017. The four rules of § *Superseding a frozen
  document* apply by their own numbering, rule 2 being *point at the ADR, not at the
  spec that implemented it*, with the note that the spec end is one-way.

  - **One ADR-level supersession:** ADR-0017's CI-chaining sub-decision. Tool
    choices, severity floor and the real-fix-first ladder stand. ADR-0086's
    `Supersedes:` names **only** ADR-0017 — an ADR cannot supersede a spec's
    acceptance criterion.
  - **ADR-0086 must carry, as a *decision* and not merely a consequence:**
    "provenance is `$(origin SAST_DELEGATED)`, not any environment variable" — it is
    what `local-gate-ci-parity`'s annotation points at, and rule 2 requires the
    pointer to land on the ADR carrying the reasoning.
  - **Spec-side Status annotations** on `docs/specs/local-gate-ci-parity/`, naming
    **AC3, AC3a and AC3b's verdict case-set**. Both `spec.md` (`Status: Shipped`) and
    `plan.md` (`Status: Done`) are annotated, per CONVENTIONS' two prescribed forms.
  - **Two boundaries confirmed unaffected, recorded as a decision not a gap:**
    `docs/specs/windows-ci-bundler/` and `docs/specs/build-check-windows/` each
    phrase their boundary as "the Linux `build-check.yml` job (the required status
    check)". AC2 preserves that intent, so neither needs annotation.
  - **`docs/specs/sast-sca-tooling/`** is stamped only if it *teaches* the
    CI-chaining rule, per #979's precedent of declining 12 mechanical stamps.

  Also record whether ADR-0017's existing non-conforming ADR-0084 Status clause is
  normalized in the same edit — permitted, Status being the one mutable field.

- [ ] **AC10 — local gates unchanged, and ADR-0086's central claim enforced.**
  `make build-check`, `make ci`, `make sast` behave identically on a developer
  machine. **Makefile changes are confined to AC5a–AC5f** — which includes AC5c's
  widening of the `$(MAKE) sast` branch condition and AC5f's retirement of the
  `ci-skip` branch.

  After this change **no CI path executes the `$(MAKE) sast` branch**, so an
  assertion pins it or deleting it would go green everywhere. Three mechanism traps,
  each found by inspection:
  - `build_gate_chain.py` is the **make-free Windows contributor entry point** — a
    shipped AC of `local-gate-ci-parity` — so the assertion **skips cleanly when
    `make` is absent**.
  - GNU Make exports command-line overrides to child makes via
    `MAKEFLAGS`/`MAKEOVERRIDES`, so a nested `make -n build-check` inherits
    `SAST_DELEGATED=1` and takes the delegated branch. The child environment scrubs
    `MAKEFLAGS`, `MAKEOVERRIDES`, `SAST_DELEGATED`, `SKIP_SAST`.
  - Make **executes** rather than prints recipe lines containing `$(MAKE)` under
    `-n`, so grepping for the literal fails. The assertion keys on a marker unique
    to the `sast` recipe's expansion.

  It asserts **reachability**, not text presence, and is mutation-verified with the
  parent invocation's environment present.

- [ ] **AC11 — the metrics are measured** *(deferred:
  ci-gate-parallelization-critical-path-measurement)*. Measurement needs a
  post-merge run and both documents freeze at ship, so the result is recorded in the
  backlog entry. **This AC is the only place targets appear.**

  - **Merge-blocking** (the required check alone): **≤200s**.
  - **Jobs this change touches** — `build-check.yml`'s four and Gate A's two:
    **≤200s**.
  - **Repo-wide all-green:** reported for information, **not gated** — bounded by
    `docs.yml` and Windows cold-runner variance, neither in scope.

  A miss **within 20s** is treated as measurement noise given A2 and the observed
  20s spread, and re-measured on a second run before any conclusion; a larger miss
  is diagnosed and recorded.

- [ ] **AC12 — job-level settings are set deliberately, not inherited.**
  - **`fetch-depth: 0` on the three work jobs.** Not an enumeration exercise:
    `make build-check` runs `build_gate_chain.py`, which transitively invokes at
    least three gates that fail **open** on missing history —
    `lint-catalogue-curation-guard.py` (path-gate `ran=False`, exit 0; tracked as
    `curation-guard-silent-base-skip`), `lint-build.py`'s top-level-directory audit
    (warns, returns 0 — and it enforces this spec's own `Never do`), and
    `lint-spec-status.py`'s base-ref resolution. Proving which job needs history
    means traversing every transitive gate, so all three get it.
    **The aggregator is exempt, deliberately:** it runs one stdlib script that parses
    one workflow file and touches no history, so the blanket rationale does not reach
    it and a shallow checkout keeps the required check's critical path short.
  - **`python-version: "3.11"` explicit on all four jobs**, matching what the single
    job pins today, and asserted per job by AC13 so there is no exemption for a
    future job to hide behind. A drifted interpreter changes what the scanners
    resolve and what the sdist suite's ensurepip/setuptools do — silently, since both
    surface only as pass/fail.
  - **`timeout-minutes` explicit per job**, with RFC-0082's rationale and comment
    travelling to `gate-export-boundary` and a value above its 120s + 900s internal
    budget. (Not true that every other multi-job workflow does this — `docs.yml` has
    eight jobs and none.)
  - **`permissions: contents: read`** top-level, no job-level block; no step needs
    more (all 56 reviewed: no token use, no artifact upload, no PR comment, no push).
  - **`persist-credentials: false`** on every checkout.
  - **`concurrency`**, as the literal expression — a property statement is not
    pinnable, and `cancel-in-progress` gating alone is insufficient because GitHub
    permits one running plus one *pending* run per group regardless of the flag, so a
    third queued run cancels the pending one:
    ```yaml
    concurrency:
      group: build-check-${{ github.event_name == 'pull_request' && github.ref || github.run_id }}
      cancel-in-progress: ${{ github.event_name == 'pull_request' }}
    ```
    `github.head_ref` must **not** be used: it is fork-supplied, so two fork PRs on
    the same branch name would share a group and either could cancel the other's
    in-flight required check. The `github.run_id` fallback gives every non-PR event a
    unique group, so no push-to-main SAST run can be cancelled — that run is the
    belt-and-braces the head-commit self-certification residual depends on.

- [ ] **AC13 — the job graph has a posture test that derives *and* floors its set,
  and runs where it is load-bearing.** `tools/test-build-check-windows-workflow.py`
  is the precedent — genuinely wired, via `build_gate_chain.py` and
  `test_build_gate_chain.py`'s `EXPECTED_SCRIPT_STEPS` — and it is **pure stdlib**.
  (`tools/test-ci-security-workflow.py` imports PyYAML and is invoked **nowhere**
  despite a shipped AC claiming it gates `ci-security.yml`; it is an anti-precedent,
  and a backlog entry records the defect.)

  `tools/test-build-check-workflow.py` is **pure stdlib**, matching the wired
  precedent and `AGENTS.md`'s stdlib rule. This is not incidental: the test runs in
  the aggregator, and a test that can fail on a missing import is a test someone will
  import-guard under time pressure — an import-guarded posture test is a vacuous one.
  Boundaries § Ask first forbids that weakening explicitly.

  It asserts:
  - **Derived set-equality *and* a literal floor.** Derivation from the workflow's
    `jobs:` map catches a job **added** and never wired; a literal
    `{gate-main, gate-sast, gate-export-boundary}` catches a job **deleted
    entirely** — removing the `gate-main:` block with its `needs:` entry, env var and
    comparison otherwise leaves a self-consistent two-job graph and a green required
    check with ~40 chain gates gone. Both directions are required; earlier revisions
    had only one. The derivation is scoped to the `jobs:` block, since a bare
    2-space-indent key regex also matches `pull_request:`, `branches:` and `group:`.
  - Each work job's AC3 three-way binding, using AC3's explicit transform.
  - **Exactly one** job named `make build-check` (AC2); the aggregator's
    `if: ${{ always() }}`; **no work job carries a `needs:` key** (which would
    reintroduce a skip state).
  - top-level `permissions: {contents: read}`; no job-level `permissions:`;
    `pull_request_target` absent; AC12's literal `concurrency` expression;
    `timeout-minutes` and `python-version` per job; `persist-credentials: false` on
    every checkout; `fetch-depth: 0` on the three work jobs.
  - `gate-main` contains the `Run make build-check` anchor step and a bandit install
    (AC14); the `make sast` step's literal `if:` polarity;
    `gate-export-boundary`'s AC14 tree-shape probe and skip check, and that its
    checkout carries **no `sparse-checkout`**.

  **It runs in the aggregator, not only in `gate-main`, and asserts that it does.**
  Wired only into `build_gate_chain.py` it executes inside `gate-main` — the far side
  of the edge it protects: deleting `- gate-main` from `needs:` with its env var and
  comparison leaves the aggregator not consulting the job that hosts its own guard,
  and the required check reports success. **The placement must be self-enforcing,**
  because otherwise deleting the aggregator's step *and* its `STEP_DISPOSITION` entry
  is one self-consistent edit — `lint-ci-parity.py` rejects only an *orphan*
  disposition — after which the surviving copy in `gate-main` still passes. So the
  test asserts its own invocation appears on a `run:` line inside the aggregator
  block. The `build_gate_chain.py` invocation is retained as the local-parity path,
  which is why AC6 dispositions its step `LOCAL`.

  **Every assertion is line-anchored, comment-stripped, and mutation-proven.** The
  first draft of this test was demonstrated to print `✓ posture OK` against a
  four-job workflow that verified nothing: `gate-main` ran no `make build-check`,
  `gate-sast` ran no scan, and both export-boundary guards carried `|| true`, with
  every required substring supplied by a YAML comment. That is the antipattern this
  repo recorded in `docs/knowledge/observations/antipattern/2026-08.jsonl` — *"the
  substring survives the deletion because it names where the control is CALLED, not
  what it DOES… an unmutated assertion is an unverified one."* Aggregate redness is
  **not** validation: a stub can be red overall while individual assertions pass for
  the wrong reason. The test therefore carries a `--self-test` mutation matrix that
  deletes or neuters each control in turn and requires a specific violation id for
  each, plus a coverage check that no assertion lacks a mutation case.

  **It also asserts what `$(origin)` depends on:** that `gate-main` passes
  `SAST_DELEGATED=1` as a make **argument**, not an environment prefix. As a prefix
  the origin is `environment`, AC5c then runs the SAST leg inside `gate-main` as well
  as `gate-sast` — the scan runs twice, the objective is silently unmet, every job is
  green, and the only thing that would notice is AC11's measurement, which is
  deferred post-merge.

  Wiring it **requires updating `test_build_gate_chain.py`**, which compares
  `EXPECTED_SCRIPT_STEPS` by exact equality and pins the step count.

- [ ] **AC14 — the two *silent* fail-open gates keep their prerequisites.** Loud
  fail-opens are AC15's business; these two report green.

  1. **`lint-nosec-form`'s unknown-ID check goes inert without bandit.** It resolves
     bandit's test IDs and, when bandit is absent, sets a caveat string and **exits
     0** — dropping the check rather than failing. It runs inside
     `make build-check`'s chain, i.e. in `gate-main`, while the SAST install moves to
     `gate-sast`, so the check would become inert on **every** PR. The repo already
     tracked this fail-open scoped to `SKIP_SAST` PRs.

     **Superseded by events, and worth recording as such:** while this spec was in
     review, #986 landed the fix on `main` independently — a *pinned* bandit install
     plus a runtime probe that its registry resolves as `lint-nosec-form`'s
     `id_checker()` expects — and closed
     `build-check-installs-bandit-unconditionally`. That is strictly better than the
     bare `pip install bandit` this AC originally specified, so the spec adopts it.

     What remains split-specific, and is all this AC now requires: **that step must
     live in `gate-main`**, because it runs inside `make build-check`'s chain while
     the SAST provisioning moves to `gate-sast`. #986 also encodes that it must
     *immediately precede* the gate — any step between them could replace a shared
     transitive dependency of bandit while exiting 0 — so the partition preserves
     adjacency. AC13 asserts placement only; #986's probe is the efficacy guarantee
     and is stronger than anything a text matcher can claim.
  2. **The export-boundary suite skips silently on tree shape.** All three
     real-artifact tests — including the only caller of `check_sdist()`, and therefore
     of `_preflight_dependencies` and `_check_skip_integrity` — are guarded by
     `skipif(not (REPO_ROOT / "packages" / "agentbundle").is_dir())`. If that
     directory is absent the whole gate exits 0 having verified nothing, and no
     module probe detects it. This spec introduces `sparse-checkout` into this
     workflow as a blessed pattern, which makes "sparse-checkout the 150s job too"
     the obvious next optimization — and it would land green. So
     `gate-export-boundary` asserts the tree shape (`test -d packages/agentbundle`)
     and **fails on any skip** in the outer suite (`pytest -rs` plus a check for the
     skip reason), and AC13 asserts its checkout is not sparse.

  **No module-import probe is specified**, and no drift test for
  `_DEPENDENCY_IMPORTS`. Both would pin nothing: `_preflight_dependencies` already
  **raises** on any missing member, and the suite already asserts `find_spec` for
  `build`/`setuptools` — so the module direction is fail-closed already, and drift
  that *adds* an entry is caught by that same raise. Recorded so a later revision
  does not add a mirror check that verifies nothing.

  **`gate-main` keeps its entire existing install set** besides the bandit addition,
  so every other fail-open coupling — the credbroker `[crypto]` extra whose absence
  makes the vendored-floor purity deny-list assert vacuously, `httpx`,
  `jsonschema`/`pyyaml`, ripgrep, the render libraries — needs no analysis.

- [ ] **AC15 — the coupling graph is completed empirically, against CI.** AC1's
  provisioning column is known-required, not exhaustive; completion is reached by
  iterating real CI runs until green, **not** by further derivation. The bar:
  - Every job green on a real run of the **SAST-relevant** diff class.
  - `gate-export-boundary`'s run shows the export-boundary tests **executed, not
    skipped** (AC14's `-rs` check makes this a gate, not a log read).
  - No gate script's dependency declarations edited, and no posture-test assertion
    weakened, to achieve green (Boundaries § Ask first).
  - Each discovered requirement is added to AC1's provisioning column, so the table
    becomes the manifest this repo lacked.

  **The non-relevant diff class is out of this PR**, and this is a mechanism
  statement rather than an omission: `SAST_CONFIG` contains both `Makefile` and
  `.github/workflows/build-check.yml`, which every iteration of this change edits, so
  the branch is permanently SAST-relevant; and `on: pull_request: branches: [main]`
  means a sibling PR cannot target this branch. Pre-merge coverage of that path is
  AC5's banner tests plus AC13's assertion on the `make sast` step's literal `if:`
  polarity. The live run is recorded in the AC11 backlog entry post-merge.
  Boundaries § Never do forbids narrowing `SAST_CONFIG` to manufacture the case.

- [ ] **AC16 — local↔CI parity becomes one-to-many, and addressability is
  contractual.** This is the property the split actually costs, and it is not a
  bypass — it is a change to the repo's verification model, so it is stated rather
  than discovered later.

  **What changes.** Today `"Run make build-check"` carries the disposition
  *"Invokes the local gate itself — this is the parity anchor, not a divergence."*
  One CI job equals one local command. After the split `gate-main` runs
  `make build-check SAST_DELEGATED=1` — the local gate **minus SAST** — so no single
  local command equals any single CI job, and that anchor claim stops being true.

  **The covering relation is per STEP, not per job** — which is the granularity
  `lint-ci-parity.py` already models, and an earlier draft of this AC got wrong.
  `gate-main` is ~35 steps whose local counterparts are `make test`, `make lint-ruff`,
  `make lint-mypy` and `make pre-pr`, **not** `make build-check`; so "`make
  build-check` green implies `gate-main` green" is false. Only `make ci` supports a
  job-level ⟹ claim, and it supports it for all four jobs.

  **Addressability is the replacement invariant, and it is contractual:** every CI
  step keeps a local invocation (that is `lint-ci-parity.py`'s existing rule), and
  each job's *anchor* step gets a named one:

  | Job | Local target covering its anchor step | Residual |
  | --- | --- | --- |
  | `gate-main` | `make build-check SAST_DELEGATED=1` — **CI-equivalence only, not the pre-push command** | its other ~35 steps map to `make test` / `lint-ruff` / `lint-mypy` / `pre-pr` |
  | `gate-sast` | `make sast` | none |
  | `gate-export-boundary` | `make test` runs the same suite (`Makefile:350`) | **without** `-rs`, the skip check or the tree probe — so green `make test` is compatible with a red job |
  | aggregator | `make build-check` runs the AC13 posture test via `build_gate_chain.py` | the `needs.*.result` guard has **no** local counterpart, in any target |
  | **all four** | **`make ci`** — the only job-level ⟹ claim | — |

  **`make build-check SAST_DELEGATED=1` is not the pre-push command.** It is the one
  documented invocation that *skips* the SAST leg, so labelling it a reproduction
  risks habituating contributors into never running SAST locally — which matters
  because the relevance predicate self-certifies from the head commit (§ Risks).
  AC5a's quiet banner therefore names the covering command, so the skip is actionable
  rather than silent.

  This is the model mature repos converge on — an umbrella local target plus
  per-check granularity (Kubernetes' `make verify` + `hack/verify-*.sh`; Rust's
  `x.py` + `src/ci/`) — rather than one-to-one job correspondence, which does not
  survive past a handful of jobs. What those repos treat as the hard rule is exactly
  what `lint-ci-parity.py` enforces: no CI shell without a local invocation. That
  rule needs addressability, not identity, and the split preserves it.

  **Done means:** the `Run make build-check` disposition states the joint mapping
  explicitly; the four reproductions above appear as a comment block in
  `build-check.yml` next to the job definitions, so a contributor debugging one job
  does not have to derive the command; and `docs/CONVENTIONS.md`'s parity discussion
  is left alone — this is a workflow-level fact, not a convention change.

## Cost

Four jobs replace one. Two extra work-job setups at one provisioning cost each (A1); the aggregator adds
its own checkout and interpreter. AC8 removes a duplicated pack suite from Gate A,
and AC12's `concurrency` reduces waste on superseded pushes. Net runner-seconds are
down. `fetch-depth: 0`, the unconditional scanner install, and `gate-main`'s bandit
install each cost seconds, paid deliberately to remove fail-open classes.

## Verification

- Branch-protection API re-queried **pre-merge**, result recorded in the PR
  description (AC2).
- `make ci` green locally (SAST included — this diff is SAST-relevant).
- `python3 tools/lint-ci-parity.py` green, disposition diff matching AC6.
- `python3 tools/test_build_gate_chain.py` green after `EXPECTED_SCRIPT_STEPS` and
  its pinned count are updated — **and** after checking its second hold, which
  textually pins that the agentbundle+pytest install precedes `Run make build-check`
  in the workflow file.
- `actionlint` green; `zizmor --min-severity high` green. **Note the limit:** the
  two audits matching AC12's additions — `artipacked` (credential persistence) and
  `excessive-permissions` — rank *below* `high`, so at the repo's threshold neither
  fires. **AC13 is the sole enforcement** for `permissions` and
  `persist-credentials`; `high` covers the `${{ }}`-in-`run:` and
  `pull_request_target` boundaries via `template-injection` and
  `dangerous-triggers`.
- AC13's posture test, AC5's banner tests, and AC10's chain assertion, each
  mutation-verified.
- AC15's bar on the SAST-relevant class.
- A post-merge run supplies AC11's measurement and AC15's non-relevant-class run
  into the backlog entry.

## Risks

- **Aggregator correctness.** It wears the required-check name. Mitigated by the
  three-way binding with an explicit transform, derived set-equality *plus* a
  literal floor, running the guard inside the aggregator, a pure-stdlib test with no
  import to guard, and mutation tests.
- **A silent fail-open loses its prerequisite** — bandit for `lint-nosec-form`, tree
  shape for the export-boundary suite, history for the three transitive gates. This
  is the class AC15 explicitly does *not* delegate to CI.
- **The tempting wrong fixes**, named because they will look reasonable under time
  pressure: dropping an entry from `_DEPENDENCY_IMPORTS`; import-guarding or
  `sys.exit(0)`-ing the posture test; narrowing `SAST_CONFIG` to reach AC15's
  unreachable diff class. All three are Boundaries violations.
- **`test_build_gate_chain.py`'s two holds** both trip on this change.
- **The SAST floor keeps rising** — #977 and #980 both added to it in one day.
- **Pre-existing, recorded not fixed:** the relevance predicate evaluates
  `SAST_CONFIG` from the head commit, so a PR narrowing it self-certifies as
  non-scannable.

## Learnings

The work-loop's Capture learnings gate could not complete: `project-knowledge
--capture` times out on this repo (recorded as
`project-knowledge-capture-times-out`). **Named skip taken, not a silent one** — and
per that skill's producer contract this workflow does not select a journal path or
create a fallback store, so the lesson is recorded here instead of being lost.

**Fix the predicate, not the assertion that was demonstrated.** When review
demonstrates a bypass of a verifier, hardening the one assertion in front of you
leaves every sibling open, and the next round finds one you did not touch. That
happened **six times** in this single change:

| # | Instance fixed | Sibling left open |
| --- | --- | --- |
| 1 | whole-line comment stripping | trailing `#` comments |
| 2 | substring → command-word for some controls | the rest, incl. the comparisons |
| 3 | a discarded-exit check inside `_invocation` | the comparison loop, which bypassed it |
| 4 | `MAKEFLAGS` scrub in the chain assertion | the identical hazard in the verdict harness |
| 5 | banning `continue-on-error` | its exact twin, a falsy step-level `if:` |
| 6 | load-bearing-exit on the export step | the aggregator's guard body |
| 7 | quote-tolerant key matching in `_has_if` | five other key checks still bare-spelled |

The diagnostic is textual: **if a fix reads "add check X to assertion Y", it is an
instance fix.** Push it into the shared helper so every call site inherits it, then
replay the demonstrated bypass against *every* assertion of that shape.

**The deepest instance of the same error was choosing the wrong QUESTION, not the
wrong scope.** Four rounds hardened "do this statement's argv tokens contain something
forbidden?" by enumerating forbidden things — dry-run flags, then redirect flags, then
command substitutions. Every round the next reviewer found a way to reach `make` that
is not an argv token at all: a shell assignment prefix (`MAKEFLAGS=-n make …`), make's
fake-success flags (`-i`, `-t`), non-`$()` expansions (`${UNSET:--n}`, `$'\055n'`), and
YAML scalar folding (a `>`-folded or plain multi-line `run:` hands bash a trailing flag
on a line the checker counted as a separate statement). A denylist cannot be finished
against an open class.

The question that ends it is **"is this statement, whitespace-normalised, exactly the
pinned text?"** — and it was already in the file: the `comparison[*]` checks used
equality, and they were the only controls none of those vectors defeated. The lesson is
therefore sharper than "prefer allowlists": **when one assertion in a file resists
every round of attack and its siblings keep falling, the difference between them is the
finding.** Generalise the shape that held instead of patching the ones that broke.

Two costs of equality-pinning, both accepted: editing the workflow now requires editing
the verifier in the same commit (intended coupling — those five statements *are* the
gate), and several previously separate assertions became unfailable and were **deleted**
rather than kept, because a conjunct that cannot fail independently inflates a coverage
count without adding a proof.

**Family coverage is not class coverage.** `--self-test` reports that every assertion
family has at least one mutation. Every bypass found in the final round landed in a
family that *already* had a passing mutation. A coverage metric over assertions says
nothing about whether the classes each assertion can be defeated by are enumerated —
so the metric is now phrased as the count it is, and the class argument lives in prose
next to the code.

**The recurring shape, named by the reviewer on the fourth sighting: an allowlist over
one dimension with a second dimension left free.** Every round of this verifier failed
the same way, and reading the rounds together is what makes it visible:

| Round | Allowlisted / pinned | Left free | Bypass |
| --- | --- | --- | --- |
| 8 | command words | argv tokens | `make -n` |
| c1 | argv tokens | the statement | `MAKEFLAGS=-n make …` |
| c2 | the statement | the working directory | `working-directory: tools` |
| c3 | command words in a body | what a statement reads/writes | `echo "raise SystemExit(0)" > <the auditor>` |
| c4 | the action's ref | the action's **inputs** | `ref: main` — the gate runs against `main`, not the PR |

Round c4 is the one worth dwelling on, because it is the furthest from where anyone was
looking: `ref: main` on a checkout leaves every pinned statement byte-identical, passes
every cwd and body assertion, and runs the entire chain green against a tree that does not
contain the change. `repository: attacker/x` on the aggregator's checkout makes the
posture test — still exactly its pinned statement, inside a set-pinned body — audit the
attacker's copy of itself. And `token: ${{ secrets.PAT }}` escapes the
`permissions: contents: read` bound entirely, since that only scopes `GITHUB_TOKEN`.

**The generalisation, and the actionable part: each round pinned the innermost thing and
left the next layer out free.** The ladder is word → argv → statement → what the statement
reads → who else runs in the job → what the pinned thing runs against. A reader adding an
assertion should ask *which layer is now outermost-unpinned*, rather than hardening the
innermost one again.

Each fix was correct and each left a sibling dimension unconstrained, so the next round
found it. The escape is not a better allowlist — it is to ask whether the thing being
constrained is **finitely enumerable**, and if it is, pin the whole set. The two
aggregator bodies are five statements and two statements; the aggregator's non-run steps
are two SHA-pinned actions. Set-equality over those needs no enumeration of redirections,
`-c` payloads, heredocs, or lookalike action refs — the classes a denylist would have had
to anticipate. Where the set genuinely varies (the export-boundary body, a `pip install`
whose argument is read from a requirements file), the allowlist stays, and that is the
honest boundary of the technique.

The corollary for reviewers: **when the same fix shape recurs, stop fixing instances and
report the shape.** That single sentence closed more of this file than the previous four
rounds of patches.

**A no-op transform reads exactly like a passing test.** Twice more this round a mutation
appeared to prove something it never ran: a replace-string that did not match the real
workflow (comment lines sat between the keys) reported "GREEN — regression" for a
duplicate-key case that was in fact blocked. The self-test catches this for the mutation
matrix — it fails any transform equal to its input — but ad-hoc verification scripts have
no such guard, so assert `mutated != original` in those too. This is the same lesson the
Makefile parse-error mutation taught, recurring in a different tool.

**Where a belief cannot be argued, execute it.** The one recorded "probed and safe"
claim that was wrong (folded scalars) had been written from reasoning, not from a run.
The file now carries a differential harness: for the guard body that decides the
required check, it runs candidate bodies through **real bash** and requires that
anything bash would take green with a gate failed is rejected by the verifier. It is
proven load-bearing by neutering one guard function, which makes it fire seven
findings. Assertions encode beliefs about a system; the system is available, so ask it.

**Corollary, and the one that cost most:** a mutation must fail for the *right
reason*. One mutation here produced a make **parse error** rather than the condition
under test, so a check's headline claim was half-proven while its suite reported
green. Before trusting that a mutated artifact's missing marker means what you think,
assert the artifact still parses and executes.

**Second-order:** verify with a pattern that *can* fail. Twice this change a check
returned a null result that read like success — a `grep` whose pattern could not match
the text it was searching for, and three probes run through a `timeout` binary that
did not exist on the box. A verification that cannot produce a negative is not a
verification.

## Deferred

- **`ci-gate-parallelization-critical-path-measurement`** — AC11's measurement plus
  AC15's non-relevant-diff run.
- **`ci-gate-parallelization-required-workflow-pinned-ref`** — AC3's residual;
  closable via a pinned-ref ruleset plus `CODEOWNERS`, **neither of which exists today**.
- **`ci-gate-parallelization-workflow-codeowners`** — add `CODEOWNERS` covering
  `.github/workflows/**`. Highest-leverage item on this list: it makes every bypass this
  spec's verifier chases require a second human, and it needs no GitHub API call. Left
  out of this spec deliberately — naming reviewers is a decision about people.
- **`ci-security-posture-test-unwired`** — `tools/test-ci-security-workflow.py` is
  invoked nowhere despite a shipped AC claiming it gates `ci-security.yml`; also
  records that `ci-security.yml` and `codeql.yml` both carry the
  `cancel-in-progress` belief AC12 refutes.
- **`catalogue-tooling-workflow-hardening`** — `permissions` and
  `persist-credentials` for `catalogue-tooling-ci-gates.yml`. Deliberately not a
  bundled ride-along: seven gates, two of which move artifacts, none reviewed here.
- **Splitting the residual `gate-main` job further** — chases single-digit seconds.
- **Investigating the export-boundary gate's own cost** — the second floor.
