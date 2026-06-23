# Research: making `work-loop` function for infrastructure development

> Discipline: applied (practitioner-pattern survey)

Grounding for RFC-0041. Question: how do leading repos/tools make an
iterative development loop work for **infrastructure** (IaC, cloud
deploys), and what is the general principle that a task's **verification
mechanism must exist before the work is claimable**? Findings feed two
candidate RFC pillars — (a) a generalized verification-mechanism
preflight in the loop, and (b) a progressive-disclosure
operational-safety reference module loaded when infra/destructive work
is detected.

Confidence tags follow the applied-mode overlay (GRADE minus the
no-peer-review penalty; plus `survivorship bias` and `stale prior art`).
Material claims (`[high]`/`[moderate]`) triangulate ≥3
practitioner-independent sources.

---

## SQ1 — Convergent inner loop for infra

**Finding 1.1 — Preview-then-converge (plan/apply) is the universal safety gate. [high]**
Every leading IaC tool separates "what will change" from "execute the
change": Terraform `plan`/`apply`, Pulumi `preview`/`up`, AWS CDK `diff`
+ CloudFormation change sets [T-intro][pulumi-how][cdk-diff]. The diff is
computed against *both* stored state and live resources before any
mutation. **Transferable principle:** a dry-run preview that diffs
desired vs. actual is the primary safety gate for any iterative infra
loop — the agentic analog of "show the plan before you apply it."

**Finding 1.2 — Declarative + idempotent re-apply is what makes retry safe; imperative scripts collide. [high]**
Declarative IaC converges on re-run ("if already in desired state, no
actions taken"); imperative scripts re-attempt steps and either
re-create existing resources or leave inconsistent state
[T-apply][opsmill][pulumi-how]. (The no-op/empty-diff behavior is stated
on the apply tutorial, not the intro page — citation corrected after the
integrity pass.) This is the direct root cause of the
user's "manual stop/start errors": iterating on non-idempotent scripts
makes every failed retry a new mess. **Transferable principle:**
idempotent convergent apply is a *precondition* for progressive
refinement, not a nicety. An agentic loop on imperative steps must add
existence-check/conditional-delete guards to match what declarative
tools give structurally.

**Finding 1.3 — Shared state needs a single-writer lock. [moderate]**
Terraform serializes mutation via state locks (native S3 lockfiles from
1.10; DynamoDB deprecated) [T-s3]. **Transferable principle:**
single-writer-at-a-time on shared infra state is not optional — relevant
when an agent and a human (or two agents) could apply concurrently.

**Finding 1.4 — Drift detection is read-only and separable from remediation. [high]**
`terraform plan -refresh-only`, CloudFormation drift-aware change sets
(3-way: declared-baseline / live-actual / new-desired), and driftctl all
answer "are we drifted?" without mutating [T-drift][cfn-drift][spacelift-drift].
GitOps loops (ArgoCD, Flux) take the *opposite* default — continuous
reconciliation auto-reverts out-of-band edits [gitops][argo][flux].
**Transferable principle:** keep detection (safe, frequent, read-only)
separate from remediation (mutating, gated). Auto-remediation default is
contested — see Known unknowns.

---

## SQ2 — Verification mechanisms for infra

**Finding 2.1 — Verification is a layered gate sequence, not one check. [high]**
The canonical layering: **static preflight → plan/preview → apply →
smoke/health → progressive-delivery gate → rollback trigger**
[spacelift-test][T-tests][terratest][argo-rollouts]. Each layer catches a
different failure mode at a different cost/speed point; skipping one
pushes its failure downstream where it costs more. **Transferable
principle:** this maps directly onto the loop's GATES step — infra GATES
is a *sequence*, not a single "tests pass."

**Finding 2.2 — "Created" ≠ "works"; smoke/health checks are mandatory before promotion. [high]**
Terraform `check` blocks (post-apply runtime assertions — e.g. endpoint
returns 200), Terratest (deploy → validate via real HTTP/SSH/API →
undeploy) [T-tests][terratest]. **Transferable principle:** infra
verification must exercise the *real built artifact* end-to-end — already
the doctrine in work-loop's Visual/manual-QA mode for "a service
endpoint." Infra just adds the stack-status + health-probe layer beneath
it.

**Finding 2.3 — Policy-as-code is a preflight gate with enforcement levels. [high]**
OPA/Conftest (evaluates `plan -json`, i.e. what *will* be created),
Checkov, tfsec/Trivy, Sentinel — run pre-commit / PR / plan-eval, with
advisory / soft-mandatory / hard-mandatory levels
[scalr-policy][T-policy]. **Transferable principle:** a named, versioned
policy gate with graded enforcement is the infra analog of lint+typecheck
— mechanical, runs before apply.

**Finding 2.4 — Ephemeral per-PR environments isolate verification from shared infra. [moderate]**
Create-on-open, fully isolated, destroy-on-close [ephemeral]. **Transferable
principle:** iterate in a throwaway environment; the PR is a deployment
unit, not just a code unit. (Cost caveat — Known unknowns.)

**Finding 2.5 — Progressive delivery puts an automated metric gate between traffic increments. [moderate]**
Argo Rollouts / Flagger: `setWeight → pause → AnalysisRun(metrics) →
promote-or-rollback` [argo-rollouts][flagger]. The `AnalysisTemplate` is
a reusable, versioned verification contract. **Tool-specific** (mostly
Kubernetes) but the **transferable principle** is the gate-between-
increments shape. Likely *out of scope* for a first RFC pass (see Known
unknowns).

**Finding 2.6 — Terraform has no atomic rollback; re-apply prior known-good config. [moderate]**
No `terraform rollback` command; safest path is applying the previous
versioned config, not state surgery [spacelift-test][T-tests].
**Transferable principle:** because rollback is hard, *early detection*
(smoke tests) and *small increments* matter more — they make rollback
rarely needed.

---

## SQ3 — Guardrails for destructive / irreversible / costly ops

**Finding 3.1 — Parse the plan structurally; gate on destroy/replace counts. [high]**
`plan -out=tfplan` (binary) → `show -json` → count `delete`/`replace`
actions with jq → fail the step on nonzero, require explicit override
[T-plan][controlmonkey]. **Transferable principle:** gate destructive ops
on *parsed plan structure*, never on grepping text. This is a concrete,
mechanical preflight an agent can run.

**Finding 3.2 — Decouple proposer identity from approver identity. [high]**
Convergent across Atlantis `apply_requirements: [approved]`
(operator-controlled, not self-approvable — note this gate is *blanket*
over all applies, covering the destructive subset rather than being
destructive-scoped, verified in the integrity pass), GitHub Environments
required reviewers + prevent-self-review + disable-admin-bypass, HCP
Terraform/Sentinel hard-mandatory (no override), CDK
`ConfirmPermissionsBroadening` (this one *is* destructive/broadening-scoped)
[atlantis][gh-env][hcp-policy][cdk-approval]. **Transferable principle:**
for irreversible ops the agent proposes, a *different* identity (the
human) approves. Maps cleanly onto "get user confirmation for destructive
commands" already in AGENTS.md.

**Finding 3.3 — Environment isolation by account/state boundary. [high]**
AWS multi-account per SDLC stage; separate state backends so staging
credentials can't touch prod; sandbox-OU SCP guardrails
[aws-multi-account][aws-sandbox]. **Transferable principle:** the
strongest isolation unit is the account/subscription/project boundary;
separate state enforces it in IaC. Iterate away from prod.

**Finding 3.4 — Cost is a first-class CI gate, not a post-deploy surprise. [moderate]**
Infracost cost-diff on PRs with absolute/percentage/budget-ceiling
guardrails → failed status check blocks merge; AWS Budgets Actions
(deny-policy / stop instances) [infracost][aws-budgets]. **Transferable
principle:** estimate cost from the plan before apply; a cost ceiling is a
gate.

**Finding 3.5 — Tag-at-creation TTL + destroy-on-close prevents orphans; destroy needs its own plan. [moderate]**
`plan -destroy` before `destroy`; TTL tag scanned by scheduled cleanup;
`prevent_destroy` on must-survive resources (but bypassable by removing
the block / `state rm`) [ephemeral-bp][T-lifecycle]. **Transferable
principle:** a destroy plan is as important as a create plan; failed runs
must fail *visible*, not leave half-built stacks.

---

## SQ4 — The "verification mechanism must exist first" principle (agnostic core)

**Finding 4.1 — Walking skeleton / tracer bullet: build the thin runnable+testable end-to-end path first. [high]**
Pragmatic Programmer tracer bullets ("lean but complete… part of the
skeleton of the final system"); Cockburn's walking skeleton — a tiny
end-to-end implementation that "links together the main architectural
components" (Cockburn's own site is currently unreachable, expired TLS;
definition attested via *Crystal Clear* + secondary sources); GOOS
"iteration zero" dedicates the first iteration to an automatically
build/deploy/test harness *before* feature work — **GOOS, not Cockburn,
is the primary source for the deploy-to-a-real-environment emphasis**
(citation corrected after the integrity pass) [pragprog][cockburn-2ary][goos]. **Transferable principle (the agnostic
core):** the runnable, testable path is the *prerequisite* for verifiable
work, not its reward. Directly supports a preflight: picking a
verification mode obligates the mechanism to exist first.

**Finding 4.2 — A Definition of Done / deployment pipeline that lacks an automated verification mechanism is intent, not a gate. [high]**
Continuous Delivery: a valid deployment pipeline *requires* version
control + automated build + automated tests as preconditions;
"retrofitting tests is painful and expensive"; "Done means released"
[cd-book][cd-testauto][farley-2007]. DoD literature: unverified work is
*not done* — it consumes future capacity when defects surface
[agilealliance-dod]. **Transferable principle:** you cannot claim a
verification mode without the mechanism; if it's absent, building it is
task zero. This is the RFC's generalization of the existing
verification-mode step.

**Finding 4.3 — Test-driven infrastructure is the same principle applied to infra. [moderate]**
Kief Morris, *Infrastructure as Code* (2nd/3rd ed.), Ch.8: the test
pyramid for infra; "IaC shifts the focus of quality to the definitions
and tooling" — without a harness those definitions are unverified claims;
names the three reasons infra testing is hard (tautological declarative
tests, slow, dependency isolation) [morris-iac][morris-summary].
**Transferable principle:** the infra verification flavor is not an
exception to the agnostic core — it's the core with infra-specific
mechanisms.

*Recency:* tracer-bullet (1999) and walking-skeleton predate cloud/IaC,
but the principle (end-to-end runnable path before end-to-end claim) is
domain-stable — no `stale prior art` penalty.

---

## SQ5 — Agentic loops and long/stateful/environment-dependent verification

**Finding 5.1 — Ground-truth-from-environment is the named best practice; human-as-relay is the anti-pattern. [high]**
ReAct's act→observe→reason loop; Anthropic: "it's crucial for the agents
to gain 'ground truth' from the environment at each step… to assess its
progress" [react][anthropic-agents]. **Transferable principle:** the
agent must run the verification command and read the real output itself.
The user's copy-paste churn *is* the human-relay anti-pattern this names.

**Finding 5.2 — Guardrails belong on the agent-computer interface, not the prompt. [high]**
SWE-agent's ACI runs lint before applying an edit and returns structured
errors; output is windowed to prevent context overflow; lifted SWE-bench
from ~3% to 12.5% mostly via interface design [swe-agent][anthropic-agents].
**Transferable principle:** infra guardrails (destroy-count gate, policy
preflight) should be mechanical interface checks the agent hits, not prose
it's asked to remember.

**Finding 5.3 — Claude Code already has the primitives for slow/stateful deploy verification. [moderate]**
Hooks: `PreToolUse` can block destructive commands (exit 2); `PostToolUse`
runs linters/transforms real output; `asyncRewake` wakes the agent on a
background job's exit with stderr surfaced; per-hook timeouts (default
600s, raise for deploys); background tasks keep long processes alive;
subagents delegate log-reading verification [cc-hooks][cc-autonomous].
**Tool-specific** but maps onto every layer the RFC needs. *Recency:*
async-rewake is early-2026, production patterns thin (Known unknowns).

**Finding 5.4 — Sandboxed/ephemeral execution contains costly/destructive agent ops. [moderate]**
E2B (Firecracker microVM), Modal, Daytona, Fly — per-execution logging
and traceable multi-invocation behavior is what lets the agent observe
and react without a human in the path [modal-sandbox]. **Transferable
principle:** contain agent-driven infra ops in an isolated, observable
environment.

**Finding 5.5 — The external-deploy-CLI case is under-studied. [low]**
No surveyed paper addresses an agent driving *external* deploy CLIs
(`terraform`, `kubectl`) against real infra with slow non-deterministic
feedback — only the code-execution case is well-studied
[modal-sandbox][agentmarketcap]. This is precisely the RFC's gap and an
argument that it's novel-but-grounded, not solved-elsewhere.

---

## Synthesis for the RFC

Four pillars, each grounded:

- **P1 — Generalized verification-mechanism preflight (agnostic core).**
  Picking a verification mode obligates confirming the mechanism exists;
  if not, task zero builds it. Grounds: F4.1, F4.2, F5.1. Applies to
  *every* mode (TDD needs a runner; deploy needs smoke+idempotent apply).
- **P2 — Infra as a first-class verification flavor.** GATES for infra is
  the layered sequence static-preflight → plan → apply → smoke →
  (progressive) → rollback; idempotent convergent apply is a precondition.
  Grounds: F1.1, F1.2, F2.1, F2.2, F2.3, F4.3.
- **P3 — Operational-safety progressive-disclosure module** (security-checklists
  shape), loaded when the infra/destructive trigger fires. Candidate
  modules: state-and-idempotency (F1.2,F1.3), blast-radius (F3.1,F3.2),
  environment-isolation (F3.3), cost-and-teardown (F3.4,F3.5),
  drift-and-rollback (F1.4,F2.6). Overlap to *avoid duplicating*:
  security-checklists already covers config-misconfig, secrets-and-crypto,
  supply-chain (≈ IAM/secrets/module-provenance).
- **P4 — Agent drives verification itself** (close the human-relay gap).
  Grounds: F5.1–F5.4. Mechanical interface guardrails (F5.2), background
  + async-rewake for slow deploys (F5.3), sandbox/throwaway env (F5.4).

Hook point already exists: RFC-0025's risk-trigger set already routes
destructive/irreversible and infra/build-edit work to full mode — so the
loop already *enters the right gear*; it just lacks the infra content once
there.

---

## Follow-up research (module taxonomy + observability)

**Resolution of "five modules or merge state-and-idempotency with
drift-and-rollback?" — keep them separate. [high]** Every major
operational taxonomy splits write-path convergence from
divergence-detection-and-recovery: AWS Well-Architected separates
**Change Management** from **Failure Management** [waf-rel]; Google SRE
separates **Release Engineering** (Part II) from **Incident/Emergency
Response** (Part III), treating rollback as an incident-mitigation tool
not a release concern [sre-toc][sre-release]; Terraform splits write
`apply` from read-only `-refresh-only` [T-drift]; Pulumi names **Day 1
(prevention)** vs **Day 2 (drift detection + remediation)** as
"complementary defense layers" [pulumi-day2]. Reference-checklist
libraries (OWASP ASVS, CIS) err fine-grained. So these are two distinct
lifecycle phases, not one "state fidelity" family → **keep separate**.

**Observability is a distinct, sixth operational concern. [moderate]**
AWS Well-Architected Operational Excellence treats "understand
operational health" / telemetry as its own design area, and Google SRE
centers monitoring as a first-class practice [waf-rel][sre-toc]. The
user requirement (load the real CDN/site URL, confirm render, read access
logs to debug a failed smoke) is an observability + active-probe concern
distinct from the other five — supports adding an `observability-and-smoke`
module rather than folding it into reliability prose.

Taxonomy sources: [waf-rel] AWS Well-Architected Reliability Pillar —
Change Management vs Failure Management (primary); [sre-toc] Google SRE
Book ToC (primary); [sre-release] Google SRE Release Engineering, Ch.8
(primary); [pulumi-day2] Pulumi "Day 2 Operations: Drift Detection and
Remediation" (primary).

## Known unknowns

- **Known-unknown:** does the operational-safety surface belong as a *new*
  reference library or as added modules under `security-checklists`?
  Would be closed by: an inventory diff of the candidate modules against
  the existing ten security-checklists modules to measure real overlap
  vs. genuinely-new operational surface.
- **Known-unknown:** is progressive delivery (F2.5) in scope for a first
  RFC, given it's largely Kubernetes-specific? Would be closed by: scoping
  the RFC to the tool-agnostic layers (preflight→plan→apply→smoke) and
  deferring the progressive-delivery gate to a follow-up.
- **Known-unknown:** what's the production failure mode of Claude Code
  `asyncRewake` for multi-minute deploys? Would be closed by: a spike
  driving a real `terraform apply` via a background task + async-rewake.
- **Unknowable (now):** the right default for auto-remediation of drift in
  an agentic loop — the Terraform community (gate it) and GitOps community
  (auto-sync) disagree by risk tolerance, and no evidence settles it
  across both contexts. Belongs as a *tension* the RFC names, not a
  finding it resolves.
- **Unknowable (now):** whether external-deploy-CLI agent loops have an
  emerging best practice — the literature gap (F5.5) means we're partly
  defining it, so confidence on "the right shape" is inherently bounded
  until we ship and observe.

---

## Sources

Primary unless tagged. Practitioner-independence applied (same-vendor =
one source).

- [T-intro] Terraform Introduction — HashiCorp Developer (primary)
- [T-apply] Apply tutorial (empty-diff / no-op behavior) — HashiCorp Developer, developer.hashicorp.com/terraform/tutorials/cli/apply (primary; replaces [T-intro] for the idempotency no-op claim)
- [T-s3] Backend Type: S3 — HashiCorp Developer (primary)
- [T-drift] Manage Resource Drift — HashiCorp Developer (primary)
- [T-plan] terraform plan command reference — HashiCorp Developer (primary)
- [T-tests] Tests — Terraform Configuration Language — HashiCorp Developer (primary)
- [T-policy] HCP Terraform policy enforcement — HashiCorp Developer (primary)
- [T-lifecycle] lifecycle meta-argument — HashiCorp Developer (primary)
- [pulumi-how] How Pulumi Works — Pulumi Docs (primary)
- [cdk-diff] cdk diff — AWS CDK v2 Docs (primary)
- [cfn-drift] CloudFormation Drift-Aware Change Sets — AWS DevOps Blog (primary)
- [opsmill] Declarative vs. Imperative Automation — OpsMill (secondary)
- [spacelift-drift] Terraform Drift Detection — Spacelift (secondary)
- [gitops] GitOps.tech — Weaveworks principles (primary)
- [argo] Understanding ArgoCD Reconciliation — Rafay (secondary)
- [flux] Flux Concepts — FluxCD Docs (primary)
- [spacelift-test] How to Test Terraform Code — Spacelift (secondary)
- [terratest] Terratest — Gruntwork (primary)
- [scalr-policy] OPA vs Sentinel — Scalr (secondary)
- [ephemeral] Ephemeral Environments — Autonoma (secondary); ephemeralenvironments.io
- [argo-rollouts] Argo Rollouts — official docs (primary)
- [flagger] ArgoCD Rollouts vs Flagger — OneUptime (secondary)
- [controlmonkey] Terraform Plan Made Simple — ControlMonkey (secondary)
- [atlantis] Command Requirements — Atlantis (primary)
- [gh-env] Managing environments for deployment — GitHub Docs (primary)
- [hcp-policy] HCP Terraform policy enforcement — HashiCorp (primary)
- [cdk-approval] Manually Approving Security Changes in CDK Pipeline — AWS DevOps Blog (primary)
- [aws-multi-account] Organizing Your AWS Environment Using Multiple Accounts — AWS Whitepaper (primary)
- [aws-sandbox] Best practices for sandbox accounts — AWS Blog (primary)
- [infracost] Cost guardrails — Infracost Docs (primary)
- [aws-budgets] Configuring budget actions — AWS Cost Management Docs (primary)
- [ephemeral-bp] Best Practices for Ephemeral Environments — ephemeral-environments.com (secondary)
- [pragprog] Hunt & Thomas, *The Pragmatic Programmer* — tracer bullets (primary)
- [cockburn-2ary] Cockburn, "Walking Skeleton" — canonical def via *Crystal Clear* + secondary sources (own site alistair.cockburn.us unreachable, expired TLS; downgraded primary→secondary in the integrity pass)
- [goos] Freeman & Pryce, *Growing Object-Oriented Software, Guided by Tests* (primary)
- [cd-book] Humble & Farley, *Continuous Delivery* (primary)
- [cd-testauto] continuousdelivery.com — Test Automation (secondary)
- [farley-2007] Farley, "The Deployment Pipeline" (2007) (primary)
- [agilealliance-dod] Agile Alliance — Definition of Done (secondary)
- [morris-iac] Morris, *Infrastructure as Code* 2nd ed., Ch.8 (primary)
- [morris-summary] IaC book summary — Medium (secondary)
- [react] Yao et al., ReAct (arXiv 2210.03629) (primary)
- [anthropic-agents] Anthropic, Building Effective Agents, 2024 (primary)
- [swe-agent] Yang et al., SWE-agent, NeurIPS 2024 (primary)
- [cc-hooks] Claude Code Hooks Reference (primary)
- [cc-autonomous] Anthropic, Enabling Claude Code to Work More Autonomously, 2026 (primary)
- [modal-sandbox] Modal — Best Code Execution Sandboxes for Coding Agents (secondary)
- [agentmarketcap] AI Agent Sandbox Infrastructure 2026 — AgentMarketCap (tertiary)
