# Plan: loop-engine repo-root memoisation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/AGENTS.md` § *Version bump rule* and
  § *Writing pack tests*; the in-source commentary under the
  `the lock-hold budget (ADR-0074 / spec/work-loop-in-process-guards AC22)`
  heading in `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`;
  `docs/architecture/loop-infrastructure.md` for the lock domains.
  Analogous implementations: `packs/core/tests/skills/work-loop/test_loop_concurrency.py`
  (`_subprocess_edges_under_lock`, the AST counter that pins the budget) and
  `packs/core/tests/skills/work-loop/test_loop_engine_no_child_python.py`
  (the `engine` fixture, the established pattern for loading the engine
  in-process inside a throwaway git repository). Named uncertainty: whether the
  static edge count moves — checked by running the counter, not assumed.

## Approach

Wrap the existing body of `_get_repo_root` in a module-level dict keyed on
`os.getcwd()`, deriving the key inside the function's existing `try` so the
`ValueError`-only error surface is preserved.

The process working directory is the input that varies in practice. It is not
the only input: `_GIT_OVERRIDE_VARS` scrubs five variables and leaves others
that also decide the answer, and filesystem state above the working directory
decides it too. Keying on the working directory covers the only one of those
that any caller here changes — no script under this directory calls `os.chdir`
or mutates `os.environ` — and it covers it without a reset hook, which an
in-process caller bypassing `main()` would miss.

Only a success is stored. The failure path keeps today's behaviour exactly —
every failing call spawns — which is what keeps the lock-hold worst case
unchanged and stops one transient timeout becoming permanent.

## Constraints

- The `subprocess.run` call stays inside `_get_repo_root` with its `timeout=`
  and its scrubbed `env=`, so all three AST scans over the engine source keep
  seeing the shape they assert on: the timeout scan and the edge counter in
  `test_lock_hold_budget`, and the `argv[0] == "git"` check in
  `test_only_git_runs_under_the_lock`.
- No new call edge from `cmd_transition`: the memo is a dict lookup in the
  existing function, not a new helper, so the static edge count stays 2.
- `packs/core/.apm/` is source; the repository-root `.claude/` and `.agents/`
  skill trees are self-hosted projections written by `make build-self`, never
  edited by hand.

## Construction tests

**Integration tests:** two — confinement under a cache hit (AC5, across
`_resolve_spec_dir`) and the per-invocation spawn count (AC6, across `main()`).
**Manual verification:** the measurement probe in T1's `Done when`, run on the
unchanged tree and again on the changed tree by the same method.

## Durable-output map

Conditions are stated once, in `spec.md` § *Durable Outputs*. This map carries
only ownership and where the evidence lands.

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Release history | T2 | The new section in `docs/product/changelog.md` | Per `spec.md` § *Durable Outputs*, row 1 |
| Three-copy parity | T2 | `make build-self` output | Per `spec.md` § *Durable Outputs*, row 2 |
| Eval record | T2 | The new entry in `evals/evals.json` | Per `spec.md` § *Durable Outputs*, row 3 |

## Design (LLD)

### Design decisions

**D1 — cache key is `os.getcwd()`, not unconditional.** *Owned by: T1.*
The alternatives were an unconditional module-level cache and a per-invocation
reset. An unconditional cache is wrong the moment anything changes directory
mid-process, and the pack's own harnesses do exactly that: they load engine
modules by path, in-process, across different temporary repositories. A
per-invocation reset only covers callers that enter through `main()`, and
`test_contract_amendment_wave4.py:252` calls `cmd_transition` directly. Keying
on the working directory covers both, and costs one `getcwd` syscall per call.

The key is derived inside the function's existing
`try`/`except (OSError, subprocess.TimeoutExpired)`. `os.getcwd()` raises
`FileNotFoundError` when the working directory has been unlinked, and
`_resolve_spec_dir` catches only `ValueError` while `main()` catches only
`GuardsUnavailable`/`KeyboardInterrupt` — so a key derived above that `try`
would leave the function as an unhandled traceback printing absolute internal
paths, which is what the comment at the `raise ValueError` in
`_get_repo_root` exists to prevent.
An absolute `--spec-dir` reaches it, because `Path(raw).resolve()` does not
touch the working directory and so does not fail first.

**D2 — successes are cached, failures are retried.** *Owned by: T1.*
`_get_repo_root` raises `ValueError` on a non-zero exit, empty output, `OSError`
or `TimeoutExpired`. Caching that would convert a transient failure — a timeout
under load, a momentarily unreadable git directory — into a permanent refusal
for the life of the process, which is strictly worse than today. Retrying
instead means the failure path spawns exactly as often as it does now, so the
`SUBPROCESS_TIMEOUT_S x MAX_SUBPROCESS_CALLS_UNDER_LOCK` arithmetic continues
to bound the real worst case without being touched.

**D3 — the lock-hold budget constant does not move.** *Owned by: T1.*
`_subprocess_edges_under_lock` is a static AST walk that resolves callees and
sums per-call subprocess counts. A runtime memo changes no call site and adds
no edge, so the count stays 2. This is checked by running the counter, not
asserted: if it did move, the constant and `test_lock_hold_budget` would move
together and the test names that in its own failure message.

### Failure, edge cases & resilience

- Concurrent callers within one process: the engine is single-threaded and the
  worst case of a benign race is a duplicate `git rev-parse`, never a wrong
  root. No lock is added.
- A monkeypatched `_get_repo_root` (used by `test_contract_amendment_wave4.py`
  and `test_loop_cohort.py`) replaces the function wholesale and never reaches
  the cache, so those fixtures are unaffected.
- `test_loop_engine.py` loads one engine module at import, and only its
  `tmp` fixture chdirs into a throwaway repository. A case taking `tmp_path`
  alone therefore resolves against the repository's own working directory and
  would share one memo entry with every other such case, for the life of the
  file. Each case below loads its own engine instance through `_fresh_engine`
  and chdirs explicitly, so none of them shares a key.
- The root's highest-consequence consumers are `_resolve_spec_dir`'s
  confinement check and `cmd_reset`'s `shutil.rmtree` of `.loop-run/`
  (`cmd_reset`). Both are reached once per process in production,
  where one invocation runs one verb; the memo is populated by that verb's own
  first call, so neither can read a root resolved for a different directory
  outside an in-process harness.

### Quality attributes (NFRs)

Traces to the criterion that one `wave-complete` transition spawns exactly
one `git rev-parse` process. The observable bar is the
spawn count, not a wall-clock threshold: a timing criterion would become a
standing test that fails on a loaded machine. The measured latency is recorded
as PR evidence instead.

## Tasks

### T1: `_get_repo_root` resolves once per working directory

**Depends on:** none

**Tests:** all six land in
`packs/core/tests/skills/work-loop/test_loop_engine.py`.

| Test function | AC | stub |
| --- | --- | --- |
| `test_get_repo_root_resolves_once_per_working_directory` | AC1 | `stub: true` |
| `test_get_repo_root_follows_the_working_directory` | AC2 | `stub: true` |
| `test_get_repo_root_does_not_cache_a_failure` | AC3 | `stub: true` |
| `test_get_repo_root_raises_value_error_on_an_unreadable_cwd` | AC4 | `stub: true` |
| `test_confinement_rejects_an_out_of_tree_spec_dir_on_a_cache_hit` | AC5 | `stub: true` |
| `test_one_transition_spawns_one_rev_parse` | AC6 | `stub: true` |
| AC7 | AC7 | `no stub (goal-based)` — `test_lock_hold_budget` already owns it |

```python
# ── repo-root memoisation ──────────────────────────────────────────────────


def _fresh_engine(name: str):
    """A private engine module instance, so one case's cache cannot reach another.

    The module-level `_engine` is loaded once at import in the repository working
    directory. These cases chdir between throwaway repositories, so sharing that
    instance would make a green result depend on which case ran first.
    """
    spec = importlib.util.spec_from_file_location(name, str(ENGINE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rev_parse(calls):
    """Only the `git rev-parse` spawns.

    `mod.subprocess` is the same module object the test itself imports, so a
    patch on it counts every spawn in the process — including a fixture's own
    `git init`. Filtering here is what keeps these counts about the memo.
    """
    return [c for c in calls if "rev-parse" in " ".join(c)]


def _counting_spawns(mod):
    """Count subprocess spawns while patched; return (calls, restore)."""
    calls = []
    real = mod.subprocess.run

    def counting(cmd, *a, **kw):
        calls.append(tuple(cmd) if isinstance(cmd, (list, tuple)) else (cmd,))
        return real(cmd, *a, **kw)

    mod.subprocess.run = counting
    return calls, (lambda: setattr(mod.subprocess, "run", real))


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True)
    return path


# STUB: AC1
def test_get_repo_root_resolves_once_per_working_directory(tmp_path, monkeypatch):
    """Spec: docs/specs/loop-engine-repo-root-memo/spec.md AC1"""
    repo = _init_repo(tmp_path / "a")
    mod = _fresh_engine("_engine_ac1")
    calls, restore = _counting_spawns(mod)
    try:
        monkeypatch.chdir(repo)
        first = mod._get_repo_root()
        second = mod._get_repo_root()
        assert second == first, f"second call returned {second}, first {first}"
        seen = _rev_parse(calls)
        assert len(seen) == 1, (
            f"two calls from one unchanged working directory spawned {len(seen)} "
            f"`git rev-parse` processes, want 1: {seen}"
        )
    finally:
        restore()


# STUB: AC2
def test_get_repo_root_follows_the_working_directory(tmp_path, monkeypatch):
    """Spec: docs/specs/loop-engine-repo-root-memo/spec.md AC2"""
    repo_a = _init_repo(tmp_path / "a")
    repo_b = _init_repo(tmp_path / "b")
    mod = _fresh_engine("_engine_ac2")
    calls, restore = _counting_spawns(mod)
    try:
        monkeypatch.chdir(repo_a)
        mod._get_repo_root()
        monkeypatch.chdir(repo_b)
        assert mod._get_repo_root() == repo_b.resolve(), (
            "after chdir the cache handed back the previous repository's root — "
            "a silent wrong answer feeding _resolve_spec_dir's confinement check"
        )
        assert len(_rev_parse(calls)) == 2, (
            f"a new working directory must re-resolve: {_rev_parse(calls)}"
        )
    finally:
        restore()


# STUB: AC3
def test_get_repo_root_does_not_cache_a_failure(tmp_path, monkeypatch):
    """Spec: docs/specs/loop-engine-repo-root-memo/spec.md AC3"""
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    mod = _fresh_engine("_engine_ac3")
    calls, restore = _counting_spawns(mod)
    try:
        monkeypatch.chdir(outside)
        with pytest.raises(ValueError):
            mod._get_repo_root()
        _init_repo(outside)
        assert mod._get_repo_root() == outside.resolve(), (
            "a remembered failure made a now-resolvable directory permanently "
            "unresolvable for the life of the process"
        )
        assert len(_rev_parse(calls)) == 2, (
            f"the retry must re-spawn: {_rev_parse(calls)}"
        )
    finally:
        restore()


# STUB: AC4
def test_get_repo_root_raises_value_error_on_an_unreadable_cwd(tmp_path, monkeypatch):
    """Spec: docs/specs/loop-engine-repo-root-memo/spec.md AC4"""
    gone = tmp_path / "deleted"
    _init_repo(gone)
    mod = _fresh_engine("_engine_ac4")
    monkeypatch.chdir(gone)
    shutil.rmtree(gone)
    try:
        mod._get_repo_root()
    except ValueError:
        pass
    except OSError as exc:
        pytest.fail(
            f"_get_repo_root raised {type(exc).__name__}, not ValueError. Every "
            "caller reaches it through a handler that catches only ValueError and "
            "main() catches neither, so this exits as a path-disclosing traceback."
        )
    else:
        pytest.fail("an unreadable working directory must not resolve")


# STUB: AC5
def test_confinement_rejects_an_out_of_tree_spec_dir_on_a_cache_hit(tmp_path, monkeypatch):
    """Spec: docs/specs/loop-engine-repo-root-memo/spec.md AC5"""
    repo = _init_repo(tmp_path / "repo")
    inside = repo / "docs" / "specs" / "demo"
    inside.mkdir(parents=True)
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    mod = _fresh_engine("_engine_ac5")
    calls, restore = _counting_spawns(mod)
    try:
        monkeypatch.chdir(repo)
        assert mod._resolve_spec_dir(str(inside)) == inside.resolve()
        populated = len(_rev_parse(calls))
        with pytest.raises(ValueError, match="inside the repository"):
            mod._resolve_spec_dir(str(outside))
        assert len(_rev_parse(calls)) == populated, (
            "the second resolution re-spawned, so it was a cache miss and this "
            "case proves nothing about confinement under a cache hit"
        )
    finally:
        restore()


# STUB: AC6
def test_one_transition_spawns_one_rev_parse(tmp, monkeypatch):
    """Spec: docs/specs/loop-engine-repo-root-memo/spec.md AC6"""
    spec_dir = _drive_to_code_implementation(tmp, "memo-transition")
    mod = _fresh_engine("_engine_ac6")
    calls, restore = _counting_spawns(mod)
    argv = sys.argv
    try:
        sys.argv = ["loop-engine.py", "transition", str(spec_dir), "wave-complete"]
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                mod.main()
            except SystemExit as exc:
                assert exc.code in (0, None), f"wave-complete exited {exc.code}"
    finally:
        sys.argv = argv
        restore()
    rev = _rev_parse(calls)
    assert len(rev) == 1, (
        f"one wave-complete transition spawned {len(rev)} `git rev-parse` "
        f"processes, want 1: {rev}"
    )
    assert calls == rev, f"a non-git child was spawned under the lock: {calls}"
```

**Validation (recorded 2026-09-22, disposable scratch, copy removed).**
`python3 -m py_compile`: PASS. Intended-red pass against the unchanged engine:
**3 failed, 3 passed**.

- Genuinely red, so falsifiable against a missing implementation: AC1 (two
  calls spawn 2, want 1), AC5 (the second resolution re-spawns, so it is a
  cache miss), AC6 (one transition spawns 3, want 1).
- Green before the change, by construction: AC2, AC3 and AC4 are the
  pure-exclusion and invariant criteria `tdd-stubs.md` § *Earning a red*
  describes — nothing caches yet, so nothing can go stale, remember a failure,
  or raise the wrong type. They are paired with AC1, which is the positive
  case that makes the set falsifiable, and they are what catches a memo that
  caches unconditionally, caches failures, or derives its key outside the
  `try`.
- One defect the red pass caught and fixed before approval: `mod.subprocess`
  is the same module object the test file imports, so patching
  `mod.subprocess.run` counts every spawn in the process, including a
  fixture's own `git init`. `_rev_parse()` filters the counts to the calls the
  criteria are about.

**Done when:** the six tests above are green; `test_lock_hold_budget` and
`test_only_git_runs_under_the_lock` still pass;
`MAX_SUBPROCESS_CALLS_UNDER_LOCK` is still `2`; and the measurement probe
reports fewer `git rev-parse` calls per `wave-complete` transition on the
changed tree than the figure the same probe derives from the unchanged tree.

The probe drives a real run to `CODE-IMPLEMENTATION` through the CLI, then
executes the final `wave-complete` in-process with `subprocess.run` wrapped to
count and time every spawn, reporting the median over eleven repetitions. Both
figures are derived by running it; neither is stored here. The before and after
readings are execution observations and go to `notes/verification-ledger.md`.

### T2: the pack ships the change

**Depends on:** T1

**Tests:** no stub (goal-based).

**Done when:** `packs/core/pack.toml` and
`packs/core/.claude-plugin/plugin.json` both read the next patch above the
published `core` version, re-derived from a fresh `git fetch origin` immediately
before pushing; `docs/product/changelog.md` carries a `## [core][<that same
version>]` section directly beneath `[Unreleased]`;
`evals/evals.json` names the changed behaviour; and `make build-self` reports
three-copy parity for `loop-engine.py`.

## Rollout

- **Delivery:** big bang, within one pack patch release. Reversible by
  reverting the commit; no persisted state, schema, or on-disk format changes.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none — T2's projections are regenerated from T1's
  source in the same commit.

## Risks

- A harness that holds one engine module across two working directories would
  read a stale root under an unconditional cache. Mitigated by D1; the risk is
  retired by the second acceptance criterion, not by inspection.
- The version bump collides silently if another branch ships the same patch
  version first.
  Mitigated by re-deriving the version from a fresh `git fetch origin`
  immediately before pushing.

## Changelog

- 2026-09-22 — Drafted.
- 2026-09-22 — Revised from the pre-EXECUTE review's twelve sustained findings.
- 2026-09-22 — Revised again from the round-2 adversarial review's fifteen
  findings. Stubs regenerated per `tdd-stubs.md`, compiled, and red-proven.
- 2026-09-22 — Owner waived further pre-EXECUTE review rounds after two rounds
  produced 31 findings, all against spec and plan prose and none against the
  change. Round 2's findings were applied without a `finding-adjudicator` pass;
  that deviation is recorded rather than repaired, and post-GATES review is
  unaffected.
- 2026-09-22 — Spec approved by the owner.
- 2026-09-22 — Plan approved by the owner.
- 2026-09-22 — Implemented; post-GATES review applied two blockers, three
  concerns and two nits over two rounds.
