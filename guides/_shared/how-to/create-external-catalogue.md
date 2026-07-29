---
title: "Create an external catalogue"
summary: "Scaffold a catalogue outside this repository, validate it locally, and publish it via CI."
pack: _shared
kind: how-to
status: stable
---

# Create an external catalogue

**Use this when:** You are building a catalogue in a separate repository — not a fork of
this one — and want to validate it with the same tooling before publishing.

**Prerequisites:**
- Python 3.11+
- `agentbundle` ≥ 0.22.0 (`pip install agentbundle`)

---

## Step 1 — Create the catalogue layout

A catalogue is a directory with a `catalogue.toml` at its root and a packs directory
containing at least one pack.

```text
my-catalogue/
  catalogue.toml          # catalogue metadata and distribution config
  packs/
    my-pack/
      pack.toml
      .apm/
      ...
```

`catalogue.toml` has required fields across five nested tables. See
[Catalogue format reference](../../_reference/catalogue-format.md) for the complete
schema — the full surface spans ~20 fields and is not shown inline here.

---

## Step 2 — Generate `marketplace.json`

Before running `catalogue lint`, generate `marketplace.json` by running the self-host
command. The linter requires this file (CAT-L002).

```bash
agentbundle catalogue self-host --root . --write
```

This writes `marketplace.json` (and related generated outputs declared in
`catalogue.toml`) into your working tree. Commit the result.

---

## Step 3 — Lint

```bash
agentbundle catalogue lint --root .
```

Exits 0 on a clean catalogue. Exits 1 on validation failures (listed on stdout).
Exits 2 on CLI usage errors.

Fix all reported issues before proceeding.

---

## Step 4 — Verify

```bash
agentbundle catalogue verify --root .
```

Runs the full admission check — schema, structural invariants, and distribution
consistency. Pass `--format json` to get machine-readable output for CI annotation.

---

## Step 5 — Publish via CI

Once `lint` and `verify` both exit 0 locally, the catalogue is ready for a CI
release pipeline.

For the full publication contract — packaging command, channel descriptor shape,
exit codes, phase ordering, and responsibility boundary between the CLI and your CI
system — see the [Catalogue CI contract](../reference/catalogue-ci-contract.md).
