# Plan: iac-terraform-remote-exec

- **Spec:** [`spec.md`](spec.md)
- **RFC:** [RFC-0070](../../rfc/0070-iac-terraform-remote-exec-platforms.md)
- **Status:** Done
- **Verification mode:** goal-based check (Markdown files — no test runner)

## Assumptions

1. The existing `generate-iac` SKILL.md structure (Inputs table, Stage sequence
   code block, References section, Anti-patterns section) is stable — confirmed
   by reading the file.
2. `references/remote-exec/` directory does not yet exist — confirmed.
3. Both platforms use `backend "remote"` / `cloud {}` transparently via the
   `terraform` / `tofu` CLI — no API scripting needed in the skill.

## Tasks

### T1 — New `references/remote-exec/hcp-terraform.md`

**Depends on:** none

**Done when:** file exists with all 8 required sections (config block, auth/token guard, dynamic credentials, remote operations, run states, policy enforcement, CI trigger notes, bootstrap).

**Approach:** write per RFC-0070 Proposal §1 and the pre-researched detail from the authoring session.

### T2 — New `references/remote-exec/scalr.md`

**Depends on:** none

**Done when:** file exists with all 8 required sections (config block + naming trap, auth, provider integrations, three-tier hierarchy, OpenTofu compat, OPA enforcement, CI trigger notes, bootstrap).

**Approach:** write per RFC-0070 Proposal §1.

### T3 — Update `generate-iac` SKILL.md (5 edits)

**Depends on:** none

**Done when:**
1. Inputs table has `Remote execution platform` row with constraint note
2. Stage 3 loads `references/remote-exec/<platform>.md` when `platform ≠ none`
3. Stage 5 has backend branching section
4. Stage 5 or new WRITE OUTPUT step emits `REMOTE_EXEC_SETUP.md`
5. References section lists `references/remote-exec/<platform>.md`
6. Anti-patterns has 2 new never-emit rules

**Approach:** targeted Edit calls to the existing SKILL.md.

### T4 — Update `reconcile-iac` SKILL.md (1 edit)

**Depends on:** none

**Done when:** Procedure section has backend-type detection step before existing step 1; ADR compliance domain map includes `terraform { cloud {} }` → `state`.

**Approach:** Edit the Procedure code block.

### T5 — Update `opentofu-differences.md` (1 edit)

**Depends on:** none

**Done when:** the "HCP Terraform cloud blocks" bullet includes a Scalr recommendation note for OpenTofu + remote exec.

**Approach:** Edit that single bullet.

## Dependency order

T1, T2, T3, T4, T5 are all independent — no data dependencies. Execute in parallel.

## Deferred

None.
