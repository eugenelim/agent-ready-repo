---
title: How to create a self-hosted catalogue
summary: Derive, brand, validate, and package an owned catalogue from an existing source without losing provenance or safety rails.
pack: _shared
kind: how-to
---

# How to create a self-hosted catalogue

**Use this guide when** you want to create an enterprise-derived or domain-specific
catalogue from an existing source catalogue — for example, rebranding a public catalogue
for your organization or customizing a set of packs for a restricted environment.

**Prerequisites:**
- `agentbundle` installed (`python -m pip install agentbundle`)
- A source catalogue accessible at a local path
- An empty (or nonexistent) target directory

---

## Quick start

```bash
agentbundle catalogue init my-catalogue \
  --preset self-hosted \
  --source /path/to/source-catalogue \
  --name my-org-catalogue \
  --display-name "My Org Catalogue" \
  --owner-name "Platform Engineering" \
  --owner-email "platform@example.com"
```

This copies selected packs and profiles from the source, generates a `catalogue.toml`
with your identity fields, and runs a fail-closed leak check before writing anything.

---

## Tooling modes

### External tooling (default)

The curation tools (`catalogue-curation` pack, `agentbundle` CLI) are installed from
the registry — not embedded in the target directory.

```bash
agentbundle catalogue init my-catalogue \
  --preset self-hosted \
  --source /path/to/source \
  --tooling external
```

After init, follow the printed next steps to install `catalogue-curation` in your target.

### Vendored tooling

For air-gapped environments, use `--tooling vendored`. This copies the agentbundle
source and `catalogue-curation` pack into `.agentbundle/tooling/` inside the target.

```bash
agentbundle catalogue init my-catalogue \
  --preset self-hosted \
  --source /path/to/source \
  --tooling vendored
```

Then install from the vendored copy:

```bash
python -m pip install -e my-catalogue/.agentbundle/tooling/agentbundle/
```

---

## Identity modes

### White-label (default)

All source-catalogue identity strings (name, owner, URL) are replaced with your target
values. The init fails if any source identity survives the transformation.

```bash
agentbundle catalogue init my-catalogue \
  --preset self-hosted \
  --source /path/to/source \
  --attribution white-label \
  --repository-url https://example.com/my-catalogue
```

### Attributed

Source identity is preserved but only allowed in designated attribution surfaces
(`catalogue.toml` and `ATTRIBUTION.md`). Use this when you want to credit the upstream
source publicly.

```bash
agentbundle catalogue init my-catalogue \
  --preset self-hosted \
  --source /path/to/source \
  --attribution attributed
```

---

## Selecting packs and profiles

By default, all packs (except `catalogue-curation`, which is tooling) and all profiles
are copied. Use `--pack` and `--profile` to narrow the selection:

```bash
agentbundle catalogue init my-catalogue \
  --preset self-hosted \
  --source /path/to/source \
  --pack core \
  --pack governance-extras \
  --profile engineering
```

---

## Guide inclusion

Use `--guides selected` (default) to copy `guides/_shared/` from the source, or
`--guides none` to omit guides entirely:

```bash
agentbundle catalogue init my-catalogue \
  --preset self-hosted \
  --source /path/to/source \
  --guides none
```

---

## Dry run

Preview what would be created without writing any files:

```bash
agentbundle catalogue init my-catalogue \
  --preset self-hosted \
  --source /path/to/source \
  --dry-run
```

---

## Packaging for distribution

Once the catalogue is initialized and customized, package it for Artifactory upload:

```bash
# Runtime archive (standard distributable)
agentbundle catalogue package \
  --root my-catalogue \
  --bundle my-org \
  --release 1.0.0 \
  --channel stable \
  --output /path/to/output

# Source archive (for self-hosted downstream catalogues)
agentbundle catalogue package \
  --root my-catalogue \
  --bundle my-org \
  --release 1.0.0 \
  --channel stable \
  --output /path/to/output \
  --flavor source
```

The `--flavor source` archive includes `catalogue.toml`, packs, profiles,
`guides/_shared/`, and legal files. It also emits a `self-hosted-source-manifest.json`
with `kind = agentbundle-self-hosted-source` for downstream verification.

---

## Verifying the result

After initialization, verify the target catalogue is well-formed:

```bash
agentbundle catalogue verify --root my-catalogue
```

---

## All flags

| Flag | Description | Default |
|---|---|---|
| `--preset self-hosted` | Enable self-hosted init | — (required) |
| `--source PATH` | Source catalogue root | — (required) |
| `--tooling external\|vendored` | Tooling mode | `external` |
| `--attribution white-label\|attributed` | Identity mode | `white-label` |
| `--guides none\|selected` | Guide inclusion | `selected` |
| `--name NAME` | Catalogue identifier | Derived from target dirname |
| `--display-name TEXT` | Human-readable name | Title-cased from `--name` |
| `--description TEXT` | One-sentence description | Auto-generated |
| `--owner-name TEXT` | Maintainer name | Derived from display name |
| `--owner-email EMAIL` | Maintainer email | Empty (prompted on TTY) |
| `--repository-url URL` | Repository URL | Empty |
| `--pack NAME` | Pack to include (repeatable) | All packs |
| `--adapter NAME` | Adapter to include (repeatable) | All adapters |
| `--profile NAME` | Profile to include (repeatable) | All profiles |
| `--dry-run` | Preview without writing | Off |
| `--format table\|json` | Output format | `table` |
