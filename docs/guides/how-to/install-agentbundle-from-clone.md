# How to install `agentbundle` from a clone

You're here because you cloned the catalogue ([README route 4](../../../README.md#install))
and want credentialed skills like `jira` or `figma` to work when an
agent harness invokes their scripts.

Every credentialed skill in this catalogue (`jira`, `figma`,
`confluence-publisher`, `confluence-crawler`, `jira-align`, plus the
worked example `example-credentialed-skill`) imports the credential
loader directly:

```python
from agentbundle.credentials import load_credentials
```

The clone-and-build install route ships the bundled CLI as a zipapp at
`dist/agentbundle.pyz`, but a zipapp is a single executable — it does
not register `agentbundle` as an importable module on your
interpreter's `sys.path`. One `pip install` closes the gap.

## Before you start

- A local clone of the catalogue (`git clone …`).
- A Python interpreter ≥ 3.11 on PATH, ideally inside a virtualenv you
  control (see [On venvs and which interpreter](#on-venvs-and-which-interpreter)
  below).

## Step 1 — Install the module

From the clone root, use the editable install:

```bash
pip install -e packages/agentbundle/
```

This writes a finder hook into your active interpreter's
`site-packages` pointing back at `packages/agentbundle/agentbundle/`.
`from agentbundle.credentials import load_credentials` succeeds from
anywhere that interpreter runs, and any `git pull` against the clone
is picked up by importers without re-running `pip install`.

**Editable is the right default** for both contributors and adopters
working from a clone — the clone is already on disk, the finder-hook
shape costs nothing, and source updates land transparently. The
[`how to add a credentialed skill`](add-a-credentialed-skill.md)
walkthrough uses the same idiom.

> **Snapshot install — narrow exception.** `pip install ./packages/agentbundle`
> (no `-e`) copies the package as it exists at install time. Edits or
> `git pull`s to the clone are *not* seen by importers until you re-run
> `pip install`. Use this only if you cloned to a pinned tag, never
> intend to update or edit, and want install isolation from the clone
> directory.

## Step 2 — Smoke-check the install

```bash
python -c "from agentbundle.credentials import load_credentials"
```

Exits 0 silently on success. On failure, stderr ends with a multi-line
traceback whose last line is `ModuleNotFoundError: No module named
'agentbundle'` — credentialed-skill scripts will fail the same way at
runtime. Re-check the [pitfalls](#common-pitfalls) below before
continuing.

## On venvs and which interpreter

Credentialed-skill scripts under `packs/*/.apm/skills/*/scripts/*.py`
all start with `#!/usr/bin/env python3`. That resolves through PATH,
so whichever Python is *first on PATH* when the agent invokes the
script is the one that needs `agentbundle` installed. Three idioms
work:

- **Activated venv** — `python -m venv .venv && source .venv/bin/activate`
  before `pip install`. The activated shell's `python3` becomes
  whichever the venv resolves to; the catalogue's skill scripts pick
  up the same interpreter when invoked from that shell.
- **System interpreter** — `pip install` against the global Python.
  Works, but conflicts with other projects' dependency pins are
  on you. Avoid on shared machines.
- **`pipx` / `uv tool`** — both install `agentbundle` into a private
  environment behind a launcher. Works for the CLI surface
  (`agentbundle …`) but the credentialed-skill scripts still need
  `agentbundle` on the *script's* `sys.path`, which `pipx` does not
  expose. Skip these for this use case; use a venv or a system
  install.

The install is **the same regardless of pack install scope**: a single
`pip install` covers credentialed skills landed at `~/.claude/skills/<name>/`
(user scope) and `<repo>/.claude/skills/<name>/` (repo scope), because
the script-resolved interpreter is the same in both cases.

## Common pitfalls

- **Two interpreters on PATH.** `pip install` lands the package in
  whichever `pip` resolved to, but `#!/usr/bin/env python3` in the
  skill script might resolve to a *different* `python3`. Confirm with
  `python3 -c "import sys; print(sys.executable)"` matches
  `pip -V`'s reported Python.
- **Venv not activated when the skill runs.** Agent harnesses spawn
  scripts from their own shell environment, which may not have your
  venv activated. Either activate the venv in the shell that launches
  the agent, or install `agentbundle` into a Python that's on PATH
  unconditionally (system Python, or a venv whose `bin/` is on PATH).
- **`error: externally-managed-environment` from `pip install`.** Python
  3.11+ on Debian 12 / Ubuntu 23.04+ and recent macOS Homebrew Python
  enforce [PEP 668](https://peps.python.org/pep-0668/) — `pip install`
  against the system Python is refused by default. Fix by creating a venv
  (`python3 -m venv .venv && source .venv/bin/activate`) and re-running
  the install there. Avoid `--break-system-packages` unless you
  understand what you are overriding.
- **`ModuleNotFoundError` after install.** Re-run the smoke check
  *from the same shell as the agent harness*. A passing smoke check
  in one shell and a failing import in another is a PATH mismatch.

## Reference

- README install routes: [`README.md § Install`](../../../README.md#install)
- Adding a credentialed skill: [`add-a-credentialed-skill.md`](add-a-credentialed-skill.md)
- Loader contract: [`docs/specs/skill-secrets/spec.md` § AC3, AC4c](../../specs/skill-secrets/spec.md)
- Package source: [`packages/agentbundle/`](../../../packages/agentbundle/)
