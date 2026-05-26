# How to install `agentbundle` from a clone

You're here because credentialed skills like `jira` or `figma` need
the `agentbundle` Python module importable on the interpreter that
runs them. All four [README install routes](../../../README.md#install)
ship pack content — skills, agents, hooks — but not that Python
module, so every route converges here for the pip install.

Every credentialed skill in this catalogue (`jira`, `figma`,
`confluence-publisher`, `confluence-crawler`, `jira-align`, plus the
worked example `example-credentialed-skill`) imports the credential
loader directly:

```python
from agentbundle.credentials import load_credentials
```

That import has to resolve against the interpreter's `sys.path` at the
time the agent harness spawns the skill script. The pip install
registers `agentbundle` on `sys.path` for you; the zipapp at
`dist/agentbundle.pyz` doesn't (see [Fallback](#fallback-build-the-zipapp)).

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

## How this works

The clone carries two things in one repo, and the `pip install` step
ties them together so they work as a pair:

- **`packs/`** — the **catalogue**. The install verb
  (`agentbundle install --pack <name> . --output <target>`) reads from
  here and projects pack content into your target repo (or `~/.claude/`
  for user-scope packs).
- **`packages/agentbundle/`** — the **runtime library**. Every
  credentialed skill in the catalogue does
  `from agentbundle.credentials import load_credentials` from its own
  subprocess at runtime. That import has to resolve to *this* directory.

```
your-clone/
├── packs/                          ← catalogue source (install verb reads this)
│   ├── core/.apm/skills/…
│   └── atlassian/.apm/skills/…
└── packages/agentbundle/           ← runtime library source (pip install -e links here)
    └── agentbundle/
        ├── cli.py                  (entry point for the `agentbundle` command on PATH)
        ├── credentials.py          (public shim — what skills import)
        └── creds/                  (loader internals)
```

`pip install -e packages/agentbundle/` exposes two surfaces on your
active interpreter:

1. **Importable module** — `from agentbundle.credentials import …`
   succeeds anywhere that interpreter runs. This is what credentialed
   skill scripts depend on when an agent harness spawns them.
2. **`agentbundle` console script on PATH** — the same CLI verbs the
   zipapp exposes (`install`, `creds`, `validate`, etc.), now running
   directly from the live source instead of from a frozen archive.

Both surfaces link back at the editable source, so **`git pull`
cascades to both**: next `agentbundle install` picks up new pack
content, next Python process importing `agentbundle.credentials` sees
the updated module — no re-install needed.

**`make zipapp` is not part of the primary path** once the `pip
install` has happened. The launcher on PATH already runs the CLI from
the live source. The zipapp at `dist/agentbundle.pyz` remains useful
as a [fallback](#fallback-build-the-zipapp) for environments where
`pip install` is blocked, or as a portable artifact to hand off to
users who don't pip-install — but you don't need it for your own
machine.

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

## Fallback: build the zipapp

If `pip install` is blocked in your environment — locked-down
corporate Python without venv permissions, PEP 668 strict policy where
you can't opt in to a venv — the catalogue ships a fallback. `make
zipapp` packages the `agentbundle/` source into a single executable
archive at `dist/agentbundle.pyz` that runs the CLI without an
install:

```bash
make zipapp                                              # builds dist/agentbundle.pyz
./dist/agentbundle.pyz install --pack core . --output /path/to/your/project
```

**The zipapp does not register `agentbundle` on the interpreter's
`sys.path`.** The archive contains every module credentialed skills
import (`zipimport` makes a `.pyz` self-contained), but Python looks
up `from agentbundle.credentials import …` against `sys.path` at
import time, and a standalone `.pyz` doesn't add itself. Credentialed
skills spawned by an agent harness run a bare `#!/usr/bin/env python3`
subprocess with no `PYTHONPATH` plumbing — that subprocess will fail
`ModuleNotFoundError` against a host where the zipapp is the only
agentbundle artifact.

Use the zipapp when one of these holds:

- **You only install non-credentialed packs** (`core`,
  `governance-extras`, `user-guide-diataxis`, `monorepo-extras`,
  `contracts`). The CLI is all you need; no skill in those packs
  imports `agentbundle.credentials`.
- **Split-host topology where pip is blocked on the install host but
  not the agent host** — host A is locked-down (CI runner, air-gapped
  builder) and runs the zipapp to project pack content into a target
  repo, the CLI never imports `agentbundle.credentials`; host B is the
  developer workstation that has a normal Python install where you
  `pip install agentbundle` so skill scripts resolve the loader there.
- **You're handing the zipapp off to a third party** who doesn't have
  `pip` and won't run credentialed skills — the zipapp is a portable
  artifact for that case by design.

The pip install remains the right default when nothing blocks it; the
zipapp is the escape hatch when something does.

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
