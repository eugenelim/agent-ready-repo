# How to create an external catalogue

An external catalogue is any directory that follows the catalogue layout and contains a
`catalogue.toml`. It does not need to be this repository, does not require the `Makefile`, and
does not require any files from `tools/`.

## Prerequisites

- Python 3.11+
- AgentBundle ≥ 0.14.0: `python -m pip install agentbundle`

## Step 1 — Create the layout

```
my-catalogue/
  catalogue.toml
  packs/
    my-first-pack/
      pack.toml
      .claude-plugin/plugin.json
      .apm/skills/my-skill/SKILL.md
```

## Step 2 — Write `catalogue.toml`

```toml
[catalogue]
name        = "my-catalogue"
version     = "0.1.0"
description = "Example external catalogue."
```

See the [catalogue.toml reference](../reference/catalogue-toml.md) for all fields.

## Step 3 — Write `pack.toml`

```toml
[pack]
name             = "my-first-pack"
version          = "0.1.0"
description      = "My first pack."
adapter-contract = "0.14"
```

## Step 4 — Write a skill

Create `.apm/skills/my-skill/SKILL.md`:

```markdown
---
name: my-skill
description: Does a thing when the user needs a thing done.
---

# Body

Step 1: identify the thing.
Step 2: do the thing.
```

## Step 5 — Lint

```bash
agentbundle catalogue lint --root my-catalogue/
```

Fix any errors before continuing. Add `--format json` to get machine-readable output.

## Step 6 — Verify

```bash
agentbundle catalogue verify --root my-catalogue/
```

This runs the full 18-step pipeline including a build into a temp directory. It must exit 0 before
you publish or distribute the catalogue.

## Step 7 — Project to self-host adapters (optional)

If this catalogue is also used in the repository that hosts it:

```bash
agentbundle catalogue self-host --root my-catalogue/ --write
```

## Step 8 — Build the dist tree

```bash
agentbundle catalogue build --root my-catalogue/ --output my-catalogue/dist
```

`dist/` is ready for use as a source in agentbundle or for uploading to a registry.

## What you don't need

- The `Makefile` from this repository — it is home-repository governance.
- Any file from `tools/` — all portable logic is in `agentbundle catalogue *`.
- A specific CI system — you can run the same commands in any CI environment.
