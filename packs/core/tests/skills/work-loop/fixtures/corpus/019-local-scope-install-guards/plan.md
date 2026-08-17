# Plan: local-scope-install-guards

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `agentbundle/local_exclude.py` — `tracked_paths` helper (git already lives here).
- `agentbundle/commands/install.py` — `_local_preflight_refusal` + its call site.
- `tests/integration/test_local_scope_install.py` — seven new tests.
- `docs/specs/local-scope-install/spec.md`, version, both changelogs, `workspace.toml`.

**What demonstrates done**
- 16 integration tests; mutation revert; `make ci`.

**What I am NOT changing**
- The pack-level mutual exclusion (AC11/AC12) — still correct, just insufficient.
- Uninstall, or the exclude-block mechanics.
- Repo- or user-scope install behaviour.

## Security reasoning (inline — `security-reviewer` is a named skip)

- **Ownership / destructive-operation boundary.** Every case here ends in
  `uninstall` deleting a file this tool did not create. The guard is what makes
  the exact-restoration guarantee true rather than aspirational.
- **`path-and-file`.** AC2 is the subtle one: `git ls-files` without
  `--literal-pathspecs` interprets its arguments as pathspecs, so a projected
  path carrying a glob metacharacter silently checks the wrong thing. A guard
  that fails open on a crafted filename is worse than none, because callers stop
  looking.
- **Fail-closed ordering.** The pre-flight runs before the exclude block and
  before any write, so refusal is atomic by construction rather than by rollback.
  Rollback is the thing that goes wrong under a crash.
- **Not in scope.** This does not detect a path collision with a *user*-scope
  pack: RFC-0080 explicitly permits user/local coexistence, because user-scope
  files land in `~/.claude/` outside the working tree.

## Declined patterns

- **Tempted:** call `git ls-files --error-unmatch` per path, as the AC's
  parenthetical suggests. **Declined:** it exits non-zero on the first untracked
  path, so it cannot report the set, and it costs one subprocess per file. One
  batch `ls-files` and an intersection gives the whole answer.
- **Tempted:** treat byte-identical content as ownership, so reinstalls over a
  hand-copied file "just work". **Declined:** that is precisely the case AC10b
  calls out — uninstall would delete a file the user placed.
- **Tempted:** also refuse on user-scope path collisions, for symmetry.
  **Declined:** RFC-0080 permits user/local coexistence by design.
- **Tempted:** write first and roll back on conflict, reusing the existing
  rollback machinery. **Declined:** the no-footprint promise is strongest when
  nothing is written at all.

## Anchor-test sweep

- `tests/integration/test_local_scope_install.py` — nine existing tests, all
  still pass unchanged.
- Release-surface pins under `tests/roster/` — re-run after the bump.
- No test pinned `install.py`'s pre-flight ordering by line number.

## Verification log

- **AC1–AC8** 16 integration tests green against a real git repo.
- **AC9** mutation: replacing the refusal branch with `if False:` fails all four
  AC10 tests; restoring passes all 16.
- **AC11** 0.36.2 -> 0.37.0; both changelogs.
- One test bug found and fixed during the run: the no-footprint helper asserted
  the projected path was absent, but several cases refuse *because* a file is
  already there and it belongs to someone else. It now asserts only that nothing
  of ours was created.
- **REVIEW** `adversarial-reviewer` and `security-reviewer` = named skips.
