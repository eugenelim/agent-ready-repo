# Spec: iac-terraform-remote-exec

<!-- Mode: full (structural change — new reference directory, new public clarify input) -->

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0070](../../rfc/0070-iac-terraform-remote-exec-platforms.md) — Remote execution platforms for `iac-terraform`
- **Brief:** none
- **Discovery:** none
- **Shape:** mixed — new `remote_exec_platform` clarify input + two new reference files + backend branching in generate-iac + backend-type detection in reconcile-iac

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `iac-terraform` pack generates cloud-native state backends (S3/GCS/Azure
Blob) only. Adopters running HCP Terraform (HashiCorp's managed remote execution
SaaS) or Scalr (a Terraform-compatible commercial SaaS alternative) get wrong backend configs.

This spec adds `hcp-terraform` and `scalr` as first-class options for the
`remote_exec_platform` clarify input in `generate-iac`. The change is additive —
`platform = none` (vanilla CI) remains the default and is unchanged.

## Boundaries

### Always do

- Add `Remote execution platform` row to `generate-iac` Inputs table
- Load `references/remote-exec/<platform>.md` in PLAN stage when `platform ≠ none`
- Branch backend generation in WRITE TF stage per platform
- Emit `REMOTE_EXEC_SETUP.md` when `platform ≠ none`
- Add 2 new never-emit rules (deprecated `backend "remote"` to TFC; `cloud {}` for OpenTofu)
- Add `backend "remote"` platform-type detection step to `reconcile-iac` Procedure
- Add Scalr OpenTofu recommendation to `opentofu-differences.md`
- Ship two new reference files: `references/remote-exec/hcp-terraform.md` and `references/remote-exec/scalr.md`

### Ask first

- Adding a remote-exec platform beyond `hcp-terraform` / `scalr` — requires a
  new reference file and a new RFC or ADR.
- Bumping the pack version (`pack.toml` / `plugin.json`) for these reference
  files — the no-bump is a documented decision (see Never do); reverse it with
  a human confirmation first.

### Never do

- Modify `pack.toml`, `plugin.json`, or any CI workflow — the reference files
  are skill-internal; the published pack interface has not changed. A version
  bump is deferred to the next pack release cycle. **This is an intentional
  no-bump decision**: governance docs (RFC, spec) are excepted from the
  `packs/iac-terraform/` scope constraint below.
- Change any code or pack file outside `packs/iac-terraform/` (governance docs
  in `docs/rfc/` and `docs/specs/` are explicitly excepted)
- Add seeds or agents
- Emit `cloud {}` for OpenTofu targets (already banned, now doubly enforced)
- Emit Sentinel (already banned)

## Acceptance criteria

- [x] `generate-iac` SKILL.md Inputs table has a `Remote execution platform` row with `none | hcp-terraform | scalr` and the OpenTofu constraint note
- [x] `generate-iac` SKILL.md Stage 3 (PLAN) mentions loading `references/remote-exec/<platform>.md` when `platform ≠ none`
- [x] `generate-iac` SKILL.md Stage 5 (WRITE TF) has backend branching section covering `none` / `hcp-terraform` / `scalr`
- [x] `generate-iac` SKILL.md has emission of `REMOTE_EXEC_SETUP.md` when `platform ≠ none`
- [x] `generate-iac` SKILL.md Anti-patterns has 2 new never-emit rules
- [x] `generate-iac` SKILL.md References section lists `references/remote-exec/<platform>.md` as a conditional load
- [x] `reconcile-iac` SKILL.md Procedure has a backend-type detection step before the existing step 1
- [x] `opentofu-differences.md` Terraform-only features bullet for HCP Terraform cloud blocks has a Scalr recommendation note
- [x] `references/remote-exec/hcp-terraform.md` exists with: config block + env vars, token scoping guard, dynamic provider credentials + fallback, remote operations model, run states, policy enforcement, CI trigger notes, bootstrap narrative
- [x] `references/remote-exec/scalr.md` exists with: config block + naming trap, auth, provider integrations + fallback, three-tier hierarchy, OpenTofu compatibility, OPA enforcement, CI trigger notes, bootstrap narrative

## Testing strategy

Goal-based verification — grep for key strings that confirm each acceptance criterion:

```bash
# AC1 — Inputs table has Remote execution platform row
grep -q "Remote execution platform" packs/iac-terraform/.apm/skills/generate-iac/SKILL.md

# AC2 — Stage 3 PLAN loads remote-exec/<platform>.md
grep -q "remote-exec/<platform>" packs/iac-terraform/.apm/skills/generate-iac/SKILL.md

# AC3 — Stage 5 WRITE TF has backend branching for all three platforms
grep -q "platform = none" packs/iac-terraform/.apm/skills/generate-iac/SKILL.md && \
grep -q "platform = hcp-terraform" packs/iac-terraform/.apm/skills/generate-iac/SKILL.md && \
grep -q "platform = scalr" packs/iac-terraform/.apm/skills/generate-iac/SKILL.md

# AC4 — REMOTE_EXEC_SETUP.md emission when platform != none
grep -q "REMOTE_EXEC_SETUP.md" packs/iac-terraform/.apm/skills/generate-iac/SKILL.md

# AC5 — never-emit anti-pattern: deprecated backend "remote" to TFC
grep -q "app.terraform.io" packs/iac-terraform/.apm/skills/generate-iac/SKILL.md

# AC6 — References section lists remote-exec/<platform>.md as conditional load
grep -q "references/remote-exec/<platform>.md" packs/iac-terraform/.apm/skills/generate-iac/SKILL.md

# AC5 (second rule) — never-emit anti-pattern: cloud {} for OpenTofu
grep -qi "cloud.*opentofu\|opentofu.*cloud" packs/iac-terraform/.apm/skills/generate-iac/SKILL.md

# AC7 — reconcile-iac detection
grep -q "backend-type\|remote.*exec.*platform\|cloud.*block\|backend.*remote" packs/iac-terraform/.apm/skills/reconcile-iac/SKILL.md

# AC8 — opentofu-differences
grep -q "scalr\|Scalr" packs/iac-terraform/.apm/skills/generate-iac/references/opentofu-differences.md

# AC9/10 — reference files exist
test -f packs/iac-terraform/.apm/skills/generate-iac/references/remote-exec/hcp-terraform.md
test -f packs/iac-terraform/.apm/skills/generate-iac/references/remote-exec/scalr.md
```
