# Plan: ci-gate-credbroker

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (`docs/CONVENTIONS.md` § Document lifecycle).

## Approach

Four files change together — `.github/workflows/build-check.yml`,
`tools/test-build-check-workflow.py`, `tools/fixtures/build-check-good.yml`, and
`tools/lint-ci-parity.py` — and **cannot be split across individually-green
commits.** Both gates fail closed on a partial edit by design: adding
`"gate-credbroker"` to `REQUIRED_WORK_JOBS` reddens `work-jobs-floor` immediately,
and adding a step reddens `lint-ci-parity` until its roster entry exists. That
coupling is what stops a job landing unwired, so T1 is one atomic edit.

**T0 comes first because the gate T1 asserts cannot pass before it.**
`SKIP_SAST=1 make build-check` chains `lint-spec-status`
(`tools/repo/build_gate_chain.py:242`), which fails invariant (iv) on a
`(deferred: <slug>)` that does not resolve in `[backlog].open`. Measured on this
branch before T0: exit 1, 2 hard violations.

### The eight edits to `tools/test-build-check-workflow.py`

Six are evident from its assertion list. Two are not:

- `_ALLOWED_STEP_ENV` (`:220`) allowlists step-level `env:` keys — without
  `GATE_CREDBROKER_RESULT`, `step-env-keys-allowlisted[build-check]` fails. Loud.
- `_differential_failures()` (`:1845`) sets `GATE_*_RESULT` for real `bash`. **This
  one is silent.** An unset fourth variable makes affected variants die on `set -u`,
  so they are never reported "green and accepted". Measured against the post-change
  guard body: **6/12 variants green without the edit, 10/12 with** — exactly four
  proofs lost (`subshell-or-true`, `reassign-result`, `always-false-conjunct`,
  `chained-false-test`).

A third coupling constrains the fixture: `_differential_failures()` splices
`_GUARD_BASE` — built from `REQUIRED_WORK_JOBS` in list order — by exact text, and
reports "harness is blind" if absent. So the fixture's comparison order must equal
`REQUIRED_WORK_JOBS` order; the new job appends to both.

### Fixture placement

Several mutations rewrite the first (or first two) occurrences of a literal
*file-wide*, so one retargets if a new job supplies an earlier match. Derived by
diffing every transform against the `gate-credbroker` job span:

**Placement-sensitive — two, both `count=1`. Fourth placement satisfies both:**

| Mutation | Literal | First match must stay |
|---|---|---|
| `drop-strict-shell` (`:1416`) | `set -euo pipefail` | `gate-export-boundary` |
| `architecture-on-setup-python` (`:1760`) | `python-version: "3.11"` | `gate-main` |

**Retired — the new job carries no such literal:** `duplicate-with-on-checkout`
(`:1773`) and `drop-checkout` (`:1523`), by AC1a's shallow checkout;
`grep-untied-from-tee` (`:1460`) and `grep-reads-suffixed-path` (`:1653`), by the
`credbroker-out.txt` tee target.

**Placement-insensitive despite sharing a literal:** `drop-python-version` (`:1521`)
is `count=2` and `gate-main` sits within the first two jobs at every placement, so
its occurrence is always among the two removed — a *different* mechanism from
`architecture-on-setup-python`, which shares the literal but is `count=1`.

**All-occurrence, placement irrelevant:** `or-true-grep` (`:1354`) and
`un-negate-grep` (`:1390`); the latter touches the new step too, harmlessly.

**Correctly absent:** `strict-shell-late` (`:1419`) anchors its literal as
`set -euo pipefail\n          test -d`, and `test -d` appears only in
`gate-export-boundary`'s tree probe.

### One mutation added, no assertion

The named unpinned layer: `guard-body-exact` derives `_want_cmp` from `work_jobs`
(`:1000`), and both its existing mutations alter the guard *body* — nothing mutates
the *job-set input*. A future edit substituting a literal list would keep both green
while a job could land unwired, and this PR is the "add a work job" event.
`add-work-job-unwired` targets that existing assertion, so counts move 143 → 144
with families steady at 67.

Equality-pinning the new job's statements is **declined here** and registered as
`ci-gate-credbroker-job-statements-pin`. As two bare labels it costs +2 families and
+2 mutations (`self_test()` fails on any evaluated family with no mutation); as a
parameterised `job-statements-pinned[<job>]` it is +1 and +1 and closes the 3/4
asymmetry for all jobs at once — that is the shape the follow-up should take. AC4's
two in-step controls close the exposure meanwhile.

## Constraints

- **ADR-0086** decides a leg of `build-check.yml` may become its own job, staying
  inside the workflow, always running, independently required. This applies that
  shape.
- **ADR-0017** keeps scanners CI-only and the Makefile chain intact; nothing here
  touches the SAST leg or adds a dependency.
- **`docs/specs/ci-gate-parallelization/`** is Shipped and frozen. Its AC16
  one-to-many parity model is inherited, so the new job's header comment names
  `make test` (`Makefile:332`). The frozen spec is not amended.
- Conventional Commits with a `Spec: docs/specs/ci-gate-credbroker/spec.md` footer;
  `AGENTS.md` § *Check before acting* — no new top-level directory, no new
  dependency, repo-settings writes go to the owner.

## Construction tests

**Integration tests:** none beyond per-task. The two gate scripts *are* the
integration test — each parses the real workflow and the fixture and fails closed.

**Manual verification:** (1) a real PR run read from `gh pr checks` (AC11); (2) the
`gate-credbroker` step log's collected/passed counts against what the same step
reported inside `gate-main` before the move; (3) per-job and per-step timings from
post-merge runs (AC12).

Every gate is read from **its own exit code**, never through `tail` or `grep` — a
filtered gate reports the filter's status. This bit once already:
`lint-spec-status … | tail -15` printed `EXIT=0` while the script exited 1.

## Design (LLD)

Shape is `integration`: *dependencies & integration*, *interfaces & contracts*,
*failure & resilience*.

### Dependencies & integration

Provisioning is the whole coupling: `actions/checkout` and `actions/setup-python` at
the SHAs `PINNED_USES` admits, then
`python -m pip install -e './packages/credbroker[crypto]' pytest`. No
`tools/requirements.txt`, no editable `agentbundle`, no `httpx`.

The checkout is shallow (AC1a) — `packages/credbroker` invokes git nowhere, and the
aggregator already carries this carve-out at `build-check.yml:811`.

The `[crypto]` extra is not self-evidencing: a bogus extra exits 0. AC4 answers with
**two** controls because they fail on different things — the probe names the
precondition and diagnoses fast; the reason-agnostic grep catches a shrunken
collection whose cause nobody anticipated. Of five non-crypto skip sites, four are
platform-gated and the fifth is gated on `.agentbundle/bin/sso-broker.py` being
tracked; spec.md § Assumptions is the single home for that inventory.

`gate-main` **keeps** its own credbroker install — the credential-setup suite, both
Atlassian SSO suites, and the user-libs vendored-floor purity test depend on it.

Traces to: AC1, AC1a, AC2, AC4 · contracts: none.

### Interfaces & contracts

| Consumer | Reads | Failure if not updated |
| --- | --- | --- |
| `tools/test-build-check-workflow.py` | job ids, per-job `with:`, the derived guard body | fails closed, loudly |
| `tools/fixtures/build-check-good.yml` | the baseline the above is proved against | `baseline should be clean` |
| `tools/lint-ci-parity.py` | every step name | `no entry in STEP_DISPOSITION` |

A fourth consumer sits outside the repo: `main`'s required-check set, applied by the
owner post-merge via the sub-resource endpoint with `checks[]` + `app_id` (AC13).

Traces to: AC3, AC5, AC6, AC7, AC8, AC13 · contracts: none.

### Failure, edge cases & resilience

- **Partial edit → red, never green.** Desired, and why T1 is atomic.
- **A silently-vacuous differential harness.** Four of twelve proofs; guarded by the
  env-dict edit and by reading the self-test's printed counts.
- **A step-name suffix colliding with a `_step_named` needle**, which fails closed on
  *more than one* match and misattributes an unrelated assertion. Audited by probe:
  none of the seven needles is a substring of any new name; exact-duplicate count is
  0 for each.
- **AC1a's checkout pin is what keeps the fifth skip site quiescent** — a future
  `sparse-checkout` or `path` key would fail `checkout-with[gate-credbroker]` before
  it could narrow the tree.
- **Two open PRs go pending** once the fifth check is required; named in the AC13
  handoff, not rebased from inside this loop.

Traces to: AC5, AC8, AC13 · contracts: none.

## Tasks

### T0: the spec's deferrals resolve, so the build-check chain can pass

**Depends on:** none · **Touches:** workspace.toml, docs/specs/README.md
**Verification mode:** goal-based check. No stub (goal-based).

**Tests:**
- `python3 .claude/skills/work-loop/scripts/lint-spec-status.py` exits 0, read from
  its own exit code. Verifies AC12/AC13 deferral anchors.
- `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"` succeeds.
- `docs/specs/README.md` lists `ci-gate-credbroker`.
- `spec.md` reads `Status: Implementing`.

**Approach:**
- Record the human approvals (`Approved` on both files at the two gates), then
  advance `spec.md → Implementing` and `plan.md → Executing`. Nothing enforces this
  (`lint-spec-status.py:20` puts `plan.md`'s status out of scope), which is why it is
  written down.
- Add three `[backlog].open` entries:
  - `ci-gate-credbroker-critical-path-measurement` — method (matched event class,
    each duration `completed_at - started_at`), the ≥3-run stop condition,
    "inconclusive is a valid outcome", and the consequence (no shift → follow-up
    questioning whether the extra runner earns its cost). **Carries the raw five-row
    run table, not derived means** — the comparison happens after `spec.md` freezes,
    so a hand-copied mean would be an undetectable transcription risk.
  - `ci-gate-credbroker-branch-protection-widening` — the sub-resource endpoint, the
    `checks[]`-with-`app_id` body, the read-diff-write-verify sequence, all five
    contexts, the read-back.
  - `ci-gate-credbroker-job-statements-pin` — the expiry condition of a hard Never-do.
    Scope, stated once: a `PINNED_JOB_STATEMENTS = {job: (statements…)}` dict
    emitting `job-statements-pinned[<job>]`, pinning each work job's load-bearing
    statements **and its `working-directory`**. Cost +1 family, +1 mutation.
- Register the spec in `ini-002`'s `[work]` block; add it to `docs/specs/README.md`.
- **Bundled fix**, same file and concern: correct
  `ci-gate-parallelization-branch-protection-widening`'s comment, which still
  describes the three-work-job widening as pending. It was applied (API-verified
  2026-08-17). Maps to no AC by design; declared under `Bundled fixes:` in the PR.

**Done when:** all four checks pass, read unfiltered. The fourth — `Status:
Implementing` — is the one nothing else enforces.

### T1: both gate scripts and the workflow agree on a five-job graph

**Depends on:** T0
**Touches:** .github/workflows/build-check.yml, tools/test-build-check-workflow.py, tools/fixtures/build-check-good.yml, tools/lint-ci-parity.py
**Verification mode:** goal-based check. Every item is a configuration property a
one-liner decides. No stub (goal-based).

**Tests:**
- `python3 tools/test-build-check-workflow.py` exits 0 (its `--self-test` runs on
  every invocation). Verifies AC1, AC1a, AC3, AC5, AC7.
- `--self-test` printed counts read, not merely exit-checked, against the counts
  stated once in § Approach. Verifies AC5, AC6.
- `python3 tools/lint-ci-parity.py` and `python3 tools/test-lint-ci-parity.py` exit
  0. Verifies AC8.
- `[ "$(grep -c 'pytest credbroker (RFC-0023 Phase 1)' .github/workflows/build-check.yml)" = 1 ]`
  — an equality, because `grep -c` exits 0 for any non-zero count and would pass a
  copy. `lint-ci-parity`'s `duplicates` check (`:1010`) is the fail-closed second
  artifact. Verifies AC2.
- The step body is, in order: `set -euo pipefail`; `python -c "import cryptography,
  argon2"`; the `-rs` pipeline into `tee`; the negated `grep`. Verifies AC4.
- `SKIP_SAST=1 make build-check` and `python3 tools/lint-ruff.py` exit 0, read from
  their own exit codes. Verifies AC10.

**Approach:** edit in this order, so the loudest failure surfaces first.

1. **`build-check.yml`** — add `gate-credbroker` after `gate-export-boundary`:
   `timeout-minutes: 10`, four steps (unnamed checkout with `persist-credentials:
   false` only, carrying the "touches no history" reason; `Set up Python
   (gate-credbroker)`; `Install credbroker (editable, with crypto extra) + pytest
   (gate-credbroker)`; the moved `pytest credbroker (RFC-0023 Phase 1)` with AC4's
   four-line body plus the comment naming the two known non-crypto `^SKIPPED`
   triggers). Delete the step from `gate-main`. Add the aggregator's `needs:` entry,
   the `GATE_CREDBROKER_RESULT` binding, and the guard comparison. Update the
   header's per-job block to five jobs with `make test` for this one (AC9).
2. **`tools/test-build-check-workflow.py`** — `REQUIRED_WORK_JOBS` += `"gate-credbroker"`
   (**appended**, so `_GUARD_BASE` matches the fixture);
   `PINNED_CHECKOUT_WITH["gate-credbroker"] = {"persist-credentials": "false"}`;
   `_ALLOWED_STEP_ENV` += `"GATE_CREDBROKER_RESULT"`; `_differential_failures()`'s
   `env.update({…})` += `"GATE_CREDBROKER_RESULT": "success"`; and
   `add-work-job-unwired` in `_MUTATIONS`. Two comments go stale and are corrected
   with it: `_baseline`'s "four-job baseline", and `PINNED_CHECKOUT_WITH`'s carve-out
   note (`:288`) which names the aggregator as the sole `fetch-depth` exemption.
3. **`tools/fixtures/build-check-good.yml`** — declare `gate-credbroker` **fourth**,
   mirroring the real step shape including `working-directory:`. Move the fixture's
   existing `pytest credbroker` step out of `gate-main`. Add the aggregator's
   `needs:`, `env:` binding, and comparison — the comparison **last**, in
   `REQUIRED_WORK_JOBS` order. **Spell the invocation `-rs`, not `-q -rs`:**
   `_MUTATIONS` apply to `_baseline()` (`:1292-1306`), which reads *this fixture* and
   never the real workflow, and `collect-only` (`:1424`) replaces the literal
   `"-q -rs"` with no count — mirroring `gate-export-boundary`'s spelling would pull
   this step into that mutation's blast radius.
4. **`tools/lint-ci-parity.py`** — three `CI_ONLY` entries:
   `<unnamed step in gate-credbroker>`, `Set up Python (gate-credbroker)`, and
   `Install credbroker (editable, with crypto extra) + pytest (gate-credbroker)`.
   `pytest credbroker (RFC-0023 Phase 1)` keeps its `LOCAL("test")` — dispositions
   are keyed by name, so a move preserves it.

**Done when:** all six checks pass — four commands read from their own exit codes,
two inspections — and the self-test's printed line is recorded verbatim in the PR
description.

### T2: every check is green on a real PR run

**Depends on:** T1
**Verification mode:** visual / manual QA. No stub. Local gates cannot stand in: the
thing under test *is* GitHub's scheduling of this graph.

**Tests:**
- `gh pr checks <n> --watch` reports every check `success`. Verifies AC11.
- The `build-check` run shows five jobs, `gate-credbroker` among them, `success`.
- The `gate-credbroker` step log's collected/passed counts match what the same step
  reported inside `gate-main` at `823cd174`, with no `[crypto]`-attributable skips.

**Done when:** the artifacts are moved to their shipped states — `spec.md` `Shipped`,
`plan.md` `Done`, AC1–AC11 `[x]`, AC12/AC13 deferred — **as the final commit**, and
the run's conclusions are recorded per-check in the PR description.

Order matters: flipping to `Shipped` changes the head and fires a new run, so a run
quoted in the *same* commit is not the run of the commit quoting it. AC1–AC10 close
against the pre-flip run; **AC11 closes against the run of the final pre-merge
commit**. And `lint-spec-status` invariant (ii) is hard and fires on the transition
(`transitioned = base_token != "Shipped"`, true for a new spec), so the flip with any
AC unchecked-and-undeferred reddens `make build-check`.

### T3: the move is confirmed on a real post-merge run, and the widening is handed off

**Depends on:** T2 (merge)
**Verification mode:** visual / manual QA. No stub.

**Tests:**
- On the first post-merge push-to-main run: the step is in `gate-credbroker`'s list
  and absent from `gate-main`'s; `gate-credbroker` within AC12's bound. Verifies AC12.

The throughput comparison is **not** a test of this task and cannot be — "≥3
post-merge runs" means three subsequent merges, which do not exist when this runs. It
lives in the register entry with its own stop condition.

**Approach:**
- Record the first run's figures in `ci-gate-credbroker-critical-path-measurement`
  with the run's **event class** and whether `gate-sast`'s scan ran or skipped — the
  comparison is meaningless on a skipped-scan run, and a cross-class comparison is
  not a comparison.
- Leave it open until ≥3 same-class runs exist, then compare against that class's
  baseline re-derived from the raw table. **"Inconclusive at n=3" is a permitted and
  expected outcome**; a quiet pass is not.
- Hand the owner the widening as **read-diff-write-verify**: `GET` first, diff
  against the five names, `app_id: 15368` and `strict: true` (mismatch on any → stop,
  return to owner), then `PATCH` with `{"strict": true, "checks": [<what the GET
  returned> + gate-credbroker]}`. Hand it over as a **JSON body** (`gh api --method
  PATCH … --input -`), never `-f key=value` — `checks` is an array of objects that
  `-f` cannot express. Supply the five contexts as copy-pasteable text but **label it
  the expectation to diff against, never the body to send**; an owner who takes it at
  face value and skips the `GET` reintroduces the staleness the sequence prevents.
  Close with the `GET` read-back asserting all three dimensions.
- Name PRs #993 and #994 as needing a rebase once the check is required.

**Done when:** the first run's figures are recorded, the measurement entry states its
stop condition, and the owner has the exact command and read-back. This task does
**not** write branch protection.

## Rollout

- **Delivery:** big bang, one PR, reversible — reverting restores the three-job
  graph, and nothing outside the repo changes until the owner applies AC13.
- **Infrastructure:** none. One additional `ubuntu-latest` runner per run, free tier.
- **Deployment sequencing:** one-directional. Merge, let the post-merge run report
  `gate-credbroker`, *then* add the required check. The reverse leaves every open PR
  pending on a check nothing reports.

## Risks

- **A fixture-placement mutation retargets.** The exposed set is derived in
  § Approach and not restated here. Mitigated by fourth placement; detected by
  `--self-test`, which names the failing mutation id.
- **The throughput measurement never becomes conclusive.** Likely: the spread exceeds
  the effect and the per-class baselines are thin (n=3, n=2). This is why it is a
  register entry with a stop condition rather than a criterion — a bar set here would
  be either unmeetable or unfalsifiable.
- **AC4's controls have no machine backstop.** The posture test does not pin that
  step, branch protection anchors at job granularity, and `lint-ci-parity`'s roster
  is per-step — `roster-residual-hidden-gate-in-known-step` asserts that residual
  deliberately. A Never-do is the stopgap, with an explicit expiry. Recorded as a
  risk because a prose rule is weaker than a pin and should not be filed as one.
- **A conflict with the parallel pip-audit change** over a `workspace.toml`
  `[backlog].open` entry — a trivial union, keep both blocks. With `strict: true`,
  whichever merges second rebases.
- **`lint-ci-parity` layer-2 may raise a coverage complaint** on AC4's added lines.
  That layer cannot grant a false pass, only a false alarm — fix it at the extractor
  or by wording, never by weakening the step.

## Changelog

- 2026-08-17: initial plan.
- 2026-08-17: reshaped after spec-stage adversarial + security review (13 rounds).
  Material changes to the approach, as distinct from wording: **T0 added** — the
  deferral slugs must resolve before `make build-check` can pass, so registration
  precedes the code edit. **`fetch-depth: 0` dropped** from the new job per the
  aggregator's existing carve-out. **AC4 gained two standing in-step controls**
  (import probe + reason-agnostic zero-skip), replacing a one-time human read.
  **AC13 became read-diff-write-verify with `checks[]` + `app_id`**, replacing a
  transcribed `contexts`-shaped body that would have substituted an auto-select
  heuristic for an explicit pin. **The throughput claim stopped being an acceptance
  criterion** — the pre-change spread exceeds the effect and the baselines mix event
  classes, so it moved to a register entry with a stop condition. **One mutation
  added** (`add-work-job-unwired`) against the named unpinned layer; equality pins
  declined and registered as follow-up.
- 2026-08-17: trimmed both documents. The review narration — which finding arrived in
  which round, and what each superseded — was removed in favour of the conclusions;
  the reasoning that is still load-bearing (why fourth placement, why two AC4
  controls, why `checks[]` over `contexts`) stays where it is used.
