# Credential operators have a setup guide

- **Slug:** `credential-operator-guide`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **De-risked:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [credential architecture](../../architecture/credentials.md)

## Outcome

An operator can store a credential by following a dedicated credential-broker setup guide.

## Opportunity

`guides/credential-brokers/` has the author-facing `how-to/add-a-credentialed-skill.md`, whose summary is `"Keep credentials out of the AI loop ..."`, but it has no guide for the operator who must store a credential. The credential-setup skill already ships without that guide.

## What this absorbs

### credential-operator-setup-guide

Create the missing operator setup guide. `docs/architecture/credentials.md` distinguishes the authoring guidance from operator setup, and `guides/credential-brokers/how-to/add-a-credentialed-skill.md` remains author-facing. **Unblocks when:** ready now — the skill it documents already ships.

## Assumptions

- The guide documents the shipped credential-setup skill rather than changing credential-broker behavior.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

## Current truth

Verified 2026-11-05: `guides/credential-brokers/how-to/` holds only `add-a-credentialed-skill.md`; the `credential-setup` skill ships in `packs/credential-brokers/.apm/skills/credential-setup`. The explanation page already describes the tiers and the flow, so the guide is a short task page.

## Readiness

- **Route:** direct-light, documentation only.
- **First slice:** add `guides/credential-brokers/how-to/store-a-credential.md` and link it from the guide README.
- **Agent-only proof:** the guide link and conventions checks pass, and every command in the page matches the skill's documented flags.
- **Manual dependency:** none.

## Non-goals

- Changing credential-broker behavior or the `credential-setup` skill.
- Rewriting the author-facing `add-a-credentialed-skill.md` guide.

## Riskiest assumption

**Riskiest assumption:** the shipped `credential-setup` skill's flags and prompts match what the existing explanation page describes, so a task page can be written from them. Tested agent-only by comparing each command and flag in the new guide against the skill's `SKILL.md` and scripts, and running the guide link and conventions checks.

## De-risk result

2026-11-05. Extracted every `--flag` from `packs/credential-brokers/.apm/skills/credential-setup/scripts/setup.py` and from the explanation page `guides/credential-brokers/explanation/credentialed-skills.md`. Result: the script defines four options (`--schema-path`, `--allow-insecure-fallback`, `--allow-permissive-acl`, and one more); the page documents only `--allow-insecure-fallback`, which exists. The page's `--bearer-header` and `--auth-header` belong to MCP-server skills, not setup. Nothing in the page contradicts the skill, and the new guide adds the three undocumented options. Verdict: supported.
