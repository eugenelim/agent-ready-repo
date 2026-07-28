---
title: "build-check-windows: --windows flag on catalogue self-host --check"
slug: build-check-windows
status: Shipped
---

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Constrained by:** docs/specs/windows-ci-bundler/spec.md (inherits the "Linux required check stays unfiltered" boundary)

Mode: full (structural/public-interface change: new CLI flag on public command + new module; dependent tasks)

## Boundaries

### Always do

- Keep the Linux `build-check.yml` job unfiltered — it is the required status check on main and must never be gated by `paths-ignore`.
- Use `sys.executable` (never bare `python` or `python3`) in every subprocess call inside `run_windows_compat`.
- When adding a new Windows-specific test step, add it to `self_host_windows.py` only — not to the YAML file.

### Never do

- Gate the Linux required check on `paths-ignore` filters — doc-only PRs must never block on a required check that doesn't report.
- Add a `--windows` call inside `run_windows_compat` (would cause infinite recursion — the internal drift check step calls `self-host --check` only).
- Introduce a new `pip` dependency inside `run_windows_compat` (the compat suite must run with the same installs the CI "Install dependencies" step provides).

## Objective

Replace the 20-step inline pytest list in `build-check-windows.yml` with a single
`agentbundle catalogue self-host --check --windows --root .` invocation, backed by
a new `catalogue_tooling/self_host_windows.py` module that encapsulates the Windows
portability compat suite. The core agentbundle verify tasks (the individual pytest
steps in `build-check.yml`) remain Linux-only and are unchanged.

## Acceptance Criteria

- [x] `--windows` flag is wired onto `catalogue self-host --check` in `cli.py`
- [x] `--windows` without `--check` exits 2 with a clear stderr message
- [x] `commands/catalogue_self_host.py` dispatches to `run_windows_compat(root)` when `--windows` is set
- [x] `catalogue_tooling/self_host_windows.py` exists and runs all Windows-compat steps in sequence via `sys.executable` subprocesses
- [x] Each step uses the correct `cwd` and the canonical `sys.executable` (not bare `python`)
- [x] First failing step causes immediate return with that exit code (matches current CI stop-on-failure behaviour)
- [x] `build-check-windows.yml` is rewritten to 4 steps: checkout, setup-python, install deps, `agentbundle catalogue self-host --check --windows --root .`
- [x] `build-check.yml` is unchanged
- [x] `docs/guides/reference/catalogue-commands.md` documents the new `--windows` flag on `self-host --check`
- [x] `docs/guides/how-to/enterprise-app-store.md` CI integration section shows the Windows check step alongside the base check

## Testing Strategy

- Unit test: `test_self_host_windows.py` — mocks `subprocess.run`, asserts each step command list and cwd; asserts stop-on-first-failure; asserts `--windows` without `--check` returns 2 (via the CLI handler path)
- Manual QA: `agentbundle catalogue self-host --check --windows --root .` invoked locally (or observed passing in CI)

## Tasks

1. **`cli.py`** — add `--windows` arg to `catalogue self-host` subparser (goal-based)
2. **`commands/catalogue_self_host.py`** — dispatch to `run_windows_compat` when `args.windows and args.check`; reject `--windows` without `--check` (TDD)
3. **`catalogue_tooling/self_host_windows.py`** — new module: `run_windows_compat(root: Path) -> int` (TDD)
4. **`build-check-windows.yml`** — rewrite to 4 steps (goal-based)
5. **Docs** — update `catalogue-commands.md` and `enterprise-app-store.md` (goal-based)
