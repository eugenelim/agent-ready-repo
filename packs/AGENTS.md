# packs/

This directory holds every first-party pack in the catalogue. Each pack is a self-contained directory that agentbundle reads, validates, and installs into an adopter's repo.

## Pack layout

| Path | Purpose |
|---|---|
| `pack.toml` | Pack manifest — name, version, description, scope, dependencies, adapter contract, evals allowlist, maintainer metadata. The source of truth for what the pack declares. |
| `README.md` | Install manifest for adopters — what ships, the skills table with adapter support, install command, compatibility, and first-value guidance. |
| `.apm/skills/<name>/SKILL.md` | Skill definition. Projected into the adapter's tool directory at install time (e.g. `.claude/skills/<name>/`). |
| `.apm/skills/<name>/references/` | Per-skill reference files loaded on demand by SKILL.md instructions. Never projected; never shared via a central directory — see **Shared reference files** below. |
| `.apm/agents/<name>.md` | Subagent definition. Projected into the adapter's agent directory at install time (e.g. `.claude/agents/<name>.md`). |
| `seeds/` | Files delivered into the adopter's repo on first install (repo-scope packs only). Seeds are scaffold — they carry placeholder content, not instance content. |
| `evals/` | Activation eval queries (`evals/eval_queries.json`) and LLM-judge rubrics (`evals/evals.json`) for skill-level activation testing. Catalogue-internal; never installed. |
| `docs/` | Concept anchor and pack-local guides — never projected or installed; travels in Artifactory packages. `docs/index.md` explains what the pack IS, why it exists, and how it relates to other packs (distinct from README.md, which is the install manifest). |
| `AGENTS.md` | Pack-local agent context for agents working on the pack itself — migration notes, naming conventions, pack-specific build rules. |

## Skill reference files

No shared `references/` directory exists. References are copied per-skill; each skill stands alone.

- **Intra-pack**: source copy says `> Note: this reference is intentionally duplicated into \`<skill>\`'s \`references/<file>\`.`; receiving copy says `duplicated from`. Copies stay byte-identical except the note wording.
- **Cross-pack** (e.g. `digital-experience-contract.md`): file carries `schema-version:` in YAML frontmatter; all copies byte-identical. When updating, grep for the filename and update every copy in the same commit.
