# Plan: lint-performance-p0

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Audit:** [`notes/lint-inventory.md`](notes/lint-inventory.md) — the scope contract

## Approach

Four waves, ordered so each one's evidence gates the next. Wave 1 lands the one
new primitive (a batched Git-ignore resolver) plus the source-level rule that
keeps it the only home for `check-ignore`. Wave 2 restructures the single
dominant offender — `tools/lint-pack-test-boundary.py` — around an explicit
context, one per-invocation inventory and structured findings, then converts its
falsification suite from twelve real-worktree lint launches to fixture plants
plus a minimal real-tree end-to-end layer. Wave 3 migrates the one remaining
confirmed offender (`tools/lint-agents-md.py`) and records no-change
dispositions. Wave 4 runs the terminal gates and captures after-evidence.

The refactor follows an existing repository precedent rather than inventing a
pattern: `tools/lint-ci-parity.py` already pairs a `--root` option with
fixture-root self-tests plus one real-root end-to-end launch
(`tools/test-lint-ci-parity.py:482,505,517`). The boundary lint adopts the same
shape.

Two deliberate non-extractions. There is **no** universal linter framework and
**no** `CatalogueInventory` holding every repository file: the inventory is
local to the boundary lint, carries only the data its own six checks consume,
and is never persisted. And there is **one** resolver, not three — measurement
found zero portable-`agentbundle` or shipped-pack callers needing ignore
batching, so a per-boundary helper would have no caller.

## Constraints

- Repo-only helpers live under `tools/`; portable `agentbundle` code must not
  import them, and shipped pack/skill content must not depend on them.
- Python standard library only. No third-party pathspec or Git library.
- New `tools/` scripts are pure-stdlib Python `.py` (AGENTS.md § *New tool
  scripts*).
- Root `AGENTS.md` ≤ 250 lines, subdirectory `AGENTS.md` ≤ 150 lines.
- `.github/workflows/docs.yml` path triggers must keep matching
  `python3 <script>` invocation form.
- Every changed Python file must pass `make lint-ruff` and `make lint-mypy`.

## Construction tests

Per-task `Tests:` blocks below are authoritative. Cross-cutting anchors that
must stay green and are **not** allowed to be edited to accommodate the diff:

- `tools/test-lint-ci-parity.py:292` — asserts
  `run_call_targets(AGGREGATOR) == {"tools/lint-agents-md.py"}`. The
  `_run("agents-md hygiene", …)` line in `tools/catalogue/pre_pr_catalogue.py`
  must stay byte-stable.
- `tools/test_build_gate_chain.py:235` and `tests/roster/test_core_pre_pr_hook.py:50`
  pin `tools/lint-agents-md.py` into the gate chain and the pre-PR hook.
- `tools/test_lint_agents_md_{legacy,diataxis,risk}_block.py` — three
  fixture-based self-tests of unrelated checks in the same file.
- `.github/workflows/docs.yml:161,166` — the two production CI gate steps.
- `tools/test-all.py:120,122` — umbrella runner entries.

## Design (LLD)

Shape is `service`, so the sub-sections below are the service set; `ui` and
`data` sub-sections are pruned as not applicable.

### Design decisions

1. **One resolver, repo-only.** `tools/lintlib/git_ignore.py` (new package
   `tools/lintlib/`) exports `git_ignored_paths(...)` and `MissingGitPolicy`.
   Rejected: a portable `agentbundle` twin (zero callers — measured), and
   putting it in an existing grab-bag module (no such module exists under
   `tools/`).
2. **`missing_git_policy` is a required keyword argument, no default.** Both
   call sites pass `FAIL_OPEN`. The parameter is retained despite both callers
   agreeing because the spec's contract mandates it and because a required
   argument forces each call site to state its ignore-failure posture in source
   rather than inherit a silent default. `RAISE` remains a member, exercised by
   the resolver's own unit tests.
3. **Context + findings, not globals.** `BoundaryContext` (roots and file
   locations) and `Finding` (check name, message, paths) are frozen dataclasses.
   `inspect_boundary(context, checks=None) -> tuple[Finding, ...]` is the
   callable surface; the CLI is a thin shell that builds a context, calls it,
   formats and exits.
4. **Inventory is per-invocation and lint-local.** `BoundaryInventory` is built
   once from the context and threaded to each check. Not cached to disk, not
   shared across processes, not generalised beyond this lint's six checks.
5. **Confinement memo keyed by resolved path.** `_glob_tree_is_confined`
   results are cached in a dict on the inventory keyed by the resolved base
   path, collapsing 45 scans over 16 distinct bases to 16. Fail-closed outcomes
   are cached identically to successes, so a refusal cannot be lost by a cache
   miss.

### Interfaces & contracts

```python
class MissingGitPolicy(enum.Enum):
    FAIL_OPEN = "fail-open"   # Git absent/unusable -> nothing is ignored
    RAISE = "raise"           # Git absent/unusable -> propagate

def git_ignored_paths(
    repo_root: Path,
    candidates: Iterable[Path],
    *,
    missing_git_policy: MissingGitPolicy,
    timeout: float = 30.0,
) -> frozenset[Path]:
    """Ignored subset of *candidates*, one batched `git check-ignore` per call."""
```

Properties: dedupe before invoking Git; deterministic ordering into Git and
deterministic set out; **zero** subprocesses for an empty candidate set; at most
one subprocess per call; candidates over stdin, NUL-delimited, via
`git check-ignore --stdin -z`; `--no-index` deliberately **absent** so tracked
files stay excluded; exit 0 and 1 both normal; no shell; explicit timeout;
prints nothing.

Boundary lint surfaces:

```python
@dataclass(frozen=True)
class BoundaryContext:
    root: Path
    packs_root: Path
    recipe_path: Path
    projected_roots: tuple[Path, ...]
    runner_files: tuple[Path, ...]

@dataclass(frozen=True)
class Finding:
    check: str
    message: str
    paths: tuple[Path, ...] = ()

def inspect_boundary(
    context: BoundaryContext,
    checks: Collection[str] | None = None,
) -> tuple[Finding, ...]: ...
```

CLI: unchanged no-argument behaviour; adds repeatable `--check <name>` and
`--root <path>` (fixture root). A run with either flag prints a partial-run
header naming the checks that ran and **suppresses** the
`✓ lint-pack-test-boundary: passed (6 cases).` line.

### Component / module decomposition

| Module | Role |
| --- | --- |
| `tools/lintlib/__init__.py` | package marker |
| `tools/lintlib/git_ignore.py` | batched resolver + `MissingGitPolicy` |
| `tools/lint-pack-test-boundary.py` | context, inventory, six checks, callable API, CLI |
| `tools/lint-agents-md.py` | migrated probe batch (3 → 1) |
| `tools/test-lintlib-git-ignore.py` | resolver unit tests |
| `tools/test-lint-no-direct-check-ignore.py` | AST source-enforcement gate |
| `tools/test-lint-pack-test-boundary.py` | 3-layer falsification suite |

### State & control flow

One invocation: build context → build inventory (one pack enumeration, one
projection enumeration, one runner read+parse, one destination build, one
batched ignore resolution over the union of all candidates) → run selected
checks against that inventory, accumulating findings → CLI formats and exits.
The single batched ignore call happens during inventory construction, so no
check can reintroduce a per-path probe.

### Behavior & rules

All six existing check semantics are preserved verbatim, including the
non-vacuity failures and the `_NO_RUNNER` staleness relation. The `evals/` skip
and `_TRANSIENT` prune stay in the walk. Symlink and junction handling is
unchanged and still evaluated before any resolution.

### Failure, edge cases & resilience

- Git absent or erroring → `FAIL_OPEN` at both call sites: nothing is ignored.
  For the boundary lint that reproduces today's "judge every file on disk". For
  `lint-agents-md`, whose probe assertion is inverted and whose `note()` is
  fatal, it yields a clean `exit 1` with three drift notes instead of today's
  unhandled `FileNotFoundError`.
- Git timeout → same as Git error, per policy.
- Resolution error inside confinement scanning → still fail-closed, and the
  fail-closed result is what gets memoised.
- Fixture root missing or not a directory → CLI refuses with a non-zero exit and
  a message naming the path; it must not silently fall back to the real root.

### Quality attributes (NFRs)

Bars are the spec's Acceptance Criteria: ≤1 `check-ignore` process per Git root
per invocation, 0 for an empty candidate set, exactly 1 inventory construction,
runner files parsed exactly once, and the full falsification suite completing
inside the five-minute inner-loop budget. Structural counts are asserted; wall
clock is recorded as evidence only.

### Dependencies & integration

No new dependencies. Integration points unchanged: `docs.yml:161,166`,
`test-all.py:120,122`, `pre_pr_catalogue.py:113`.

## Tasks

### T1: The batched resolver satisfies every enumerated ignore property

**Depends on:** none

**Touches:** tools/lintlib/*.py, tools/test-lintlib-git-ignore.py

**Tests:** (TDD — red first)
- empty candidate iterable → returns empty frozenset and launches **zero**
  subprocesses (asserted by a patched runner that counts invocations). AC:
  *empty candidate set launches zero processes*.
- one candidate, ignored → returned; one candidate, not ignored → absent.
- 500 candidates → exactly **one** subprocess. AC: *at most one process per Git
  root per batch*.
- duplicate candidates collapse before invocation (payload asserted
  duplicate-free). AC: *deduplicates candidates*.
- mixed ignored/non-ignored batch partitions correctly.
- filenames containing a space, a tab, a newline, Unicode, and a leading dash
  all round-trip correctly through NUL framing, in a real temporary Git
  repository. AC: *special filenames*.
- Git exit 0 and exit 1 are both normal, non-raising outcomes. AC: *exit 0 and 1*.
- `CalledProcessError`-shaped failure and `FileNotFoundError` each resolve per
  policy: `FAIL_OPEN` → empty set; `RAISE` → propagates. AC: *Git absence and
  error behaviour explicit*.
- `subprocess.TimeoutExpired` resolves per policy; the call passes a bounded
  `timeout`. AC: *explicit bounded timeout*.
- output ordering is deterministic across repeated calls on shuffled input. AC:
  *deterministic ordering*.
- Windows-shaped inputs normalise to POSIX-relative payload entries.
- the invocation is asserted to use no shell: argv is a list and `shell=True`
  never appears. AC: *no shell*.
- `--no-index` is asserted **absent** from the argv, and a tracked file is
  asserted not-ignored. AC: *tracked/generated/untracked semantics unchanged*.
- the helper writes nothing to stdout or stderr. AC: *prints nothing*.

**Approach:**
- Add `tools/lintlib/__init__.py` and `tools/lintlib/git_ignore.py`.
- Normalise each candidate to a repo-root-relative POSIX string; dedupe with an
  order-preserving pass; return early on empty.
- One `subprocess.run(["git","check-ignore","--stdin","-z"], input=…,
  cwd=repo_root, capture_output=True, timeout=…)`; split stdout on `\0`; map
  back to absolute `Path`s; return a `frozenset`.
- Treat returncode 0 and 1 as success; anything else and `OSError` go through
  the policy.

**Done when:** `python3 tools/test-lintlib-git-ignore.py` exits 0 with every
case above green.

### T2: No production lint constructs a direct `check-ignore` call outside the helper

**Depends on:** T1

**Touches:** tools/test-lint-no-direct-check-ignore.py

**Tests:** (TDD)
- the gate passes on the current tree once T3 and T5 land, and fails on a
  synthetic in-memory source that builds `["git","check-ignore",…]` directly.
- the approved helper module itself is exempt.
- fixture strings used to test detection are not flagged.
- a call assembled through a list variable or an alias is still detected (AST
  analysis, not substring matching).
- the inventory of scanned files is asserted non-empty, so the gate cannot pass
  vacuously.

**Approach:**
- Walk production lint sources (`tools/lint*.py`, `tools/check*.py`,
  `tools/validate*.py`, `tools/lint_*.py`, `tools/catalogue/*.py`,
  `tools/repo/*.py`, and the pack-owned lint scripts), parse each with `ast`,
  and flag any call whose resolved argv sequence begins `git`, `check-ignore`.
- Whitelist exactly `tools/lintlib/git_ignore.py`.
- Exclude `tools/test-*.py` and `*/tests/*` by construction — the scope is
  production lint sources — and document why
  (`tools/test-run-pack-evals.py:686` legitimately asserts a real `.gitignore`
  fact on a single path).

**Done when:** `python3 tools/test-lint-no-direct-check-ignore.py` exits 0, and
exits 1 when handed the synthetic offending source.

### T3: `lint-pack-test-boundary` runs six checks off one inventory with one batched ignore call

**Depends on:** T1

**Touches:** tools/lint-pack-test-boundary.py

**Tests:** (TDD)
- structural: one complete six-check invocation performs exactly **one**
  inventory construction, **at most one** `check-ignore` subprocess, parses each
  runner file **once**, and builds the destination inventory **once** — asserted
  by instrumenting the real boundaries (counters on the inventory constructor,
  the runner reader and a patched subprocess seam), not by source strings. AC:
  *one inventory per invocation*, *runner files parsed once*.
- confinement memo: a fixture with the same glob base reached from several call
  sites scans that base **once**; a fail-closed refusal is memoised as a refusal
  and re-returned on the next hit. AC: *tree-confinement results cached without
  weakening fail-closed*.
- `inspect_boundary` parses no arguments, calls no `sys.exit`, prints nothing
  (captured streams asserted empty), and mutates no file (fixture tree hashed
  before/after). AC: *side-effect-free callable API*.
- findings order is deterministic across repeated calls.
- no-argument CLI emits all six `ok   [<check>]` lines in the existing order
  plus `✓ lint-pack-test-boundary: passed (6 cases).`, exit 0 on the clean tree.
  AC: *default CLI runs all six checks in the same order*.
- `--check` accepts each of the six stable names, runs only that check, names
  which checks ran, and does **not** emit the six-check terminal line. AC:
  *targeted checks clearly marked as partial*.
- `--root <fixture>` scopes the run; a missing fixture root exits non-zero
  naming the path and does not fall back to the real root.
- every preserved failure contract still fires with its existing substring:
  `no packs found`, `no skill test directories found`, the unprojected-pack
  refusal, `multiple skill suites`, the `_NO_RUNNER` stale-exemption message,
  `linked`, `symlink`, and the runner-file-missing and unparseable-runner
  messages. AC: *existing messages remain compatible*.
- API/CLI parity: for the same fixture, `inspect_boundary` and the CLI reach the
  same pass/fail decision. AC: *callable API and CLI produce equivalent
  decisions*.

**Approach:**
- Introduce `BoundaryContext`, `Finding`, `BoundaryInventory`; delete the
  `FAILURES` global; convert each `case_*` into a function taking
  `(inventory)` and returning findings.
- Build the inventory once: pack list, self-host include list, pack skill dirs,
  projected skill dirs, authored test-content candidates, the **single** batched
  ignored-candidate set, pack test roots and Python test files, runner file
  contents, parsed runner invocations, suite destinations, basenames, and the
  confinement memo.
- Replace `_is_ignored` per-path calls with one `git_ignored_paths(...)` over the
  union of candidates gathered during traversal; walk first, filter second.
- Thread the memo dict through `_glob_tree_is_confined`.
- Keep `main()` as the formatter/exit shell.

**Done when:** `python3 tools/lint-pack-test-boundary.py` passes on the clean
tree with identical stdout to the pre-change run, and the structural test
asserts ≤1 `check-ignore` process and exactly one inventory build.

### T4: The falsification suite proves every plant from a fixture, with a minimal real-tree layer

**Depends on:** T3

**Touches:** tools/test-lint-pack-test-boundary.py

**Tests:** (TDD — the suite *is* the test; these are its own invariants)
- **Layer 1, in-process, no CLI:** all existing matcher shapes (`_MATCH`,
  `_NO_MATCH`, `_MATCH_DIR`, `_NO_MATCH_DIR`), every path-provenance case
  currently asserted (parents index, negative index, dynamic index, parents
  alias, parents iteration, function-local alias, constructor alias,
  module-qualified alias, `abspath`, `cwd`/`getcwd`, lexical `..`, `joinpath`,
  multi-argument `Path`, dynamic segments, glob/rglob traversal, Windows
  segments and Windows glob, linked glob base, resolve error,
  `rev-parse --show-toplevel` direct and helper-shaped), plus workflow
  `working-directory` parsing with and without pytest. Count preserved or
  higher; none removed.
- **Layer 2, fixture plants** — each builds a temporary catalogue of tens of
  files and invokes **only** its target check, asserting all four falsification
  properties (fails · names the plant/policy · comes from the intended check ·
  removal restores pass):

  | Plant | Target check |
  | --- | --- |
  | test file under `.apm/` | `apm-carries-no-tests` |
  | singular `test/` directory | `apm-carries-no-tests` |
  | allowed `evals/` content | `apm-carries-no-tests` (negative) |
  | test content in projection | `projection-carries-no-tests` |
  | pack in include list, no projected skill | `projection-carries-no-tests` |
  | empty `tests/` tree | `tests-live-in-the-pack-tree` |
  | pack test tree outside owning pack | `pack-tests-stay-in-pack` |
  | symlinked test source | `pack-tests-stay-in-pack` |
  | linked test directory and linked test root | `pack-tests-stay-in-pack` |
  | one pytest command spanning conflicting suites | `runners-keep-suites-isolated` |
  | suite directory with no runner declaration | `every-suite-dir-has-a-runner` |
  | stale `_NO_RUNNER` entry | `every-suite-dir-has-a-runner` |
  | missing runner file | runner inventory refusal |
  | malformed runner file | runner inventory refusal |

- **Layer 3, minimal real tree (4 launches):** clean production tree passes the
  complete lint; one runtime-boundary plant is detected and named; one
  runner-or-linked-tree plant is detected and named; cleanup restores a passing
  tree. Each plant refuses to run if its target already exists and cleans up in
  `finally`.
- the suite performs **no** write to the real `Makefile`, workflows, recipes or
  projected trees. Asserted by hashing those paths before and after the run.

**Approach:**
- Add a fixture builder that synthesises a minimal catalogue (a `pack.toml`, a
  couple of `.apm/skills/<skill>/`, a `tests/skills/<skill>/`, a self-host
  recipe, and a runner file) under `tmp_path`.
- Route Layer-2 plants through `inspect_boundary` with `--check`-equivalent
  selection against the fixture root; keep Layer-3 on the real CLI.
- Delete the two real-`Makefile` rewrites; the collision and undeclared-suite
  cases move to fixture runner files.

**Done when:** `python3 tools/test-lint-pack-test-boundary.py` exits 0, reports a
case count no lower than the pre-change count, launches the production CLI
exactly 4 times, and the before/after hashes of the real `Makefile` match.

### T5: `lint-agents-md` resolves its three probes in one batched call

**Depends on:** T1

**Touches:** tools/lint-agents-md.py

**Tests:** (TDD)
- the three session-scratch probes are resolved in **one** `check-ignore`
  process (patched-seam counter), down from three. AC: *no production lint
  launches one process per candidate*.
- a probe that is gitignored produces no note; a probe that is not produces the
  existing `drift-watch:` note naming that probe, with the existing wording.
- with Git absent, the resolver's `FAIL_OPEN` yields three `drift-watch:` notes
  and `exit 1` — a clean failure, not a traceback. Asserted explicitly, because
  this is the one deliberate behaviour change in the diff.
- checks 8, 10d and 10g still behave as their three existing self-tests assert.

**Approach:**
- Replace the `for probe in (...)` subprocess loop with one
  `git_ignored_paths(..., missing_git_policy=MissingGitPolicy.FAIL_OPEN)` call
  over the three probes; note each probe absent from the returned set.
- Keep the note wording and `note()`'s fatal semantics untouched.

**Done when:** `python3 tools/lint-agents-md.py` passes, its three existing
self-tests pass, and the process-count test asserts exactly one `check-ignore`.

### T6: Terminal gates pass and after-evidence is recorded

**Depends on:** T2, T4, T5

**Touches:** docs/specs/lint-performance-p0/notes/*.md, workspace.toml

**Tests:** (goal-based check)
- `python3 tools/lint-pack-test-boundary.py` → exit 0.
- `python3 tools/test-lint-pack-test-boundary.py` → exit 0, completes.
- `python3 tools/test-lintlib-git-ignore.py`,
  `python3 tools/test-lint-no-direct-check-ignore.py` → exit 0.
- `python3 tools/lint-agents-md.py` and its three self-tests → exit 0.
- `tools/test-lint-ci-parity.py`, `tools/test_build_gate_chain.py`,
  `tests/roster/test_core_pre_pr_hook.py` → exit 0 (aggregator anchors intact).
- `agentbundle catalogue lint --deep`, `agentbundle catalogue verify` → exit 0,
  unchanged terminal wording.
- `python3 tools/catalogue/pre_pr_catalogue.py` → exit 0.
- `make lint-ruff`, `make lint-mypy` → exit 0 for all changed Python.

**Approach:**
- Re-run the Wave-0 measurement probes and write the after-column into
  `notes/lint-inventory.md` and a `notes/performance-evidence.md`.
- Move `selftest-mutates-tracked-makefile` from `workspace.toml [backlog].open`
  to `[backlog].closed` — this spec discharges it.
- Run `make build-self` if any `packs/` file changed (expected: none).

**Done when:** every command above has been run and its actual exit code
recorded, and the before/after evidence table is committed.

## Rollout

- **Delivery:** big bang, fully reversible — a pure repo-tooling change with no
  runtime artifact, no migration and no published interface. Rollback is
  `git revert`.
- **Infrastructure:** none.
- **External-system integration:** none. No new dependency; `git` is already
  required by every gate.
- **Deployment sequencing:** T1 before T3 and T5 (both consume the resolver);
  T3 before T4 (the suite targets the new callable API); T2's gate only passes
  once T3 and T5 have migrated, so T2's assertion lands red and turns green
  within the wave.

## Risks

- **Behavioural drift hidden by a passing suite.** The boundary lint's six
  checks share subtle ordering and short-circuit behaviour (`return` after a
  hit, `len(FAILURES) == before` guards). Converting to returned findings can
  silently change which failures surface. Mitigation: the T3 test list asserts
  each preserved substring individually, and API/CLI parity is asserted.
- **Fixture catalogues that don't reproduce the real shape.** A plant proven only
  against a synthetic tree can pass while the real projection differs.
  Mitigation: Layer 3 keeps four real-tree launches, including the clean-tree
  pass and one projection-adjacent plant.
- **The memo caching a stale refusal.** Caching fail-closed outcomes is correct
  within one invocation but would be wrong across invocations. Mitigation: the
  memo lives on the per-invocation inventory only, and a test asserts no
  persistence.
- **`lint-agents-md` behaviour change.** Unifying to fail-open converts a
  Git-absent crash into `exit 1` + three notes. This is authorised and specced,
  but it is a real change and is asserted explicitly rather than left implicit.
- **Case-count regression going unnoticed.** Restructuring a 679-line suite can
  quietly drop assertions. Mitigation: T4's done-condition compares the reported
  case count against the pre-change count.

## Changelog

- 2026-08-17 — Initial plan. Scope narrowed to the three files the task-zero
  audit measured as carrying a P0 pattern (from an anticipated broader sweep),
  and the portable-`agentbundle` resolver dropped as caller-less, both on
  explicit human confirmation. Git-missing policy unified to fail-open by human
  decision, diverging from the originating brief's preserve-both instruction;
  the divergence is recorded in `spec.md` § Assumptions.
