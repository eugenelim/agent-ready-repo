# Plan: PR-gate suite disposition

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `tools/lint-ci-parity.py` (the forward gate this extends,
  and the source of the roster-anchor/extraction-corroboration pattern);
  `tools/test-lint-ci-parity.py` (the self-test route, 143 existing cases run from
  `main()` via `tools/selftest_harness.py`); `tools/AGENTS.md` (stdlib-only rule,
  `STEP_DISPOSITION` obligation, hyphenated-entry-point collection rule);
  `tools/lint-pack-test-boundary.py` `_NO_RUNNER` (the adjacent, differently-scoped
  runner table). Named uncertainty: `extract_ci_targets` is written against
  `build-check.yml` and is now read over eleven more workflow files; T1 measures
  whether any of them exercises a shape it mishandles.

> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Approach` and `Design (LLD)` are working material.

## Approach

Add a second roster to the module that already owns the forward direction, rather
than a new lint. The decisive reason is self-gating: `tools/lint-ci-parity.py` is
already invoked by `tools/repo/build_gate_chain.py` inside `make build-check`, which
`build-check.yml`'s `gate-main` runs, so the new check is covered by a required
pull-request check the moment it exists. A separate `tools/lint-suite-disposition.py`
would need its own wiring, and the natural place to wire it — a `run-test-suite`
line — is precisely the ungated position this work exists to expose.

The module already parses the Makefile for the forward direction, including
`$(call run-test-suite,...)` expansion, so the suite enumeration reuses
`_expanded_recipe_lines`, `_segments`, `_strip_inline_comment`, `_strip_shell_noise`
and `_pytest_path_args` rather than adding a second parser.

## Constraints

- Pure stdlib. PyYAML is already a hard dependency of this module (it exits 2 when
  absent), so reading more workflow files adds none.
- The `run-test-suite` define is not edited, keeping
  `APPROVED_STANDALONE_PLAN_DIGEST` and `APPROVED_COMPOSED_PLAN_DIGEST` still. Any
  task that finds itself needing to move a line in that define stops and returns to
  the spec's *Ask first*.
- New self-test cases go in `tools/test-lint-ci-parity.py`, which pytest does not
  collect from a directory sweep; it must be run directly and is already named in
  the gate chain.
- `tools/lint-ci-parity.py` sits in the shared-test dedup suite's blast radius only
  through `STEP_DISPOSITION`; adding a `build-check.yml` step does not move the plan
  digests, which are taken over the Makefile. T4 confirms rather than assumes this.

## Construction tests

Per-task `Tests:` below. All new cases land in `tools/test-lint-ci-parity.py`,
following its existing shape: each case builds its own roster dict, workflow mapping
and Makefile text and passes them as keyword arguments, so no case mutates module
globals.

## Durable-output map

| Durable output | Task |
| --- | --- |
| `tools/lint-ci-parity.py` module docstring — suite-roster contract and its four residuals | T4 |
| `tools/AGENTS.md` — the `SUITE_DISPOSITION` obligation | T6 |
| `notes/verification-ledger.md` — baseline counts, timings, per-arm void-probes | T1, T3, T7 |

## Design (LLD)

### Design decisions

**The anchor is the define's recipe lines, not its extracted targets.** This is the
one decision the whole design rests on. `STEP_DISPOSITION` is safe because its
closed set — the workflow's YAML steps — is structurally enumerated, so no shell
shape can remove a step from it. Keying a suite roster on the *targets* a command
yields does not inherit that property: a command the extractor cannot read yields no
key, demands no disposition, and leaves the gap silent. `Makefile:585`'s
`npm run test:plugins --prefix docs-site` is not hypothetical — it is a real
`node --test` suite that yields no path operand at all.

So `suite_lines(makefile_text)` enumerates the define's command lines lexically:
join backslash continuations, then drop only blank lines and `#` comment lines.
Those two are the sole content-blind exclusions the design permits, and they are
safe because neither can execute anything.

A `@` prefix is **not** an exclusion. It suppresses echo; it does not stop the
command running, so dropping `@`-prefixed lines would reopen the escape hatch one
notch down — `@test -d docs-site/node_modules && npm run test:plugins --prefix
docs-site` is a single valid line combining two shapes that sit adjacent at
`Makefile:584-585` today, and a syntactic `@` drop would hide the suite inside it.
`suite_lines` strips a leading `@` and treats the line like any other.

Every surviving line must resolve to at least one `SUITE_DISPOSITION` entry, and
every entry must be resolved by at least one line. A roster key is either a target
path (the readable, stable form) or a literal substring of the line, for a command
with no path operand. Extraction proposes the target keys; it never decides whether
a line needs an entry. Four lines in the define carry no extractable target and so
need a substring key each: the two `@` shell guards, `npm run test:plugins`, and
`$(PYTHON) -c "import httpx"`.

**What each layer proves, stated without overclaiming.** Completeness is
extraction-independent and fails closed. Corroboration is best-effort in *both*
directions: a false-positive extraction can satisfy a wrong `PR_GATED` claim, and a
false-negative one can let a stale `NO_PR_GATE` claim stand. Neither can make a line
escape the roster, which is the property that matters, and the docstring says
exactly this rather than repeating the forward gate's stronger one-way claim.

**Two constructors for coverage, because both filter kinds are conditional.**
`PR_GATED(where)` requires a workflow whose `pull_request` trigger carries neither
`paths` nor `paths-ignore`, and a step and job carrying neither `continue-on-error`
nor an `if:`. `PR_GATED_IF(where, condition)` covers every weaker case and states
the condition. `paths-ignore` lands here: it skips a pull request confined to the
ignored set, so calling it gated would rebuild the false confidence this work exists
to remove. `NO_PR_GATE(reason)` states why no check applies.

**Why trigger and enforcement shape are checked, not merely named.** Without the
check, an author can write `PR_GATED("docs.yml …")` and assert an unconditional gate
that is conditional. `continue-on-error` and `if:` are checked for the same reason
one layer down: a step can name a suite and not block the pull request. No current
candidate step carries either, so the check needs no exception list today.

### Component / module decomposition

Six additions to `tools/lint-ci-parity.py`, all module-level beside their forward
counterparts:

- `PR_GATED` / `PR_GATED_IF` / `NO_PR_GATE` constructors, beside `LOCAL` and
  `CI_ONLY`.
- `SUITE_DISPOSITION`, beside `STEP_DISPOSITION`.
- `suite_lines(makefile_text)` — the lexical line enumeration described above. The
  completeness anchor; reuses `_join_continuations`, strips a leading `@`, and
  interprets nothing else.
- `line_targets(line)` — the per-line target proposal, reusing `_segments`,
  `_strip_inline_comment`, `_strip_shell_noise` and `_pytest_path_args`. Corroboration
  only.
- `pr_gate_sources(root)` — target → list of (workflow, trigger kind, step,
  conditional?), unioning per-workflow `extract_ci_targets` with
  `script_step_targets` for a workflow step that invokes `make build-check`,
  mirroring `local_targets()`.
- a `check_suites(...)` arm called from `main()` alongside `check(...)`, taking its
  tables as keyword parameters so each self-test case supplies its own.

### Failure, edge cases & resilience

- A workflow with no `pull_request` trigger contributes no coverage.
- A workflow that fails to parse is a tool error, exit 2, as the module already does.
- A `run-test-suite` line with no path operand still demands an entry, keyed by a
  literal substring. Four exist on the standalone route: the two `@` guards
  (`command -v npm`, `test -d docs-site/node_modules`), `npm run test:plugins` (a
  real `node --test` suite over two `.test.ts` files), and
  `$(PYTHON) -c "import httpx"` (an import precondition, not a suite). Each is
  dispositioned on its own terms, and T1 confirms the enumeration finds exactly
  these four and no more.

### Quality attributes (NFRs)

`gate-main` gains 1.54s + 65.4s of pytest against a documented 25-minute budget.

## Tasks

### T1: Enumerate and corroborate, in a throwaway probe

**Depends on:** none

**Tests:** goal-based check — no repository test file, and the probe is not
committed. It traces to no acceptance criterion by design: the skill's
disconfirming-evidence step requires one throwaway check against the load-bearing
mechanism before review, and its output is evidence for the ledger, not contract.

**Approach:** settle four things the design rests on before any of it becomes module
code. That `suite_lines`'s lexical enumeration finds every command line of the
define, and that exactly three carry no path operand. That unioning
`script_step_targets` reclassifies `tools/test_workspace_status.py` and
`tools/test_workspace_status_cli.py` from ungated to gated, proving the union is
load-bearing rather than decorative. That re-classifying `paths-ignore` as
conditional moves the four `catalogue-tooling-ci-gates.yml` suites out of
`PR_GATED`. And that no other workflow exercises an `extract_ci_targets` shape that
misreports. Discard the probe.

**Done when:** `notes/verification-ledger.md` records the per-category counts, and
the *Repository anchors* uncertainty is closed or converted into a task.

### T2: `suite_lines`, `SUITE_DISPOSITION` and the check arm

**Depends on:** T1

**Touches:** `tools/lint-ci-parity.py`, `tools/test-lint-ci-parity.py`

**Tests:** one self-test case per violation string, each supplying its own roster,
Makefile text and workflow mapping as keyword arguments:
- a define line resolving to no entry, where the line's operands parse (AC-0001)
- a define line resolving to no entry, where the line has no path operand at all —
  the `npm run test:plugins` shape, which is the case a target-keyed roster misses
  (AC-0001)
- a define line resolving to no entry where the line is `@`-prefixed and carries a
  suite after a `&&`, which is the case a syntactic `@` drop would hide (AC-0001)
- an entry resolved by no define line (AC-0002)
- `PR_GATED` naming a `paths`-filtered workflow, and one naming a
  `paths-ignore`-filtered workflow (AC-0003)
- `PR_GATED_IF` naming an unfiltered workflow whose step and job are both
  unconditional, and — as the discriminating pair — `PR_GATED_IF` naming an
  unfiltered workflow whose *job* carries `if:` while its step does not, which must
  be accepted (AC-0004)
- `PR_GATED` naming a step carrying `continue-on-error`, and one naming a step
  carrying `if:` (AC-0005)
- `PR_GATED` whose suite no extracted step reaches (AC-0006)
- `PR_GATED` satisfied *only* through `build_gate_chain.py` coverage, which fails if
  the union is dropped (AC-0006)
- `NO_PR_GATE` whose suite an unfiltered workflow does reach (AC-0007)
- `NO_PR_GATE` and `PR_GATED_IF` with whitespace-only reasons (AC-0008)

**Approach:** add the constructors, `suite_lines`, `line_targets`, `pr_gate_sources`
and `check_suites`, then populate the roster from T1's output and review every entry
against the workflow it names. Call the arm from `main()` so its violations join the
existing report.

**Done when:** every case above passes and `python3 tools/lint-ci-parity.py` reports
the `NO_PR_GATE` targets as dispositioned rather than as violations.

### T3: End-to-end negative case through the entry point

**Depends on:** T2

**Touches:** `tools/test-lint-ci-parity.py`

**Tests:** one case building a fixture root — a `Makefile` with a `run-test-suite`
define carrying an undispositioned line, plus a minimal `.github/workflows/` — and
invoking the module's command entry point, asserting exit 1 and the AC-0001 violation
string (AC-0009).

**Approach:** every T2 case calls `check_suites` directly, so all of them stay green
if the arm is never wired into `main()`. This case is the one that reddens when the
gate is disconnected rather than broken. It is a separate task because it verifies
the wiring, not the rule, and T6 void-probes it as its own arm.

**Done when:** AC-0009 holds, and deleting the `check_suites(...)` call from
`main()` reddens this case while leaving every T2 case green — recorded in the
ledger.

### T4: Docstring — contract and residual

**Depends on:** T2, T3

**Touches:** `tools/lint-ci-parity.py`

**Tests:** goal-based check — `python3 tools/test-lint-ci-parity.py` stays green, and
the docstring names all four residuals below.

**Approach:** extend the module docstring's two-layer section to cover both rosters,
and state the suite roster's own *what it does not prove*: corroboration is
best-effort in both directions, not one-way like the forward gate's;
`PR_GATED_IF` records a condition nobody evaluates, so a conditional gate may not
run; a target key matches by written spelling, so a suite reached through a
differently spelled path is not matched; and a `NO_PR_GATE` reason's *truth* is a
human-review control, with only its presence checked.

**Done when:** a reader of the docstring can state what a clean run does and does
not establish about pull-request coverage.

### T5: PR-gate the two suites

**Depends on:** T2

**Touches:** `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`

**Tests:**
- `python3 tools/lint-ci-parity.py` exits 0, which fails if either new step lacks a
  `STEP_DISPOSITION` entry (existing forward arm, unchanged) or if either suite's
  entry still reads `NO_PR_GATE` (AC-0007's arm) — AC-0010, AC-0011
- `python3 -m pytest tools/test_local_ci_shared_test_deduplication.py -q` stays
  green, confirming a workflow-only change moves neither plan digest
- `python3 tools/lint-ci-parity.py` exits 0 against the repository with every
  recipe line of the define dispositioned (AC-0012) — this is the task that completes
  it, because T2 lands the roster and T5 lands the last two entries it corroborates

**Approach:** add two `gate-main` steps, their `STEP_DISPOSITION` entries as
`LOCAL("test-after-build-check")`, and flip both `SUITE_DISPOSITION` entries to
`PR_GATED` naming the new steps. Neither step may carry `if:` or
`continue-on-error`, or AC-0005's arm rejects the claim it is meant to support.

**Done when:** AC-0010 and AC-0011 hold — each entry reads `PR_GATED` naming its
new step — and the lint corroborates both.

### T6: `tools/AGENTS.md`

**Depends on:** T2

**Touches:** `tools/AGENTS.md`

**Tests:** goal-based check — the bullet names `SUITE_DISPOSITION` and
`tools/lint-ci-parity.py`, and both resolve.

**Approach:** consolidate with the existing `STEP_DISPOSITION` bullet so the two
obligations read as one pair in one place, rather than adding a second unrelated
caveat.

**Done when:** a maintainer adding a `run-test-suite` line finds the obligation
beside the one for adding a workflow step.

### T7: Void-probe every new arm

**Depends on:** T2, T3, T5

**Tests:** goal-based check — `python3 tools/test-lint-ci-parity.py` passes and
carries a case per arm named in AC-0001 through AC-0009 (AC-0013). Then, for each arm in turn, remove
that arm, re-run, record which named case fails, and restore. The `main()` wiring is
probed by deleting the call, not the arm.

**Approach:** this is the evidence that each control can fail. An arm whose removal
reddens nothing is a control that cannot fail and the case for it is rewritten
before the arm is restored.

**Done when:** `notes/verification-ledger.md` names a specific reddened case per
arm, and the suite is green again.

### T8: Retire the defect entry

**Depends on:** T5

**Touches:** `workspace.toml`

**Tests:**
- `python3 tools/test_workspace_status.py` and
  `python3 tools/test_workspace_status_cli.py` stay green
- the entry whose `path` is `tools/repo/build_gate_chain.py` and whose `kind` is
  `defect` appears once, under `[backlog].closed` (AC-0014)

**Approach:** move the entry, carrying a comment recording where the fix landed,
that `tools/repo/build_gate_chain.py` — the entry's own `path` — is untouched, that
the shared-test dedup suite was a second instance showing the gap reached `tools/`
construction tests, and that 52 targets remain `NO_PR_GATE` by declaration rather
than by omission. Check the four-revision window for a merge resurrecting a retired
entry before committing.

**Done when:** the entry is closed and no `[backlog].open` entry restates it.

## Rollout

- **Delivery:** big bang, single PR. Reversible by reverting; nothing persists
  state.
- **Infrastructure:** none.
- **Deployment sequencing:** T5 lands with T2 or after it. Landing T5 first would
  leave two `build-check.yml` steps whose suites the roster does not yet know about.

## Risks

- `extract_ci_targets` mishandling a shape in one of the eleven newly-read workflow
  files. Mitigated by T1 measuring first. Not bounded to false alarms: a
  false-positive read satisfies a wrong `PR_GATED` claim and a false-negative one
  lets a stale `NO_PR_GATE` stand. What *is* bounded is completeness — no misread
  removes a line from the roster — and T4's docstring states the difference.
- A `NO_PR_GATE` reason that is true today and quietly false later. Mitigated by the
  stale-declaration arm, which reddens when a pull-request workflow starts covering
  a suite declared ungated.
- `gate-main` runtime. Measured at 66.9s added against a 25-minute budget.

## Changelog

- 2026-09-16: Drafted. Roster placement and the dedup suite's gating both settled by
  owner decision before authoring; derive-vs-declare resolved toward the module's
  recorded precedent, with the disagreement recorded in the spec.
- 2026-09-16: Two independent review rounds found the same central defect — the
  roster was keyed on extracted targets, so completeness inherited the parser's
  blind spots and a command the extractor could not read escaped it silently.
  `Makefile:585`'s `npm run test:plugins` is a live instance. The anchor moved to
  the define's recipe lines, read lexically, and the one-way-safety claim inherited
  from the forward gate was dropped as untrue here. Same rounds: `paths-ignore`
  reclassified from gating to conditional, `continue-on-error`/`if:` added to the
  enforcement check, and T3 added because every other case would stay green if the
  arm were never wired into `main()`.
- 2026-09-16: Round 2 reviewed the repairs and found five of them had left drift.
  The `@`-prefix exclusion was a second content-blind drop and reopened the escape
  hatch round 1 closed; only blanks and comments are dropped now. AC-0004 rejected a
  correct `PR_GATED_IF` whose job alone was conditional. Two baseline count sets
  contradicted each other (61/1/52 beside 57/5/52); the measured 56/6/52 is now
  stated once. AC-0010 and AC-0011 could both pass with the whole change absent, so
  they now read off the roster and lean on AC-0006 for the step. AC-0013 was
  restated differentially, because a self-test case that cannot fail satisfies
  "carries a case".
