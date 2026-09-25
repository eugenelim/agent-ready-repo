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

## Re-run a self-hosted init

Run the same command again when you want to recreate a catalogue from its
recorded recipe:

```bash
agentbundle catalogue init my-catalogue \
  --preset self-hosted \
  --source /path/to/source-catalogue
```

The command reads `.agentbundle/self-host-state.json` in the target. With no
replacement flags, it reuses the recorded catalogue identity and selected packs
and profiles. Pass an identity, `--pack`, or `--profile` flag to replace that
recorded value for this run.

The re-run overwrites files that the earlier init wrote. It does not restore
the recorded attribution, tooling, or guide mode: omit those flags and their
safe defaults apply.

After a re-run, use `agentbundle catalogue verify --root my-catalogue` to check
the recreated catalogue.

---

## Check a derived catalogue against its source

`agentbundle catalogue sync` compares a derived catalogue against its source
catalogue, and can bring it up to date. `--dry-run` and `--check` are both
read-only — neither writes a file to the target:

```bash
# Preview the plan sync would apply: which files would update, which would
# get a `.upstream.<ext>` companion because you edited them, and which the
# source no longer has.
agentbundle catalogue sync my-catalogue --source /path/to/source-catalogue --dry-run

# Answer whether the target still matches the source, without printing a plan.
agentbundle catalogue sync my-catalogue --source /path/to/source-catalogue --check
```

The plan names the source catalogue only when the target's recorded
`--attribution` is `attributed`. Under the default `white-label`, the plan
and its output never disclose the source's identity — the same rule `init`
follows for the files it writes.

Supplying neither `--dry-run` nor `--check` runs the plan for real — see
§ Apply upstream changes below.

---

## Apply upstream changes to a derived catalogue

Running `agentbundle catalogue sync` with neither `--dry-run` nor `--check`
writes the plan it would otherwise only print. It asks for confirmation
first and writes nothing until you give it:

```bash
agentbundle catalogue sync my-catalogue --source /path/to/source-catalogue
```

```text
<the printed plan, same shape as --dry-run>
Apply this plan? [y/N]:
```

Answer `y` at the prompt, or pass `--yes` to skip it — useful in a script or
CI job where nothing is watching the terminal:

```bash
agentbundle catalogue sync my-catalogue --source /path/to/source-catalogue --yes
```

Anything else — `n`, an empty answer, or piping the command with no terminal
attached and no `--yes` — leaves the target directory exactly as it was; the
run writes nothing until consent is given.

**What a run writes.** A file you never edited updates to the source's bytes.
A file you edited keeps your bytes; the source's version lands beside it as
`<name>.upstream.<ext>` instead. Resolve that companion yourself — merge
whatever changed into your file, then delete the companion — before your next
`agentbundle adapt --ci` run, which refuses while an unresolved companion
remains. A file the source stopped shipping is removed only if this
catalogue's recorded state carries it; the run never removes a file it never
knew about. And a file the source added to a pack this catalogue already has
selected is reported on the plan but not written — sync refreshes what you
already selected, it never widens the selection with a new upstream file.

**Scope the run to part of the catalogue** with one or more of these flags
instead of syncing everything:

```bash
# Only these packs (repeatable)
agentbundle catalogue sync my-catalogue --source /path/to/source-catalogue --pack core --pack governance-extras

# Only this profile
agentbundle catalogue sync my-catalogue --source /path/to/source-catalogue --profile engineering

# Only guides/_shared/
agentbundle catalogue sync my-catalogue --source /path/to/source-catalogue --guides

# Only one package destination
agentbundle catalogue sync my-catalogue --source /path/to/source-catalogue --package credbroker
```

Naming a pack or profile you have not selected before adds it to this
catalogue's recorded selection for good — a later, unscoped sync keeps
syncing it too. `catalogue.toml`, `tests/conformance/`, and identity fields
move only on a full, unscoped sync.

### Syncing the package destinations

`--package` takes two names, and each is present only under its own
condition:

| Name | What it syncs | Present when |
| --- | --- | --- |
| `credbroker` | `packages/credbroker/` | your catalogue selects the `credential-brokers` pack — in either tooling mode |
| `agentbundle` | `.agentbundle/tooling/`, the whole vendored tooling root | you sync with `--tooling vendored` |

The `agentbundle` destination is the whole root, not just the `agentbundle/`
directory inside it. Your vendored engine and the vendored
`packs/catalogue-curation/` copy beside it were installed as a pair, so they
move as a pair.

Asking for a destination that is not present is refused rather than reported
as a successful sync of nothing — `--package agentbundle` without
`--tooling vendored` stops and tells you which flag is missing. A run that
claimed success would also refresh your recorded pin, leaving it describing a
subtree the run never wrote.

Packages are written **last**, after every pack, profile, guide and
derivation-wide path has landed. If a package write fails, the whole run is
rolled back.

**If you `pip install -e` your vendored engine, sync will refuse to overwrite
it.** A vendored sync whose target supplies the `agentbundle` you are running
stops before it writes anything, because replacing that code mid-run means
what executes afterwards is not what you reviewed. To take upstream changes
into that tree, run the sync from an `agentbundle` installed somewhere else —
a virtualenv or a plain `pip install agentbundle` — and it will proceed.

This refusal covers the vendored engine only. `packages/credbroker/` is a
build input your catalogue resolves by relative path, not an install source,
so syncing it cannot replace running code.

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
