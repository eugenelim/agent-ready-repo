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

1. `PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle render <checkout>/packs/core --target codex --output <scratch>/render`
2. `git init <scratch>/repo`
3. `PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle install <checkout> --pack core --scope repo --adapter codex --yes --output <scratch>/repo`
4. `PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle diff --root <scratch>/repo --scope repo <checkout>/packs/core`

### Features

Render of the core pack, repo-scope install with the Codex adapter, and drift detection between the install and a fresh render.

### Evidence

Write each command, its exit status, and its output to `<evidence-dir>`, which is `.context/verify/agentbundle-cli/<run-id>/` (ignored by Git). Render passes when it exits 0 and the rendered `work-loop/SKILL.md` exists. Install passes when it exits 0. Diff passes when it exits 0.

### Proof limits

`diff` proves the install matches a fresh render. It does not prove that installed skills behave.

### Cleanup

Remove only `<scratch>`, the directory this run created. Then check that `<evidence-dir>` still holds the transcript. If the handle is empty, do nothing.

### Helpers

None. The entry uses `git`, `python3`, and `mktemp`.

### Stand-in gap

Codex is the one adapter driven. The other adapters stay uncovered.
