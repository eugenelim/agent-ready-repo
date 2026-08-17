# Plan: lint-performance-p0

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Audit:** [`notes/lint-inventory.md`](notes/lint-inventory.md) — the scope contract and the single canonical home for before/after figures. This plan does not restate them.

## Approach

Four waves, ordered so each one's evidence gates the next. Wave 1 lands the one
new primitive (a batched Git-ignore resolver) plus the source-level rule that
keeps it the only home for `check-ignore`, wired into standing CI. Wave 2
restructures the single dominant offender — `tools/lint-pack-test-boundary.py` —
around an explicit context, one per-invocation inventory and structured findings,
then converts its falsification suite from twelve real-worktree lint launches to
fixture plants plus a four-launch real-tree layer. Wave 3 migrates the one
remaining confirmed offender (`tools/lint-agents-md.py`). Wave 4 runs the terminal
gates, records after-evidence, and closes the governance debt.

The refactor follows an existing repository precedent rather than inventing a
pattern: `tools/lint-ci-parity.py` already pairs a `--root` option with
fixture-root self-tests plus one real-root end-to-end launch
(`tools/test-lint-ci-parity.py:482,505,517`).

Three deliberate non-extractions. There is **no** universal linter framework and
**no** `CatalogueInventory` holding every repository file: the inventory is local
to the boundary lint, carries only what its own six checks consume, and is never
persisted. There is **one** resolver, not three — measurement found zero
portable-`agentbundle` or shipped-pack callers. And it is a **flat module**, not a
package: `tools/catalogue/` and `tools/repo/` carry no `__init__.py`, so an
importable `tools/lintlib/` would be the first package under `tools/` and would
collide with the spec's own *never add a new module boundary* rail.

## Constraints

- Repo-only helpers live under `tools/` as flat modules; portable `agentbundle`
  code must not import them, and shipped pack/skill content must not depend on
  them.
- Python standard library only. No third-party pathspec or Git library.
- New `tools/` scripts are pure-stdlib Python `.py` (AGENTS.md § *New tool
  scripts*).
- `.github/workflows/docs.yml` path triggers must keep matching
  `python3 <script>` invocation form.
- Every changed Python file must pass `make lint-ruff`. **`make lint-mypy` does
  not apply** — `tools/lint-mypy.py:19-22` targets only
  `packages/agentbundle/agentbundle` and `packages/credbroker/credbroker`, and
  this diff is entirely under `tools/`. Widening it is an `Ask first` item, not
  taken here.
- Root `AGENTS.md` ≤ 250 lines, subdirectory `AGENTS.md` ≤ 150 lines.

## Construction tests

Per-task `Tests:` blocks are authoritative. The preserved-behaviour enumeration
is **not** restated here — `spec.md § Preserved failure contract` (F1–F21) and
`spec.md § Preserved falsification controls` (C1, C2) are canonical, and T3/T4
reference them by identifier.

Cross-cutting anchors that must stay green and may not be edited to accommodate
the diff:

- `tools/test-lint-ci-parity.py:292` — asserts
  `run_call_targets(AGGREGATOR) == {"tools/lint-agents-md.py"}`. The
  `_run("agents-md hygiene", …)` line in `tools/catalogue/pre_pr_catalogue.py`
  must stay byte-stable.
- `tools/test_build_gate_chain.py:235` and `tests/roster/test_core_pre_pr_hook.py:50`
  pin `tools/lint-agents-md.py` into the gate chain and the pre-PR hook.
- `tools/test_lint_agents_md_{legacy,diataxis,risk}_block.py` — three
  fixture-based self-tests of unrelated checks in the same file.
- `.github/workflows/docs.yml:161,166` and `tools/test-all.py:120,122` — existing
  production gate wiring, and the precedent T2 follows for the two new gates.

## Design (LLD)

Shape is `service`; `ui` and `data` sub-sections are pruned as not applicable.

### Design decisions

1. **One resolver, repo-only, flat.** `tools/lint_git_ignore.py` exports
   `git_ignored_paths(...)`, `IgnoreResolution` and `MissingGitPolicy`. The
   `tools/lint_*.py` name means the source-enforcement gate's own glob scans the
   file it whitelists, rather than exempting something it never looked at.
2. **`missing_git_policy` and `timeout` are both required keyword arguments.**
   Both call sites pass `FAIL_OPEN`. The parameters are required so each call site
   states its ignore-failure posture and its process bound in source rather than
   inheriting a silent default. `RAISE` remains a member for the one recorded
   trigger below.
3. **`RAISE`'s recorded trigger.** No production caller uses it today. It is the
   option a future lint takes when a missing ignore verdict would make its result
   *unsound* rather than merely noisier — e.g. a lint that reports only ignored
   files, where an empty set would be a false clean. Recorded so the member is a
   documented option rather than an untested branch; its own unit test exercises
   the propagating path.
4. **Degradation is representable.** The resolver returns
   `IgnoreResolution(ignored: tuple[Path, ...], degraded: bool, detail: str | None)`
   — a deterministically **sorted tuple**, not a `frozenset`, because a frozenset
   has no order and the spec requires ordering stable across processes. `degraded`
   lets `lint-agents-md` say "git unavailable" instead of falsely reporting
   `.gitignore` drift.
5. **Candidate domain is closed.** Candidates may be absolute-under-root or
   root-relative; anything resolving outside `repo_root` raises `ValueError` at the
   boundary. Git exits 128 with a *partial* result for an out-of-repo path, so
   forwarding one would silently under-report the entire batch.
6. **Context + findings, not globals.** `BoundaryContext` and `Finding` are frozen
   dataclasses; `inspect_boundary(context, checks=None) -> tuple[Finding, ...]` is
   the callable surface; the CLI is a thin format-and-exit shell.
7. **Confinement memo keyed by the unresolved normalised path.**
   `Path(os.path.normpath(str(base)))` — **not** `base.resolve()`. A resolved key
   collapses a symlink and its target into one entry, which loses the symlink
   refusal when the target is scanned first and falsely refuses the real tree when
   the link is scanned first: wrong in both directions and dependent on filesystem
   iteration order. Fail-closed outcomes are cached as refusals.
8. **The ignored-set is scoped to `_walk`.** `case_pack_tests_stay_in_pack` walks
   with a raw `os.walk` and deliberately inspects gitignored `.py` files; applying
   the batched set universally would newly exempt them from source confinement.

### Interfaces & contracts

```python
class MissingGitPolicy(enum.Enum):
    FAIL_OPEN = "fail-open"   # Git absent/unusable -> nothing ignored, degraded=True
    RAISE = "raise"           # Git absent/unusable -> propagate

@dataclass(frozen=True)
class IgnoreResolution:
    ignored: tuple[Path, ...]      # sorted; keyed to the caller's own objects
    degraded: bool                 # True iff git was absent/errored/timed out
    detail: str | None             # git stderr or the failure reason; never printed here

def git_ignored_paths(
    repo_root: Path,
    candidates: Iterable[Path],
    *,
    missing_git_policy: MissingGitPolicy,
    timeout: float,
) -> IgnoreResolution: ...
```

Properties: dedupe before invoking Git; deterministic sorted output; **zero**
subprocesses for an empty candidate set; exactly one otherwise; candidates over
stdin as `os.fsencode`d bytes, NUL-delimited, in a single `subprocess.run(...,
input=...)` call (which routes through `communicate()` and therefore cannot
deadlock on a payload larger than the pipe buffer); `--no-index` deliberately
absent; exit 0 and 1 normal; any other exit surfaced via `degraded`/`detail`;
`ValueError` for an out-of-root candidate or candidates spanning two Git roots;
no shell; prints nothing.

```python
@dataclass(frozen=True)
class BoundaryContext:
    root: Path                            # canonicalised once
    packs_root: Path
    recipe_path: Path
    projected_roots: tuple[Path, ...]
    runner_files: tuple[Path, ...]
    no_runner: Mapping[str, str]          # injectable; the 8 real entries by default

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

`no_runner` is in the context because `_NO_RUNNER`
(`tools/lint-pack-test-boundary.py:827`) is a module constant of eight real repo
paths; against a fixture root it would emit eight stale-exemption findings.
`_pack_test_escapes` takes the packs root as an argument rather than reading the
`PACKS` global, which otherwise makes every fixture pack test fail with
`test is not below packs/<pack>/`.

CLI: unchanged no-argument behaviour; adds repeatable `--check <name>` and
`--root <path>`. Either flag prints a partial-run header naming the checks that
ran and suppresses the `✓ … (6 cases).` line. An unrecognised name, or a
selection resolving to zero checks, exits non-zero naming the accepted set.

### Component / module decomposition

| Module | Role |
| --- | --- |
| `tools/lint_git_ignore.py` | batched resolver, `IgnoreResolution`, `MissingGitPolicy` |
| `tools/lint-pack-test-boundary.py` | context, inventory, six checks, callable API, CLI |
| `tools/lint-agents-md.py` | migrated probe batch (3 → 1) + degradation diagnostic |
| `tools/test-lint-git-ignore.py` | resolver unit tests |
| `tools/test-lint-no-direct-check-ignore.py` | AST source-enforcement gate |
| `tools/test-lint-pack-test-boundary.py` | 3-layer falsification suite |

### State & control flow

One invocation: canonicalise root → build context → build inventory (one pack
enumeration, one projection enumeration, one runner read+parse, one destination
build, one batched ignore resolution over the union of `_walk` candidates) → run
selected checks against that inventory, accumulating findings → CLI formats and
exits. The single batched ignore call happens during inventory construction, so
no check can reintroduce a per-path probe.

### Behavior & rules

All six check semantics are preserved verbatim, including every F1–F21 string,
their attribution, and the two-findings-for-one-missing-runner count. The
`evals/` skip and `_TRANSIENT` prune stay in the walk. Symlink and junction
handling is unchanged and still evaluated before any resolution. The batched
ignored-set applies **only** where `_walk` applies it today.

### Failure, edge cases & resilience

- Git absent, erroring, or timing out → `FAIL_OPEN` at both call sites returns
  `degraded=True` with an empty ignored set. The boundary lint reproduces today's
  "judge every file on disk"; `lint-agents-md` emits a git-unavailability
  diagnostic and exits 1, rather than three notes falsely blaming `.gitignore`.
- Non-0/1 Git exit → `degraded=True` with git's stderr in `detail`; never
  collapsed silently.
- Out-of-root candidate, or candidates spanning two Git roots → `ValueError`.
- Non-UTF-8 filename → handled by the bytes payload; cannot raise
  `UnicodeEncodeError`.
- Confinement resolution or key-computation error → cached refusal.
- `--root` missing, not a directory, a symlink/junction, unresolvable, or lacking
  `packs/` + the recipe → non-zero exit naming the path, before any traversal.

### Quality attributes (NFRs)

Bars are the spec's Acceptance Criteria: exactly one `check-ignore` process per
invocation (zero for an empty set), exactly one inventory construction, runner
files parsed once, ≥82 suite cases, four production-CLI launches, and the suite
completing inside the five-minute budget against the measured 306.4 s baseline.
Structural counts are asserted; wall clock is recorded as evidence only.

### Dependencies & integration

No new dependencies. Existing integration points unchanged
(`docs.yml:161,166`, `test-all.py:120,122`, `pre_pr_catalogue.py:113`); T2 adds
two new entries alongside them.

## Tasks

### T1: The batched resolver satisfies every enumerated ignore property

**Depends on:** none

**Touches:** tools/lint_git_ignore.py, tools/test-lint-git-ignore.py

**Tests:** (TDD — red first)
- empty candidates → empty `ignored`, `degraded=False`, and **zero** subprocesses
  (patched runner counts invocations).
- one ignored candidate; one non-ignored candidate.
- 500 candidates → exactly **one** subprocess.
- duplicates collapse before invocation (payload asserted duplicate-free).
- mixed ignored/non-ignored batch partitions correctly.
- **candidate domain:** absolute-under-root, root-relative, and non-existent
  candidates all resolve, and membership is testable with the **caller's own
  objects** (this is what `lint-agents-md`'s three relative, non-existent probes
  require).
- an out-of-root candidate raises `ValueError` naming the path; candidates
  spanning two Git roots raise `ValueError`.
- special filenames — space, tab, newline, Unicode, leading dash, **leading `:`,
  leading `!`** — round-trip correctly; the argv is asserted to contain **no**
  `:(literal)` prefix (this subcommand rejects it) and no `--no-index`.
- ordering: the returned tuple is sorted and identical across two separate
  **processes** (subprocess-launched, so hash randomisation is live).
- payload built via `os.fsencode`, parsed via `os.fsdecode`; a surrogate-escaped
  name does not raise `UnicodeEncodeError`. On-disk creation is skipped where the
  filesystem rejects the name (macOS APFS: `Errno 92`); the encode/decode path is
  asserted directly.
- delivery is a single `subprocess.run(..., input=...)`; asserted with a payload
  larger than the pipe buffer (≥1 MiB) so a `Popen`+`write`+`wait` shape that
  could deadlock cannot pass.
- Git exit 0 and exit 1 → `degraded=False`. Exit 128 → `degraded=True` with
  stderr in `detail`.
- `FileNotFoundError` and `TimeoutExpired` → `FAIL_OPEN` gives
  `degraded=True`, empty ignored; `RAISE` propagates.
- argv is a list; `shell=True` never appears; `timeout` is passed.
- the helper writes nothing to stdout or stderr.

**Approach:**
- Add `tools/lint_git_ignore.py`. Normalise each candidate to a root-relative
  POSIX path, retaining a map back to the caller's original object; dedupe
  order-preservingly; return early on empty.
- One `subprocess.run(["git","check-ignore","--stdin","-z"], input=payload,
  cwd=repo_root, capture_output=True, timeout=timeout)`; split stdout on `\0`;
  map back through the retained map; return a sorted tuple.
- Treat 0/1 as success; everything else and `OSError` through the policy.

**Done when:** `python3 tools/test-lint-git-ignore.py` exits 0 with every case
green.

### T2: A standing gate keeps `check-ignore` inside the approved helper

**Depends on:** T1

**Touches:** tools/test-lint-no-direct-check-ignore.py, .github/workflows/docs.yml, tools/test-all.py

**Tests:** (TDD)
- the gate fails on synthetic sources for **each** bypass shape:
  `["git","check-ignore",…]`; `["git","-C",root,"check-ignore",…]` (not at
  position 1); a list built through a variable/alias;
  `subprocess.run("git check-ignore …", shell=True)`; `os.system(...)`;
  `os.popen(...)`.
- the approved helper is exempt **and** is asserted present in the scanned
  inventory — so "exempt" cannot mean "never looked at".
- fixture strings used to test detection are not flagged.
- the scanned file count is asserted against a recorded floor, not merely
  non-empty.
- the gate passes on the tree once T3 and T5 land.

**Approach:**
- Scan every `*.py` under `tools/`, `packs/`, `packages/`, excluding test files by
  one explicit documented rule (basename matches `test-*`/`test_*`, or the path
  contains a `tests/` segment) and recording the exclusion count. Rationale for
  excluding tests: `tools/test-run-pack-evals.py:686` legitimately asserts a real
  `.gitignore` fact on a single path.
- Parse with `ast`; flag `check-ignore` anywhere in a resolved argv sequence, and
  any shell-string / `os.system` / `os.popen` construction containing it.
- Wire a `docs.yml` step and a `tools/test-all.py` entry next to the existing
  boundary-lint pair. `docs.yml` is outside `lint-ci-parity`'s scope
  (`tools/lint-ci-parity.py:92-95`), so no `STEP_DISPOSITION` entry is needed; a
  `build-check.yml` step would need one and is therefore not used.

**Done when:** `python3 tools/test-lint-no-direct-check-ignore.py` exits 0, exits
1 for each synthetic bypass, and both new wiring entries are present.

### T3: `lint-pack-test-boundary` runs six checks off one inventory with one batched ignore call

**Depends on:** T1

**Touches:** tools/lint-pack-test-boundary.py

**Tests:** (TDD)
- structural: one complete six-check invocation → exactly **one** inventory
  construction, exactly **one** `check-ignore` subprocess, each runner file parsed
  **once**, destination inventory built **once** — instrumented at the real
  boundaries, not source-matched.
- **failure count and attribution:** a fixture with one missing and one malformed
  runner file yields the same finding count, the same suppressed `ok` lines, and
  the same `✖ … N failure(s)` line as pre-change (F20, F21 attributed to **both**
  consuming checks).
- **every** F1–F21 string in `spec.md § Preserved failure contract` has a case.
- confinement memo: a fixture where one glob base is reached from several call
  sites scans it once; **and** a linked base plus its direct target each get their
  own verdict in **both** scan orders (link-first and target-first); a
  resolution/key error yields and caches a refusal.
- the ignored-set is not applied to `pack-tests-stay-in-pack`: a gitignored
  `packs/<p>/tests/test_x.py` that climbs above its pack still fails.
- `inspect_boundary` parses no arguments, calls no `sys.exit`, prints nothing
  (captured streams empty), mutates nothing (fixture tree hashed before/after).
- findings order deterministic across two processes.
- no-argument CLI emits all six `ok   [<check>]` lines in `main()`'s existing
  order plus `✓ lint-pack-test-boundary: passed (6 cases).`, exit 0 on the clean
  tree.
- `--check` accepts each of the six names, runs only that check, names which ran,
  and omits the six-check terminal line.
- an unrecognised `--check`, and a selection resolving to zero checks, exit
  non-zero naming the accepted set — from the CLI and as `ValueError` from the
  API. Never a zero-finding exit 0.
- `--root`: canonicalised once; a symlinked/junctioned root refused; an
  unresolvable root refused with `(OSError, RuntimeError)` handling; a root
  lacking `packs/` + recipe refused **before** traversal.
- under `--root`, the resolver's repo root is the fixture root, the fixture lives
  outside the real worktree, and a fixture-local `.gitignore` entry is asserted to
  come back ignored — proving the ignore layer resolved rather than degraded to a
  no-op.
- all non-vacuity refusals (F1, F3, F4, F5, F16) still fire against a
  deliberately empty fixture root.
- API/CLI parity: same fixture → same pass/fail decision.

**Approach:**
- Introduce `BoundaryContext` (incl. `no_runner`), `Finding`,
  `BoundaryInventory`; delete `FAILURES`; convert each `case_*` to a function
  taking the inventory and returning findings, preserving each `return`-after-hit
  and accumulate-then-guard shape.
- Build the inventory once: pack list, include list, pack skill dirs, projected
  skill dirs, `_walk` candidates, the **single** batched ignored set, pack test
  roots and Python test files, runner contents, parsed runner invocations, suite
  destinations, and the confinement memo. **No test basenames** — no check
  consumes them; `_test_basenames` stays a lazily-called helper for the suite.
- Pass the packs root into `_pack_test_escapes`; thread the memo through
  `_glob_tree_is_confined`.
- Keep `main()` as the formatter/exit shell.

**Done when:** `python3 tools/lint-pack-test-boundary.py` passes on the clean tree
with stdout byte-identical to the pre-change run, and the structural test asserts
one `check-ignore` process and one inventory build.

### T4: The falsification suite proves every plant from a fixture, with a four-launch real-tree layer

**Depends on:** T3

**Touches:** tools/test-lint-pack-test-boundary.py

**Tests:** (the suite *is* the test; these are its own invariants)
- **Layer 1, in-process, no CLI:** every matcher shape (`_MATCH`, `_NO_MATCH`,
  `_MATCH_DIR`, `_NO_MATCH_DIR`) and every path-provenance case currently
  asserted (parents index, negative index, dynamic index, parents alias, parents
  iteration, function-local alias, constructor alias, module-qualified alias,
  `abspath`, `cwd`/`getcwd`, lexical `..`, `joinpath`, multi-argument `Path`,
  dynamic segments, glob/rglob traversal, Windows segments, Windows glob, linked
  glob base, resolve error, `rev-parse --show-toplevel` direct and helper-shaped),
  plus workflow `working-directory` parsing with and without pytest. None removed.
- **Layer 2, fixture plants** — each builds a temporary catalogue of tens of files
  (including `.claude/skills` / `.agents/skills` projected roots and a
  fixture-local `.gitignore`), invokes **only** its target check, and asserts all
  four falsification properties:

  | Plant | Target check | F |
  | --- | --- | --- |
  | test file under `.apm/` | `apm-carries-no-tests` | F6 |
  | singular `test/` directory | `apm-carries-no-tests` | F6 |
  | allowed `evals/` content | `apm-carries-no-tests` (negative) | — |
  | transient dir (`__pycache__`) | `apm-carries-no-tests` (negative) | — |
  | test content in projection | `projection-carries-no-tests` | F7 |
  | pack in include list, no projected skill | `projection-carries-no-tests` | F5 |
  | empty `tests/` tree | `tests-live-in-the-pack-tree` | F8 |
  | pack test climbing above its pack | `pack-tests-stay-in-pack` | F12 |
  | gitignored pack test climbing above | `pack-tests-stay-in-pack` | F12 |
  | test not below `packs/<pack>/` | `pack-tests-stay-in-pack` | F13 |
  | unparseable pack test | `pack-tests-stay-in-pack` | F14 |
  | symlinked test source | `pack-tests-stay-in-pack` | F11 |
  | linked test dir / linked test root | `pack-tests-stay-in-pack` | F10, F9 |
  | one pytest command spanning two suites | `runners-keep-suites-isolated` | F15 |
  | suite dir named by no runner | `every-suite-dir-has-a-runner` | F18 |
  | stale `_NO_RUNNER` entry (injected map) | `every-suite-dir-has-a-runner` | F19 |
  | `_NO_RUNNER` entry a runner also names | `every-suite-dir-has-a-runner` | F17 |
  | missing runner file | both consuming checks | F20 |
  | malformed runner file | both consuming checks | F21 |
  | empty fixture root | non-vacuity | F1, F3, F4, F16 |

- **Preserved controls:** C1 (docx/pptx basename overlap still exists — a
  real-tree assertion) and C2 (a broad runner spanning `adapt-to-project` +
  `flow-metrics` fails and names **both** suites) are retained as named cases, per
  `spec.md § Preserved falsification controls`.
- **Layer 3, real tree, exactly 4 CLI launches:** clean tree passes the complete
  lint; one runtime-boundary plant detected and named; one runner-or-linked-tree
  plant detected and named; cleanup restores a passing tree. Each plant refuses to
  run if its target exists and cleans up in `finally`.
- the suite performs **no** write to the real `Makefile`, workflows, recipes or
  projected trees — asserted by hashing those paths before and after.
- reported case count ≥ **82**.

**Approach:**
- Add a fixture builder synthesising a minimal catalogue: `pack.toml`,
  `.apm/skills/<skill>/`, `tests/skills/<skill>/`, projected skill roots, a
  self-host recipe, a runner file, an injected `no_runner` map, and a
  fixture-local `.gitignore`. Fixture roots are created outside the real worktree.
- Route Layer-2 plants through `inspect_boundary` with an explicit check selection
  against the fixture root; keep Layer 3 on the real CLI.
- Delete both real-`Makefile` rewrites (lines 568, 606); the collision and
  undeclared-suite cases move to fixture runner files. C2 moves with them; C1
  stays a real-tree assertion.

**Done when:** `python3 tools/test-lint-pack-test-boundary.py` exits 0, reports
≥82 cases, launches the production CLI exactly 4 times, and the before/after
hashes of the real `Makefile` match.

### T5: `lint-agents-md` resolves its three probes in one batched call

**Depends on:** T1

**Touches:** tools/lint-agents-md.py

**Tests:** (TDD)
- the three session-scratch probes resolve in **exactly one** `check-ignore`
  process (patched-seam counter), down from three.
- a gitignored probe produces no note; a non-ignored probe produces the existing
  `drift-watch:` note naming it, with existing wording and fatal semantics.
- with Git absent / erroring / timing out (`degraded=True`), the lint exits 1 and
  emits a diagnostic naming **git unavailability**, and does **not** emit three
  `drift-watch:` notes claiming `.gitignore` drifted, and does not raise a
  traceback. This is the diff's one deliberate behaviour change and is asserted
  explicitly.
- checks 8, 10d, 10g still behave as their three existing self-tests assert.
- `tools/test-lint-ci-parity.py` still passes (aggregator anchor).

**Approach:**
- Replace the `for probe in (...)` subprocess loop
  (`tools/lint-agents-md.py:307-322`) with one `git_ignored_paths(...,
  missing_git_policy=FAIL_OPEN, timeout=…)` call over the three probes; branch on
  `degraded` first, then note each probe absent from `ignored`.
- Keep note wording and `note()`'s fatal semantics untouched.

**Done when:** `python3 tools/lint-agents-md.py` passes, its three self-tests
pass, and the process-count test asserts exactly one `check-ignore`.

### T6: Terminal gates pass, evidence and governance debt are recorded

**Depends on:** T2, T4, T5

**Touches:** docs/specs/lint-performance-p0/notes/lint-inventory.md, docs/specs/pack-test-boundary-remaining-packs/spec.md, workspace.toml

**Tests:** (goal-based check — each command run, actual exit code recorded)
- `tools/lint-pack-test-boundary.py`; `tools/test-lint-pack-test-boundary.py`
- `tools/test-lint-git-ignore.py`; `tools/test-lint-no-direct-check-ignore.py`
- `tools/lint-agents-md.py` + its three `test_lint_agents_md_*_block.py` suites
- `tools/test-lint-ci-parity.py`; `tools/test_build_gate_chain.py`;
  `tests/roster/test_core_pre_pr_hook.py`
- `agentbundle catalogue lint --deep`; `agentbundle catalogue verify`
- `python3 tools/catalogue/pre_pr_catalogue.py`
- `make lint-ruff` (mypy explicitly not claimed — see § Constraints)

**Approach:**
- Re-run the Wave-0 probes; write the after-column into
  `notes/lint-inventory.md § Baseline evidence` (the canonical home). Relativize
  every recorded path to the repository root — no absolute home-directory paths.
- Annotate `AC10a` in `docs/specs/pack-test-boundary-remaining-packs/spec.md` with
  the supersession note (stdin delivery replaces the `--` terminator; the
  argv-injection protection is strengthened, not lost), per
  `docs/CONVENTIONS.md § Superseding a frozen document`.
- Move `selftest-mutates-tracked-makefile` from `workspace.toml [backlog].open` to
  `[backlog].closed`.
- Run `make build-self` if any `packs/` file changed (expected: none).

**Done when:** every command above has run with its exit code recorded, the
after-evidence table is committed, `AC10a` carries its annotation, and the backlog
item is closed.

## Rollout

- **Delivery:** big bang, fully reversible — repo tooling only, no runtime
  artifact, no migration, no published interface. Rollback is `git revert`.
- **Infrastructure:** none.
- **External-system integration:** none. No new dependency; `git` is already
  required by every gate.
- **Deployment sequencing:** T1 before T3 and T5 (both consume the resolver); T3
  before T4 (the suite targets the new callable API); T2's tree assertion only
  passes once T3 and T5 have migrated, so it lands red and turns green within the
  wave.

## Risks

- **Behavioural drift hidden by a passing suite.** The six checks share subtle
  ordering, short-circuit and count behaviour — notably F20/F21's
  two-findings-from-one-cause. Mitigation: F1–F21 are enumerated canonically in
  the spec, each has a case, and the failure count and `ok`-line suppression are
  pinned.
- **Fixture catalogues that don't reproduce the real shape.** A plant proven only
  against a synthetic tree can pass while the real projection differs. Mitigation:
  Layer 3 keeps four real-tree launches; C1 stays a real-tree assertion; the
  non-vacuity refusals are asserted against an empty fixture.
- **`--root` turning a real gate vacuous.** The tempting fix for
  "no projected skills tree found" under a fixture is to relax the refusal.
  Mitigation: the fixture builder creates projected roots, and F1/F3/F4/F5/F16 are
  asserted to still fire.
- **The memo caching a stale or aliased refusal.** Mitigation: unresolved
  normalised key, order-independence asserted in both scan orders, per-invocation
  lifetime, no persistence.
- **`lint-agents-md` behaviour change.** Fail-open converts a Git-absent crash
  into exit 1 plus a git-unavailability diagnostic. Authorised and specced;
  asserted explicitly rather than left implicit.
- **Case-count regression.** Mitigation: ≥82 reported cases is a done-condition;
  the pre-change figures (82 runtime, 47 static sites) are recorded in the audit
  note before the diff lands.

## Changelog

- 2026-08-17 — Initial plan. Scope narrowed to the three files the task-zero audit
  measured as carrying a P0 pattern; the portable-`agentbundle` resolver dropped as
  caller-less; Git-missing policy unified to fail-open — all three on explicit
  human confirmation, recorded in `spec.md § Assumptions`.
- 2026-08-17 — Revised after pre-EXECUTE adversarial + security review (2 security
  Blockers, 11 adversarial Blockers, 21 Concerns/Nits; substantially all upheld).
  Material changes: `tools/lintlib/` package replaced by a flat
  `tools/lint_git_ignore.py` (the package contradicted the spec's own *no new
  module boundary* rail and would have been exempted-but-unscanned by the
  enforcement gate); confinement memo re-keyed from `base.resolve()` to the
  unresolved normalised path after a fixture probe proved the resolved key loses
  the symlink refusal in one scan order and falsely refuses the real tree in the
  other; return type changed from `frozenset` to a sorted tuple carrying an
  explicit `degraded` flag, so a Git-absent run cannot report `.gitignore` drift
  as the cause; candidate domain closed with `ValueError` for out-of-root paths
  after probing showed an out-of-repo candidate makes Git exit 128 with a
  *partial* result; payload moved to `os.fsencode` bytes; F1–F21 and C1/C2 made
  canonical in the spec to stop three drifting copies; `_NO_RUNNER` and the packs
  root moved into the context so fixture runs are possible at all; the two new
  gates wired into `docs.yml` + `test-all.py` rather than run once by hand.
  **Rejected one reviewer fix:** a `:(literal)` prefix to escape pathspec magic —
  probing showed `check-ignore --stdin` applies no pathspec magic (leading `:`/`!`
  round-trip verbatim) and rejects `:(literal)` outright, so the proposed fix
  would have broken every candidate.
- 2026-08-17 — Audit corrections folded in: the self-test census missed the 32
  underscore-named `tools/test_*.py` files (67 total, not 27); all were
  subsequently audited (0 `check-ignore`, 0 real-tree mutation) so the `CHANGE`
  scope is unchanged. The "≈6.5 min suite floor" estimate was withdrawn in favour
  of the measured 306.4 s. Recorded that
  `docs/specs/pack-test-boundary-remaining-packs/plan.md:636` already specified
  stdin batching and only its `--` terminator clause shipped; this spec completes
  it and supersedes that spec's `AC10a` wording. `make lint-mypy` dropped as a
  claimed gate — it type-checks nothing under `tools/`.
