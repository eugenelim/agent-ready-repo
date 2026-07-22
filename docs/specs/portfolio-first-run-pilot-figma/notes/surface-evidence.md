# Surface evidence: portfolio-first-run-pilot-figma

**Date:** 2026-07-22
**Grading:** Limited
**Spec AC:** AC16

## Path described

Tutorial: `docs/guides/figma/tutorials/figma-first-session.md`

The described path:
1. Install `credential-brokers` pack (`agentbundle install credential-brokers --scope user`)
2. Install `figma` pack (`agentbundle install figma --scope user`)
3. Generate a Figma PAT at Figma → Settings → Security → Personal access tokens
4. Run `credential-setup` skill (user-interactive; stores credentials in the OS keychain on macOS/Windows, or a locked-down local file on Linux)
5. Ask the agent "Check my Figma connection" → agent runs `figma check` (exit 0) + `figma whoami` → confirms account name
6. Ask the agent to read a Figma file's structure (starter-prompt + file URL) → agent runs `figma get-file <KEY> --depth 1` then `get-file <KEY> --depth 2` → returns pages and top-level frames

## Basis for the described path

The tutorial was authored from:
- `packs/figma/.apm/skills/figma/SKILL.md` — the skill's documented instruction set (Steps 1–8, dispatch table, exit-code semantics)
- `packs/figma/.apm/skills/figma/scripts/figma.py` — the CLI implementation (subcommand set, exit-code taxonomy, token-refusal rules)
- `packs/figma/.apm/skills/figma/references/creds-schema.toml` — the `FIGMA_API_TOKEN` key declaration
- `packs/figma/pack.toml [pack.first-value]` — the contract fields (starter-prompt, expected-result, recovery)
- Tier-A activation eval coverage: `evals/eval_queries.json` — verifies the skill activates on representative prompts (no credentials required)

## Blocker for "Verified" grading

**No Figma PAT was available during this authoring session.** The live auth path (`figma check` → exit 0 → `figma whoami` → account name) was not exercised. The tutorial describes what the documented behavior produces; it has not been confirmed against a live API response.

A live run requires:
1. A Figma account with a valid PAT
2. Access to at least one Figma file with view permission
3. The `behavior-check-for-backend-skills` backlog item providing a reproducible test harness (or a manual session with broker-provisioned test credentials)

## Path to "Verified"

To upgrade this entry to "Verified":
1. Run the tutorial against a live Figma account
2. Record the outcome at each step (credential check output, `whoami` response, file structure response)
3. Redact any PII from `whoami` output (name, email) and any credential fragment before committing
4. Replace this grading with "Verified" and add the dated session record below

The `behavior-check-for-backend-skills` backlog item (`workspace.toml [backlog].open`) is the structured path to repeatable verification.
