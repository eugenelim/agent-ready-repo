---
title: "How a catalogue works"
summary: "Publish your own packs and profiles for your agents to install from."
pack: _shared
kind: how-to
status: stable
---

# How a catalogue works

Create a catalogue with one command, then add your own packs to it.

## Create the catalogue

A catalogue is a folder with a `catalogue.toml` at its root, a `packs/` folder of packs, and a `profiles/` folder of named pack lists. With [`agentbundle`](install-agentbundle.md) installed, scaffold it:

```bash
agentbundle catalogue init my-catalogue --name my-catalogue
```

This writes `catalogue.toml`, a root `AGENTS.md` (which `catalogue package` needs to build a release), and an `_example` pack and profile. It never overwrites an existing file, so running it again is safe. A fresh catalogue packages into an empty release until you add a real pack.

## Check it

Confirm the scaffold is valid:

```bash
agentbundle catalogue verify --root my-catalogue
```

A failure names the check and its fix.

## Add your first pack

Copy `packs/_example` to `packs/my-pack` and edit its `pack.toml`:

```toml
schema = 1

[pack]
name        = "my-pack"
display-name = "My Pack"
description  = "A short description of what this pack does."
version     = "0.1.0"
```

Folders that start with `_` are templates that discovery skips, so run `verify` again after you add a real pack.

## Lint and publish

Lint before CI packages and publishes it:

```bash
agentbundle catalogue lint --root .
```

The [Catalogue CI contract](../reference/catalogue-ci-contract.md) defines the packaging and publish steps.

Next, [configure `catalogue.toml`](../reference/catalogue-format.md) to set the catalogue's identity and distribution.
