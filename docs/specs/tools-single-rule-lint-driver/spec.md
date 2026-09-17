# Spec: tools-single-rule-lint-driver

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0075 (test ownership and per-owner inclusion — this spec moves ten `tools/`-owned self-tests onto a shared runner without changing their owner or their inclusion route)
- **Brief:** none
- **Discovery:** none
- **Contract:** none <!-- no external interface surface; the callable rule APIs are internal repo-tooling seams -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

**Scope contract:** the twelve scripts listed under
[§ The rule set](#the-rule-set) are the whole subject. A script absent from that
list is out of scope, and [§ Boundaries](#boundaries) says so as a rule rather
than as advice.

## Objective

A maintainer changing one of this repository's single-rule lint checks edits a
rule, not a program. Each of the twelve scripts named below declares its file
set, its predicate and its message, and hands them to one shared driver that
owns the walk, the report and the exit status, and runs the argument parser the
rule declares. Their
self-tests declare cases and hand them to one shared runner instead of
hand-rolling a loader and a pass/fail protocol each.

Nothing a caller can observe changes. For every input in the captured corpus,
each script writes the same stdout bytes, the same stderr bytes and the same
exit status it wrote before the change. Every script keeps its current path and
its current argument and environment-variable surface, so the roughly sixty-three
gate-chain steps, six workflow path filters, Makefile recipes and prose
references that name these files by hand keep resolving without edit.

The gain is concentrated in the two places duplication actually hurts. A rule's
reviewable content stops competing with its plumbing, and the fail-closed
empty-scan guard — the control that stops a run which gated nothing from reading
like a run that gated everything — exists once instead of being re-derived per
script and present in only some of them.

### The rule set

Six rules apply one pattern across a file set:
`lint-conformance-portability.py`, `lint-experience-agnostic.py`,
`lint-guides-no-repo-only-refs.py`, `lint-nosec-form.py`,
`lint-nosemgrep-form.py`, `lint_zone_violations.py`.

Six apply one structured per-file predicate:
`lint-guide-titles.py`, `lint-journey-contract.py`,
`lint-pack-descriptions.py`, `lint-pack-journeys.py`,
`lint-pack-maintainer-emails.py`, `lint-sso-config.py`.

Ten of the twelve have a self-test. `lint-conformance-portability.py` and
`lint_zone_violations.py` have none, and this spec adds none: their protection
is the captured corpus, and inventing coverage for them here would be a second
change wearing this one's approval.

### Why these twelve and not the rest

Two scripts that look single-rule are not. `check-semgrep-version.py` walks no
files: it runs `semgrep --version` as a subprocess and compares the result
against a range pinned in `tools/requirements-sast.txt`. `check-docs-contrast.py`
walks no file set either — it iterates theme by colour-pair inside one
stylesheet, and prints a line for **every** pair, passing ones included, so a
predicate returning only violations cannot reproduce its stdout. Both need a
driver that returns all results rather than offending ones, which is a different
driver.

The nine parity checks — among them `lint-plugin-membership.py`,
`lint-site-scope-parity.py` and `check-guide-index.py` — compare two sources of
truth rather than walking one. They share a shape with each other, not with this
driver; folding them in means a second driver and a separate decision.

`lint_git_ignore.py` is a library with no command-line surface.
`lint-pack-test-boundary.py` is byte-pinned by `PINNED_COMMIT` and
`PINNED_BLOB_SHA256` in `tools/test-lint-boundary-golden.py`, so any edit to it
reddens a pinned baseline.

The remaining bespoke scripts are multi-stage, stateful or cross-file, and a
rule table would model them worse than their current code does.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Maintainer procedure | [`tools/AGENTS.md`](../../../tools/AGENTS.md) | eugenelim | The corrected collection mechanism, and one line naming the shared drivers as the home for a new single-rule check | Both statements present and true against a measured run |
| Current architecture | the two new modules' docstrings | eugenelim | Each module states what it owns, what stays with the caller, and its import contract | Docstrings state the boundary a reader needs to place a new rule |
| Reusable learning | `project-knowledge` seam | eugenelim | The two-mechanism collection rule, and the import-resolution dependency | Routed at the work-loop capture gate |

No release history entry applies: these are repository-internal tooling seams
with no published surface, so no changelog entry and no version bump is owed.

## Boundaries

### Always do

- Capture each script's stdout, stderr and exit status from the **unmodified**
  script before editing it, and keep those captures as the comparison value.
- Keep every script's existing path, argument names and environment-variable
  names exactly as they are.
- Keep each script's rationale docstring and its named regression cases with the
  rule they explain.

### Ask first

- Before changing any message text, exit status or argument name, even where the
  current one looks like a mistake.
- Before adding a thirteenth rule to the table, or moving a script off the
  excluded list.

### Never do

- Never add a third-party import to `tools/`. Both new modules are pure-stdlib,
  and a new dependency is a structural change this spec does not carry.
- Never introduce a new top-level directory, package boundary or module outside
  `tools/` — the two new modules are the whole structural surface.
- Never mutate `sys.path` at import time in any module the test suite collects.
- Never edit a file outside `tools/` and this spec's own directory to make a
  script keep working.
- Never normalise the differing exit contracts or message formats into a common
  shape.

## Testing Strategy

- **Byte-for-byte replay — goal-based check.** The captured stdout, stderr and
  exit status from each unmodified script is the preserved-behaviour contract,
  following the discipline `docs/specs/lint-performance-p0/spec.md` established:
  behaviour preservation is proven by capture, not by description. A hand-written
  enumeration of expected messages would be a second implementation of the rule
  and would drift.
- **Import resolution — TDD.** A test loads a rule module in each of the three
  ways the repository actually loads one, because the resolution that makes this
  work is incidental to `tools/` having no `__init__.py` and would break silently.
- **Import-time path hygiene — goal-based check.** Reuses the existing
  `tools/test_import_time_path_leaks.py` mechanism rather than adding a second
  one.
- **Empty-scan fail-closed behaviour — TDD.** Per rule, because the correct exit
  status differs per rule and a shared guard is exactly where that difference
  gets flattened by accident.
- **Self-test migration — goal-based check.** Each migrated self-test is invoked
  directly and its exit status read. A directory sweep does not collect the
  hyphenated ones, so a sweep reporting green says nothing about them.
- **Repository gate — goal-based check.** `make lint-ruff lint-mypy`.

## Acceptance Criteria

- [x] For every rule, the captured corpus covers each of these input modes, and
  the rule writes stdout bytes, stderr bytes and an exit status identical to the
  capture taken before any edit: a clean real tree; a fixture containing at
  least one violation; a root where the rule's target directory exists but holds
  none of its target files; and a root where that directory is absent. One field
  of the 48 moves and is not caused by the refactor: both SAST-form lints report
  a repo-wide count of the files they scanned, so adding this change's three
  files takes `lint-nosec-form`'s clean line from 1216 to 1219. Untracking those
  three restores IDENTICAL across all 48, which isolates the cause.
- [x] Each of the twelve rule scripts obtains its file walk, violation
  reporting and exit status from `tools/lint_harness.py`, and none retains its
  own copy of them.
- [x] A rule module resolves its import of the shared driver when run as a
  script, when run as a subprocess from a test, and when loaded in-process by
  `importlib` from a pytest-collected test under `tools/`.
- [x] Neither `tools/lint_harness.py` nor `tools/selftest_harness.py` mutates
  `sys.path` at import time.
- [x] Neither `tools/lint_harness.py` nor `tools/selftest_harness.py` imports a
  module outside the Python standard library.
- [x] Each of the ten in-scope self-tests obtains its case running from
  `tools/selftest_harness.py`.
- [x] Each self-test that loads its subject in-process obtains that loader from
  `tools/selftest_harness.py`; a self-test that drives the subject as a
  subprocess keeps doing so.
- [x] Each of the ten in-scope self-tests reports the same case names, in the
  same number, as it reported before the migration, and exits 0 when invoked
  directly by path.
- [x] The files changed by the implementing commit are confined to `tools/` and
  `docs/specs/tools-single-rule-lint-driver/`.
- [x] `make lint-ruff lint-mypy` exits 0.
- [x] `tools/AGENTS.md` states that a directory sweep collects no
  `tools/test-lint-*.py`.
- [x] `tools/AGENTS.md` contains no claim that naming a `tools/test-lint-*.py`
  explicitly fails to collect it.
- [x] `tools/AGENTS.md` names `tools/lint_harness.py` and
  `tools/selftest_harness.py` as the home for a new single-rule check.

## Follow-ons

- **Shared self-test loader for the remaining in-process `importlib` callers.**
  Roughly fifteen further test files hand-roll the same loader. Excluded here
  because they test scripts this spec does not touch, and three of them
  (`test-lint-boundary-golden.py`, `test-lint-pack-test-boundary.py`,
  `test-lint-ci-parity.py`) carry byte pins or bespoke structure that deserve
  their own review. Owner: eugenelim.
- **A parity driver for the nine parity checks.** They share a shape with each
  other. Owner: eugenelim.

## Assumptions

- Technical: new `tools/` additions must be pure-stdlib `.py` files
  (`tools/AGENTS.md`, first bullet).
- Technical: `tools/` is `sys.path[0]` when pytest collects a test under it,
  because `tools/` has no `__init__.py` and pytest's default `prepend` import
  mode inserts the test file's directory (measured 2026-09-16, pytest 9.0.3).
- Technical: `pytest tools/` collects no `test-lint-*.py`, because the default
  `python_files = test_*.py` requires the underscore and `pyproject.toml` sets no
  override; naming such a file explicitly does collect whatever `test_*`
  functions it defines (measured 2026-09-16: 0 from the sweep, 11 from
  `tools/test-lint-pack-descriptions.py`).
- Technical: `check-semgrep-version.py` performs no file walk — it contains no
  `glob`, `rglob` or `iterdir` call.
- Technical: the twelve rules do not agree on exit status or message format —
  `lint-pack-descriptions.py` returns 2 on an empty scan while
  `lint-journey-contract.py` returns 0 with a stdout success line, and
  `lint-experience-agnostic.py` prefixes `::error::` where
  `lint-pack-maintainer-emails.py` prefixes its own name (read from those four
  files, 2026-09-16). A shared format would therefore change observable output.
- Technical: `tools/posture_harness.py` is the precedent for moving a driver out
  of several callers while every predicate stays in its own caller.
- Process: the spec owner is eugenelim, matching
  `docs/specs/lint-performance-p0/spec.md` and
  `docs/specs/pack-guidebook-walkability/spec.md`.
- Process: behaviour preservation is proven by capture rather than description
  (`docs/specs/lint-performance-p0/spec.md`).
- Product: the beneficiary is the maintainer or agent editing a lint rule, and
  the work ends at the twelve single-rule scripts (user confirmation
  2026-09-16).
- Process: layer two — the remaining in-process loader migrations — is a separate
  spec (user confirmation 2026-09-16).
- Process: the `tools/AGENTS.md` correction lands in this change (user
  confirmation 2026-09-16).
