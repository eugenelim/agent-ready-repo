# Verification entries

Per-surface launch-and-drive recipes for this repository. Follow the `work-loop` skill's verify-entries doctrine when you use or edit one.

## Verify: agentbundle CLI

### Surface

The `agentbundle` command line, run from this checkout's own module so the run drives the tree under change.

### Launch

`PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle` (written `<ab>` below).

### Ready

`install` exits 0 and `<scratch>/repo/.agentbundle-state.toml` exists.

### Doctor

`PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle --version` exits 0.

### Isolation

Create `<scratch>` with `mktemp -d` and record the path as the handle. Every render and install writes under `<scratch>`. The run never writes to `<checkout>`.

### Drive

Run in order:

1. `PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle render <checkout>/packs/core --output <scratch>/render`
2. `git init <scratch>/repo`
3. `PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle install <checkout> --pack core --scope repo --adapter codex --yes --output <scratch>/repo`
4. `PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle diff --root <scratch>/repo --scope repo <checkout>/packs/core`

### Features

Render of the core pack's distribution build, repo-scope install with the Codex adapter, and drift detection between the install and a fresh render.

### Evidence

Write each command, its exit status, and its output to `<evidence-dir>`, which is `.context/verify/agentbundle-cli/<run-id>/` (ignored by Git). Render passes when it exits 0 and `<scratch>/render/apm/core/.apm/skills/work-loop/SKILL.md` exists. Render with no `--target`: a direct-install adapter target such as `codex` selects no distribution recipe, so it exits 0 and writes nothing. Install passes when it exits 0. Diff passes when it exits 0.

### Proof limits

`diff` proves the install matches a fresh render. It does not prove that installed skills behave.

### Cleanup

Remove only `<scratch>`, the directory this run created. Then check that `<evidence-dir>` still holds the transcript. If the handle is empty, do nothing.

### Helpers

None. The entry uses `git`, `python3`, and `mktemp`.

### Stand-in gap

Codex is the one adapter driven. The other adapters stay uncovered.

## Verify: repository precheck

### Surface

`make precheck` (runs `tools/precheck.py`), run from this checkout. It maps changed paths to the checks they trigger.

### Launch

`make precheck`. Pass flags with `make precheck PRECHECK_ARGS="--with-tests --base origin/main"`. The Makefile puts the checkout's `packages/` on `PYTHONPATH`; the runner adds the same paths itself, so `python3 tools/precheck.py` runs the same checks.

### Ready

It prints each triggered check, or `no trigger matched`, and exits.

### Doctor

`make precheck PRECHECK_ARGS=--help` exits 0.

### Isolation

Create a separate throwaway git worktree on a throwaway branch, and record its path and branch name as the handle. The run drives only that worktree, never the checkout under change.

### Drive

Run in the throwaway worktree, in order:

1. Touch one file under `packs/core/.apm/`.
2. Run `make precheck`. Expect a non-zero exit with a self-host drift result.
3. Run `PYTHONPATH=packages/agentbundle python3 -m agentbundle catalogue self-host --root . --write`.
4. Run `make precheck` again. Expect exit 0.

### Features

The four checks (self-host drift, deep skill lint, core release bump, and bandit on the changed files) and the named skips for a missing tool.

### Evidence

Write each command, its exit status, and its output to `<evidence-dir>`, which is `.context/verify/repository-precheck/<run-id>/` (ignored by Git). The first run passes when it exits non-zero and names self-host drift. The second passes when it exits 0.

### Proof limits

It is not CI. It runs pack tests only with `--with-tests`. It proves nothing about suites it does not trigger.

### Cleanup

Remove only the worktree and branch this run created. Check the recorded handle first, and if it is empty, do nothing. Then check that `<evidence-dir>` still holds the transcript.

### Helpers

None. The entry uses `git`, `make`, and `python3`.

### Stand-in gap

A tool missing from the interpreter is a named skip, so that check stays uncovered.
