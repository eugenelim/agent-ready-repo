# Spec: loop-engine repo-root memoisation

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0074
- **Contract:** none

## Outcome

An agent driving the work-loop engine waits on one `git rev-parse` per engine
invocation instead of three. A `wave-complete` transition spawns exactly one
child process, and the repo-root confinement boundary it resolves is the same
boundary it resolves today.

## What Changes

- `_get_repo_root()` caches its resolved root per process working directory —
  `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`
- Regression coverage for the cache's keying, its failure behaviour, its error
  surface, and the confinement boundary it backs —
  `packs/core/tests/skills/work-loop/test_loop_engine.py`
- Patch version bump and release entry — `packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`
- Eval contract record — `packs/core/.apm/skills/work-loop/evals/evals.json`
- Regenerated self-hosted projections — `.claude/skills/work-loop/scripts/`,
  `.agents/skills/work-loop/scripts/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Release history | Applicable — a non-cosmetic pack change bumps `core` | `docs/product/changelog.md` | work-loop author | A `## [core][<version>]` section | The section is the topmost released one, directly beneath `[Unreleased]`, and names the behaviour a consumer sees rather than the mechanism |
| Interface compatibility | Applicable — `packs/core/.apm/` is source, self-hosted into the repository-root adapter trees | `.claude/skills/work-loop/scripts/`, `.agents/skills/work-loop/scripts/` | `make build-self` (`agentbundle catalogue self-host --check`) | The target's parity report | All three copies of `loop-engine.py` are byte-identical |
| Reusable learning | Applicable — a pack eval record is owed on a non-cosmetic pack update | `packs/core/.apm/skills/work-loop/evals/evals.json` | work-loop author | The record names the changed behaviour | Record present; it is a contract record, not verification |
| Current architecture | Not applicable | — | — | — | `loop-infrastructure.md` describes the lock and its budget, neither of which moves |
| Decision rationale | Not applicable | — | — | — | No convention, contract, or published interface changes |

## Agent Rules

### Always do

- Key the cache on the process working directory, because `_get_repo_root`
  passes no `cwd=` and so resolves against it.
- Derive that key inside `_get_repo_root`'s existing
  `try`/`except (OSError, subprocess.TimeoutExpired)`, so every failure of the
  key computation leaves the function through the `ValueError` it already
  contracts.
- Keep the scrubbed-environment `git rev-parse` call as the only subprocess
  call in the function, with its existing `timeout=SUBPROCESS_TIMEOUT_S`.
- Re-run the lock-hold budget test by name after every edit to the engine.

### Ask first

- Any change to `MAX_SUBPROCESS_CALLS_UNDER_LOCK` or to the inequality it
  feeds.
- Any change to what `_resolve_spec_dir` accepts or rejects.

### Never do

- Cache a failed resolution. A cached `ValueError` turns one transient timeout
  into a permanent process-wide refusal.
- Let any exception type other than `ValueError` escape `_get_repo_root`. Every
  caller reaches it through a handler that catches only `ValueError`, and
  `main()` catches neither `OSError` nor its subclasses.
- Lower `MAX_SUBPROCESS_CALLS_UNDER_LOCK` to match observed runtime behaviour.
  It documents a static worst case that this change does not reduce.
- Restore a deliberately broken guard with `git checkout`, `reset`, or `stash`.
  The stash stack is shared across worktrees; restore by editing back.

## Testing Strategy

- Cache keying, cache hit, failure retry, and the `ValueError`-only error
  surface: **TDD**. Each is a compressible invariant over a single function
  with an injectable subprocess seam.
- Confinement under a cache hit: **TDD**, exercised by an **integration** test.
  It needs two resolutions in one process — the first populating the memo, the
  second answering from it — which no single call to `_resolve_spec_dir`
  produces.
- Per-invocation spawn count: **TDD**, exercised by an **integration** test.
  `cmd_transition` reaches `_get_repo_root` at two call sites — the one inside
  `_resolve_spec_dir` and the direct call before `_recover_pending` — along
  three edges, since
  `_resolve_spec_dir` runs both in the `_locked` decorator before the lock and
  again in the verb. Those three edges share the one `subprocess.run` site the
  budget arithmetic counts. No unit case over `_get_repo_root` alone sees them
  joined; `cmd_transition(args)` is the lowest seam that joins them, and the
  check drives `main()` so it also covers the entry point an operator invokes.

Two behaviours therefore need an integration surface: confinement under a cache
hit, and the per-invocation spawn count.
- Static lock-hold budget: **goal-based check**. The existing
  `test_lock_hold_budget` already derives the edge count from source; this
  spec re-runs it rather than adding a second counter.

## Acceptance Criteria

- [x] Two `_get_repo_root()` calls from one unchanged process working directory
      spawn one `git rev-parse` process in total.
- [x] `_get_repo_root()` called from a working directory whose repository root
      differs from a previously resolved one returns the root of the current
      working directory.
- [x] A `_get_repo_root()` call that raises `ValueError` leaves nothing cached:
      the next call from that same working directory spawns `git rev-parse`
      again.
- [x] `_get_repo_root()` raises `ValueError` — not `OSError` or any other
      type — when the process working directory cannot be read.
- [x] After a successful `_get_repo_root()` resolution has populated the cache,
      a second `--spec-dir` resolving outside the repository root, from that
      same unchanged process working directory, is still rejected.
- [x] One `wave-complete` transition driven through `loop-engine` `main()`
      spawns exactly one `git rev-parse` process.
- [x] `MAX_SUBPROCESS_CALLS_UNDER_LOCK` is `2` and `test_lock_hold_budget`
      passes, so the static subprocess-edge count reachable from
      `cmd_transition` is unchanged.

## Follow-ons

- work-loop author: `workspace.toml [backlog].open`, slug
  `loop-cohort-repo-root-uncached` — `loop-cohort.py` carries its own uncached
  `_get_repo_root`. It is not
  memoised here, and the two copies share one process whenever
  `_cohort_mutator()` loads it (`loop-engine.py`, reached from
  `cmd_transition`). Deferring it is safe because this change caches only
  successes and alters no refusal text, so the convergence
  `test_git_lookup_failure_refuses_boundedly_in_both_tools` pins between the two
  copies is untouched.

## Assumptions

- Technical: should the cache key cover the complement of
  `_GIT_OVERRIDE_VARS`? Today it covers the process working directory but not the
  complement of `_GIT_OVERRIDE_VARS` — `GIT_DISCOVERY_ACROSS_FILESYSTEM`,
  `GIT_CEILING_DIRECTORIES`, `GIT_COMMON_DIR` and the `GIT_CONFIG_COUNT`
  triple are neither scrubbed nor keyed, and neither is filesystem state above
  the working directory. A process that changed any of those between two calls
  from one working directory would read a stale root. The modules the engine
  loads in-process — itself, `_loop_guards.py`, `_statelock.py`, and
  `loop-cohort.py` via `_cohort_mutator()` — neither call `os.chdir` nor mutate
  `os.environ`, so no engine invocation reaches it; `lint-knowledge.py:338` in
  the same directory does call `os.chdir`, but the engine never loads it
  (settled by: a future writer extending the scrub set, the key, or the set of
  modules the engine loads in-process).
