---
title: "Install agentbundle"
summary: "Install the agentbundle command with pip, from a clone, or with APM."
pack: _shared
kind: how-to
aliases:
  - guides/_shared/how-to/install-agentbundle-from-clone
---

# Install agentbundle

`agentbundle` installs packs into your agent and keeps them up to date. It needs Python 3.11 or newer.

## Install

Install it with pip, inside a virtual environment:

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install agentbundle
```

Check that it runs:

```bash
agentbundle --help
```

Use the same Python your agent runs, because some skills import `agentbundle` from their scripts.

## Ask your agent

Your agent can do the install for you:

```text
Install agentbundle in a virtual environment for this repository and check that it runs.
```

It creates the environment, installs the package, and runs `agentbundle --help`.

## Install from a clone

Use a clone when you work on packs or cannot reach PyPI:

```bash
git clone https://github.com/eugenelim/agent-ready-repo
cd agent-ready-repo
python -m pip install -e packages/agentbundle
```

`agentbundle` now installs packs from your clone, and `git pull` updates both the command and the packs.

## Install with APM

If your team uses APM, install a pack's files without the Python command:

```bash
apm install <owner>/<catalogue>/<pack>
```

APM copies the pack only. To upgrade it later with `agentbundle`, run `agentbundle init-state` once.

## Behind a corporate network

If installs fail with `CERTIFICATE_VERIFY_FAILED`, point `agentbundle` at your company's certificate bundle:

```bash
AGENTBUNDLE_CA_BUNDLE=/path/to/corp-ca.pem agentbundle install --pack core
```

The [command reference](../reference/agentbundle.md#corporate-networks) covers proxies, WSL, and macOS trust.

Next, [install packs for your agent](install-packs.md).
