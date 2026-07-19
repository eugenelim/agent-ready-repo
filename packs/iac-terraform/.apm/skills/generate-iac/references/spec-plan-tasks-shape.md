# Spec and plan task shape for IaC work

> **Load this during PLAN** when the work uses `generate-iac` and has a spec.
> It describes the ADR-compliance table and the per-stage task shape that maps
> to `generate-iac`'s 8-stage sequence.

## ADR-compliance table (always in the spec)

Every `generate-iac` spec must include an ADR-compliance table that maps
each architectural decision to the ADR that establishes it. This is the
traceability requirement.

| Decision | ADR | Notes |
| --- | --- | --- |
| Engine choice (terraform / tofu) | ADR-NNNN-engine | Record rationale if non-default |
| Account/project isolation model | ADR-NNNN-isolation | Separate account vs workspace |
| State backend and locking | ADR-NNNN-state | S3/GCS/AzureRM; lockfile mechanism |
| Reversibility class per resource group | ADR-NNNN-reversibility | Use the three-value enum |
| Policy-as-code tool | ADR-NNNN-policy | OPA/Conftest (Sentinel prohibited for OpenTofu targets) |
| CI system | ADR-NNNN-ci | GitHub Actions / ADO / GitLab |
| Credential mechanism | ADR-NNNN-creds | OIDC preferred; no static creds |

Create ADRs using the `new-adr` skill with `mode: infra` (see
`governance-extras` pack, `new-adr/references/infra-decisions.md`).

## Plan task shape

Each task in `plan.md` must map to one of `generate-iac`'s stages.
Use the stage prefix in the task name for traceability:

```markdown
## Tasks

### T0: Stage 0 — ADR gate
Mode: goal-based check
Done when: all ADRs in the compliance table are accepted (or newly drafted in this PR)
Dependencies: none
```

```markdown
### T1: Stage 1 — Scaffold
Mode: goal-based check
Done when: directory layout matches §10 of RFC-0065; terraform init -backend=false exits 0
Dependencies: T0
```

```markdown
### T2: Stage 2 — Provider contract
Mode: TDD (validate four-file contract exists and passes fmt -check / validate)
Done when: all four files exist; `terraform fmt -check` and `terraform validate` pass
Dependencies: T1
```

```markdown
### T3: Stage 3 — Standards application
Mode: goal-based check
Done when: naming, tagging, networking, IAM, and secrets standards applied;
           reviewed by adversarial-reviewer (Clean)
Dependencies: T2
```

```markdown
### T4: Stage 4 — Policy gate
Mode: goal-based check
Done when: conftest test passes against the plan JSON; any DENY outputs resolved
Dependencies: T2
```

```markdown
### T5: Stage 5 — Security scan
Mode: goal-based check
Done when: trivy config exits 0 at CRITICAL/HIGH threshold
Dependencies: T2
```

```markdown
### T6: Stage 6 — Pipeline wiring
Mode: goal-based check
Done when: CI job exists; plan job produces plan artifact; apply job requires human approval
Dependencies: T3, T4, T5
```

```markdown
### T7: Stage 7 — G4 handoff
Mode: manual QA (review handoff artifact set)
Done when: ADR records reversibility class; OPA evidence attached; Trivy evidence attached;
           reversibility enum value per resource group is documented
Dependencies: T6
```

## Acceptance criteria template

```markdown
## Acceptance Criteria

- [ ] All six provider-contract files exist (four per engine if dual-engine)
- [ ] `terraform fmt -check` passes
- [ ] `terraform validate` passes (or `tofu validate` if OpenTofu)
- [ ] `conftest test` exits 0 against plan JSON
- [ ] `trivy config` exits 0 at CRITICAL/HIGH
- [ ] CI apply job requires human approval (no autonomous apply)
- [ ] All resources have a reversibility class in the ADR
- [ ] G4 handoff ADR is accepted or drafted in this PR
```
