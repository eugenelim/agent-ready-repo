# Plan: lint-performance-p0

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Audit:** [`notes/lint-inventory.md`](notes/lint-inventory.md) — scope contract and single canonical home for all figures and counts. Not restated here.

## Approach

Seven tasks in four waves. The ordering constraint that shapes everything: **the
golden baseline must be captured from the unmodified lint before the refactor
touches it.** That is T2, and T4 cannot start until it lands.

- **Wave 1** — the resolver (T1) and the captured baseline (T2). Independent of
  each other; both prerequisites for everything after.
- **Wave 2** — the enforcement gate (T3), then the boundary-lint refactor (T4)
  proven against T2's baseline.
- **Wave 3** — the falsification suite (T5) and `lint-agents-md` (T6).
- **Wave 4** — the ADR, supersession, terminal gates and evidence (T7).

The refactor follows existing repository precedent: `tools/lint-ci-parity.py`
already pairs a `--root` option with fixture-root self-tests plus one real-root
end-to-end launch.

Four deliberate non-extractions. No universal linter framework. No
`CatalogueInventory` spanning the repository — the inventory is local to this
lint, carries only what its own checks consume, and is never persisted. One
resolver, not three — measurement found no portable or shipped-pack caller. And
it is a **flat module**, not a package: `tools/catalogue/` and `tools/repo/`
carry no `__init__.py`, so an importable `tools/lintlib/` would be the first
package under `tools/` and would collide with the spec's own rail.

## Constraints

- Repo-only helpers are flat modules under `tools/`; portable `agentbundle` must
  not import them, and shipped pack/skill content must not depend on them.
- Python standard library only.
- New `tools/` scripts are pure-stdlib Python `.py` (AGENTS.md § *New tool
  scripts*), and their `docs.yml` path triggers must match `python3 <script>`.
- `make lint-ruff` applies to every changed file. **`make lint-mypy` does not** —
  it targets only two `packages/` trees. Widening it is `Ask first`, not taken.
- Root `AGENTS.md` ≤ 250 lines; subdirectory `AGENTS.md` ≤ 150.

## Construction tests

Behaviour preservation is **not** enumerated here. `spec.md § Golden baseline` is
the contract, and T2 materialises it. Tasks reference the baseline, never a
hand-written expectation.

Anchors that must stay green and may not be edited to accommodate the diff,
cited by name rather than line so T3's insertions cannot stale them:

- `tools/test-lint-ci-parity.py` — its `run-call-extraction` check asserts the
  aggregator's extracted target set is exactly `{"tools/lint-agents-md.py"}`, so
  the `agents-md hygiene` `_run` line in `tools/catalogue/pre_pr_catalogue.py`
  must stay byte-stable.
- `tools/test_build_gate_chain.py` and `tests/roster/test_core_pre_pr_hook.py` —
  both pin `tools/lint-agents-md.py` into the gate chain and the pre-PR hook.
- `tools/test_lint_agents_md_{legacy,diataxis,risk}_block.py` — three
  fixture-based self-tests of unrelated checks in the same file.
- `tools/test-pre-pr.sh` — its sandbox is a real Git repository *specifically* so
  the drift-watch probe path can call `check-ignore`, and it asserts on the
  agents-md gate failing. T6 changes exactly that path.
- The existing `docs.yml` boundary-lint steps and `tools/test-all.py` entries —
  the precedent T3 follows.

## Design (LLD)

Shape is `service`; `ui` and `data` sub-sections pruned.

### Design decisions

1. **One resolver, repo-only, flat.** `tools/lint_git_ignore.py` exports
   `git_ignored_paths(...)`, `IgnoreResolution`, `MissingGitPolicy`. The
   `lint_*` name means T3's own `tools/` enumeration scans the file it exempts.
2. **`missing_git_policy` and `timeout` are both required keyword arguments,** so
   each call site states its ignore-failure posture and process bound in source.
3. **`RAISE`'s recorded trigger.** No production caller today. It is for a future
   lint where a missing ignore verdict makes the result *unsound* rather than
   noisier — e.g. one reporting only ignored files, where an empty set is a false
   clean. Its own unit test exercises the propagating path.
4. **Degradation is representable.**
   `IgnoreResolution(ignored: tuple[Path, ...], degraded: bool, detail: str | None)`
   — a sorted tuple, because a frozenset has no order and the spec requires
   ordering stable across processes. Both call sites must act on `degraded`; see
   decision 9.
5. **Containment is lexical, not resolved.** A candidate is in-root by lexical
   comparison against the canonical root. Using `resolve()` would make a
   symlinked candidate raise instead of producing the symlink finding the lint
   owes.
6. **Pathspec guard.** A candidate whose root-relative form begins with `:` is
   rejected at the boundary — `check-ignore --stdin` parses pathspec magic and
   fatals 128 with a partial echo, so one such candidate would zero the batch.
7. **Non-0/1 exits are hard errors, not policy.** Including the nested-Git-root
   fatal. Only Git absence, execution error and timeout route through
   `MissingGitPolicy`.
8. **Context + findings, not globals.** `BoundaryContext` and `Finding` are
   frozen dataclasses; `inspect_boundary(context, checks=None)` is the callable
   surface; the CLI is a thin format-and-exit shell.
9. **Degradation is fatal at both call sites.** Not cosmetic: `_walk` *subtracts*
   the ignored set, and existing findings fire on the *emptiness* of what
   remains, so an empty ignored set converts failures into passes. Git absence
   already behaves this way, but the new bounded timeout is a new silent route,
   so both sites diagnose and exit non-zero rather than reporting an
   ignore-derived verdict from an unresolved layer.
10. **Confinement memo keyed by the unresolved normalised path** —
    `Path(os.path.normpath(str(base)))`, **not** `base.resolve()`. A resolved key
    collapses a symlink and its target into one entry, losing the refusal in one
    scan order and falsely refusing in the other. **This divergence from decision
    5's sibling concern is intentional:** the memo key must stay lexical *and*
    unresolved; applying `resolve()` here reopens a confirmed Blocker.
11. **The runner parse is memoised, its findings are not.** The runner reader
    appends its own findings and is reached by two checks, so one missing or
    malformed runner file yields **two** findings today. `parse_runners` therefore
    returns `(lines, parse_findings)` and each consuming check re-appends
    `parse_findings`. One parse, two emissions — otherwise "parsed once" and
    "reproduce the baseline byte-for-byte" are mutually unsatisfiable.
12. **Every Git subprocess runs under a scrubbed environment.** Resolver calls
    and staged-lint calls alike. A `git init`-ed fixture still honours
    `core.excludesFile` and ambient `GIT_DIR`/`GIT_INDEX_FILE`, and this repo runs
    these lints from a pre-PR hook where Git sets both — so without scrubbing, a
    maintainer's global ignore file can capture non-vacuity failures as required
    passes.
13. **The `_NO_RUNNER` map and packs root move into the context.** Proven
    necessary: the unmodified lint staged into a fixture root emits one
    stale-exemption finding per real entry. The import-time `packs/` guard moves
    into `--root` canonicalisation so a fixture load does not trip it against the
    real root.

### Interfaces & contracts

```python
class MissingGitPolicy(enum.Enum):
    FAIL_OPEN = "fail-open"   # git absent/unusable -> empty ignored, degraded=True
    RAISE = "raise"           # git absent/unusable -> propagate

@dataclass(frozen=True)
class IgnoreResolution:
    ignored: tuple[Path, ...]      # sorted; keyed to the caller's own objects
    degraded: bool
    detail: str | None             # git stderr / failure reason; never printed here

def git_ignored_paths(
    repo_root: Path,
    candidates: Iterable[Path],
    *,
    missing_git_policy: MissingGitPolicy,
    timeout: float,
) -> IgnoreResolution: ...

@dataclass(frozen=True)
class BoundaryContext:
    root: Path                            # canonicalised once
    packs_root: Path
    recipe_path: Path
    projected_roots: tuple[Path, ...]
    runner_files: tuple[Path, ...]
    no_runner: Mapping[str, str]

@dataclass(frozen=True)
class CheckResult:
    check: str
    findings: tuple[Finding, ...]
    summary: str                          # the `ok   [check] (…)` payload

def build_inventory(context: BoundaryContext) -> BoundaryInventory: ...   # instrumentation seam
def parse_runners(context: BoundaryContext) -> RunnerIndex: ...           # instrumentation seam
def inspect_boundary(
    context: BoundaryContext,
    checks: Collection[str] | None = None,
) -> tuple[CheckResult, ...]: ...
```

`CheckResult.summary` exists because the CLI's six `ok` lines embed per-check
counters computed inside the checks; a bare `tuple[Finding, ...]` cannot carry
them and the golden comparison would fail on stdout. `build_inventory` and
`parse_runners` are named so the structural once-per-invocation counts have real
seams to instrument.

CLI: no-argument behaviour reproduces the real-tree golden baseline. Adds
repeatable `--check <name>` and `--root <path>`; either prints a partial-run
header and suppresses the six-check pass line. An unrecognised name or a
zero-resolving selection exits non-zero naming the accepted set.

### Component / module decomposition

| Module | Role |
| --- | --- |
| `tools/lint_git_ignore.py` | batched resolver, `IgnoreResolution`, `MissingGitPolicy` |
| `tools/lint-pack-test-boundary.py` | context, inventory, six checks, callable API, CLI |
| `tools/lint-agents-md.py` | probe batch (3 → 1) + degradation diagnostic |
| `tools/test-lint-git-ignore.py` | resolver unit tests |
| `tools/test-lint-no-direct-check-ignore.py` | AST source-enforcement gate |
| `tools/test-lint-boundary-golden.py` | golden capture/compare harness + fixture builders |
| `tools/lint-boundary-golden.json` | captured baselines (committed data) |
| `tools/test-lint-pack-test-boundary.py` | 3-layer falsification suite |

### State & control flow

One invocation: canonicalise root → build context → `build_inventory` (one pack
enumeration, one projection enumeration, one `parse_runners`, one destination
build, one batched ignore resolution over the union of walk candidates) → run
selected checks against that inventory → CLI formats and exits. The single
batched ignore call happens during inventory construction, so no check can
reintroduce a per-path probe.

### Behavior & rules

Check semantics are preserved by construction and verified by byte-identical
golden comparison. The batched ignored-set applies only where the current lint
applies it — at least one check walks with a raw `os.walk` and deliberately
inspects gitignored files.

### Failure, edge cases & resilience

- Git absent / erroring / timing out → `degraded=True`; both call sites diagnose
  and exit non-zero (decision 9).
- Non-0/1 exit, including nested-Git-root fatal → hard resolver error naming the
  path from stderr.
- Out-of-root or `:`-prefixed candidate → `ValueError`; each call site converts
  it to a named finding or diagnosed exit, never a traceback.
- Non-UTF-8 filename → handled by the bytes payload.
- Confinement resolution error → cached refusal; key-computation error → refusal
  without caching.
- `--root` missing, not a directory, symlinked, junctioned, unresolvable, or
  missing `packs/` **or** the recipe → CLI exits non-zero naming the path. The
  callable API accepts such a context so non-vacuity refusals stay testable.

### Quality attributes (NFRs)

Bars are the spec's ACs: exactly one `check-ignore` process per invocation (zero
for an empty set), one inventory construction, runners parsed once, byte-identical
golden reproduction, no case-count regression, and the suite inside the
five-minute budget. Structural counts asserted; wall clock recorded as evidence.

### Dependencies & integration

No new dependencies. Existing integration points unchanged; T3 adds entries
alongside them and into the unfiltered required gate chain.

## Tasks

### T1: The batched resolver satisfies every enumerated ignore property

**Depends on:** none

**Touches:** tools/lint_git_ignore.py, tools/test-lint-git-ignore.py

**Tests:** (TDD — red first)
- empty candidates → empty `ignored`, `degraded=False`, **zero** subprocesses.
- one ignored / one non-ignored candidate; mixed batch partitions correctly.
- 500 candidates → exactly **one** subprocess.
- duplicates collapse before invocation (payload asserted duplicate-free).
- candidate domain: absolute-under-root, root-relative, and non-existent
  candidates all resolve, membership testable with the **caller's own objects**.
- containment is lexical: a candidate reachable through a symlink does **not**
  raise; a lexically out-of-root candidate raises `ValueError` naming the path.
- a candidate whose root-relative form begins with `:` raises `ValueError`;
  `:!x` and `:(glob)x` are covered explicitly.
- special filenames — space, tab, newline, Unicode, leading dash, leading `!` —
  round-trip; argv asserted to contain no `:(literal)` and no `--no-index`.
- ordering: returned tuple sorted and identical across two separate
  **processes** (hash randomisation live).
- payload via `os.fsencode`, parsed via `os.fsdecode`; a surrogate-escaped name
  does not raise `UnicodeEncodeError`. On-disk creation skipped where the
  filesystem rejects it; the encode/decode path asserted directly.
- delivery is a single `subprocess.run(..., input=...)`, asserted with a ≥1 MiB
  payload so a `Popen`+`write`+`wait` shape cannot pass.
- exit 0 and 1 → `degraded=False`. Exit 128 → hard error carrying stderr, **not**
  policy-routed; a nested-Git-root fatal is covered.
- `FileNotFoundError` and `TimeoutExpired` → `FAIL_OPEN` gives `degraded=True`
  with empty `ignored`; `RAISE` propagates.
- argv is a list; `shell=True` never appears; `timeout` passed; nothing printed.

**Approach:** normalise each candidate to a root-relative POSIX path retaining a
map back to the caller's object; dedupe order-preservingly; return early on
empty; one `subprocess.run(["git","check-ignore","--stdin","-z"], input=…,
cwd=repo_root, capture_output=True, timeout=…)`; split stdout on `\0`; map back;
return sorted.

**Done when:** `python3 tools/test-lint-git-ignore.py` exits 0.

### T2: The current lint's behaviour is captured as a byte-exact baseline

**Depends on:** none — and it **must** land before T4 touches the lint.

**Touches:** tools/test-lint-boundary-golden.py, tools/lint-boundary-golden.json

**Tests:** (goal-based check — the harness is the artifact; these are its own invariants)
- the harness reads its capture subject from a **pinned Git revision**, not the
  working tree, so it stays regenerable after T4 lands.
- capture is byte-exact on stdout and stderr **separately**, plus exit code.
- three consecutive captures of the same root are identical (determinism gate).
- no captured stream contains an absolute path.
- every fixture root is `git init`-ed, and a fixture-local `.gitignore` entry is
  asserted to come back ignored — proving the ignore layer resolved rather than
  no-opped.
- regeneration is a separate explicit action (`--regenerate`) that the ordinary
  test path cannot trigger.
- the real-tree baseline is captured and stored.

**Approach:**
- Fixture builders synthesise minimal catalogues, one shape per behaviour: a
  clean pack; a test file under `.apm/`; a singular `test/` dir; allowed
  `evals/`; a transient `__pycache__`; test content in a projected skill; a pack
  in the include list with no projected skill; an empty `tests/` tree; a pack
  test climbing above its pack; a gitignored pack test climbing above; an
  unparseable pack test; a symlinked test source; a linked test dir; a linked
  test root; a runner spanning two suites; a suite named by no runner; a stale
  exemption; a missing runner file; a malformed **`.py`** runner file (the parse
  failure only arises in the Python runner path, not the workflow path); an
  empty include list; an include list with no projected root; and — the shape
  that proves ignore-subtraction still happens — **a `tests/` tree whose only
  content is gitignored**, which must still raise the empty-test-tree finding.
- **Two roots are deliberately not fixture shapes:** a root without `packs/` and
  a root without the recipe. Both trip an import-time refusal whose message
  embeds an **absolute** path, so their bytes are host-dependent and cannot be
  committed or reproduced. T4 proves those refusals by direct assertion on the
  CLI's exit code and relativized message instead.
- Each fixture supplies a minimal self-host recipe and the runner files, so a
  planted behaviour is isolated rather than buried under recipe and
  stale-exemption noise. Record in the spec which checks' *passing* output is
  pinned only by the real-tree capture.
- No fixture builder writes any `.py` into `<fixture>/tools/` beyond the staged
  subject and the resolver; the harness asserts this before running, because
  staging makes that directory the subject's `sys.path[0]`.
- Every link plant's target resolves strictly inside its own fixture root;
  fixture roots live outside the repository worktree; cleanup never follows a
  link or junction.
- Each non-vacuity refusal gets its **own** fixture shape, because several are
  mutually exclusive within one invocation — their checks return early.
- Stage `git show <sha>:tools/lint-pack-test-boundary.py` into
  `<fixture>/tools/` under a scrubbed Git environment, run it, record the triple
  base64-encoded into `tools/lint-boundary-golden.json` alongside the pinned
  40-hex SHA and the SHA-256 of the extracted blob. Verify the `git show` exit
  code before staging — a shallow clone returns 128 with empty stdout.
- Sort findings before forming the compared surface, and exclude any message
  embedding an interpreter-version-dependent string. Verify byte-determinism on
  the CI platform as well as the capture host.

**Done when:** `python3 tools/test-lint-boundary-golden.py` exits 0 against the
unmodified lint, and the committed JSON holds a baseline for the real tree and
every fixture shape.

### T3: A standing gate keeps `check-ignore` inside the approved helper

**Depends on:** T1

**Touches:** tools/test-lint-no-direct-check-ignore.py

**Tests:** (TDD)
- fails on synthetic sources for each bypass shape: `["git","check-ignore",…]`;
  `["git","-C",root,"check-ignore",…]` (not at position 1); a list built through
  a variable or alias; `shell=True` string; `os.system`; `os.popen`.
- a file it cannot read, decode or parse **fails** the gate naming the path —
  never skipped. A synthetic unparseable file covers it.
- exemptions are an explicit file allowlist, each entry carrying a reason; a
  filename *pattern* is asserted **not** to be used, because `tools/test-*.py`
  files are CI gates in this repository.
- the approved helper is asserted present in the scanned inventory and exempted
  there.
- the scanned set comes from `git ls-files` (tracked files only), asserted
  against the floor recorded in the audit note.
- the gate passes on the tree once T4 and T6 land.
- CI reachability: a change touching only a `tools/` or `packages/` Python file
  reaches both new gates.

**Approach:**
- Enumerate tracked `*.py` under `tools/`, `packs/`, `packages/` via
  `git ls-files`; parse with `ast`; flag `check-ignore` anywhere in a resolved
  argv sequence, or in a shell-string / `os.system` / `os.popen` construction.
- **CI wiring is deferred to T7**, deliberately: this gate only goes green once
  T4 and T6 land, so wiring it into the required chain during Wave 2 would leave
  `make build-check` red across a wave boundary.
- Record the non-Python surface (`.sh`, `Makefile`, workflow `run:`) as either
  textually covered or a knowingly accepted gap in the audit note.

**Done when:** the gate exits 0 on the migrated tree and 1 for every synthetic
bypass and for an unparseable file. (Chain membership is T7's done-condition.)

### T4: The refactored lint reproduces the golden baseline byte-for-byte

**Depends on:** T1, T2

**Touches:** tools/lint-pack-test-boundary.py, tools/test-lint-boundary-golden.py, tools/test-lint-boundary-structural.py

**Tests:** (TDD)
- **the golden comparison is the behavioural contract:** every baseline in
  `tools/lint-boundary-golden.json` is reproduced byte-for-byte on both streams
  with the same exit code, given the real `_NO_RUNNER` map. The `_NO_RUNNER`
  injection divergence documented in `spec.md § Golden baseline` is the only
  permitted difference.
- structural: one complete invocation → exactly one `build_inventory` call,
  exactly one `parse_runners` call, exactly one `check-ignore` subprocess, one
  destination build — instrumented at the named seams.
- confinement memo: one glob base reached from several call sites is scanned
  once; a linked base and its direct target each get their own verdict in
  **both** scan orders; a resolution error caches a refusal; a key-computation
  error yields a refusal without caching.
- degraded resolution (git absent, and separately a timeout) → the lint
  diagnoses git unavailability and exits non-zero; it does **not** emit an
  ignore-derived verdict from an unresolved layer.
- the ignored-set is not applied to the check that walks with raw `os.walk`: a
  gitignored pack test climbing above its pack still fails.
- `inspect_boundary` parses no arguments, calls no `sys.exit`, prints nothing,
  mutates nothing; findings deterministic across two processes.
- `--check` accepts each of the six names; an unrecognised name and a
  zero-resolving selection exit non-zero naming the accepted set, from CLI and
  API.
- `--root`: canonicalised once; symlinked/junctioned root refused; unresolvable
  root refused with `(OSError, RuntimeError)`; missing `packs/` **or** recipe
  refused by the CLI; the canonical form is what the resolver receives.
- the callable API accepts a context missing `packs/` or the recipe, so the
  non-vacuity refusals remain reachable.
- **injected `_NO_RUNNER`:** a fixture-supplied map produces the stale-exemption
  and unnamed-suite findings against that fixture's own destinations. This is the
  licensed divergence, so it is the one behaviour the baseline cannot check.
- the two uncaptured refusals (`packs/`-missing, recipe-missing) are asserted
  directly on the CLI's exit code and **relativized** message, since their
  captured bytes would embed an absolute path.
- the gitignored-only `tests/` tree fixture still raises the empty-test-tree
  finding, proving ignore-subtraction survived.
- fixture-root CLI launches are counted and bounded; the bound is recorded.

**Approach:** compare by co-staging the refactored lint **and**
`tools/lint_git_ignore.py` into each fixture root and invoking with no
arguments — `--root` cannot be the comparison path, because it prints a
partial-run header by design. Then introduce `BoundaryContext` (incl.
`no_runner`), `Finding`,
`CheckResult`, `BoundaryInventory`; delete `FAILURES`; convert each `case_*` to
a function taking the inventory and returning a `CheckResult`, preserving each
early-return and accumulate-then-guard shape. Build the inventory once, carrying
only what checks consume. Move the import-time `packs/` guard into `--root`
canonicalisation. Pass the packs root into the source-confinement analysis.
Thread the memo through the confinement scan. Keep `main()` as the
formatter/exit shell.

**Done when:** the golden harness reports every baseline reproduced, and the
structural test asserts one inventory build, one runner parse and one
`check-ignore` process.

### T5: The falsification suite proves each plant from a fixture

**Depends on:** T4

**Touches:** tools/test-lint-pack-test-boundary.py

**Tests:**
- **Layer 1, in-process, no CLI:** every matcher shape and every
  path-provenance case currently asserted, none removed — including the
  off-tree source-confinement case, which no fixture plant can reach because the
  walk only visits paths under a pack's test tree.
- **Layer 2, fixture plants:** each reuses T2's fixture builders, invoking only
  the check(s) it targets, asserting all four falsification properties. The
  missing- and malformed-runner cases deliberately select **both** consuming
  checks, because the two-findings-from-one-cause behaviour is only observable
  when both run.
- **Real-tree controls:** C1 and C2's precondition stay real-tree per
  `spec.md § Real-tree controls`; only C2's runner plant moves to a fixture.
- **Layer 3, real tree:** the four wiring outcomes, launch count recorded and
  bounded, each plant refusing to run if its target exists and cleaning up in
  `finally`.
- no write to the real `Makefile`, workflows, recipes or projected trees —
  asserted by hashing those paths before and after.
- reported case count no lower than the measured pre-change count in the audit
  note.
- `_walk` and `_test_basenames` remain callable without an inventory, since a
  real-tree control calls the latter directly.

**Approach:** reuse T2's fixture builders rather than duplicating them. Route
Layer-2 plants through `inspect_boundary` against a fixture root; keep Layer 3
on the real CLI. Delete both real-`Makefile` rewrites; those cases move to
fixture runner files.

**Done when:** the suite exits 0, reports no fewer cases than baseline, its
real-tree launch count matches the recorded bound, and the real `Makefile` hash
is unchanged.

### T6: `lint-agents-md` resolves its three probes in one batched call

**Depends on:** T1

**Touches:** tools/lint-agents-md.py

**Tests:** (TDD)
- the three probes resolve in **exactly one** `check-ignore` process.
- a gitignored probe produces no note; a non-ignored probe produces the existing
  note naming it, with existing wording and fatal semantics.
- degraded (git absent, and separately a timeout) → exits 1 and names **git
  unavailability**; does not emit three notes claiming `.gitignore` drifted; no
  traceback. This is the diff's one deliberate behaviour change.
- the three existing block self-tests pass.
- `tools/test-lint-ci-parity.py` passes (aggregator anchor).
- `bash tools/test-pre-pr.sh` passes — its sandbox exists precisely so this
  probe path can run against a real `.gitignore`.

**Approach:** replace the per-probe subprocess loop with one
`git_ignored_paths(..., missing_git_policy=FAIL_OPEN, timeout=…)`; branch on
`degraded` first, then note each probe absent from `ignored`. Keep note wording
and fatal semantics untouched.

**Done when:** the lint passes, all four dependent suites pass, and the
process-count test asserts exactly one `check-ignore`.

### T7: Governance debt is closed and terminal gates pass

**Depends on:** T3, T5, T6

**Touches:** docs/adr/, docs/specs/pack-test-boundary-remaining-packs/{spec,plan}.md, docs/specs/lint-performance-p0/notes/lint-inventory.md, workspace.toml, tools/repo/build_gate_chain.py, tools/test_build_gate_chain.py, .github/workflows/docs.yml, tools/test-all.py

**Anchor carve-out:** `tools/test_build_gate_chain.py` is listed in
§ Construction tests as an anchor. Appending the new gate steps requires updating
its exact ordered `EXPECTED_SCRIPT_STEPS` list. That specific update is
authorised — it records the new steps rather than accommodating a failure — and
is the **only** permitted edit to that file.

**Tests:** (goal-based check — each run, actual exit code recorded)
- `tools/lint-pack-test-boundary.py`; `tools/test-lint-pack-test-boundary.py`;
  `tools/test-lint-boundary-golden.py`
- `tools/test-lint-git-ignore.py`; `tools/test-lint-no-direct-check-ignore.py`
- `tools/lint-agents-md.py` + its three block self-tests
- `tools/test-lint-ci-parity.py`; `tools/test_build_gate_chain.py`;
  `tests/roster/test_core_pre_pr_hook.py`; `bash tools/test-pre-pr.sh`
- `agentbundle catalogue lint --deep`; `agentbundle catalogue verify`
- `python3 tools/catalogue/pre_pr_catalogue.py`
- `make lint-ruff` (mypy explicitly not claimed — see § Constraints)

**Approach:**
- Wire all three new gates — the resolver unit test, the AST source gate, and
  **the golden harness** — into the unfiltered required chain via
  `tools/repo/build_gate_chain.py`, plus `docs.yml`'s `paths:` and step list and
  a `tools/test-all.py` entry. The golden harness's job checks out at
  `fetch-depth: 0`, because `docs.yml`'s `actions/checkout` sets no depth and
  defaults to 1, which cannot resolve `git show <pinned-sha>:…`. Deferred here
  from T3 so the chain is never wired red across a wave boundary.
- Author an ADR recording the argv-terminator → stdin-batching reversal: the
  `--` terminator's protection is *strengthened*, not lost, because candidates
  leave argv entirely for NUL-framed stdin, which no option parser reads. Fill
  the assigned ADR number into `spec.md § Assumptions`.
- Annotate `docs/specs/pack-test-boundary-remaining-packs/spec.md` and its
  `plan.md` **only** in their `Status` fields, pointing at that ADR, per
  `docs/CONVENTIONS.md § Superseding a frozen document`. No body edit — an
  append is a body edit, and the AC text stays untouched.
- Re-run the Wave-0 probes; write the after-column into the audit note's
  canonical baseline section, relativized.
- Move `selftest-mutates-tracked-makefile` from `[backlog].open` to
  `[backlog].closed`.
- Run `make build-self` if any `packs/` file changed (expected: none).

**Done when:** every command has run with its exit code recorded, all three new
gates appear in the required chain and run on a PR touching only a `tools/` or
`packages/` Python file, the ADR exists with its number filled into the spec,
both `Status` fields carry the pointer with no body edit, the after-evidence is
committed, and the backlog item is closed.

## Rollout

- **Delivery:** big bang, fully reversible — repo tooling only, no runtime
  artifact, no migration, no published interface. Rollback is `git revert`.
- **Infrastructure:** none.
- **External-system integration:** none; `git` is already required by every gate.
- **Deployment sequencing:** T2 strictly before T4 — the baseline must come from
  the unmodified lint. T1 before T4 and T6. T4 before T5. T3's tree assertion
  turns green only once T4 and T6 land, so it lands red within its wave.

## Risks

- **Capturing a baseline that encodes a latent bug as required behaviour.** A
  golden test preserves whatever the lint does today, including anything wrong.
  Mitigation: the audit note records the two behaviours deliberately *not*
  preserved (the `_NO_RUNNER` injection, and degradation now being fatal), and
  any further difference is an `Ask first` spec amendment rather than a
  rebaseline.
- **Regenerating the golden file to make a failure pass.** The failure mode that
  turns a golden test into theatre. Mitigation: a `Never do` rail; regeneration
  is a separate explicit action; the subject is a pinned Git revision, so
  regeneration cannot silently pick up the refactored lint.
- **Fixtures that do not reproduce the real shape.** Mitigation: Layer 3 keeps
  real-tree launches, and C1 plus C2's precondition stay real-tree assertions
  precisely because their job is to detect real-tree drift.
- **The memo caching an aliased refusal.** Mitigation: unresolved lexical key,
  order-independence asserted in both scan orders, per-invocation lifetime.
- **`lint-agents-md` behaviour change.** Fail-open plus a fatal `note()` would
  misdiagnose git absence as `.gitignore` drift; the diff instead diagnoses
  unavailability. Authorised, specced, asserted explicitly.
- **T3's gate is only a drift guard.** An AST allowlist cannot close obfuscated
  argv construction (`"check-" "ignore"`, `shlex.split`, starred args).
  Mitigation: documented as such; the runtime process-count assertion carries the
  strong property.

## Changelog

- 2026-08-17 — Initial plan. Scope narrowed to the lints the task-zero audit
  measured as carrying a P0 pattern; the portable `agentbundle` resolver dropped
  as caller-less; Git-missing policy unified to fail-open — all on explicit human
  confirmation.
- 2026-08-17 — Revised after pre-EXECUTE review round 1 (13 Blockers). Package
  replaced by a flat module; memo re-keyed to the unresolved path after a fixture
  probe proved the resolved key loses the symlink refusal; return type changed to
  a sorted tuple carrying `degraded`; candidate domain closed. Rejected one
  reviewer fix — a `:(literal)` prefix — because probing showed this subcommand
  rejects it outright.
- 2026-08-17 — **Restructured after review round 2 (16 further Blockers).**
  Round 2 showed the failure mode was structural: the spec was encoding
  executable precision in prose — 22 failure strings with sites, exact failure
  counts, six mutually-exclusive non-vacuity shapes, a 20-row plant-to-check
  table — and each round's fixes introduced new contradictions (an
  `--root` precheck that made two refusals unreachable; a four-launch cap that
  conflicted with three other ACs; a `Never do` rail that forbade legitimate
  zero-finding fixture passes). On human direction the preserved-behaviour
  contract became **executable**: T2 now captures the unmodified lint's exact
  stdout/stderr/exit code against the real tree and staged fixtures, and T4 must
  reproduce it byte-for-byte. The prose enumeration is deleted. De-risked first:
  staging the lint into a synthetic root works, its output is root-relative with
  no absolute paths, and three consecutive runs are byte-identical on both
  streams. That probe also confirmed the `_NO_RUNNER` map must become injectable
  — the staged unmodified lint emits one stale-exemption finding per real entry.
  Round 2 also corrected: degradation is now **fatal** at both call sites,
  because `_walk` subtracts the ignored set and existing findings fire on the
  emptiness of what remains, so fail-open converts failures into passes; the
  pathspec assumption was wrong (`:!x`, `:(glob)x` and friends fatal 128 with a
  partial echo, so a `:`-prefixed candidate is now rejected at the boundary); the
  enforcement gate moves to the unfiltered required chain because `docs.yml` is
  `paths`-filtered and would not have fired; its exclusion rule becomes an
  explicit allowlist because a `test-*` pattern would exempt this repo's actual
  CI gates; it enumerates tracked files rather than the filesystem; and
  `tools/test-pre-pr.sh` was added to the census and to T6/T7 after review found
  it exercises the exact probe path T6 rewrites.
- 2026-08-17 — Governance route corrected: `CONVENTIONS.md § Superseding a frozen
  document` requires the pointer in the `Status` field **only**, citing an ADR
  rather than a spec, and forbids body edits including appends. Annotating the
  shipped spec's `AC10a` was therefore prohibited. T7 now authors an ADR and
  annotates only the two `Status` fields, on human direction.
- 2026-08-17 — Round 3 (15 further Blockers across both lenses) hardened the
  golden mechanism itself. On human direction the design-affecting findings were
  applied and the remaining bookkeeping/coverage findings folded into task test
  lists rather than a fourth prose round. Applied: the runner parse is memoised
  but its findings are re-emitted, because the reader is reached by two checks and
  parsing once would delete six findings from any baseline with a bad runner file
  — "parsed once" and "byte-identical" were otherwise mutually unsatisfiable; the
  `packs/`-missing and recipe-missing fixture shapes are **dropped**, because the
  import-time refusal embeds an absolute path and their bytes are unreproducible
  (those refusals are now proven by direct assertion); the comparison drive is
  co-staging the refactored lint plus the resolver and running argument-free,
  since `--root` prints a partial-run header by design and could never match;
  findings are sorted before comparison and interpreter-version-dependent text is
  excluded, because the walk returns filesystem order and three same-host runs
  proved neither that nor CPython-minor stability; every Git subprocess runs under
  a scrubbed environment after a probe showed a hostile `core.excludesFile`
  silently captures non-vacuity failures as required passes; the pin gained a
  40-hex SHA plus subject-blob hash and a `git show` exit-code check; baselines
  are stored base64 and compared as bytes; a fixture shape covering a
  gitignored-only `tests/` tree was added, being the one shape that proves
  ignore-subtraction survived; and all CI wiring — including the golden harness,
  which had none — moved to T7 with `fetch-depth: 0`, since T3 would otherwise
  wire a red gate across a wave boundary. Also corrected: the enforcement floor
  had been measured under the filename-pattern rule the spec forbids (≈763 under
  the allowlist, not 292); the allowlist now names `tools/test-run-pack-evals.py`
  and `tools/test-pre-pr.sh`; and the audit note's `lint-agents-md` row still
  described the drift-note behaviour the spec now forbids.

