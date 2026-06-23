---
name: operational-safety
description: Progressive-disclosure operational-safety-depth modules for the quality-engineer reviewer. Holds six failure-mode-keyed checklists (state-and-idempotency, blast-radius, environment-isolation, cost-and-teardown, drift-and-rollback, observability-and-smoke) as references/, each grounded in standing operational taxonomy (AWS Well-Architected, Google SRE, the Terraform/Pulumi Day-1/Day-2 split). The work-loop's orchestrator loads only the matching modules and inlines them into the quality-engineer's brief when infra/destructive work is detected; the subagent never self-discovers this skill. Not a reviewer prompt itself — it is the depth library the reviewer reasons from. Carves against security-checklists on the reliability-vs-security lens — security-checklists owns security config while operational-safety owns reliability/ops config.
---

# Skill: operational-safety

This skill is the **depth library** behind the `quality-engineer` agent for
infrastructure and destructive operational work. The reviewer's body carries
the *universal method* (its testability / observability / reliability /
maintainability lens, the severity rubric, the report format). The
*shape-specific depth* — what to actually check at each operational failure
mode — lives here, in six `references/<module>.md` modules, so the agent prompt
stays lean and the depth scales without bloat. It is the operational-lens twin
of [`security-checklists`](../security-checklists/SKILL.md), built on the same
orchestrator-loaded, table-routed mechanism — **no new reviewer** (the CHARTER
three-reviewer ceiling; ADR-0023), no executable code (ADR-0031).

## How it loads (orchestrator-driven, not self-discovered)

**The orchestrator drives loading; the subagent does not.** There is no
mechanism to force a subagent to invoke a skill, skill discovery is
model-invoked and adapter-variable, and the `quality-engineer`'s `tools:` list
does not include a Skill tool. So depth must not depend on the reviewer finding
this library itself.

Concretely, at the work-loop's REVIEW `quality-engineer` step, when the change
is infra/destructive (the destructive/irreversible risk trigger routed it to
full mode, and the diff touches IaC / deploy config / a stateful migration),
the orchestrator:

1. Detects which **operational failure modes** the diff or spec crosses.
2. Loads **only the matching modules** via the deterministic failure-mode→module
   routing table in `work-loop/SKILL.md` (the `operational-safety` table,
   beside the `security-checklists` one).
3. **Inlines the selected modules' content** into the `quality-engineer`
   subagent's brief — so the reviewer receives a focused checklist as prompt
   text, never a path to resolve.

Loaded 1–N per the routing table, never a flat march of all six. Where an
adapter *does* support subagent skill auto-discovery, that is a redundant
convenience layered on top — never the load-bearing mechanism.

## The reliability-vs-security carve (load-bearing)

This library and [`security-checklists`](../security-checklists/SKILL.md) split
infrastructure review along one clean line, and the split must stay clean both
ways:

- **`security-checklists` owns *security* config.** Over-broad IAM, public
  exposure, secrets in state, unencrypted-at-rest, metadata SSRF, CORS — the
  security failure classes. Its `config-misconfig` module is the IaC-security
  home.
- **`operational-safety` (this skill) owns *reliability / ops* config.**
  Idempotent convergence, blast radius, environment isolation, cost/teardown,
  drift/rollback, observability/smoke — the operational failure classes.

The routing therefore assigns **IaC-security → `config-misconfig`**,
**IaC-reliability → `operational-safety`**. Do not duplicate security config
into an operational module, and do not migrate operational config out of where
it correctly lives. When a check seems to belong to both lenses, ask which
*failure* it guards against — a leaked credential is security; a half-applied,
non-convergent stack is reliability.

## The three-bucket delegation legend

Every check in every module is tagged so the reviewer knows who owns it —
the same legend `security-checklists` uses, read through the operational lens:

- **`tool`** — scanner / CI-gate-owned. Confirm the gate is *wired*; don't
  re-check by hand. The operational analogs of the security scanners are the
  policy-as-code / CSPM scanner (which also feeds the security pass), the
  cost-diff gate, and the plan-parse destroy/replace counter. If the delegated
  gate is **absent**, do not silently skip: either reason the class best-effort
  and flag it `degraded: no gate`, or state the gap explicitly. A silent skip
  is the worst outcome — it looks like coverage.
- **`hybrid`** — the gate surfaces the signal; *you* judge the fix. A plan
  diff or a drift report points at the change, but whether the apply converges,
  whether the destroy is intended, or whether the rollback path is real is
  reasoning work.
- **`reason`** — reviewer-only. Whether the loop is genuinely idempotent,
  whether proposer≠approver holds for a destructive op, whether a smoke probe
  actually exercises the artifact end-to-end — the classes no scanner sees. The
  highest-value findings live here.

## Module index

| Module | Operational failure mode | Grounded in |
|---|---|---|
| [`state-and-idempotency`](references/state-and-idempotency.md) | convergent re-apply, state locking, single-writer | F1.2, F1.3 |
| [`blast-radius`](references/blast-radius.md) | destroy/replace gating, `prevent_destroy`, proposer≠approver | F3.1, F3.2 |
| [`environment-isolation`](references/environment-isolation.md) | throwaway/staging vs prod, separate state/accounts | F3.3 |
| [`cost-and-teardown`](references/cost-and-teardown.md) | cost-ceiling-as-gate, destroy-on-fail, TTL, no orphans | F3.4, F3.5 |
| [`drift-and-rollback`](references/drift-and-rollback.md) | read-only drift detection, known-good re-apply path | F1.4, F2.6 |
| [`observability-and-smoke`](references/observability-and-smoke.md) | active end-to-end probe, log access, health, verify-status | F2.2; taxonomy follow-up |

`state-and-idempotency` (write-path convergence) and `drift-and-rollback`
(divergence detection + recovery) are kept **deliberately separate** — every
major operational taxonomy splits the two (AWS Well-Architected *Change
Management* vs *Failure Management*; Google SRE *Release Engineering* vs
*Incident Response*; Terraform `apply` vs `-refresh-only`; Pulumi Day-1 vs
Day-2). `observability-and-smoke` is its own sixth module, not folded into
reliability prose, because "load the real URL, confirm render, read the logs to
debug a failed smoke" is a distinct active-probe + telemetry concern.
