---
title: "Create a catalogue"
summary: "Initialize a new AgentBundle catalogue directory with a single command, then validate and run it."
pack: _shared
kind: how-to
status: stable
---

# Create a catalogue

**Use this when:** You want to start a new AgentBundle catalogue from scratch —
in a fresh directory or inside an existing repository — and want a validated,
ready-to-run directory layout in one step.

**Prerequisites:**
- Python 3.11+
- `agentbundle` ≥ 0.24.0 (`pip install agentbundle`)

---

## Step 1 — Run init

```bash
agentbundle catalogue init my-catalogue --name my-catalogue
```

This creates a `my-catalogue/` directory (or uses an existing empty one) and
writes every scaffold file into it:

```
my-catalogue/
  catalogue.toml
  .claude-plugin/
    marketplace.json
  packs/
    README.md
    AGENTS.md
    _example/
      pack.toml
      README.md
      .claude-plugin/plugin.json
      .apm/skills/example-skill/SKILL.md
      evals/eval_queries.json
  profiles/
    README.md
    AGENTS.md
    _example/
      profile.toml
      README.md
  guides/
    _shared/
      reference/
        catalogue-ci-contract.md
        catalogue-authoring-standards.md
```

`init` is **additive and idempotent** — it never overwrites existing files.
Run it again in the same directory and every file is reported as
`SKIP (already-present)`.

### Name derivation

If `--name` is omitted, the name is derived from the target directory's
basename. Directory basenames that are valid catalogue names (letters, digits,
hyphens, underscores, starting with a letter or digit) are used as-is.

### Metadata flags

| Flag | Default |
|------|---------|
| `--name NAME` | Derived from directory basename |
| `--display-name NAME` | Title-cased from `--name` |
| `--description TEXT` | Auto-generated from `--name` |
| `--owner-name NAME` | Same as `--display-name` |
| `--preferred-adapter ADAPTER` | From `install-defaults.toml`, or `claude-code` |

### Preview before writing

Pass `--dry-run` to see exactly which files would be created without touching
the filesystem:

```bash
agentbundle catalogue init my-catalogue --dry-run
```

---

## Step 2 — Verify the catalogue

Confirm the scaffold is valid:

```bash
agentbundle catalogue verify --root my-catalogue
```

A fresh scaffold passes all 18 verification checks. If any fail, the output
names the failing checks and their remediation steps.

---

## Step 3 — Inspect with the CLI

```bash
agentbundle list-packs my-catalogue/   # → empty (no real packs yet)
agentbundle list-profiles my-catalogue/ # → empty (no real profiles yet)
```

The `_example` pack and profile are prefixed with `_` — they are excluded from
discovery by convention and serve as authoring templates only.

---

## Step 4 — Add your first pack

Copy or rename `packs/_example` to `packs/my-pack`, then edit `pack.toml`:

```toml
schema = 1

[pack]
name        = "my-pack"
display-name = "My Pack"
description  = "A short description of what this pack does."
version     = "0.1.0"
```

After editing, re-run verify to confirm the pack is valid:

```bash
agentbundle catalogue verify --root my-catalogue
```

---

## Step 5 — Set up CI

The `guides/_shared/reference/catalogue-ci-contract.md` file in your new
catalogue describes the portable CI contract: verify → package → publish.

A minimal CI pipeline runs:

```bash
agentbundle catalogue verify --root . --format json
agentbundle catalogue package \
  --root . \
  --bundle  "$BUNDLE" \
  --release "$RELEASE" \
  --channel stable \
  --output  dist/
```

---

## Troubleshooting

**Init reports `CONFLICT` for one or more files.**
The target directory already contains those files with different content.
Resolve the conflict (remove or rename the conflicting file) and re-run init.
Or use a new target directory.

**`--name` fails validation.**
Catalogue names must match `[A-Za-z0-9][A-Za-z0-9_\-]*`. Avoid spaces,
dots, and slashes.

**`agentbundle catalogue verify` reports `CAT-V-016 install-defaults drift`.**
Run `agentbundle catalogue sync-defaults --write --root my-catalogue` to
generate the defaults file from your `catalogue.toml`.
