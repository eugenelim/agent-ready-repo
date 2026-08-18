# Spec: loop-tooling-hygiene

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none — no public interface. One CI posture assertion is added; two
  loader/subprocess call sites are bounded.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full (work-loop). Risk trigger that fired: security boundary — AC1 touches
the bytecode path of the module that implements the state lock, and AC3 touches the
posture test guarding the sole required status check. Adversarial review is a NAMED
SKIP (operator disabled subagent dispatch); mutation evidence per criterion stands in
for it. -->

## Objective

Three one-or-two-line hardening items whose entries each say, in so many words, that
the fix is determined and the only reason they were deferred is that they fell outside
their parent PR's touched area. They are taken together because all three are
loop/CI tooling hygiene with no shared logic and no shared risk.

## Acceptance Criteria

- [x] **AC1 — the `_statelock.py` loaders stop writing and reading `__pycache__`.**
  Both `importlib` loaders (`loop-engine.py` and `loop-cohort.py`) set
  `sys.dont_write_bytecode` across the load and restore it to its **prior** value, not
  unconditionally to `False` — mirroring the `_loop_guards` loader that already sits a
  few hundred lines above in `loop-engine.py`.

  Why it matters more here than for a guard: a poisoned or stale `.pyc` executes
  inside the **lock-holding** engine process, and one that made `exclusive()` a no-op
  would admit a second writer while both believe they hold the lock.

  Measured, both directions, in a scratch copy so the real tree stays clean:

  | Load | `.pyc` written |
  | --- | --- |
  | without `dont_write_bytecode` | 1 — `_statelock.cpython-313.pyc` |
  | with it | 0 |

  Frame: taken in a shell where `PYTHONDONTWRITEBYTECODE` was **unset** — which the
  "without" row's non-zero result confirms, since the env var would otherwise have
  masked the difference and made the fix look like a no-op.

- [x] **AC2 — `loop-cohort.py`'s `run_git` is bounded.**
  `timeout=GIT_TIMEOUT_S` (20.0, deliberately the same number as `loop-engine.py`'s
  `SUBPROCESS_TIMEOUT_S`, though the two scripts share no module).

  Honest scope, recorded in the docstring rather than implied: this helper has **no
  callers** — verified repo-wide — and is unreachable while the engine holds its lock,
  so it sits outside that budget's arithmetic and `MAX_SUBPROCESS_CALLS_UNDER_LOCK` is
  unchanged. It is bounded because it is the nearest copy-paste hazard to the guard
  extraction site. `TimeoutExpired` is left to propagate: every entry point is a CLI
  verb that already turns an exception into a non-zero exit, and swallowing it would
  invent a "git timed out so we continued" path no caller asked for.

- [x] **AC3 — a work job's `name:` is pinned to its job id.**
  `tools/test-build-check-workflow.py` gains a parameterised
  `job-name-is-id[<job>]` assertion inside the existing `for job_id in work_jobs`
  loop, plus one mutation. `_family` collapses it to **one** family covering every
  work job present and future.

  Why: branch protection requires a check by **name**. Renaming `gate-credbroker`'s
  `name:` to anything else passed every one of the previous 77 assertion families, all
  177 mutations, and `lint-ci-parity` — while the required check never reports and
  every PR pends forever. It fails loud (PRs visibly hang) rather than silently green,
  which is why this is availability rather than a security bypass.

  `[]` is accepted alongside `[job_id]`: with no `name:` key GitHub displays the job
  id, so an absent key is already correct. Otherwise exactly-one-value semantics, so a
  **duplicate** `name:` fails too. The aggregator is the deliberate exception (id
  `build-check`, name `make build-check`); it is excluded because `work_jobs` excludes
  it, and `one-required-name` + `required-name-is-aggregator` already pin it.

  Suite goes **77 → 78 families, 177 → 178 mutations**.

- [x] **AC4 — the baseline fixture is made shape-representative for this property.**
  `tools/fixtures/build-check-good.yml` declared **no** `name:` key on any work job
  while the real `build-check.yml` declares `name: <id>` on all four. So the fixture
  could not prove AC3's assertion against production's mechanism — the exact drift its
  own docstring warns about ("SHAPE-REPRESENTATIVE of the real workflow, not merely
  valid"). Discovered by AC3's mutation reporting `transform was a no-op — proves
  nothing`, which is the harness catching the author.

  The key is inserted **after `timeout-minutes:`**, not directly after the job id.
  Placing it first broke four unrelated mutations that rely on
  `  <job>:\n    runs-on: …` adjacency — the same replace-string fragility the file's
  own § *Any script claiming a payload was blocked* documents. Mapping key order is
  irrelevant to YAML and to every assertion.

- [x] **AC5 — AC3 is proved against the real workflow, not only the fixture.**
  Renaming `gate-credbroker`'s `name:` in the actual `.github/workflows/build-check.yml`
  produces `✖ 1 posture violation(s): job-name-is-id[gate-credbroker]` at exit 1;
  reverting returns exit 0 with the file byte-identical. The self-test's fixture
  mutation proves the assertion is wired; this proves it fires on the artifact that
  actually gates merges.

- [x] **AC6 — the projections are regenerated.**
  `packs/core/.apm/skills/work-loop/scripts/**` is the source; `.claude/` and
  `.agents/` are projections. `make build-self` re-renders both, and the diff carries
  all three copies of each edited file.

  `FORCE=1` is required: `catalogue self-host --write` refuses on a dirty tree, and the
  source edit necessarily dirties it. That is the documented escape for exactly this
  sequence, not a workaround.

## Boundaries

**Never do**

- Bound `lint-spec-status.py`'s four `git` calls. That is
  `lint-spec-status-git-unbounded`, and its entry states plainly that it is *not* a
  mechanical ride-along: it is an observable change to a shipped CLI's failure mode on
  a slow repository and needs its own criterion.
- Change `MAX_SUBPROCESS_CALLS_UNDER_LOCK` or `SUBPROCESS_TIMEOUT_S`. AC2 adds no
  edge to the locked call graph; the budget arithmetic is untouched.
- Restore `sys.dont_write_bytecode` to `False` instead of its prior value. A caller
  that set it deliberately must not have it cleared underneath them.
- Hand-edit `.claude/` or `.agents/` copies. They are generated (AC6).

## Assumptions

1. **`GIT_TIMEOUT_S = 20.0` needs no derivation.** It matches the engine's existing
   constant. The two scripts share no module, so this is a deliberate duplicate with a
   comment saying so rather than a false abstraction.
2. **The fixture change breaks no other assertion.** Verified by the full self-test:
   baseline clean, 178 mutations each caught, every one of 78 families mutated.
3. **`run_git` remains uncalled.** Verified repo-wide at implementation time. If a
   caller appears, the `TimeoutExpired` propagation decision in its docstring is the
   thing to revisit.
