# environment-isolation — throwaway/staging vs prod, separate state/accounts

> **Loaded when:** the change provisions or iterates against an environment
> that is, or could touch, production — or where the iteration loop needs a
> safe place to fail that is not prod.
> **Grounded in:** F3.3 (environment isolation by account/state boundary).
> Operational taxonomy: AWS multi-account-per-stage; separate state backends as
> the IaC-level isolation enforcement.
> **Delegation legend:** `tool` = scanner / CI-gate-owned · `hybrid` = gate
> surfaces the signal, you judge the fix · `reason` = reviewer-only judgment.

Iterate **away from prod**. The strongest isolation unit is the
account / subscription / project boundary; separate state enforces it in IaC.
The agentic refinement loop — apply, observe, fix, re-apply — belongs in a
throwaway or staging environment, never against the production stack.

## Implementation checks

- `reason` **Iteration target is not prod.** The change's apply/test/teardown
  loop runs against a throwaway or staging environment isolated from
  production. Flag any iteration that converges by repeatedly applying to prod.
- `reason` **State backends are separated by stage.** Staging credentials and
  state cannot reach production resources — separate state backends (not a
  shared backend with a workspace toggle that a typo can cross) enforce the
  boundary. A single shared state across stages is the finding.
- `reason` **Account / subscription / project boundary where the blast radius
  warrants it.** For high-blast-radius infra, the strongest isolation is a
  distinct account boundary with guardrail policies, not just a namespace. Note
  where the isolation is weaker than the blast radius justifies.
- `hybrid` **Credentials are stage-scoped.** The credentials the change runs
  under are scoped to the target stage; a smoke or teardown step cannot
  accidentally authenticate against prod. Confirm the scoping; judge whether the
  scope is genuinely narrow. *(Carve note: the failure guarded here is the
  iteration loop converging on prod — a reliability/blast-containment failure;
  whether a grant is over-broad for **privilege-escalation** purposes is the
  security lens, owned by `security-checklists`' `config-misconfig`.)*

## Established-pattern bypass

Resolve the repo's sanctioned environment model — the per-stage account map,
the separate-state convention, the ephemeral-per-PR environment harness — and
flag a change that points a new resource at the shared/prod backend instead of
the stage-isolated one.

*Illustrative only (never normative):* an AWS account-per-stage layout with
separate Terraform state backends, or per-PR ephemeral environments, exhibit
this shape — but the check is the *property* (isolation by account/state
boundary), not any one tool or cloud.
