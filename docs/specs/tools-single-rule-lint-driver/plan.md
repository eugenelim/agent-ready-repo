# Plan: tools-single-rule-lint-driver

- **Status:** Done <!-- Drafting | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)
- **Follows:** ADR-0075 (test ownership and per-owner inclusion)

## Constraints

Twelve scripts are rewritten and ten self-tests move. The reviewable
behaviour and test surface is above two thousand lines and is not mechanically
uniform — six pattern rules and six predicate rules differ in input surface,
exit contract and message format — so the review shape is **MIXED** and the work
decomposes into dependency-ordered layers. T1 through T3 leave the repository
working with nothing migrated; T4 and T5 are independently reviewable halves of
the migration; T6 and T7 close it.

The comparison value for every behavioural claim is the T1 capture. No task
hand-writes an expected message.

## Design (LLD)

### Interfaces and contracts

`tools/lint_harness.py` exposes one keyword-only entry point, mirroring
`tools/posture_harness.py`'s `run()`. A rule supplies:

- `rule_id` — the token each message is prefixed with today; carried per rule
  because the twelve do not agree on it (`lint-pack-descriptions: `,
  `::error::`, a bare `{path}:{line}: `, and five others).
- `files` — a callable returning the ordered path sequence. A callable, not a
  glob string: four rules resolve their root from an environment variable
  (`EXPERIENCE_ROOT`, `LPJ_PACKS_DIR`, `LJC_JOURNEY_DIR`) or a positional
  argument, and a glob string cannot express that.
- `predicate` — returns the rule's violation messages for one path. The rule
  owns its message text, so the driver never formats one.
- `empty_scan` — what happens when the target directory exists but holds none
  of the rule's files. This is a per-rule outcome, not a per-rule exit code,
  because the rules disagree on more than the number: `lint-pack-descriptions.py`
  writes a fail-closed message to stderr and exits 2, while
  `lint-journey-contract.py` treats it as an ordinary pass and writes
  `lint-journey-contract: all 0 journeys conform` to **stdout** with exit 0. A
  single `empty_scan_exit` integer cannot express the second, so the field
  carries the whole outcome — stream, text and status.
- `absent_root` — the separate outcome when the target directory does not exist
  at all. `lint-journey-contract.py` exits 1 here and 0 for the empty case, so
  collapsing the two loses a distinction the current code makes. The driver
  tells them apart by the return type of `files`: `None` means the rule's root
  is absent, and a sequence — possibly empty — means it exists. An empty list
  and a missing directory are different values rather than the same falsy one,
  because `if not targets` is exactly the test that would merge them.
- `pass_line` and `summary` — callables, not strings. `lint-journey-contract.py`
  interpolates the number of files checked into its success line, and it prints
  no summary line at all on failure, so `summary` is optional.
- `report` — optional, and when supplied it replaces default emission entirely
  rather than decorating it. `lint-journey-contract.py` prints a header *before*
  its findings and no summary after them, which the driver's default
  violations-then-summary order would reverse. A writer that only adds to the
  default sequence cannot fix an ordering difference.
- `RuleAbort` — an exception a predicate raises to stop the walk with its own
  message, stream and status. `lint-experience-agnostic.py` returns 2 partway
  through the walk when a file will not decode, which is neither a violation
  (exit 1) nor an empty scan; without this the accumulated violations would be
  printed and the status would be wrong.

Argument parsing stays a per-rule callable handed to the driver rather than a
declarative schema. Three rules take `--root`, four take a positional root, two
take explicit file paths, and three read environment variables; a schema
expressive enough for all four shapes is larger than the code it replaces.

`tools/selftest_harness.py` exposes `load(script_filename)` — the `importlib`
loader the ten self-tests hand-roll — and a case runner covering both idioms
in the tree today: a sweep over module-level `test_*` callables, and an
accumulating checker for the files built around a `FAILURES` list. Both are kept
because converting a self-test's assertion style is a behaviour change to the
test, not to the driver.

### Import contract

Rules `import lint_harness` plainly. That resolves because `tools/` has no
`__init__.py`, so it is `sys.path[0]` both when a script runs directly and when
pytest collects a test beside it. The resolution is incidental to repository
layout rather than guaranteed, so T2 pins it with a test instead of leaving it
to be rediscovered. Neither module touches `sys.path`; `tools/repo/build_gate_chain.py`
once did, and `tools/test_import_time_path_leaks.py` exists because of it.

### Evidence the design holds

The driver shape was prototyped against `lint-pack-descriptions.py` before this
plan was approved, and discarded. Measured: stdout bytes, stderr bytes and exit
status identical to the unmodified script on all three of that script's exit paths — the clean
tree (exit 0), a fixture with one over-length description (exit 1), and a root
with no `packs/` (exit 2). The rule's own code fell from 149 lines to 50 with
its rationale docstring intact. That is the evidence for the empty-scan outcome being a per-rule field rather
than a driver default: exit 2 here is this rule's answer, and
`lint-journey-contract.py`'s answer to the same question is 0 on stdout.

The spike covered the easiest rule. It does not establish that the record fits
the other eleven, which is why T4 and T5 replay every rule rather than
generalising from this one.

### Resilience

The fail-closed empty-scan guard currently exists in only some of the twelve.
Moving it into the driver makes the mechanism reachable for all of them, but T4
and T5 set each rule's `empty_scan` and `absent_root` to the outcome that rule
produces **today**, not to the outcome it arguably should produce.
`lint-journey-contract.py` keeps returning 0 on an empty directory. Giving it a
guard it does not have is a behaviour change and is out of scope; the spec's
Follow-ons is where that belongs if anyone wants it.

## Tasks

### T1 — Capture the golden corpus

- **Depends on:** none
- **Implements:** the byte-for-byte replay strategy
- **Mode:** goal-based check
- **Tests:** the capture script is the instrument, so it is verified against a
  known-failing input before it is trusted: run it once against the unmodified
  tree, then again with one pack's `pack.toml` description pushed past the
  `lint-pack-descriptions.py` ceiling in a temporary root, and confirm the two
  captures differ in stdout and exit status. An instrument that records
  identical output for different inputs records nothing.
- **Done when:** for every rule in the spec's rule set the capture holds all
  four input modes the spec's first criterion names — clean real tree, a fixture
  with at least one violation, a root whose target directory exists but is
  empty, and a root where that directory is absent — and re-running it against
  the unmodified tree reproduces it with a zero diff. The last two modes are
  listed separately because they are the pair `lint-journey-contract.py`
  answers differently, and a corpus without both cannot see that.
- **Approach:** store raw streams plus exit status per (rule, case). Keep the
  corpus out of the commit unless replay needs it; the plan records where it
  lives either way.

### T2 — `tools/lint_harness.py`

- **Depends on:** T1
- **Implements:** the shared driver
- **Mode:** TDD
- **Tests:** a new `tools/test_lint_harness.py` (underscored, so the directory
  sweep collects it) covering the three load contexts, and the `empty_scan`
  versus `absent_root` split driven through a `files` callable returning an
  empty sequence in one case and `None` in the other. The load-context case
  drives the real
  `importlib` path a pytest-collected test uses, not a stand-in, because the
  failure it guards is a collection-time `ModuleNotFoundError`.
- **Done when:** its `Tests:` pass and no rule has been migrated yet.
- **Approach:** keyword-only `run()`; no `sys.path` mutation; stdlib only.

### T3 — `tools/selftest_harness.py`

- **Depends on:** T1
- **Implements:** the shared self-test runner
- **Mode:** TDD
- **Tests:** extend `tools/test_lint_harness.py` with the loader resolving a
  hyphenated filename, and both case-runner idioms reporting a seeded failure.
  Seeding a failure is the point: a runner that cannot report one is the defect
  this module could most easily introduce across ten callers at once.
- **Done when:** its `Tests:` pass and no self-test has been migrated yet.
- **Approach:** `load()` plus the two runners; stdlib only.

### T4 — Migrate the six pattern rules

- **Depends on:** T2
- **Implements:** the pattern half of the rule set
- **Mode:** goal-based check
- **Tests:** T1 replay for these six only, plus direct invocation of the four
  that have a self-test. `lint-nosec-form.py` and `lint-nosemgrep-form.py` read
  `SAST_DIRS` out of the `Makefile`, so their replay must run from the
  repository root or the file set silently empties.
- **Done when:** replay is byte-identical for these six and their self-tests
  exit 0.
- **Approach:** one rule per commit. Move the predicate; leave the docstring and
  its regression cases with it.

### T5 — Migrate the six predicate rules

- **Depends on:** T2
- **Implements:** the predicate half of the rule set
- **Mode:** goal-based check
- **Tests:** T1 replay for these six, plus direct invocation of their six
  self-tests. `lint-guide-titles.py` is the one whose self-test loads it
  in-process, so it is the case that exercises the T2 import contract against
  the real suite rather than a fixture.
- **Done when:** replay is byte-identical for these six and their self-tests
  exit 0.
- **Approach:** one rule per commit, as T4.

### T6 — Move the ten self-tests onto the shared runner

- **Depends on:** T3, T4, T5
- **Implements:** the self-test half of the objective
- **Mode:** goal-based check
- **Tests:** each of the ten invoked directly by path, with its case names
  captured before and after migration and compared as sorted sequences. Sorted
  sequences rather than sets: two cases sharing a name collapse under set
  equality, so a set comparison cannot see a dropped duplicate, and the
  criterion asks for the same names *and* the same number. The before-baseline
  is read out of the unmodified file with `ast` — the module's top-level
  `test_*` definitions and the case labels in its `FAILURES`-style calls — never
  by editing the self-test to print them. Six of the ten are hyphenated and
  pytest will not collect them, so `--collect-only` cannot supply the names, and
  making a subject emit a baseline changes the observable output this task
  exists to preserve.
- **Done when:** all ten exit 0 invoked directly, and each yields the same
  sorted sequence of case names as its pre-migration `ast` baseline.
- **Approach:** replace the hand-rolled loader and runner; leave every assertion
  and every case name as it is.

### T7 — Correct `tools/AGENTS.md` and state the new home

- **Depends on:** T6
- **Implements:** the maintainer-procedure durable output
- **Mode:** goal-based check
- **Tests:** the two commands the corrected text describes are run and their
  counts pasted into the review — the sweep returning zero, and one explicit
  invocation returning its real collected count. The claim being replaced is
  wrong because nobody ran it.
- **Done when:** the file states the sweep behaviour, drops the
  explicit-collection claim, and names the two drivers as the home for a new
  single-rule check.
- **Approach:** amend the existing bullet in place rather than appending a
  caveat beside it.

## Changelog

- 2026-09-16 — **Amendment, pending ratification.** Implementation measured
  that only six of the ten self-tests load their subject in-process; the other
  four (`test-lint-experience-agnostic`, `test_lint_guides_no_repo_only_refs`,
  `test-lint-journey-contract`, `test-lint-pack-journeys`) drive the real CLI
  through `subprocess`. The approved criterion required all ten to use the
  shared loader *and* runner, which those four cannot satisfy, and converting
  them to an in-process load would weaken them — a subprocess exercises the
  real entry point. The criterion is split: case running for all ten, the
  loader only where a self-test already loads in-process.
- 2026-09-16 — Spec review round 1. `check-docs-contrast.py` left scope: it
  iterates colour pairs inside one stylesheet and prints passing rows, so a
  violations-only predicate cannot reproduce its stdout. The Rule record gained
  `absent_root`, `RuleAbort`, and callable `pass_line`/`summary` after
  `lint-journey-contract.py` and `lint-experience-agnostic.py` defeated the
  first shape.
- 2026-09-16 — Initial plan. Layer two (the remaining in-process loader
  migrations) and a parity driver were split out to the spec's Follow-ons before
  drafting, so this plan covers layer one only.
