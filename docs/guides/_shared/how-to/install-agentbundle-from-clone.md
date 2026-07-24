# How to install `agentbundle` from a clone

**Use this when:** You need to run the `agentbundle` CLI from a local clone of the catalogue — for development, an org fork, or environments where a PyPI install is unavailable.
**Prerequisites:** A local clone of the catalogue and Python ≥ 3.11 on PATH; see "Before you start".
**Result:** `agentbundle` installed as an editable package so the CLI and pack content stay in sync with your clone via `git pull`.

You're here because the `agentbundle` CLI drives pack install, validation, adapt, and build. All four [README install routes](../../../../README.md#install) ship pack content — skills, agents, hooks — but not the CLI, so every route converges here for the pip install.

> **Credentialed skills don't resolve credentials through the `agentbundle` wheel.** Since 0.2.0 (RFC-0013) they no longer import from `agentbundle.credentials`, and since [RFC-0023](../../../rfc/0023-credential-manager-broker.md) the `auth: creds` resolver is the standalone, pip-installable [`credbroker`](../../../../packages/credbroker) library, imported in-process (`from credbroker import …`) — it replaced the build-projected `credentials_shim` sibling. From a clone, install it alongside the CLI: `pip install -e ./packages/credbroker`. (The no-PyPI corporate and zero-pip user-scope-floor paths are in Step 9 of the [credentialed-skill how-to](../../credential-brokers/how-to/add-a-credentialed-skill.md).) The CLI itself remains pip-installed from this clone; what changed is that the *Python skill bodies* resolve credentials through `credbroker`, not the agentbundle wheel.

Smoke test for the install:

```python
from agentbundle.cli import main
```

That import has to resolve against the interpreter's `sys.path` at the time you invoke `agentbundle <verb>` from a shell. The pip install registers `agentbundle` on `sys.path` for you; the zipapp at `dist/agentbundle.pyz` doesn't (see [Fallback](#fallback-build-the-zipapp)).

## Before you start

- A local clone of the catalogue (`git clone …`).
- A Python interpreter ≥ 3.11 on PATH, ideally inside a virtualenv you control (see [On venvs and which interpreter](#on-venvs-and-which-interpreter) below).

## Installing from an org fork

If your organisation maintains a fork of the catalogue with an internal Artifactory mirror configured, installing agentbundle from that fork gives every developer the org Artifactory channel at Layer 3 — no `agentbundle config set source` step is needed.

An org fork ships an `[organization.artifactory]` block in `agentbundle/_data/install-defaults.toml`:

```toml
[organization.artifactory]
enabled    = true
base-url   = "https://artifactory.example.test"
repository = "agentbundle-local"
bundle     = "core"
channel    = "stable"
```

When you run `pip install -e packages/agentbundle/` against the org fork (or install the packaged org wheel), agentbundle reads this block at install time and activates it as **Layer 3** in the five-layer source precedence chain. The developer's next `agentbundle install --pack core` resolves to the org Artifactory channel automatically, without any manual configuration.

A developer's explicit `--catalogue` argument (Layer 1) or personal `agentbundle config set source` (Layer 2) still takes precedence over the org bootstrap (Layer 3).

For the complete org-fork bootstrap sequence — including how to edit `install-defaults.toml`, package the catalogue archive, and distribute the fork — see [Flow A in use-an-artifactory-catalogue.md](use-an-artifactory-catalogue.md#flow-a--org-bootstrap-from-fork).

## Step 1 — Install the module

From the clone root, use the editable install:

```bash
pip install -e packages/agentbundle/
```

This writes a finder hook into your active interpreter's `site-packages` pointing back at `packages/agentbundle/agentbundle/`. `from agentbundle.cli import main` succeeds from anywhere that interpreter runs, and any `git pull` against the clone is picked up by importers without re-running `pip install`.

**Editable is the right default** for both contributors and adopters working from a clone — the clone is already on disk, the finder-hook shape costs nothing, and source updates land transparently. The [`how to add a credentialed skill`](../../credential-brokers/how-to/add-a-credentialed-skill.md) walkthrough uses the same idiom.

> **Snapshot install — narrow exception.** `pip install ./packages/agentbundle` (no `-e`) copies the package as it exists at install time. Edits or `git pull`s to the clone are *not* seen by importers until you re-run `pip install`. Use this only if you cloned to a pinned tag, never intend to update or edit, and want install isolation from the clone directory.

## Step 2 — Smoke-check the install

```bash
python -c "from agentbundle.cli import main"
```

Exits 0 silently on success. On failure, stderr ends with a multi-line traceback whose last line is `ModuleNotFoundError: No module named 'agentbundle'` — credentialed-skill scripts will fail the same way at runtime. Re-check the [pitfalls](#common-pitfalls) below before continuing.

## How this works

The clone carries two things in one repo, and the `pip install` step ties them together so they work as a pair:

- **`packs/`** — the **catalogue**. The install verb (`agentbundle install --pack <name> . --output <target>`) reads from here and projects pack content into your target repo (or `~/.claude/` for user-scope packs).
- **`packages/agentbundle/`** — the **CLI source**. `agentbundle install / validate / adapt / build / …` lives here. As of 0.2.0 credentialed skills don't import from this directory (see the banner above); the CLI is what pip-install gets you.

```
your-clone/
├── packs/                          ← catalogue source (install verb reads this)
│   ├── core/.apm/skills/…
│   ├── credential-brokers/.apm/   ← shim + setup skill (RFC-0013)
│   └── atlassian/.apm/skills/…
└── packages/agentbundle/           ← CLI source (pip install -e links here)
    └── agentbundle/
        ├── cli.py                  (entry point for the `agentbundle` command on PATH)
        ├── commands/               (one module per verb)
        └── build/                  (recipe loader, adapters, projections)
```

`pip install -e packages/agentbundle/` exposes two surfaces on your active interpreter:

1. **Importable module** — `from agentbundle.cli import main` succeeds anywhere that interpreter runs. The CLI is the surface; credentialed skill scripts no longer import this module.
2. **`agentbundle` console script on PATH** — verbs like `install`, `validate`, `adapt`, `build`, now running directly from the live source instead of from a frozen archive.

Both surfaces link back at the editable source, so **`git pull` cascades to both**: next `agentbundle install` picks up new pack content, next Python process importing `agentbundle.cli` sees the updated module — no re-install needed.

**`make zipapp` is not part of the primary path** once the `pip install` has happened. The launcher on PATH already runs the CLI from the live source. The zipapp at `dist/agentbundle.pyz` remains useful as a [fallback](#fallback-build-the-zipapp) for environments where `pip install` is blocked, or as a portable artifact to hand off to users who don't pip-install — but you don't need it for your own machine.

## On venvs and which interpreter

Credentialed-skill scripts under `packs/*/.apm/skills/*/scripts/*.py` all start with `#!/usr/bin/env python3`. That resolves through PATH, so whichever Python is *first on PATH* when the agent invokes the script is the one that needs `agentbundle` installed. Three idioms work:

- **Activated venv** — `python -m venv .venv && source .venv/bin/activate` before `pip install`. The activated shell's `python3` becomes whichever the venv resolves to; the catalogue's skill scripts pick up the same interpreter when invoked from that shell.
- **System interpreter** — `pip install` against the global Python. Works, but conflicts with other projects' dependency pins are on you. Avoid on shared machines.
- **`pipx` / `uv tool`** — both install `agentbundle` into a private environment behind a launcher. Works for the CLI surface (`agentbundle …`) but the credentialed-skill scripts still need `agentbundle` on the *script's* `sys.path`, which `pipx` does not expose. Skip these for this use case; use a venv or a system install.

The install is **the same regardless of pack install scope**: a single `pip install` covers credentialed skills landed at `~/.claude/skills/<name>/` (user scope) and `<repo>/.claude/skills/<name>/` (repo scope), because the script-resolved interpreter is the same in both cases.

## Fallback: build the zipapp

If `pip install` is blocked in your environment — locked-down corporate Python without venv permissions, PEP 668 strict policy where you can't opt in to a venv — the catalogue ships a fallback. `make zipapp` packages the `agentbundle/` source into a single executable archive at `dist/agentbundle.pyz` that runs the CLI without an install:

```bash
make zipapp                                              # builds dist/agentbundle.pyz
./dist/agentbundle.pyz install --pack core . --output /path/to/your/project
```

**The zipapp does not register `agentbundle` on the interpreter's `sys.path`.** The archive contains every module credentialed skills import (`zipimport` makes a `.pyz` self-contained), but Python looks up `from agentbundle.cli import main` against `sys.path` at import time, and a standalone `.pyz` doesn't add itself. Credentialed skills spawned by an agent harness run a bare `#!/usr/bin/env python3` subprocess with no `PYTHONPATH` plumbing — that subprocess will fail `ModuleNotFoundError` against a host where the zipapp is the only agentbundle artifact.

Use the zipapp when one of these holds:

- **You only install non-credentialed packs** (`core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`, `contracts`). The CLI is all you need; no skill in those packs imports `agentbundle.cli`.
- **Split-host topology where pip is blocked on the install host but not the agent host** — host A is locked-down (CI runner, air-gapped builder) and runs the zipapp to project pack content into a target repo, the CLI never imports `agentbundle.cli`; host B is the developer workstation that has a normal Python install where you `pip install agentbundle` so skill scripts resolve the loader there.
- **You're handing the zipapp off to a third party** who doesn't have `pip` and won't run credentialed skills — the zipapp is a portable artifact for that case by design.

The pip install remains the right default when nothing blocks it; the zipapp is the escape hatch when something does.

## Common pitfalls

- **Two interpreters on PATH.** `pip install` lands the package in whichever `pip` resolved to, but `#!/usr/bin/env python3` in the skill script might resolve to a *different* `python3`. Confirm with `python3 -c "import sys; print(sys.executable)"` matches `pip -V`'s reported Python.
- **Venv not activated when the skill runs.** Agent harnesses spawn scripts from their own shell environment, which may not have your venv activated. Either activate the venv in the shell that launches the agent, or install `agentbundle` into a Python that's on PATH unconditionally (system Python, or a venv whose `bin/` is on PATH).
- **`error: externally-managed-environment` from `pip install`.** Python 3.11+ on Debian 12 / Ubuntu 23.04+ and recent macOS Homebrew Python enforce [PEP 668](https://peps.python.org/pep-0668/) — `pip install` against the system Python is refused by default. Fix by creating a venv (`python3 -m venv .venv && source .venv/bin/activate`) and re-running the install there. Avoid `--break-system-packages` unless you understand what you are overriding.
- **`ModuleNotFoundError` after install.** Re-run the smoke check *from the same shell as the agent harness*. A passing smoke check in one shell and a failing import in another is a PATH mismatch.

## Reference

- README install routes: [`README.md § Install`](../../../../README.md#install)
- Adding a credentialed skill: [`add-a-credentialed-skill.md`](../../credential-brokers/how-to/add-a-credentialed-skill.md)
- Loader contract: [`docs/specs/skill-secrets/spec.md` § AC3, AC4c](../../../specs/skill-secrets/spec.md)
- Package source: [`packages/agentbundle/`](../../../../packages/agentbundle)
