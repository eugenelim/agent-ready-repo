# Spec: unify-path-jail-projection-probe

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none — internal refactoring within `packages/agentbundle`; no RFC, no ADR, no external interface change
- **Brief:** none
- **Discovery:** none
- **Contract:** none — no REST, event, or RPC surface; pure Python internal API
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Mode: full** — risk trigger: *structural change* (new public helper in `safety.py`; three call sites migrated; upgrade non-dry-run pre-flight behavior changes from per-file mid-write to whole-projection pre-flight).

## Objective

Three sites in the agentbundle codebase each implement the same two-step prefix-jail check — call `assert_under` to verify the target path stays under the repo root, then (when `allowed_prefixes` is non-None) verify via directory-boundary matching that the resolved relpath starts with one of the declared prefixes. These are `install.py` Step 8 (a read-only pre-flight over every projected file before any write), `upgrade.py`'s `--dry-run` probe (added by the projection-dry-run spec), and `safety.write_jailed`'s inline prefix block (the enforcement site inside the write primitive). Any semantics change to the rule — e.g., changing how directory-boundary matching works or when the prefix check is skipped — must be applied to all three copies or they drift and produce inconsistent refusal behavior across commands.

`safety.assert_projection_jailed(root, relpaths, allowed_prefixes, *, command)` is extracted as a new read-only helper that centralises the two-step check. All three call sites route through it. As a follow-on, upgrade's non-dry-run write loop — which currently has no standalone pre-flight and catches violations one file at a time mid-write — gains the same probe-all-before-any-write pattern that install's Step 8 uses, making its failure mode atomic (either the whole projection is jailed-safe or nothing is written).

## Boundaries

### Always do

- Implement `assert_projection_jailed` as a pure read-only function: it iterates relpaths, calls `assert_under` for the root-jail check, and when `allowed_prefixes` is non-None applies the directory-boundary prefix match. It raises `PathJailError` on first violation. It writes nothing.
- Keep `write_jailed`'s trailing-slash guard (`if not all(p.endswith("/") for p in prefixes): raise PathJailError(...)`) in place as defense-in-depth after routing the prefix-match check through `assert_projection_jailed`. The guard catches programming errors in callers that construct prefix lists in code (bypassing the contract schema). It is not part of the duplicated semantics being extracted.
- Keep `write_jailed`'s `TypeError` for `scope="user"` with `allowed_prefixes=None`. That is a caller-contract guard, not prefix-match logic, and is not affected by this refactoring.
- Place the upgrade non-dry-run pre-flight call to `assert_projection_jailed` before the `for relpath, content in sorted(work_projection.items()):` write loop — probe all paths first, then write, matching install's Step 8 ordering.
- Preserve every existing jail and prefix regression test passing without modification.

### Ask first

- Adding a `scope` parameter to `assert_projection_jailed` to preserve the "for scope 'repo'" text in the error message (the current prefix-violation messages from the probes include the scope string; routing through `assert_projection_jailed` may change the wording slightly — ask before hardening the message format in a way that would force test changes).
- Routing `write_companion` through `assert_projection_jailed` explicitly. `write_companion` delegates to `write_jailed`, which already routes through the extracted helper after T3; no direct change is needed, but confirm the transitive routing is sufficient before touching `write_companion`'s call site.
- Changing any error-message text that existing tests `match=` against. The current test coverage uses `assertRaises(safety.PathJailError)` without message matching for prefix violations; if a future test tightens the match, ask before changing the wording.

### Never do

- Change the behavior of `agentbundle install` in any way (dry-run or non-dry-run). Install's Step 8 already runs a whole-projection pre-flight before Step 9 writes; the refactored Step 8 must refuse the exact same paths at the same pre-flight stage, producing the same exit code.
- Change the behavior of `agentbundle upgrade --dry-run`. The refactored dry-run probe must surface the same jail refusals it does today, before printing any plan.
- Change the Tier-1/2/3 classification contract, `write_jailed`'s atomicity, or the companion-write logic.
- Introduce `assert_projection_jailed` anywhere other than `agentbundle/safety.py`. It is a module-level function, not a method, and not in a new file.
- Add a new top-level directory or a new runtime dependency.
- Remove or weaken the root-jail check (`assert_under`) from any of the three call sites. Both layers of the check — root containment and prefix containment — must remain enforced at every site.

## Testing Strategy

Two verification modes apply across this spec's ACs:

- **TDD (AC1, AC6):** `assert_projection_jailed` is a pure, side-effect-free function with a compressible invariant. Unit tests are written first and drive the implementation. Five sub-cases cover the complete branching: valid path with `allowed_prefixes` set (no exception), valid path with `allowed_prefixes=None` (prefix check skipped, no exception), root-escape via `../` (raises `PathJailError`), inside-root but outside all prefixes (raises `PathJailError`), and empty `relpaths` iterable (no exception). Tests live in `tests/unit/test_safety.py` alongside the existing `assert_under` tests.

- **Goal-based regression (AC2, AC3, AC4, AC5, AC7):** Each migrated call site's correctness is verified by running the existing integration tests that exercise the jail refusal for that site. No test modifications are expected; if a test needs updating, treat that as a signal the semantics changed. For AC4 (upgrade non-dry-run pre-flight), a new integration test is added confirming that a projection with a prefix-violating path causes `upgrade` to exit non-zero and write zero files to disk (probe-all-before-write contract).

## Acceptance Criteria

- [ ] AC1: `safety.assert_projection_jailed(root, relpaths, allowed_prefixes, *, command)` exists as a public function in `agentbundle/safety.py`. The `command` parameter is a string prefixed uniformly on all `PathJailError` messages the helper raises — both root-escape (caught from `assert_under` and re-raised as `PathJailError(f"{command}: {exc}")`) and prefix-violation (`PathJailError(f"{command}: path {relpath!r} is not within any declared prefix zone")`). All three call sites pass a command-name string (`"install"`, `"upgrade"`) or a scope-description string (`f"scope={scope}"`). Callers print `str(exc)` directly — the `command:` prefix is in the raised message, not added by the caller. Given any relpath that escapes `root` via `../`, it raises `PathJailError`. Given a relpath inside `root` but outside all entries in `allowed_prefixes`, it raises `PathJailError`. Given `allowed_prefixes=None`, it skips the prefix check and raises only on a root escape. Given a valid relpath inside `root` and within the declared prefix, it returns without exception. Given an empty `relpaths` iterable, it returns without exception.
- [ ] AC2: `install.py` Step 8's inner jail loop (lines 895–918) is replaced by a call to `safety.assert_projection_jailed(plan.root, projection.keys(), plan.allowed_prefixes, command="install")`. The outer `for plan in plans:` loop and its `if projection is None: continue` guard remain unchanged. `PathJailError` is caught and printed with `str(exc)` (the `command:` prefix is embedded in the message by the helper — see AC1). The integration test `test_path_jail_probe_refused` passes without modification. Note: `test_path_jail_probe_refused` exercises the root-escape branch; the install call-site prefix-branch wiring is not separately verified by an integration test (accepted as a mechanical migration — prefix logic is covered by the AC6 unit tests for `assert_projection_jailed` itself). Also note: routing through `assert_projection_jailed` removes the resolved absolute path (`target.resolve()`) that `install.py:918` currently includes in prefix-violation diagnostics; only `relpath` appears in the new message — this diagnostic narrowing is acceptable and intentional.
- [ ] AC3: `upgrade.py`'s `--dry-run` probe (lines 545–562, inside the `if getattr(args, "dry_run", False):` guard) is replaced by a call to `safety.assert_projection_jailed(root, sorted(work_projection), allowed_prefixes, command="upgrade")`. `PathJailError` is caught and printed with `str(exc)` (the `command:` prefix is embedded by the helper — see AC1). The integration test `test_dry_run_upgrade_preflight_path_jail_passthrough` passes without modification.
- [ ] AC4: `upgrade.py`'s non-dry-run path gains a pre-flight call to `safety.assert_projection_jailed(root, sorted(work_projection), allowed_prefixes, command="upgrade")` immediately before the `for relpath, content in sorted(work_projection.items()):` write loop (line 587). A new integration test confirms: given an installed pack and a projection containing a Tier-2 base path outside `allowed_prefixes` (test must run at a scope where `allowed_prefixes` is non-None — user scope or repo-per-IDE), `upgrade` exits non-zero and zero files are written to the target tree. Note: Tier-2 companion source paths today flow through `write_companion` → `write_jailed(root, str(companion), content, allowed_prefixes=None)` — meaning the prefix check is *skipped* for companion writes (only the root-jail runs). This pre-flight adds prefix enforcement to Tier-2 companion source paths for the first time: a Tier-2 base path outside the declared prefixes is currently *written* as a companion but will be *refused* after this change. The integration test must use exactly this case — a Tier-2 path outside declared prefixes — to demonstrate the behavioral change. This broadening is intentional and aligns upgrade's failure mode with install's Step 8 behavior.
- [ ] AC5: All existing jail and prefix regression tests pass without modification. Specifically: `test_write_jailed_refuses_path_escape`, `test_write_jailed_refuses_absolute_path_escape`, `test_assert_under_passes_for_path_inside` (all in `tests/unit/test_safety.py`); all `WriteJailedRepoScopeTests` cases (all adapters, trailing-slash guard, None-prefixes backward-compat; `tests/unit/test_safety_repo_scope_prefixes.py`); `test_path_jail_probe_refused` (`tests/integration/test_install_cmd.py:344`); `test_dry_run_upgrade_preflight_path_jail_passthrough` (`tests/integration/test_upgrade_cmd.py:755`).
- [ ] AC6: A focused unit test suite for `assert_projection_jailed` in `tests/unit/test_safety.py` covers all five sub-cases from the Testing Strategy (valid-with-prefixes, valid-none-prefixes, root-escape, inside-root-outside-prefix, empty-relpaths). Each sub-case is a named test function.
- [ ] AC7: `safety.write_jailed`'s inline prefix-match block (lines 342–347 — the `target_relpath = ...; if not any(...):` pair) is replaced by a call to `assert_projection_jailed(root, [relpath], allowed_prefixes, command=f"scope={scope}")`. The trailing-slash guard (lines 337–341) remains in place before this call. All `WriteJailedRepoScopeTests` cases pass without modification. (The `scope` parameter is `"repo"` or `"user"` — passing `f"scope={scope}"` preserves the diagnostic context of the existing error message; the prefix-violation message changes from the inline wording to `f"scope={scope}: path {relpath!r} is not within any declared prefix zone"` — this is acceptable since no current test matches that message text.)

## Assumptions

- Technical: The three copies share the same two-step check: `assert_under(root, target)` for root containment and a `target_relpath.startswith(p)` directory-boundary match for prefix containment. `write_jailed`'s trailing-slash guard (lines 337–341) is adjacent but not part of the duplicated pattern — it is a programming-error defense unique to the write primitive. (`safety.py:318–347`, `install.py:887–918`, `upgrade.py:533–576`, read 2026-07-23)
- Technical: Existing regression tests for prefix violations use `assertRaises(safety.PathJailError)` or `rc != 0` without matching the error-message text. Any slight wording change from routing through `assert_projection_jailed` (e.g., losing "for scope 'repo'" in the prefix-violation message) will not break current tests. (`test_safety_repo_scope_prefixes.py:38–106`, `test_upgrade_cmd.py:755–777`, read 2026-07-23)
- Technical: The non-dry-run upgrade write loop (`upgrade.py:578–619`) catches `PathJailError` from `write_jailed` per-file and returns 1, meaning some files may be written before the violation is reached. Adding a pre-flight pass before this loop changes the observable failure mode (fail-fast with zero writes) but preserves the non-zero exit and the on-disk integrity guarantee. This behavioral change is explicitly in scope. (`upgrade.py:578–619`, `docs/specs/projection-dry-run/spec.md:77`, backlog entry, read 2026-07-23)
- Technical: `write_jailed` calls `assert_under` at line 320 before the `if allowed_prefixes is not None:` block. If `write_jailed` calls `assert_projection_jailed([relpath], ...)` which also calls `assert_under` internally, `assert_under` is invoked twice for the same path. This is safe and idempotent; the double-call is acceptable rather than restructuring `write_jailed`'s control flow. (`safety.py:318–347`, read 2026-07-23)
- Technical: Runtime is stdlib Python ≥ 3.11. (`packages/agentbundle/pyproject.toml`, read 2026-07-23)
- Product: The projection-dry-run spec's "Never do: change non-dry-run behavior" (`docs/specs/projection-dry-run/spec.md:77`) was scoped to that PR's dry-run addition. Adding a pre-flight pass to upgrade's non-dry-run path is explicitly in scope here. (backlog entry `unify-path-jail-projection-probe`, read 2026-07-23)
- Process: Refactoring within `packages/agentbundle`; no ADR, no RFC, no adopter-visible CLI or contract change — spec-level work per `docs/CONVENTIONS.md` §3. (`docs/CONVENTIONS.md:§3`, read 2026-07-23)

## Tasks

See `plan.md`.

## Declined

- **Separate `_check_prefix_match` private helper instead of `assert_projection_jailed` directly:** A private `_check_prefix_match(root, target, allowed_prefixes)` helper that operates on a single pre-resolved target was considered. Rejected because the backlog explicitly names `assert_projection_jailed` as the public API that call sites route through; a private helper would be an extra indirection without the named public contract.
- **Adding `scope` as a parameter to `assert_projection_jailed`:** The current prefix-violation error messages from the probes include `for scope {scope!r}` (e.g., "for scope 'repo'"). This information could be preserved by adding a `scope` keyword to `assert_projection_jailed`. Deferred: no existing test matches on this part of the message, so the slight wording change is safe for now. Can be added if an adopter files a support issue where the scope context was needed.
- **Merging the outer `for plan in plans:` loop in install.py Step 8 into `assert_projection_jailed`:** The outer loop iterates scope plans, each with a different `root` and `allowed_prefixes`. Collapsing it into a single helper call would require a different API (list of `(root, relpaths, prefixes)` tuples). Not warranted — one call per plan is the right granularity.
- **Changing behavior for `--dry-run install`:** The projection-dry-run spec's "Never do" clause for install's dry-run path remains honored. Only upgrade's non-dry-run path gains new pre-flight behavior (AC4). Install's dry-run returns early at the top of Step 9, after Step 8's pre-flight; no change is needed there.
