# How to set up a governance index

A governance index is a single YAML manifest that maps each architectural
decision domain to the ADR(s) and standard file(s) that bind it. An agent
(or a new team member) reads the index first and loads only the 2–3 files it
points to, rather than scanning the whole `docs/adr/` tree.

The convention is tool-neutral — it works for any governed repo, not just
Terraform/IaC work. The `generate-iac` skill reads it at Stage 0 when the
`iac-terraform` pack is installed; the `governance-extras` pack ships the
template.

## Prerequisites

- `governance-extras` installed (ships the `seeds/governance/manifest.example.yaml`
  template).
- At least one accepted ADR in `docs/adr/`. The index is a pointer structure —
  if no ADRs exist yet, the index will have placeholder numbers until you
  create them.

## Step 1 — Copy the template

```bash
cp .claude/skills/new-adr/../../../seeds/governance/manifest.example.yaml \
   docs/governance-index.yaml
```

Or ask the agent: "Bootstrap a governance index from my existing ADRs."

The `generate-iac` skill will also offer to bootstrap the index on first use
if none exists.

## Step 2 — Fill in your ADR numbers

Replace each `ADR-NNNN` placeholder with the actual ADR number that covers
that domain. Use the `new-adr` skill to create any missing ADRs (see
[how to record a decision](new-adr.md)).

For IaC-specific domains (`state`, `layout`, `iam`, `tagging`, `networking`,
`pipeline_auth`, `remediation`), the `new-adr` infra mode gives you the right
framing question for each.

## Step 3 — Add standard references

The `standards:` field lists paths relative to your repo root. These are the
canonical standards documents that apply to the domain. For IaC work, the
`iac-terraform` pack's references (e.g. `terraform-standard.md`) are loaded
by the agent — you do not need to list pack-internal references here. List only
your repo's *own* standard files.

```yaml
domains:
  tagging:
    question: "What tags/labels are mandatory on every resource?"
    adrs: [ADR-0004]
    standards: [docs/standards/tagging.md]
```

## Step 4 — Commit the index

The index lives in the repo root or in `docs/` — choose one and be consistent.
Commit it as a normal PR. The governance index is a living document; update the
`adrs:` list when a new ADR supersedes an old one.

## Adding a new domain

Add a new domain row when:
- A new category of architectural decision emerges that no existing row covers.
- You extend a pack's standards with a repo-specific standard (e.g. a custom
  tagging standard that overrides the pack default).

The `generate-iac` skill adds IaC domain rows (`state`, `layout`, `iam`,
`tagging`, `networking`, `pipeline_auth`, `remediation`, `observability`)
automatically if they are absent during Stage 0.

## Optional lint

You can add a CI check that reads the index and verifies each referenced ADR
file exists at the path encoded in the filename (e.g. `docs/adr/0004-*.md`
for `ADR-0004`). This prevents stale references after ADR renumbering. The
lint is optional — the manifest's value is primarily read-time speed, not
compile-time enforcement.

## Relationship to `new-adr`

The governance index is the *consumer* of `new-adr`'s output — it references
ADR numbers, never ADR content. The index is authored once (or updated as the
architecture evolves); individual ADRs are authored by `new-adr` for each new
decision. See [how to record a decision](new-adr.md).
