# Platform Engineering

Turn infrastructure intent into reviewed Terraform, collect release evidence, and validate a change in a temporary environment before your production decision.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Run this inside the target repository:

```bash
agentbundle install --pack platform-engineering
```

The pack installs with no required dependency; core and repo-governance are optional integrations. The workflows use repository instructions, accepted decisions and explicit inputs directly; core reviewers are optional additions after required local checks. Their refusal stops the step without a weaker fallback.

Terraform authoring needs `terraform` or `tofu` on your path. Release-only work needs no Terraform tooling. Protected GitHub Actions execution needs authenticated GitHub CLI access, the repository's workflows and separate execution authority.

## What your agent can do

- Check governing sources and stop on conflicts or missing authority before writing infrastructure.
- Write schema-grounded Terraform, run format, validation, policy and security checks, and stop at a reviewed plan with a pinned digest.
- Audit managed-resource drift and propose a disposition for each resource without applying changes.
- Collect existing build, check and provenance evidence into a release candidate, or name the missing evidence.
- Admit the candidate and run focused reliability and security reviews before release stages.
- Run authorized protected GitHub Actions execution for a temporary deployment, observe results, route repairs and check cleanup.
- Write service objectives and prepare a release-readiness record for your production decision.

## Skills and agents

- **`generate-iac`** authors governed Terraform or OpenTofu and stops at a pinned plan. It never runs `apply`.
- **`reconcile-iac`** audits plan-visible drift and checks infrastructure diffs. It never applies on its own; resources outside Terraform state are outside its audit.
- **`prepare-release-handoff`** collects existing evidence into a candidate or reports named gaps. It runs no build, test, plan or fetch.
- **`release-loop`** drives release admission, focused review and authorized temporary deployment with a round cap, a cost budget and cleanup checks.
- **`define-slo`** writes an OpenSLO YAML document at `slos/<service>.yaml` for release error-budget checks.

The **`release-lead`** agent runs the release loop. **`release-reliability-reviewer`** and **`release-security-reviewer`** check the admitted candidate against their focused checklists.

A collector `ready`, admission, review `pass` or stage progression grants no execution or production authority. Run `check-review` on both focused review records and `check-stage` before advancing stages. Both records must pass at pre-deploy, post-deploy and final. Final also checks budgets, cleanup and remaining risks and returns `human-decision-required`.

## Works with

Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, Kiro CLI and Kiro IDE. Terraform and OpenTofu share a baseline; engine-specific guidance loads when needed. The workflows use the repository's deploy, smoke and teardown artifacts and name missing artifacts before execution.

## Migration

This pack replaces `iac-terraform` and `release-engineering`. See the [migration how-to](../../guides/platform-engineering/how-to/migrate-from-iac-terraform-and-release-engineering.md) for the full guide.

Inventory every installed old-pack row by adapter and scope first. If the old packs use different scopes for one adapter, choose one scope for the new pack before uninstalling. Replace `<a>` and `<s>` below with each installed adapter and scope (`repo` or `local`). Run only the uninstall commands for rows that exist.

1. Uninstall **every** old-pack row, for all adapters and scopes, before any new install:

   ```bash
   agentbundle uninstall --pack iac-terraform --adapter <a> --scope <s>
   agentbundle uninstall --pack release-engineering --adapter <a> --scope <s>
   ```

2. Install the new pack for each adapter at its chosen scope:

   ```bash
   agentbundle install <catalogue> --pack platform-engineering --adapter <a> --scope <s>
   ```

`<catalogue>` must contain `platform-engineering`; move any older source pin forward. Do not use upgrade as a substitute for the uninstall phase. Uninstall keeps adopter-edited files; install writes shipped content beside a kept edit as an `.upstream` companion. An old-pack row at another scope is not refused by the installer, so phase 1 must remove every row before phase 2. Shared paths at the same scope can cause a refusal; do not use that as the migration guard. The rename hint covers only one old pack and adapter at a time; use the full sequence above for multiple rows.

### Rollback

The pinned pre-consolidation ref is `42849d1e7`. First uninstall every `platform-engineering` row for every adapter and scope:

```bash
agentbundle uninstall --pack platform-engineering --adapter <a> --scope <s>
```

Merge each `.upstream` companion beside a kept edit into its file, then delete the companion: the old install refuses while one remains.

Then reinstall each old pack at its original adapters and scopes from a catalogue pinned to `42849d1e7`:

```bash
agentbundle install git+https://github.com/eugenelim/agent-ready-repo@42849d1e7 --pack iac-terraform --adapter <a> --scope <s>
agentbundle install git+https://github.com/eugenelim/agent-ready-repo@42849d1e7 --pack release-engineering --adapter <a> --scope <s>
```

Edited files kept by uninstall survive both directions. There is no automatic install backup; a file you delete during migration is not recovered.

## Details

Scope: repo (default) · Version: 1.0.0 · Source: `packs/platform-engineering/`
