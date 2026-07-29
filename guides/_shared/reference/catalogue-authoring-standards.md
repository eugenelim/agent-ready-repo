---
title: "Catalogue authoring standards"
summary: "Routing table for every catalogue authoring standard: pack manifests, skill frontmatter, profile format, lint and verify commands, CI contract, and packaging."
pack: _shared
kind: reference
status: stable
---

# Catalogue authoring standards

Machine contracts in `contracts/` are normative. These guides explain how to use them.

Each section below names the authoritative contract and points to the guide that
explains it. When a guide and its contract disagree, the contract is right.

---

## 1. Catalogue manifest

**Contract:** `contracts/catalogue.schema.json`

- `guides/_shared/how-to/create-a-catalogue.md` — scaffold a new catalogue with
  `agentbundle catalogue init`.
- `guides/_shared/how-to/create-external-catalogue.md` — self-hosted or enterprise-deployed
  variant. (Available in the full guide library; not bundled in this scaffold.)

---

## 2. Pack manifest

**Contract:** `contracts/pack.schema.json`

The `pack.toml` file at the root of every pack. Required fields: `[pack]` with `name`
and `version`; `[pack.adapter-contract]` with `version`.

- [packs/README.md](../../../packs/README.md) — pack layout, versioning rules, lint commands.
- [packs/AGENTS.md](../../../packs/AGENTS.md) — agent-facing schema map and primary workflow.

---

## 3. Pack README standard

A pack README serves adopters, not contributors. It states the pack's intent and the
user journey it serves — not a skill inventory. See the `_example` pack for a template.

- [packs/_example/README.md](../../../packs/_example/README.md) — canonical example.

---

## 4. Pack layout

Primitive sources live under `.apm/` and are projected per adapter by `catalogue self-host`.

| Source directory | Primitive type |
|------------------|----------------|
| `.apm/skills/` | Skills |
| `.apm/agents/` | Subagents |
| `.apm/hooks/` | Hook bodies |
| `.apm/hook-wiring/` | Hook wiring |
| `.apm/commands/` | Commands |

---

## 5. Skill frontmatter and body

**Contract:** `contracts/skill.schema.json`

Every skill is a Markdown file with YAML frontmatter. Required frontmatter keys:
`title`, `description` (≤ 1024 characters), `kind`.

- `guides/_shared/how-to/author-a-skill.md` — frontmatter key list, body structure,
  naming rules, progressive-disclosure pattern, three-tier dependency policy, and eval
  coverage. (Available in the full guide library; not bundled in this scaffold.)

---

## 6. Skill body and progressive disclosure

Long skills use progressive disclosure: a brief required-reading summary at the top,
with detail sections the agent loads on demand. This keeps context usage bounded.

See `guides/_shared/how-to/author-a-skill.md` for the full pattern.

---

## 7. Profile format

**Contract:** `contracts/profile.schema.json`

A profile is a blessed combination of packs installed in a single command.

- [profiles/README.md](../../../profiles/README.md) — profile layout and authoring rules.
- [profiles/AGENTS.md](../../../profiles/AGENTS.md) — agent-facing schema map.
- `guides/_shared/how-to/design-a-profile.md` — step-by-step authoring guide. (Available
  in the full guide library; not bundled in this scaffold.)

---

## 8. Lint and verify commands

```bash
agentbundle catalogue lint --root .           # style and basic correctness
agentbundle catalogue verify --root .         # full validation (lint + schema + self-host drift)
agentbundle catalogue self-host --root . --check  # scaffold projection drift check
```

Run all three before opening a PR. The CI contract (section 9) details the exit codes.

---

## 9. CI contract

**Contract:** `contracts/catalogue-ci-contract.md` (in this scaffold)

Provider-neutral validation, packaging, publication, and evidence requirements for a
catalogue CI pipeline.

- [catalogue-ci-contract.md](catalogue-ci-contract.md) — exit codes, required steps,
  evidence manifest.

---

## 10. Package and publication

```bash
agentbundle catalogue package --root . --output dist/
```

Produces a distributable archive with a content manifest. See the CI contract (section 9)
for the full pipeline sequence.

---

## Optional pack integrations

> **Not yet available.** Wave 2 of the catalogue-contracts initiative will define the
> `[[pack.integrations]]` convention for declaring optional cross-pack composition.
> This section will be filled in when that wave ships.

---

## Journey format

> **Not yet available.** Wave 4 of the catalogue-contracts initiative will define the
> journey format and its contract. This section will be filled in when that wave ships.
