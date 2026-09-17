# Spec: PR-gate suite disposition

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round.

## Objective

A maintainer adding a test suite to the Makefile's `run-test-suite` define learns
immediately whether a pull request will run it. `tools/lint-ci-parity.py` holds a
second roster, `SUITE_DISPOSITION`, carrying a disposition for every command the
define runs: either the PR check that gates the suite, or the stated reason no PR
check does. Completeness is measured against the define's own recipe lines, read
lexically, so a command the module cannot parse demands a disposition rather than
escaping the roster. A claim that a PR check gates a suite is then corroborated
against the workflows rather than taken on the author's word.

Two suites that were reachable only through `make test` now run on every pull
request: `packs/frontend-engineering/tests/` and
`tools/test_local_ci_shared_test_deduplication.py`.

The remaining suites with no PR gate keep that status, but it is now a written,
lint-enforced declaration instead of an omission nobody can see.

### The gap this closes

Of the repository's pull-request workflows, only `build-check.yml` and
`ci-security.yml` carry an unfiltered `pull_request` trigger. Suites reached only
inside `run-test-suite` (`Makefile:572-695`) run under `make test` and
`test-after-build-check-unleased`, and under neither `make build-check` nor any
required pull-request check. A pull request could be green on every check while
those suites were red.

Measured over the define as `test-unleased` expands it — the standalone `make test`
route, which is the superset, because the composed
`test-after-build-check-unleased` route only adds `--ignore=` operands and drops
the third macro argument: of 114 gate targets, 56 are reached by
a workflow whose `pull_request` trigger carries no path filter, 6 only conditionally
(four behind `catalogue-tooling-ci-gates.yml`'s `paths-ignore`, one behind
`build-check-windows.yml`'s `paths`, one behind `docs.yml`'s), and 52 by no
pull-request workflow at all.

`tools/lint-pack-test-boundary.py`'s `every-suite-dir-has-a-runner` rule answers a
neighbouring but different question — whether *anything* runs a pack suite, where
the Makefile counts as a runner — and its scope is pack skill test directories only.
A suite can satisfy that rule and still be gated by no pull request;
`packs/frontend-engineering/tests/` was exactly that case. `SUITE_DISPOSITION` owns
"which PR check gates this", and that rule keeps owning "is this run at all".

### Departure from the recorded defect's wording

The defect this closes asks to "derive the mapping from written path to gating suite
instead of carrying it by recall". This spec declares the mapping by hand instead,
and corroborates it by extraction.

`tools/lint-ci-parity.py`'s module docstring records why: an earlier version of the
existing forward gate made extraction the trust anchor, and four review rounds each
defeated it a different way — a `:=` assignment, a whole-line recipe comment, an
inline one, `pytest` matching inside a path, and a subshell `cd` composing a phantom
prefix that a directory match then covered. Each fix caused the next round's defect,
and the class has no completeness proof. The settled design makes the
hand-declared roster the anchor and demotes extraction to corroboration. This spec
follows that precedent rather than the defect's wording, and records the
disagreement here because `AGENTS.md` requires surfacing a conflict with documented
guidance rather than resolving it silently.

The precedent transfers only once the anchor is chosen carefully.
`STEP_DISPOSITION`'s closed set is the workflow's YAML steps, which are
structurally enumerated. A roster keyed by the *targets* a shell command yields
would inherit the parser's blind spots: a command the extractor cannot read would
produce no key, demand no disposition, and leave the gap silent — the same false
pass, arriving one layer down. So the closed set here is the define's recipe lines,
joined across backslash continuations and read without interpreting any shell
command. Every such line must resolve to at least one roster entry. A line whose
operands the extractor cannot parse therefore fails the lint instead of vanishing
from it.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable: a maintainer adding a `run-test-suite` line must know the roster exists | [`tools/AGENTS.md`](../../../tools/AGENTS.md) | Repository maintainer | The new bullet names `SUITE_DISPOSITION` and the file it lives in | The bullet resolves and names the real symbol |
| Current architecture | Applicable: the gate's own contract and residual | `tools/lint-ci-parity.py` module docstring | Repository maintainer | Docstring states both rosters, the inversion, and the new residual | Docstring names what the suite roster does *not* prove |
| Maintainer-facing residual | Applicable: the first draft made the docstring wording and the `tools/AGENTS.md` wording acceptance criteria, but an obligation whose only check is that a sentence exists is not a criterion, so both are owned here instead. Named rather than numbered on purpose: a historical criterion number silently re-points after a renumber, and reads as a live local reference while doing it, so nothing flags the change of meaning | `tools/lint-ci-parity.py` docstring; [`tools/AGENTS.md`](../../../tools/AGENTS.md) | Repository maintainer | Docstring names the `PR_GATED_IF` condition, the reason-validity human control, and the spelling-mismatch residual; `tools/AGENTS.md` names `SUITE_DISPOSITION` | Both surfaces name the real symbol and it resolves |
| Decision rationale | Applicable: the derive-vs-declare departure | This spec, § Departure from the recorded defect's wording | Spec owner | The section above | No separate ADR; the departure follows an existing recorded decision rather than making a new one |
| Reusable learning | Applicable | `docs/specs/pr-gate-suite-disposition/notes/verification-ledger.md` | Spec owner | Measured baseline, both mutation void-probes, timings | Ledger records the probe that reddened each new arm |
| Release history | Not applicable | — | — | — | No published artifact or version surface changes; `tools/` is repo-only |
| User-facing promise | Not applicable | — | — | — | No adopter-visible behaviour changes |

## Boundaries

### Always do

- Keep `SUITE_DISPOSITION` complete in both directions: every recipe line of the
  `run-test-suite` define resolves to at least one entry, and every entry is
  resolved by at least one line.
- Keep the roster's completeness independent of shell parsing, so a command the
  extractor cannot read fails the lint rather than leaving the roster.
- Give every `NO_PR_GATE` entry a reason naming the route that does run the suite
  (a make target, a dispatch-only workflow) or the missing precondition that stops
  one. The lint checks that a reason is present; whether it is *true* is a
  human-review control, and the module docstring says so.

### Ask first

- Adding or moving a line inside the `run-test-suite` define, which moves
  `APPROVED_STANDALONE_PLAN_DIGEST` and `APPROVED_COMPOSED_PLAN_DIGEST` and obliges
  the two-way re-pin disposition at
  `tools/test_local_ci_shared_test_deduplication.py:535-631`.
- PR-gating any further suite, which spends `gate-main` runtime.
- Changing which workflows `WORKFLOW_SCOPE` treats as in scope.

### Never do

- Add `run-test-suite`, `make test`, or `make test-after-build-check` to
  `.github/workflows/build-check.yml`. It is minutes of work, deliberately sharded
  four ways into the dispatch-only `test-corpus.yml`.
- Create a second home for "which PR check gates this suite". The roster is the one
  home; a new module, table, or file restating it is forbidden.
- Add a new top-level directory, a new dependency, or a non-stdlib import to
  `tools/`.
- Leave a `SUITE_DISPOSITION` entry asserting coverage the workflows no longer
  provide. A suite whose gate was removed is re-dispositioned to `NO_PR_GATE` or
  `PR_GATED_IF` with the real condition, never left reading `PR_GATED`.

## Testing Strategy

AC-0001 through AC-0007 are each a violation string `tools/lint-ci-parity.py` either
does or does not emit, so each is a compressible invariant verified by **TDD**
through the existing self-test entry point `tools/test-lint-ci-parity.py`. That file
runs its cases from `main()` via `tools/selftest_harness.py`, and each case supplies
its own roster, workflow mapping and Makefile text as keyword arguments, so no case
mutates module globals. AC-0008 drives the same module through its command entry
point instead, and the seven criteria after it concern workflow content, roster
state, mutation sensitivity and backlog state rather than a violation string. All
eight take the modes named below.

- **Roster completeness, both directions (AC-0001, AC-0002)** — TDD. Each direction is a
  distinct violation string with a distinct remedy, so each gets its own case. AC-0001's
  case uses a define line whose operands the extractor yields nothing for, because
  that is the shape that would otherwise escape the roster.
- **Trigger and enforcement classification (AC-0003, AC-0004)** —  TDD. These decide
  whether a claimed gate is unconditional, so each misclassification is asserted
  separately.
- **Corroboration of a gating claim (AC-0005, AC-0006)** — TDD. The consequential direction —
  claiming a gate that does not exist — is asserted with a roster naming a suite no
  workflow step reaches, including the case where the only coverage route is
  `tools/repo/build_gate_chain.py`.
- **Reason presence (AC-0007)** — TDD.
- **Disconnecting the gate reddens a test (AC-0008)** — TDD, at the **integration**
  surface. The other cases call the check arm directly, so they stay green if the
  arm is never wired into `main()`. This one drives the command entry point against
  a fixture root and asserts exit 1. It closes that one disconnection, not every
  way a gate can be defeated.
- **The two newly gated suites (AC-0009, AC-0010, AC-0011, AC-0012)** —
  **goal-based check**, two criteria per suite because the two states fail
  independently and have different remedies. The execution criteria (AC-0009,
  AC-0011) are read off the workflow step; the disposition criteria (AC-0010,
  AC-0012) off the roster. Omitting both halves leaves a consistent `NO_PR_GATE`
  entry and a green lint, so the lint's exit status establishes neither.
  AC-0005's arm narrows what is left: it forces the named step to carry the suite as
  a **pytest operand**, which excludes a step naming the path in passing, but it
  cannot prove execution — `echo "python -m pytest <suite>"` extracts identically to
  a real invocation. Execution is therefore its own criterion, read by a human, not
  a consequence claimed off corroboration. That each new step also carries a
  `STEP_DISPOSITION` entry is not restated as a criterion: the module's existing
  forward arm and `tools/AGENTS.md` own it.
- **The repository's own roster is honest (AC-0013)** — **goal-based check**.
- **The new arms can fail (AC-0014)** — TDD, verified **differentially**. One
  self-test case per arm asserts that arm's own violation string, so removing the arm
  removes the string and reddens a named case. The criterion is stated as the
  differential outcome rather than as the presence of a case, because a case that
  cannot fail satisfies presence.
- **The recorded defect is retired (AC-0015)** — **goal-based check**.

## Acceptance Criteria

- [ ] **AC-0001.** `tools/lint-ci-parity.py` exits 1, naming the line, when a recipe line of the
  `run-test-suite` define resolves to no `SUITE_DISPOSITION` entry — including a
  line whose operands the module's extractor yields nothing for.
- [ ] **AC-0002.** `tools/lint-ci-parity.py` exits 1, naming the entry, when a
  `SUITE_DISPOSITION` entry is resolved by no recipe line of the define.
- [ ] **AC-0003.** `tools/lint-ci-parity.py` exits 1 when a `PR_GATED` entry names a workflow
  whose `pull_request` trigger carries a `paths` allowlist or a `paths-ignore` list.
- [ ] **AC-0004.** `tools/lint-ci-parity.py` exits 1 when a `PR_GATED` entry names a step or job
  carrying `continue-on-error` or an `if:` condition.
- [ ] **AC-0005.** `tools/lint-ci-parity.py` exits 1, naming the suite, when a `PR_GATED` entry
  names a suite that no step of any workflow under `.github/workflows/` with an
  unfiltered `pull_request` trigger reaches, where "reaches" counts a pytest operand
  of that step and any target `tools/repo/build_gate_chain.py` runs when the step
  invokes `make build-check`.
- [ ] **AC-0006.** `tools/lint-ci-parity.py` exits 1, naming the covering step, when a
  `NO_PR_GATE` entry names a suite that a workflow with an unfiltered
  `pull_request` trigger does reach.
- [ ] **AC-0007.** `tools/lint-ci-parity.py` exits 1 when a `NO_PR_GATE` or `PR_GATED_IF` entry
  carries an empty or whitespace-only reason.
- [ ] **AC-0008.** `python3 tools/lint-ci-parity.py` invoked against a fixture root
  whose `run-test-suite` define carries an undispositioned recipe line exits 1.
- [ ] **AC-0009.** A step of `.github/workflows/build-check.yml` invokes pytest on
  `packs/frontend-engineering/tests/`.
- [ ] **AC-0010.** `packs/frontend-engineering/tests/`'s `SUITE_DISPOSITION` entry
  reads `PR_GATED` naming that step.
- [ ] **AC-0011.** A step of `.github/workflows/build-check.yml` invokes pytest on
  `tools/test_local_ci_shared_test_deduplication.py`.
- [ ] **AC-0012.** `tools/test_local_ci_shared_test_deduplication.py`'s
  `SUITE_DISPOSITION` entry reads `PR_GATED` naming that step.
- [ ] **AC-0013.** `python3 tools/lint-ci-parity.py` exits 0 against the repository, with every
  recipe line of the `run-test-suite` define dispositioned.
- [ ] **AC-0014.** For each check arm named in AC-0001 through AC-0007, removing
  that arm from `tools/lint-ci-parity.py` makes `python3 tools/test-lint-ci-parity.py`
  exit non-zero; and so does removing the entry-point call AC-0008 exercises.
- [ ] **AC-0015.** The `workspace.toml` entry whose `path` is `tools/repo/build_gate_chain.py`
  and whose `kind` is `defect` appears once, under `[backlog].closed`, and no
  `[backlog].open` entry restates it.

## Follow-ons

- The 52 gate targets dispositioned `NO_PR_GATE` stay ungated. Which of them should
  become PR gates is a per-suite cost decision, not this spec's scope; the roster is
  the artifact that makes the list readable when someone takes it up. Owner:
  repository maintainer; evidence: `SUITE_DISPOSITION` itself.
- `packages/agentbundle/tests/` (3,200+ collected) is reached on a pull request only
  through `catalogue-tooling-ci-gates.yml`, whose `paths-ignore` trigger skips a
  pull request confined to `docs/**`, `guides/**`, `governance/**`, `docs-site/**`,
  `web/**`, `profiles/**` or seven named root files. It is dispositioned
  `PR_GATED_IF` stating that condition. Whether the repository's largest suite
  should have an unconditional gate is a cost decision outside this spec. Owner:
  repository maintainer.

## Assumptions

- Technical: `tools/lint-ci-parity.py` runs inside `make build-check` through
  `tools/repo/build_gate_chain.py:550`, and `build-check.yml:168` runs
  `make build-check`, so a check added there is gated on every pull request with no
  new workflow step.
- Technical: the `run-test-suite` define spans `Makefile:572-695`; its standalone
  route through `test-unleased` expands to 114 distinct gate targets (probe: the
  module's own `_expanded_recipe_lines` and `_pytest_path_args`).
- Technical: the 56 / 6 / 52 split is stated once, in § The gap this closes, and
  T1 re-derives it; this assumption records only that the probe is the module's own
  `_expanded_recipe_lines` plus `extract_ci_targets` over every workflow, not a
  second copy of the numbers.
- Technical: only `build-check.yml` and `ci-security.yml` carry an unfiltered
  `pull_request` trigger (probe: YAML parse of `.github/workflows/*.yml`).
- Technical: `catalogue-tooling-ci-gates.yml` filters with `paths-ignore`, not
  `paths`, so it runs for any `packs/**` or `packages/**` change but skips a
  pull request confined to the ignored set. Both filter kinds are therefore
  conditional coverage.
- Technical: no job or step of `build-check.yml` carries `continue-on-error`, and
  the only `if:` conditions are two `gate-sast` steps and the aggregator's
  `always()`, so no `PR_GATED` claim currently needs an exception (probe: YAML
  parse; `grep -n` for `|| true` and `set +e` found none).
- Technical: `npm run test:plugins --prefix docs-site` (`Makefile:585`) is a real
  test suite — `node --test` over two `.test.ts` files, per
  `docs-site/package.json:14` — and yields no path operand, so it is the concrete
  case proving completeness cannot be keyed on extracted targets.
- Technical: `packs/frontend-engineering/tests/` is exactly
  `packs/frontend-engineering/tests/skills/frontend-engineering/` and runs 337 tests
  in 1.54s.
- Technical: `tools/test_local_ci_shared_test_deduplication.py` runs 51 tests in
  65.4s.
- Technical: pull-request coverage can arrive through the gate chain rather than a
  literal workflow `pytest` line — `tools/test_workspace_status.py` and
  `tools/test_workspace_status_cli.py` are gated that way
  (`tools/repo/build_gate_chain.py:311-317`) — so the corroborator unions
  `script_step_targets` as `local_targets()` already does.
- Process: a step added to `.github/workflows/build-check.yml` needs a matching
  `STEP_DISPOSITION` entry (`tools/AGENTS.md`).
- Process: leaving the `run-test-suite` define untouched avoids the two-way re-pin
  disposition at `tools/test_local_ci_shared_test_deduplication.py:535-631`.
- Process: the defect entry's `path`, `tools/repo/build_gate_chain.py`, is not where
  the fix lands; the entry is retired stating so (user confirmation 2026-09-16).
- Process: the roster is hand-declared rather than derived, following
  `tools/lint-ci-parity.py`'s recorded precedent over the defect's wording (user
  confirmation 2026-09-16), with completeness anchored on recipe lines so the one
  property that transfers — no recipe line escapes the roster — actually holds.
  Corroboration does not inherit the forward gate's one-way safety.
- Product: all 114 targets are dispositioned in this spec, because the completeness
  arm cannot be switched on against a partial roster (user confirmation 2026-09-16).
