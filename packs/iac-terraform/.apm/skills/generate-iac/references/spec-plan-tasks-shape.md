# Spec and plan task shape for IaC work

Load during planning for `generate-iac`. Map governing constraints to the
proposed configuration using repository-native sources and their checked summary.

## Governance-compliance table

List each material choice, its source id and applicable constraint id, and how
the plan satisfies it. Use existing accepted decisions, effective instructions
or explicit caller inputs; no particular record template is required. Stop on
uncertain authority, a conflict or an unresolved material choice. Minor choices
do not each require a decision record.

| Choice | Governing source and constraint | Plan evidence |
| --- | --- | --- |
| Engine and version | Summary source and constraint ids | Confirmed engine/version |
| Account/environment isolation | Summary source and constraint ids | Target and identity boundaries |
| Backend and workspace | Summary source and constraint ids | Locking and isolation |
| Resource recovery | Summary source and constraint ids | Reversibility class and recovery limits |
| Policy and CI authentication | Summary source and constraint ids | Policy checks and OIDC configuration |

## Stage task shape

Keep tasks aligned with the skill's stages. Order implementation tasks by
Foundation → Network → Compute/Data → App → Polish. Mark parallel work only
when files are disjoint and there is no resource or data dependency.

| Stage | Done when | Depends on |
| --- | --- | --- |
| 0 — Governance gate | Bounded discovery with `discover --target`; internal summary; `check-summary` ready | Confirmed root and target paths |
| 1 — Specify | Generic infrastructure names describe the pre-formed intent | Stage 0 |
| 2 — Clarify | Full input list confirmed; dirty input has an explicit snapshot identity | Stage 1 |
| 3 — Plan | Governance-compliance and standards mappings have no unresolved rows | Stage 2 |
| 4 — Tasks | Tier order and dependencies are explicit | Stage 3 |
| 5 — Write | Provider contract and binding standards met; live schema and validation ground every resource | Stage 4 |
| 6 — Verify and review | Gated fmt/validate/plan, policy/security checks, canonical local review and bundle validation pass | Stage 5 |

## Acceptance criteria template

- [ ] Checked summary identifies applicable governing sources and constraints.
- [ ] Target facts and exact source/input identity are confirmed.
- [ ] Provider-contract files match the chosen cloud and execution platform.
- [ ] `<engine> providers schema -json` covers every used resource type.
- [ ] `<engine> fmt -check && <engine> validate && <engine> plan -out=tfplan`
      passes in a fresh run with no saved plan after a failed step.
- [ ] Required policy and security checks pass against the reviewed input.
- [ ] [Infrastructure review](infrastructure-review.md) is complete;
      `check-summary` is `ready` and `check-review` is `pass` before bundle emission.
- [ ] `plan_bundle.py validate` accepts the bundle with the caller's policy.
- [ ] No apply or destroy is run or emitted by authoring.

Optional integrations follow the rule in `generate-iac/SKILL.md`: run them only
after direct checks, stop on refusal or failure, and use no weaker fallback.
