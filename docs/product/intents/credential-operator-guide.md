# Credential operators have a setup guide

- **Slug:** `credential-operator-guide`
- **Status:** Fulfilled
- **Fulfilled:** 2026-11-12 eugenelim: published the terminal-only operator setup task and complete setup CLI reference; guide validation, index, title, and repository-reference checks pass.
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **De-risked:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [credential architecture](../../architecture/credentials.md)

## Outcome

An operator can store a credential by following a dedicated credential-broker setup guide.

## Opportunity

Operators need a setup route separate from the author-facing `how-to/add-a-credentialed-skill.md`. The task explains safe terminal entry and resolution checks, while the reference owns complete setup flags and failures.

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

Verified 2026-11-12 against `credential-setup/SKILL.md` and `scripts/setup.py`: the operator task belongs at `guides/credential-brokers/how-to/store-a-credential.md`, linked from the pack guide home. Complete setup arguments, flags, storage choices, and exit codes belong in the existing `reference/credentialed-skill-walkthrough.md`, not the short task page.

## Readiness

- **Route:** direct-light, documentation only.
- **First slice:** publish the operator task and its guide-home link; extend the existing reference with the setup CLI contract.
- **Agent-only proof:** guide schema, index, title, and repository-reference checks pass; setup examples and flags match the parser source. Real credential entry is excluded from verification.
- **Manual dependency:** none for the documentation outcome; an operator runs their own setup and consumer check.

## Non-goals

- Changing credential-broker behavior or the `credential-setup` skill.
- Rewriting the author-facing `add-a-credentialed-skill.md` guide.
- Entering real credentials or claiming a successful service authentication.

## Riskiest assumption

The shipped setup parser and storage branches provide enough evidence for an operator recipe without changing the broker. Verification compares the task and reference with those sources; it does not execute real credential setup.

## De-risk result

2026-11-12. The parser defines one positional `namespace`, three custom flags (`--schema-path`, `--allow-insecure-fallback`, `--allow-permissive-acl`), and argparse's `-h`/`--help`. Against the explanation page's setup baseline, two custom flags need coverage, not three. Its `--bearer-header` and `--auth-header` describe MCP-server consumers, not setup. The implementation also selects an encrypted vault when crypto support is available; its keyring-fallback flag can select that vault, despite older skill prose describing only a dotfile. The new reference follows the implementation and keeps the user-invocation, terminal-only entry, reserved-namespace, and secret-argument restrictions intact. Verdict: supported for source-checked documentation.
