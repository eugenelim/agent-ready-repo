# ADR-0031: Infra `work-loop` support is doctrine on existing reviewers — operational safety via `quality-engineer`, security via a mandatory `security-reviewer` + scanner pair — not a new reviewer or runtime

- **Status:** Accepted
- **Date:** 2026-06-23
- **Decision-makers:** eugenelim
- **Consulted:** RFC-0041's applied-mode research brief, its citation-integrity pass, and the module-taxonomy follow-up (`0041-notes/research.md`); the spec-stage adversarial + design review of this ADR and the two implementing specs
- **Supersedes:** none
- **Related:** RFC-0041 (the accepted decision this records); ADR-0023 (the three-reviewer ceiling scopes the core code-review lenses — the constraint that forecloses a fourth, infra-lens reviewer); ADR-0014 + RFC-0025 (risk triggers already route a destructive/irreversible `apply` to full mode — the hook point this builds on); ADR-0018 (shift security review left + deliver its depth via an orchestrator-loaded progressive-disclosure skill — the `security-checklists` pattern P3's `operational-safety` library reuses verbatim); ADR-0017 (Bandit + pip-audit + Semgrep as the SAST/SCA gate — the scanner family the infra policy-as-code/CSPM scanner joins, complementing not replacing the reviewer)

## Context

`work-loop` is the repo's standard inner loop, and its risk triggers already route every cloud `apply` — destructive and partially irreversible by nature — to full mode (ADR-0014, RFC-0025). So the loop already *enters the right gear* for infrastructure work. Once there, it has no infra content, and that gap surfaces three ways:

- **The verification-mode step assumes the mechanism already exists.** PLAN says "pick the verification mode for each task" (the task's contract for "how do we know this is done"). TDD presupposes a runner; goal-based presupposes a build command; visual/manual-QA presupposes you can run the artifact. For a deploy, the mechanism — an idempotent apply you can safely re-run, a smoke check that proves "actually up", a throwaway target to iterate in, a teardown — frequently does not exist yet, and nothing makes the agent build it first.
- **The verification modes assume a fast, local, stateless, single-hop gate.** GATES is "lint, typecheck, tests". A deploy is slow, stateful, costs money, partially irreversible, and multi-hop: verifying it means *building the harness to verify it* (verify-status script, teardown script, seeded test/mock users, a provider-appropriate scanner), and the smoke check itself is an active end-to-end sequence — seed users → load the real CDN/site URL → confirm it renders → pull access/error logs → debug → tear down.
- **The security check on infra is discretionary, and a misconfigured deploy is high-blast-radius.** Infra changes routinely touch IAM, security groups, public buckets/CDNs, secrets, and network exposure; one wrong line ships prod open to the world. The existing security-boundary trigger *covers* this but only discretionarily.

The compound symptom is the **human-as-relay anti-pattern**: because the loop doesn't equip the agent to drive deploy-and-verify itself, the human runs the command and pastes the error back into the session by hand.

RFC-0041 settled *whether* and *how* to close this. This ADR records the load-bearing, expensive-to-reverse calls — the *form*, the *home*, and the *security posture* — so a future maintainer doesn't re-litigate them. The mechanical detail (the five-layer infra GATES sequence, the multi-artifact preflight enumeration, the exact six-module taxonomy) is spec-level and lives in the two implementing specs, not here.

Constraints in force when deciding (CHARTER Principles 1–3, plus the reviewer ceiling; Principle 4 — earns-its-place — appears in Consequences, not as a discriminating constraint):

- **Principle 3 (a habit, not infrastructure).** The repo ships doctrine and prose the agent reasons from, never a runtime engine, daemon, parser, or wrapper. This is the bar that put browser-bridge out of charter.
- **Principle 2 (no duplication).** A capability belongs in exactly one place; a parallel surface that re-implements an existing one is rejected.
- **Principle 1 (universal across stacks).** Anything that ships must hold for Terraform, Pulumi, CDK, CloudFormation, and hand-rolled scripts alike — no tool-specific bindings in normative prose.
- **The three-reviewer ceiling (ADR-0023).** Core code-review has exactly three lenses — `adversarial-reviewer`, `security-reviewer`, `quality-engineer`. A fourth is out of bounds.

## Decision

> We will make `work-loop` function for infrastructure development as **doctrine plus a reference library inside the loop — never executable infra tooling** — routing the **operational-safety** lens to the existing **`quality-engineer`** reviewer (no new reviewer), and making the **security** lens on infra a **mandatory, non-skippable `security-reviewer` + policy-as-code/CSPM scanner *pair***.

Three sub-decisions, each expensive to reverse:

- **Form & home — doctrine + reference library, inside `work-loop`.** Everything ships as prose: edits to `work-loop`'s `SKILL.md` and a new `operational-safety` skill of boundary-keyed `references/*.md` modules, structurally identical to `security-checklists`. No executable code ships — no deploy wrapper, plan-parser, cost-gate, or runtime. This is the `security-checklists` shape, a depth library a reviewer reasons from, which the repo has already accepted as a *habit*.
- **Operational safety is `quality-engineer`'s, not a new reviewer's.** The new `operational-safety` library (idempotency, blast radius, environment isolation, cost/teardown, drift/rollback, observability/smoke) is consumed by `quality-engineer`, whose existing lens — reliability, observability, maintainability — already owns exactly these concerns. The orchestrator loads only the matching modules and inlines them into the reviewer's brief via the same table-driven mechanism it already uses for `security-checklists`. **No fourth reviewer** (ADR-0023). The *security* lens on infra stays with `security-reviewer` (below); the carve is `security-checklists` owns security config, `operational-safety` owns reliability/ops config.
- **Security on infra is mandatory, and is a reviewer + scanner pair.** Infra-flavored work **non-skippably** invokes `security-reviewer` — at the spec stage (is the control specified as an acceptance criterion?) *and* on the diff — rather than leaving it to the discretionary security-boundary trigger; the orchestrator force-loads the infra-relevant `security-checklists` modules (`config-misconfig`, `access-control`, `secrets-and-crypto`, `outbound-ssrf`, `supply-chain`, loaded 1–N as the diff warrants). The reviewer is **not** the per-provider depth source — it reasons from cross-cutting standards (OWASP/ASVS/CWE + STRIDE/LINDDUN) and catches failure *classes* (over-broad IAM, public exposure, unencrypted-at-rest, secrets in state, metadata SSRF, missing audit logging). The per-provider secure-config depth comes from a **provider-appropriate policy-as-code/CSPM scanner** (Checkov / tfsec / cloud-native CSPM — the adopter's choice, never pinned), whose vendor-maintained rulesets *are* the provider baselines. So security on infra is a **pair**: scanner for per-provider breadth + reviewer for failure-class reasoning; neither substitutes for the other.

Boundaries on the decision:

- This adds **no new risk trigger** for "infrastructure" — destructive/irreversible already routes `apply` to full mode (RFC-0025); a separate infra trigger would be redundant. **"Infra-flavored" is a defined signal, not an ad-hoc judgement:** work is infra-flavored when it trips that destructive/irreversible trigger *and* the diff/spec matches the boundary→module routing table's IaC/deploy-config entry in `work-loop` SKILL.md — the same classifier already drives security-module loading. The mandatory pass (below) keys on that signal, so it cannot be silently skipped on an infra diff.
- It adds **no new reviewer and no new `security-checklists` module** — it makes the *existing* security pass mandatory and multi-module.
- The scanner requirement is **mechanism-level, not tool-level** — a provider-appropriate scanner must exist, exactly as the repo requires "tests exist" without mandating a test framework.
- Progressive delivery (canary / blue-green metric gates) is **deferred** — largely Kubernetes-specific, it fails the universal-stack bar and waits for a future RFC.

## Decision drivers

- **Principle 3 (habit, not infrastructure)** — the hard gate; rules out executable infra tooling (a plan-parser or deploy wrapper is runtime infrastructure), forcing the capability to be doctrine + a reviewer-consumed depth library.
- **Principle 2 (no duplication)** — rules out a standalone `infra-deploy` skill; a parallel surface would re-implement the PLAN/GATES/REVIEW loop `work-loop` already owns. The capability belongs *in* the loop.
- **The three-reviewer ceiling (ADR-0023)** — rules out a fourth, infra-lens reviewer; the infra reliability lens is `quality-engineer`'s existing concern, the infra security lens is `security-reviewer`'s.
- **Principle 1 (universal across stacks)** — rules out per-provider secure-config baselines living in the reviewer (they would break universality and be stale on arrival); forces per-provider depth into the self-updating scanner and the doctrine prose to stay tool-neutral.
- **Blast radius of a misconfigured deploy** — drives *mandatory* (non-skippable, spec-stage + diff) over the discretionary security-boundary trigger: the non-trivial case (a public bucket, an over-broad role) dominates the risk.
- **A standards-grounded reviewer is not a per-provider rules engine** — drives the *pair*: the reviewer's strength is failure-class reasoning and control-completeness, not AWS/Azure/GCP per-service baselines, so the scanner must carry that depth alongside it.

## Consequences

**Positive:**

- The capability reuses a proven, table-driven mechanism (the orchestrator already inlines `security-checklists` modules and already fires on IaC/deploy changes), so the operational-safety library is a second lens on an existing rail, not new infrastructure — clearing Principle 3.
- The generalized verification-mechanism preflight (P1 in RFC-0041) is exercised on **every** task, not just infra — a goal-based task that claims a build command not yet wired, or a TDD task with no runner, is caught by the same obligation — so the change earns its place on every loop, not only the rare infra one.
- Infra security is robust and proportionate to its blast radius: mandatory, multi-module, run at spec stage and on the diff, and backed by per-provider scanner depth the reviewer can't and shouldn't carry.

**Negative:**

- A second reference library is one more governed surface to maintain, and the change lengthens `work-loop`'s PLAN/REVIEW prose — real surface-area cost, justified by the recurring present pain and the universal reach of the preflight.
- For adopters who never deploy infra, the infra verification flavor and the `operational-safety` modules are dormant weight (mitigated: the preflight still earns its place on every task; the infra layers load only on the destructive/irreversible trigger).
- Requiring a provider-appropriate scanner edges toward tool-binding; the residual is accepted because the requirement is mechanism-level (a scanner must exist), not tool-level — the adopter picks the tool, exactly as with test frameworks.

**Neutral / to revisit:**

- **`quality-engineer`'s lens is assumed to stretch to operational safety** (blast radius, cost, teardown). Believed true — these are textbook reliability/observability concerns, and the agent already carries Observability and Reliability checklists — but this is the assumption to re-check if a reviewer-fit gap appears.
- **The right default for auto-remediation of drift in an agentic loop is unsettled** — the Terraform community (gate it) and the GitOps community (auto-sync) disagree by risk tolerance, and no evidence settles it across both contexts. RFC-0041 names this as a tension to surface, not resolve; the `drift-and-rollback` module records it as such.
- **Progressive delivery is deferred, not rejected** — a Kubernetes-using adopter who needs canary/blue-green metric gates reopens it as a follow-up RFC.

## Confirmation

- The two implementing specs' acceptance criteria encode the doctrine — the generalized preflight, the multi-artifact infra mechanism set, the layered infra GATES, the mandatory security reviewer + scanner pair, the six-module `operational-safety` library, and the `quality-engineer` consumer wiring — so conformance is checkable against the specs.
- The adversarial + quality + security review passes on the implementing diff check that **no executable infra tooling creeps in** (the standing scope-inflation risk), that every module stays **tool-neutral** (Principle 1), and that the **reliability-vs-security carve** between `operational-safety` and `security-checklists` holds (no security config in the operational library, no operational config migrating into the security one).
- The mandatory-security posture keys on the defined infra-flavor signal above (the destructive/irreversible trigger + the IaC/deploy-config routing entry): an infra-flavored diff that reaches DECIDE without a recorded `security-reviewer` pass (spec stage + diff) and a recorded scanner run is, by the doctrine, not done — and because "infra-flavored" is the routing-table classifier rather than a per-diff judgement, the requirement is checkable, not aspirational.

**Enforcement posture is deliberately review-time, not a standing CI gate.** Conformance is confirmed at the implementing PR (the specs' ACs) and thereafter by the three reviewer passes' standing doctrine — there is no machine fitness function asserting "no executable infra tooling under these skills" or "the carve holds" against future drift. This matches Principle 3 (the bar that forecloses a code gate is the same one that makes the controls prose) and ADR-0030's precedent of accepting a prose-enforced, reviewer-held residual. The decision-maker accepts that drift residual; a later, optional governance lint (e.g. asserting the `work-loop` and `operational-safety` skills ship no executable deploy/parse/gate script) could harden it without reversing this ADR, and is recorded as a possible follow-up, not a requirement.

## Alternatives considered

- **New executable infra tooling** (a plan-parser, deploy wrapper, or cost-gate script / runtime). Rejected against **Principle 3** — that is runtime infrastructure, and it would need per-tool bindings, also breaking Principle 1. This is the option the form-and-home sub-decision rejects.
- **A standalone `infra-deploy` skill.** Rejected against **Principle 2** — a parallel deploy skill re-implements the PLAN/GATES/REVIEW the loop already owns; the capability belongs *in* the loop, not beside it.
- **A fourth, infra-lens reviewer.** Rejected against **the three-reviewer ceiling (ADR-0023)** — the infra reliability lens is `quality-engineer`'s existing concern; the infra security lens is `security-reviewer`'s. Three is the ceiling.
- **Leaving infra security on the discretionary security-boundary trigger** (do-nothing on P5). Rejected against the **blast-radius** driver — a high-blast-radius misconfiguration (a public bucket, an over-broad IAM role) can ship because the security pass was optional rather than mandatory.
- **Do nothing.** Rejected — the loop stays implicitly application-only; infra users keep relaying deploy errors by hand, and the agnostic preflight gap silently degrades non-infra work too (a claimed verification mode whose mechanism doesn't exist). The pain is recurring and present now.

## References

- RFC-0041 — make `work-loop` function for infrastructure development (the accepted decision this ADR records).
- ADR-0023 — the three-reviewer ceiling scopes the core code-review lenses (the constraint foreclosing a fourth reviewer).
- ADR-0018 — shift security review left + orchestrator-loaded progressive-disclosure depth library (the `security-checklists` pattern `operational-safety` reuses).
- ADR-0014 / RFC-0025 — risk triggers route destructive/irreversible work to full mode (the hook point).
- ADR-0017 — Bandit + pip-audit + Semgrep SAST/SCA gate (the scanner family the infra policy-as-code/CSPM scanner complements).
- CHARTER Principles 1–3 — the universality, no-duplication, and habit-not-infrastructure bars this decision clears (Principle 4, earns-its-place, appears in Consequences).
