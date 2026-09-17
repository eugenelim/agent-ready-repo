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

`suite_lines(makefile_text)` reads the define **as `test-unleased` expands it**, not
as it sits on disk. That choice is load-bearing and easy to get wrong. The define
body carries `$(3)` literally; enumerating the body verbatim would make `$(3)` a
single undispositioned line and leave the two suites that arrive through it —
`tools/test_workspace_status.py` and `tools/test_workspace_status_cli.py` — with no
roster key at all, which is the escape the whole design exists to close. Expanding
the `test-unleased` call site substitutes them in. That route is also the superset:
`test-after-build-check-unleased` only appends `--ignore=` operands to the same
lines and passes an empty third argument, so it contributes no line the standalone
route lacks. `_expanded_recipe_lines` already performs exactly this expansion for
the forward gate.

From that expansion, `suite_lines` enumerates the command lines lexically:
join backslash continuations, then drop blank lines, and drop a `#` comment line
**only when it contains no `$(`**.

The comment carve-out is narrower than it looks because a recipe comment is not
inert. GNU Make expands functions in a recipe line before the shell ever sees it,
including a line the shell would treat as a comment, so
`# $(shell $(PYTHON) -m pytest hidden-suite/ -q)` runs its suite at expansion time.
Measured on GNU Make 3.81, the version this repository's tooling floor names: that
line wrote its evidence file under a plain `make` run **and** under `make -n`. A
content-blind comment drop would therefore hide an executing suite. The define
carries 16 comment lines today and none contains `$(`, so the rule costs nothing
now and closes the hatch permanently.

A `@` prefix is not an exclusion either.

It suppresses echo; it does not stop the
command running, so dropping `@`-prefixed lines would reopen the escape hatch one
notch down — `@test -d docs-site/node_modules && npm run test:plugins --prefix
docs-site` is a single valid line combining two shapes that sit adjacent at
`Makefile:584-585` today, and a syntactic `@` drop would hide the suite inside it.
`suite_lines` strips a leading `@` and treats the line like any other.

Every target on every surviving line must carry its own `SUITE_DISPOSITION`
entry, and every entry must be resolved by at least one line. Not "at least one
entry per line": the define batches up to nineteen modules onto a single
continued line, so a twentieth would inherit its siblings' dispositions and
demand none of its own. A roster key is either a target
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

Concretely, corroboration proves the named step carries the suite as a pytest
operand. It does **not** prove the step executes it: `echo "python -m pytest
<suite>"` yields the same operand as a real invocation, measured against
`_pytest_path_args` directly. A bare `echo <dir>` yields nothing, so the arm does
exclude a step that merely mentions a directory in passing. Execution is a separate
criterion a human reads off the step, not a consequence claimed off this layer.

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
  completeness anchor; reuses `_join_continuations`, strips a leading `@`, drops a
  `#` line only when it holds no `$(`, and interprets nothing else.
- `line_targets(line)` — the per-line target proposal, reusing `_segments`,
  `_strip_inline_comment`, `_strip_shell_noise` and `_pytest_path_args`. Corroboration
  only.
- `pr_gate_sources(root)` — target → list of (workflow, trigger kind, step,
  conditional?). Unions three coverage shapes it can recognise, because T1 measured
  that an enumeration of two rejected five correct entries: a pytest operand of a step, a script path at a command position
  in a step, and — for a step invoking `make build-check` — every
  `script_step_targets` entry of the gate chain. The first two both fall out of
  `extract_ci_targets`, which already reads paths at invocation positions; the third
  mirrors `local_targets()`. A fourth shape exists and is deliberately not read: the
  `run_with_floor` shell function at `build-check.yml:827` passes a suite directory
  to a subshell that `cd`s and runs bare `pytest`. Not reading it costs nothing
  because an unrecognised shape fails a true claim rather than passing a false one,
  and reading it would widen the amendment past its authority.
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
define, and that exactly four carry no path operand. That unioning
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
- a define line one of whose targets carries no entry, where the operands parse —
  and specifically a line whose OTHER targets are dispositioned, since inheriting
  a sibling's entry is the failure this criterion exists to catch (AC-0001)
- a define line with no path operand at all — the `npm run test:plugins` shape,
  which is the case a target-keyed roster misses entirely (AC-0002)
- a define line passing a variable expansion to pytest beside a literal target,
  so the opaque operand cannot ride free on its neighbour's entry (AC-0002)
- a define line that is `@`-prefixed and carries a suite after a `&&`, which a
  syntactic `@` drop would hide (AC-0001)
- a define line that is a `#` comment containing `$(shell ... pytest ...)`, and
  the same in `${...}` brace form, both of which GNU Make expands and runs
  (AC-0001)
- an entry resolved by no define line (AC-0003)
- `PR_GATED` naming a `paths`-filtered workflow, and one naming a
  `paths-ignore`-filtered workflow (AC-0004)
- `PR_GATED` naming a step carrying `continue-on-error`, and one naming a step
  carrying `if:` (AC-0005)
- `PR_GATED` whose suite no extracted step reaches (AC-0006)
- `PR_GATED` satisfied *only* through `build_gate_chain.py` coverage, which fails if
  that arm of the union is dropped (AC-0006)
- `PR_GATED` satisfied *only* through a script invoked at a command position —
  `python3 tools/test-pages-workflow.py` is the live shape — which fails if
  corroboration demands a pytest operand (AC-0006). Five real entries depend on
  this arm; T1 found the approved criterion had omitted it.
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

**Tests:** goal-based check — `python3 tools/test-lint-ci-parity.py` stays green,
and the docstring names all five residuals below. Traces to no criterion, for the
same round-1 finding-8 reason as T6.

**Approach:** extend the module docstring's two-layer section to cover both rosters,
and state the suite roster's own *what it does not prove*: corroboration is
best-effort in both directions, not one-way like the forward gate's;
`PR_GATED_IF` records a condition nobody evaluates, so a conditional gate may not
run; corroboration proves a step names the suite as a pytest operand, not that it
executes it; a target key matches by written spelling, so a suite reached through a
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
  entry still reads `NO_PR_GATE` (AC-0007's arm)
- `python3 -m pytest tools/test_local_ci_shared_test_deduplication.py -q` stays
  green, confirming a workflow-only change moves neither plan digest
- each new step invokes pytest on its suite, read off `build-check.yml` (AC-0010,
  AC-0012), and each suite's roster entry reads `PR_GATED` naming that step
  (AC-0011, AC-0013) — four checks, because a step present with no roster change and
  a roster change with no step are different failures with different remedies
- `python3 tools/lint-ci-parity.py` exits 0 against the repository with every
  recipe line of the define dispositioned (AC-0014) — this is the task that
  completes it, because T2 lands the roster and T5 lands the last two entries

**Approach:** add two `gate-main` steps, their `STEP_DISPOSITION` entries as
`LOCAL("test-after-build-check")`, and flip both `SUITE_DISPOSITION` entries to
`PR_GATED` naming the new steps. Neither step may carry `if:` or
`continue-on-error`, or AC-0005's arm rejects the claim it is meant to support.

**Done when:** AC-0010 through AC-0013 hold — each step invokes pytest on its suite
and each roster entry reads `PR_GATED` naming that step — and the lint corroborates
both entries.

### T6: `tools/AGENTS.md`

**Depends on:** T2

**Touches:** `tools/AGENTS.md`

**Tests:** goal-based check — the bullet names `SUITE_DISPOSITION` and
`tools/lint-ci-parity.py`, and both resolve. Traces to no criterion: finding 8 of
round 1 demoted this obligation out of the contract into Durable Outputs, because
its only check is that a sentence exists.

**Approach:** consolidate with the existing `STEP_DISPOSITION` bullet so the two
obligations read as one pair in one place, rather than adding a second unrelated
caveat.

**Done when:** a maintainer adding a `run-test-suite` line finds the obligation
beside the one for adding a workflow step.

### T7: Void-probe every new arm

**Depends on:** T2, T3, T5

**Tests:** goal-based check, run **differentially** per arm (AC-0015). For each arm
named in AC-0001 through AC-0009: remove that arm from `tools/lint-ci-parity.py`,
run `python3 tools/test-lint-ci-parity.py`, and record both its non-zero exit and
which named case failed; then restore it and confirm the suite is green. The
`main()` wiring is probed the same way by deleting the call rather than the arm.

**Approach:** the differential run, not the presence of a case, is the evidence. An
arm whose removal leaves the suite green is a control that cannot fail; its case is
rewritten and re-probed before the arm is restored, because a case added to satisfy
a count would have the same defect.

**Done when:** AC-0015 holds — every arm's removal produced a non-zero exit — and
`notes/verification-ledger.md` names the specific reddened case per arm, with the
suite green again at the end.

### T8: Retire the defect entry

**Depends on:** T5

**Touches:** `workspace.toml`

**Tests:**
- `python3 tools/test_workspace_status.py` and
  `python3 tools/test_workspace_status_cli.py` stay green
- the entry whose `path` is `tools/repo/build_gate_chain.py` and whose `kind` is
  `defect` appears once, under `[backlog].closed` (AC-0016)

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
  hatch round 1 closed; only blanks and comments are dropped now. AC-0005 rejected a
  correct `PR_GATED_IF` whose job alone was conditional. Two baseline count sets
  contradicted each other (61/1/52 beside 57/5/52); the measured 56/6/52 is now
  stated once. AC-0010 and AC-0011 could both pass with the whole change absent, so
  they now read off the roster and lean on AC-0006 for the step. AC-0013 was
  restated differentially, because a self-test case that cannot fail satisfies
  "carries a case".
- 2026-09-16: Round 3 found two further defects in round 2's repairs, both proven by
  probe rather than argued. A recipe comment is not inert — GNU Make 3.81 expanded
  and ran `# $(shell ... pytest ...)` under both `make` and `make -n` — so the
  comment drop is now conditional on the line holding no `$(`. And AC-0006 was
  claimed to force the named step to *reach* the suite; measured against
  `_pytest_path_args`, `echo "python -m pytest <suite>"` extracts identically to a
  real invocation, so the claim is narrowed to "names it as a pytest operand" and
  execution became its own criterion. That last repair reinstates round 2's original
  remedy: splitting the two gating criteria, which this plan had overridden with a
  route-to-owner that silently dropped the execution obligation.
- 2026-09-16: Contract amendment, owner-authorised. T1's probe found AC-0006
  had corroboration recognise two coverage shapes where it needed to recognise a
  third: five `run-test-suite` targets are gated only by a script invoked at a
  command position, so the criterion as
  approved rejected five correct `PR_GATED` entries and made AC-0014
  unsatisfiable. The criterion now names the three shapes corroboration
  recognises, stated as recognised rather than exhaustive: reviewing the amendment
  found a fourth, `build-check.yml:827`'s `run_with_floor` wrapper, whose two
  directories are not roster targets. T2 gains a case for the third shape. Five
  review rounds missed the original omission because none separated *how* each
  target was matched; only running the extractor per shape exposed it. Authority:
  `notes/owner-decisions.md`; evidence: `notes/verification-ledger.md`.
- 2026-09-16: Deletion pass before approval cut one criterion. The rejected-
  `PR_GATED_IF`-on-an-unfiltered-workflow check enforced precision in the harmless
  direction — an over-cautious entry understates coverage and gates nothing wrongly
  — and had already cost a round on its own logic. The consequential direction, a
  `PR_GATED` claim on a filtered workflow, is kept. 16 criteria -> 15.
