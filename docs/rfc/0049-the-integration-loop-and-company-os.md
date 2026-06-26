# RFC-0049: The integration loop — deployed e2e validation, the minimum-regret deploy carve, and the company-OS composition

- **Status:** Open <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Provisional:** a **child of [RFC-0048](0048-autonomous-product-team-operating-model.md)**, which stays provisional until its children (this included) are modelled and drift-aligned. This RFC may amend 0048 (the gate arc, the company-OS framing) as it lands.
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-25
- **Date closed:**
- **Related:** [RFC-0048](0048-autonomous-product-team-operating-model.md) (the discovery+build foundation this extends — it details G0–G4; this details G4→G5) · RFC-0041 (infra-aware `work-loop` — whose deploy *flavor* this graduates into a proper outer loop) · RFC-0025 (`work-loop`) · `operational-safety` pack (the reliability/observability reference library this reuses) · omnigent (the harness; ephemeral-env + option-card support) · promoted design in [`0049-notes/`](0049-notes/)

## The ask

**Recommendation (BLUF).** On top of RFC-0048's discovery + build foundation, add the
**integration loop** — a deployed **e2e-validation outer loop**. `work-loop` is the
**inner loop** (local build, made self-sufficient by local-infra-equivalents); the
**integration-loop** deploys the integrated whole to an **ephemeral environment**, runs
e2e, observes telemetry, and **iterates with the inner loop until the deployed whole
converges**, then ships to prod at **G5** (human-ratified). Carve autonomy by
**minimum-regret**: agents run the inner loop *and* the outer loop **on ephemeral envs**
unwatched; humans gate prod / data / spend / security / irreversible. Add an
**`integration-lead`** agent (the SRE/ops supervisor) — doctrine + reuse of
`operational-safety` + `quality-engineer` + RFC-0041's infra doctrine, **no new runtime**,
running on the omnigent harness. This completes the **"company OS"**: product (discovery)
→ engineering (build) → SRE/ops (integration).

**Why now (SCQA).** *Situation:* RFC-0048 gets the catalogue from vision → locally-built,
deploy-ready code (G0–G4). *Complication:* **deployed infrastructure surfaces what you
can't catch up front** (the irreducible shift-right ~20% — real traffic, infra drift,
version combinations, emergent behavior). RFC-0041 made `work-loop` infra-aware but kept
deploy as a *flavor* of the inner loop, with no ephemeral-env outer loop and no
iterate-until-converge — so the human becomes the relay for deployed findings.
*Question:* how far into deploy + e2e can agents go autonomously, with minimum regret?

**Decisions requested.**
1. **Adopt the inner/outer split.** `work-loop` = inner (local, with local-infra-
   equivalents); a new **`integration-loop`** = outer (ephemeral deploy + e2e + iterate).
   · decide-by: RFC accept · default: adopt.
2. **The minimum-regret carve.** Autonomous on the inner loop **and the outer loop on
   ephemeral envs** (deploy / e2e / iterate / teardown + canary with auto-rollback);
   **human-gated** at first real users/data, data migrations, spend over threshold,
   security boundaries, anything irreversible, and prod ship (G5). The unlock is the
   **reversibility primitives** — ephemeral envs + feature flags + auto-rollback. ·
   decide-by: RFC accept · default: adopt.
3. **Local-infra-equivalents as a build-loop obligation.** Packs/skills produce the
   fidelity ladder — fakes → contract tests (Pact) → Testcontainers → LocalStack →
   docker-compose — so software runs and verifies locally before deploy. · decide-by:
   RFC accept · default: adopt.
4. **Ship `integration-lead`** (the outer-loop supervisor / SRE-ops seat) as an agent +
   an `integration-loop` skill, reusing `operational-safety` + `quality-engineer` +
   RFC-0041. Its **pack home and exact agent shape** (distinct agent vs a `work-loop`
   outer-mode) are OQ1/OQ2. · decide-by: RFC accept (the seat) · default: adopt.
5. **The company-OS composition.** Three loop-teams — product (discovery) → engineering
   (build) → SRE/ops (integration) — on RFC-0048's shared substrate (sidecar + gate arc +
   harness); leads hand off at G3 (brief→spec), at deploy (work→integration), and at G5
   (integration→prod). · decide-by: RFC accept · default: adopt.
6. **Convergence by policy.** Promotion is judged by automated policy (canary metric
   analysis + e2e coverage of the changed surface + flake < 2%) up to the irreversible
   human gate; **DORA** is the health signal. · decide-by: RFC accept · default: adopt.

## Problem & goals

**Diagnosis.** RFC-0048 ends at deploy-ready code. But (a) the inner loop is only autonomous
if the software *runs locally* without the real deployed infra — which requires
local-infra-equivalents the packs must produce; and (b) a deployed, integrated, distributed
system surfaces failures that no pre-deploy testing replicates (shift-right). Without an
outer loop, those findings are relayed by a human — the anti-pattern RFC-0041 named.

**Goals.** Drive the deployed e2e loop end-to-end autonomously *on reversible (ephemeral)
infrastructure*; iterate inner↔outer until convergence; keep humans at the irreversible
exits only; complete the company OS.

**Non-goals.** Running the live product-as-a-managed-service long-term (that's adopter
ops); a new deploy *runtime* (reuse the harness + IaC via `operational-safety`); replacing
`work-loop` (it remains the inner loop).

## Proposal

The full design is in [`0049-notes/01`](0049-notes/01-three-loops-and-company-os.md);
summary:

- **Inner loop = `work-loop`.** Local build + verification via the fidelity ladder
  (fakes → Pact → Testcontainers → LocalStack → docker-compose); run as high up as a
  sub-5-min budget tolerates; push the rest to the outer loop.
- **Outer loop = `integration-loop`** under `integration-lead`: deploy the integrated whole
  to an **ephemeral environment** → run e2e → observe telemetry (observability-driven) →
  feed findings back to the inner loop → redeploy → **converge**.
- **Minimum-regret carve** (the autonomy law applied to deploy): reversible (ephemeral)
  ⇒ autonomous; irreversible (prod/data/spend/security) ⇒ human.
- **Company OS:** three loop-teams on 0048's substrate; the integration-loop is the SRE/ops
  seat, reusing `operational-safety` + `quality-engineer`.

## Options considered

Axis: **where the deploy/e2e validation happens and who drives it.**
| Option | Shape | Verdict |
| --- | --- | --- |
| **A. Do nothing** | stop at 0048's deploy-readiness; humans relay deployed findings | Cost: the shift-right ~20% reaches a human as raw deploy errors — the RFC-0041 relay anti-pattern. Rejected. |
| **B. Deploy flavor inside `work-loop`** (RFC-0041 as-is) | inner loop also does apply + smoke | Conflates fast/local with slow/stateful/deployed; no ephemeral-env iterate-until-converge. Insufficient. |
| **C. A separate outer `integration-loop` on ephemeral envs** ★ | inner/outer split; reversibility primitives | **Recommended** — the DevOps inner/outer ontology; ephemeral envs make it low-regret + autonomous. |
| **D. Full autonomous prod deploy** | agent ships to prod unwatched | Crosses the irreversible line; violates the minimum-regret carve. Rejected. |

## Risks & what would make this wrong

- **Pre-mortem:** ephemeral-env cost sprawl (mitigate: idle auto-shutdown, spot, teardown
  on cycle end); LocalStack/Testcontainers fidelity gaps mean some findings *only* appear
  in the outer loop (that's *why* the outer loop exists); AI-velocity increases change-fail
  rate (2025 DORA) — so canary gating must be strict.
- **Key assumptions (falsifiable):** ephemeral envs make deploy reversible-enough to
  automate; canary metric analysis + e2e coverage + flake are a sufficient promotion
  signal up to the human gate; the inner loop can reach useful fidelity locally.
- **Drawbacks:** ephemeral-env infra is a real adopter prerequisite; contract-testing
  (Pact) has provider-side adoption friction (Deloitte).

## Evidence & prior art

- **Spike/de-risk:** the inner/outer loop + ephemeral-env pattern is the established
  developer-experience ontology (boundary = `git push`); the reversibility-unlocks-autonomy
  claim is the same logic RFC-0048 already uses for tests-as-verifier, applied to deploy.
- **Repo precedent:** RFC-0048 (foundation), RFC-0041 (infra-aware `work-loop` — this
  graduates its deploy flavor), `operational-safety`, `work-loop` supervisor + `loop-cohort`.
- **External prior art** (fetched; full set in [`0049-notes/01`](0049-notes/01-three-loops-and-company-os.md)):
  inner/outer loop ([Telepresence](https://telepresence.io/docs/concepts/devloop)) ·
  contract testing ([Pact](https://docs.pact.io/)) · [Testcontainers](https://testcontainers.com/modules/localstack/)
  + LocalStack · ephemeral preview environments ([Northflank](https://northflank.com/blog/the-what-and-why-of-ephemeral-preview-environments-on-kubernetes-sandbox-testing)) ·
  shift-right / testing in production ([Microsoft](https://learn.microsoft.com/en-us/devops/deliver/shift-right-test-production),
  Charity Majors) · progressive delivery + auto-rollback ([Argo Rollouts](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/)) ·
  [DORA metrics](https://octopus.com/devops/metrics/dora-metrics/).

## Open questions

1. **`integration-lead`'s pack home.** A dedicated opt-in `delivery`/`integration` pack
   (mirroring `discovery-lead` in `product-engineering`) vs `core` (alongside `work-loop` /
   `operational-safety`, the build+deploy spine). Recommended default: **a dedicated opt-in
   pack** — deploy is an opt-in capability, like discovery; reuses core's `operational-safety`.
   · owner: eugenelim · decide-by: this RFC's child spec.
2. **Agent shape.** A distinct `integration-lead` agent vs a `work-loop` outer-mode.
   Recommended default: **distinct agent** (the inner/outer split is real), heavily reusing
   `operational-safety` + `quality-engineer`. · owner: eugenelim · decide-by: child spec.

## Follow-on artifacts

Filled on acceptance:
- ADR: the inner/outer loop split + the minimum-regret deploy carve.
- Spec: `integration-loop` + `integration-lead` (+ its pack).
- Amendment back into RFC-0048: reconcile its gate arc / company-OS framing once this lands.
- CONVENTIONS: the minimum-regret autonomy boundary (reversible ⇒ autonomous; irreversible ⇒ human).
