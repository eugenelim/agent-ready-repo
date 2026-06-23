# RFC-0041: make `work-loop` function for infrastructure development

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-22
- **Date closed:** 2026-06-22
- **Related:** RFC-0025 (`work-loop` light mode + risk-based escalation — the trigger set this builds on); RFC-0029 (strengthen `security-reviewer`) + `security-checklists` skill (the progressive-disclosure depth-library pattern P3 reuses); `work-loop` skill (PLAN verification-mode step; orchestrator module-routing table, SKILL.md:555-578); `quality-engineer` subagent (the reliability lens that consumes P3); `docs/CONVENTIONS.md` § "How we do non-trivial work" + the plan's `## Rollout` section (CONVENTIONS.md:335-337); `docs/CHARTER.md` Principles 1-4; research brief in [`0041-notes/research.md`](0041-notes/research.md)

## The ask

- **Recommendation (BLUF):** Extend `work-loop` so it actually functions for infrastructure development through **five additions, all doctrine — no executable tooling, no new reviewer, no new runtime**: (P1) a **generalized verification-mechanism preflight** — picking a verification mode obligates confirming the mechanism exists, and for infra that mechanism is usually a *multi-artifact set* (a verify-status script, a teardown script, mock-user/test-data seeding, and a provider-appropriate policy-as-code/CSPM scanner — the latter holding the per-provider depth), each a task-zero prerequisite; (P2) an **infra verification flavor** — GATES for deploy work is a layered sequence (static-preflight → plan/preview → apply → **active end-to-end smoke** → rollback) resting on idempotent convergent apply, where smoke is a real multi-hop probe (seed test users → load the real CDN/site URL → assert it renders → read access/error logs → debug → teardown), not a single status check; (P3) an **`operational-safety` progressive-disclosure reference library** (six modules incl. observability) loaded by the orchestrator when infra/destructive work is detected, consumed by the existing `quality-engineer` reviewer; (P4) **agent-drives-verification doctrine** — the agent runs deploy commands and reads real environment output itself (harness-agnostic), with Claude Code background tasks / `asyncRewake` / `PreToolUse` named as the accelerant; (P5) **mandatory, robust security review for infra changes** — a *pair*: a non-skippable `security-reviewer` pass (spec stage + diff, force-loading the infra-relevant `security-checklists` modules) for failure-class reasoning, **plus** the P1-required policy-as-code/CSPM scanner that holds the per-provider secure-config depth — because a misconfigured deploy is high-blast-radius and the standards-grounded reviewer is not a per-provider rules engine.

- **Why now (SCQA):** *Situation* — `work-loop` is the repo's standard loop and its risk triggers already route destructive/irreversible work (which every cloud `apply` is) to full mode (RFC-0025). *Complication* — once there, the loop has **no infra content**: its verification modes (TDD / goal-based / visual-manual-QA) assume the verification mechanism already exists and assume a fast, local, stateless gate. Cloud deploys are slow, stateful, partially-irreversible, and their verification mechanism (idempotent apply, smoke check, safe target) frequently *doesn't exist yet* — so the agent can't drive the loop, and the human becomes the relay, copy-pasting deploy errors back into the session by hand. *Question* — should `work-loop` gain the doctrine to drive an infra loop end-to-end, or stay implicitly application-only?

- **Decisions requested:**
  1. **Scope as doctrine + a reference library, never executable infra.** · recommended: yes · decide-by: on accept · default: yes.
  2. **P1 — generalize the verification-mechanism preflight to *every* mode** (not infra-only), and treat the infra mechanism as a *multi-artifact set* (verify-status + teardown + test-seed scripts + a provider-appropriate policy-as-code/CSPM scanner), each a task-zero prerequisite. · recommended: yes · decide-by: on accept · default: yes.
  3. **P2 — add an infra verification flavor** (layered GATES; idempotent convergent apply as a precondition; smoke is an *active end-to-end multi-hop probe* — seed users → load real URL → assert render → read logs → debug → teardown; cross-linked to the plan's `## Rollout` section). · recommended: yes · decide-by: on accept · default: yes.
  4. **P3 — a new `operational-safety` reference library** of **six** modules (security-checklists shape), carved against `security-checklists` on the reliability-vs-security lens, **consumed by `quality-engineer` — no new reviewer.** · recommended: yes · decide-by: on accept · default: yes.
  5. **P4 — express agent-drives-verification as harness-agnostic doctrine, with Claude Code primitives as accelerant only (never a dependency).** · recommended: yes · decide-by: on accept · default: yes.
  6. **P5 — make infra security a mandatory reviewer + scanner *pair*:** a non-skippable `security-reviewer` pass (spec stage + diff, force-loading the infra-relevant `security-checklists` modules — `config-misconfig` + `access-control` + `secrets-and-crypto` + `outbound-ssrf` + `supply-chain` as the diff warrants) for failure-class reasoning, paired with the P1-required policy-as-code/CSPM scanner for per-provider depth; plus a thin, URL-free deferred-authority pointer (CIS Benchmarks + per-provider well-architected security guidance, named not linked). · recommended: yes · decide-by: on accept · default: yes.
  7. **Defer progressive delivery** (canary/blue-green metric gates) as Kubernetes-specific. · recommended: defer · decide-by: on accept · default: defer.

## Problem & goals

**Diagnosis.** `work-loop`'s loop is sound; its *content* is implicitly application-only in two ways that surface exactly when someone deploys infrastructure.

1. **The verification-mode step assumes the mechanism exists.** PLAN says "Pick the verification mode for each plan task… the task's contract for how do we know this is done" (SKILL.md:156). TDD presupposes a runner; goal-based presupposes a build command; visual-manual-QA presupposes you can run the artifact. For application code those usually exist. For a deploy, the mechanism — an idempotent apply you can safely re-run, a smoke check that proves "actually up", a throwaway target to iterate in — frequently *doesn't exist yet*, and nothing in the loop makes you create it first. The agent proceeds, the deploy half-fails, and there is no convergent retry.

2. **The verification modes assume fast/local/stateless single-hop gates.** GATES is "lint, typecheck, tests". A deploy is slow, stateful, costs money, partially irreversible, and **multi-hop**: you cannot verify it until you have *built the harness to verify it* — a verify-status script, a teardown script, seeded test/mock users, and a provider-appropriate policy-as-code/CSPM scanner — and the smoke check itself is an active end-to-end sequence (provision test users → load the real CDN/website URL → confirm it renders → pull access/error logs → debug the failure → tear down). None of the three modes describes this; nothing names idempotent convergent apply as the precondition that makes iteration safe — so iterating on imperative scripts produces the "manual stop/start errors" that motivated this RFC.

3. **Nothing makes the security check robust, and a misconfigured deploy is dangerous.** Infra changes routinely touch IAM, security groups, public buckets/CDNs, secrets, and network exposure — a single wrong line ships prod open to the world. The loop's existing security-boundary trigger *covers* this, but discretionarily; for a surface this high-blast-radius the security pass must be **non-skippable**, run at both spec stage and on the diff, and pull *all* the infra-relevant security modules, not just one.

The compound symptom is the **human-as-relay anti-pattern**: because the loop doesn't equip the agent to drive deploy-and-verify itself, the human runs the command and pastes the error back — the exact failure ReAct/ACI and Anthropic's "ground truth from the environment at each step" guidance exist to remove (research F5.1).

**Goals.**
- Make `work-loop` able to drive an infrastructure inner loop end-to-end: build the verify/teardown/seed/scan harness → static-preflight → plan/preview → idempotent apply → active end-to-end smoke (load the real URL, read logs, debug) → converge, with the agent reading ground truth, not a human relaying it.
- Generalize the latent assumption into an explicit, tech-stack-universal preflight: a verification mode is only claimable if its mechanism exists; otherwise task zero (often *several* task-zeros) builds it.
- Give infra work a verification contract that matches its layered, stateful, multi-hop, partially-irreversible reality, with operational-safety guardrails an existing reviewer can enforce.
- Make the security check on infra **robust and non-skippable**, proportionate to the blast radius of a misconfigured deploy.

**Non-goals** (could-have-been goals, deliberately dropped):
- *Not* building any executable infrastructure — no deploy wrapper, plan-parser, cost-gate script, or runtime. This RFC ships doctrine + reference prose only (Decision 1). Building tooling would fail CHARTER Principle 3 ("a habit, not a tool"), the same bar that put browser-bridge out of charter.
- *Not* a new infra-lens reviewer. CHARTER caps reviewers at three; P3 feeds `quality-engineer` (Decision 4).
- *Not* a new risk trigger for "infrastructure". Destructive/irreversible already routes `apply` to full mode (RFC-0025); adding an infra trigger would be redundant.
- *Not* progressive delivery (canary/blue-green) — Kubernetes-specific, deferred (Decision 7).
- *Not* tool-specific bindings. P2/P3 are written Terraform/Pulumi/CDK/CloudFormation-neutral (Principle 1); examples illustrate, they don't bind.

## Proposal

Cascaded under the requested decisions.

**Decision 1 — doctrine, not tooling.** Everything below is prose: edits to `work-loop`'s SKILL.md and a new `references/*.md` module set. No executable code ships. This is the `security-checklists` shape — a depth library a reviewer reasons from — which the repo has already accepted as a *habit*, not infrastructure.

**Decision 2 — P1: generalized verification-mechanism preflight.** Add one obligation to the PLAN verification-mode step (SKILL.md:156): *picking a verification mode requires confirming the mechanism for that mode exists. If it does not, creating it is task zero — a precondition task, not an afterthought, and the loop offers to scaffold it.* This is agnostic — it applies to a missing test runner as much as a missing smoke check. It strengthens, not replaces, the existing assumption-trio: "the smoke-check exists" is precisely the kind of assumption that goes unsurfaced today because it doesn't feel like one. Grounded in walking-skeleton / tracer-bullet and CD's "the deployment pipeline must exist first" (research F4.1-4.2), which are tech-stack-universal. The preflight is **universal across both light and full mode** — it is one sentence and cheap; only the heavier P2/P3 layers remain full-mode-only.

For infra the mechanism is rarely one artifact — it is a **multi-artifact set, and the preflight enumerates each as its own task-zero**: a **verify-status** script (does the deploy report healthy?), a **teardown** script (clean down a failed/ephemeral run), **test-data / mock-user seeding** (so the smoke probe has something to exercise), and a **provider-appropriate policy-as-code / CSPM scanner** (Checkov / tfsec / cloud-native CSPM — adopter's choice, never pinned to one tool). That scanner is the load-bearing one for *per-provider depth*: its vendor-maintained rulesets hold the per-service secure-config and misconfig checks that the standards-grounded reviewers cannot and should not carry — and the **same** scanner feeds two layers, security misconfig → P5 and operational misconfig → P2's static-preflight. This is the walking-skeleton applied literally: you build the build/deploy/test/teardown/scan harness *before* the feature deploy, because until it exists the deploy is not verifiable. The loop names these as prerequisite tasks and offers to scaffold them; it does not ship them as executable tooling (Decision 1).

**Decision 3 — P2: infra verification flavor.** Add a fourth verification flavor to the PLAN list: **infra/deploy**. Its contract is a layered GATES sequence rather than a single check:

1. **Static preflight** — validate/lint/policy-as-code (the lint+typecheck analog), run via the provider-appropriate scanner the P1 preflight requires as a task-zero mechanism.
2. **Plan/preview** — a dry-run diff reviewed before any mutation (preview-then-converge, research F1.1).
3. **Apply** — idempotent convergent apply, named as a **precondition**: re-running after a fix must converge, not collide (research F1.2). Imperative non-idempotent scripts are flagged as the retry-collision root cause.
4. **Active end-to-end smoke** — not a single status check but a multi-hop probe ("created ≠ works", research F2.2): **seed test/mock users → load the real CDN/website URL → assert it actually renders → on failure, pull access/error logs and debug → tear down**. This reuses the existing visual-manual-QA doctrine ("exercise the real built artifact… for a service endpoint") and extends it with the infra-specific hops (stack-status, health probe, log-driven debugging). The observability needed for that debugging — access/error logs, health endpoints, the verify-status signal — is its own reference module (P3, `observability-and-smoke`).
5. **Rollback** — name the known-good re-apply path before the first apply (no atomic rollback exists; research F2.6).

Cross-linked to the plan's existing `## Rollout` section (CONVENTIONS.md:335-337); the verification flavor names *how we verify*, the Rollout section already owns *the deployment sequencing*. No duplication.

**Decision 4 — P3: `operational-safety` reference library, consumed by `quality-engineer`.** A new skill `operational-safety` holding boundary-keyed `references/*.md` modules, structurally identical to `security-checklists`. The orchestrator loads only the matching modules and inlines them into a reviewer's brief via the same routing mechanism it already uses (SKILL.md:555-578). **Six** modules (MECE along *operational failure mode*):

| Module | Covers | Grounded in |
|---|---|---|
| `state-and-idempotency` | convergent re-apply, state locking, single-writer | F1.2, F1.3 |
| `blast-radius` | parse-plan destroy/replace gating, `prevent_destroy`, proposer≠approver for destructive ops | F3.1, F3.2 |
| `environment-isolation` | throwaway/staging vs prod, separate state/accounts | F3.3 |
| `cost-and-teardown` | cost-ceiling-as-gate, destroy-on-fail, TTL, no orphans | F3.4, F3.5 |
| `drift-and-rollback` | read-only drift detection, known-good re-apply path | F1.4, F2.6 |
| `observability-and-smoke` | active end-to-end probe (load real URL, assert render), access/error-log access, health endpoints, the verify-status signal, log-driven debugging | F2.2; taxonomy follow-up (AWS WAF Operational Excellence, Google SRE monitoring) |

The first five and the sixth are deliberately distinct (see the taxonomy follow-up in `0041-notes/research.md`): every major operational taxonomy splits write-path convergence (`state-and-idempotency`) from divergence-detection-and-recovery (`drift-and-rollback`) — AWS Well-Architected *Change Management* vs *Failure Management*, Google SRE *Release Engineering* vs *Incident Response*, Terraform `apply` vs `-refresh-only`, Pulumi Day-1 vs Day-2 — so they are kept separate, not merged; and observability is its own design area (AWS WAF Operational Excellence, Google SRE monitoring), which the user's "load the URL + read access logs + debug" requirement makes load-bearing.

**Consumer = `quality-engineer`**, whose existing lens is *reliability, observability, maintainability* — exactly where idempotency, drift, rollback, teardown, cost, and observability live. **No new reviewer** (CHARTER three-reviewer ceiling). The **security** lens on infra stays with `security-reviewer` (P5) — the carve that clears Principle 2: `security-checklists` owns *security* config; `operational-safety` owns *reliability/ops*. The destructive-op-needs-human-approval rule is already AGENTS.md doctrine + `adversarial-reviewer`'s scope/destructive lens.

**Decision 5 — P4: agent-drives-verification.** State as harness-agnostic doctrine: the agent runs the deploy and reads the real environment output itself; a human relaying errors is the anti-pattern (research F5.1). Name Claude Code primitives as the accelerant (never a dependency, matching how `/verify` is treated): background tasks for long applies, `asyncRewake` to wake on a background deploy's exit with stderr surfaced, `PreToolUse` to gate destructive commands. Adapters without these lose the shortcut, not the doctrine.

**Decision 6 — P5: mandatory, robust security review for infra — a reviewer + scanner *pair*.** Because a misconfigured deploy is high-blast-radius and dangerous, infra-flavored work **non-skippably invokes `security-reviewer`** — at the spec stage (secure-design pass: is the control specified as an acceptance criterion?) *and* on the diff — rather than leaving it to the discretionary security-boundary trigger. The orchestrator force-loads the infra-relevant `security-checklists` modules, typically more than one: `config-misconfig` (IaC/deploy config, SKILL.md:572), `access-control` (IAM/policies), `secrets-and-crypto` (keys, secrets in state/env), `outbound-ssrf` (public exposure, CDN/origin egress), and `supply-chain` (provider/module pinning) — loaded 1–N as the diff warrants, per the existing boundary→module routing table. This adds **no new reviewer and no new module** — it makes the *existing* security pass mandatory and multi-module.

**The reviewer is not the per-provider depth source — the scanner is.** `security-reviewer` reasons from cross-cutting *standards* (OWASP/ASVS/CWE + STRIDE/LINDDUN), so it catches security failure *classes* (over-broad IAM, public exposure, unencrypted-at-rest, secrets in state, metadata SSRF, missing audit logging) and checks control-completeness — it deliberately does **not** carry AWS/Azure/GCP per-service secure-config baselines, which would break Principle 1 and be stale on arrival. That per-provider depth comes from the **policy-as-code/CSPM scanner the P1 preflight already requires** (its rulesets *are* the provider baselines, vendor-maintained). So P5 is a **pair**: scanner for per-provider breadth + reviewer for failure-class reasoning. Neither substitutes for the other; together they are robust.

**Deferred-authority pointer (kept evergreen by construction).** `config-misconfig` gains a thin pointer naming the standing authorities the reviewer reasons against — **CIS Benchmarks** (Center for Internet Security) and each provider's well-architected security guidance (**AWS Well-Architected — Security Pillar**, **Microsoft Cloud Adoption Framework / Azure Well-Architected — Security**, **Google Cloud Architecture Framework — Security**). The pointer is kept evergreen **by naming the stable publisher+document, never a URL and never a version** — the agent resolves the current document by name at use-time; and the *actual* depth lives in the self-updating scanner, not the pointer, so the pointer cannot rot in a way that matters. It complements, not replaces, SAST/SCA scanners.

**Decision 7 — defer progressive delivery.** Canary/blue-green metric gates (Argo Rollouts/Flagger) are largely Kubernetes-specific and fail the universal-stack bar; deferred to a future RFC if a Kubernetes-using adopter needs it, not built here.

## Options considered

**Axis: where does the infra capability live, and what kind of artifact is it?** This axis exhausts the design space because any solution must answer both "what form" (doctrine vs. tooling) and "what home" (existing loop vs. new surface). Options are MECE along it.

| Option | Form | Home | Verdict |
|---|---|---|---|
| **A. Doctrine + reference library in `work-loop`** ★ | prose only | existing loop + new `references/` | **Recommended** |
| B. New executable infra tooling | code | new scripts/runtime | Fails Principle 3 |
| C. A standalone `infra-deploy` skill | prose | new top-level skill | Fails Principle 2 (duplicates the loop) |
| D. A fourth infra-lens reviewer | prose | new subagent | Fails the three-reviewer ceiling |
| E. Do nothing | — | — | Cost-of-delay below |

- **A (recommended)** — mirrors `security-checklists`, an accepted precedent for a doctrine depth-library the loop already inlines. Clears all four principles; P1 (the universal core) is exercised on every task, not just infra, so it clears Principle 4 even where P2/P3 fire rarely.
- **B** — a plan-parser or deploy wrapper is *runtime infrastructure*; CHARTER Principle 3 forbids it, and it would need per-tool bindings, breaking Principle 1. This is the option Decision 1 rejects.
- **C** — a parallel deploy skill re-implements PLAN/GATES/REVIEW the loop already owns (Principle 2). The capability belongs *in* the loop, not beside it.
- **D** — the question the user raised; the charter answers it: three reviewers is the ceiling. The infra lens is `quality-engineer`'s existing reliability concern.
- **E (do-nothing)** — the loop stays implicitly application-only; infra users keep relaying deploy errors by hand, and "low-risk so I'll wing the deploy" stays a silent gap. Cost-of-delay: the pain is recurring and present now; the agnostic P1 gap (claiming a verification mode whose mechanism doesn't exist) silently degrades non-infra work too — e.g. a goal-based task that claims a build command not yet wired, or a TDD task with no runner; and most seriously, a high-blast-radius security misconfiguration (a public bucket, an over-broad IAM role) can ship because the security pass was discretionary rather than mandatory (P5).

Prior art for the *shape* of A: `security-checklists` (in-repo); Continuous Delivery's "pipeline-first" and walking-skeleton (the verification-mechanism-first principle); Terraform/Pulumi/CDK preview-then-converge (the layered-GATES content). Full citations in [`0041-notes/research.md`](0041-notes/research.md).

## Risks & what would make this wrong

**Pre-mortem.**
- *P2/P3 drift toward tool-specific prose.* If modules quietly assume Terraform, Principle 1 breaks. Mitigation: write each module tool-neutral; examples are illustrative and labelled, never normative; an adversarial pass checks for stack-binding.
- *`operational-safety` overlaps `security-checklists` and confuses reviewers about who owns what.* Mitigation: the reliability-vs-security carve is stated in both skills' front matter; the routing table assigns IaC-security → `config-misconfig`, IaC-reliability → `operational-safety`.
- *P1 becomes box-ticking* ("mechanism exists: yes") without teeth. Mitigation: the obligation is "name the mechanism or write task zero to build it" — a concrete artifact, not a checkbox.
- *Scope inflation back into tooling.* A reviewer or implementer is tempted to "just add a small plan-parser". Mitigation: Decision 1 and Non-goals make executable infra an explicit out-of-bounds; the spec inherits it as a constraint.
- *P5 mandatory-security becomes a rubber stamp* — invoked but shallow, defeating the robustness goal. Mitigation: P5 force-loads the specific infra modules and runs at both spec stage and diff; the security pass must cite which modules it applied, and is re-run to clean like the other reviewers.
- *Six modules over-segment and reviewers skip some.* Mitigation: the orchestrator loads 1–N by routing, never a flat march of all six; the taxonomy follow-up justifies each as a distinct failure-mode family.
- *The deferred-authority pointer rots (link rot).* Mitigation: the pointer names stable publisher+document only — **no URLs, no versions** (the agent resolves the current doc by name); and the actual per-provider depth lives in the self-updating scanner, not the pointer, so a stale pointer never gates a real check.
- *Requiring a policy-as-code/CSPM scanner edges toward tool-binding (Principle 1).* Mitigation: the requirement is **mechanism-level** (a provider-appropriate scanner must exist), not tool-level — the adopter picks Checkov / tfsec / cloud-native CSPM, exactly as the repo requires "tests exist" without mandating a test framework.

**Key assumptions (falsifiable).**
- *Infra work routes to full mode today via destructive/irreversible* — if false (some deploys read as low-risk and land in light mode), the heavier P2/P3 layers wouldn't load when needed. (Believed true; `apply` is destructive by nature. P1's preflight is universal across both modes by design, so it is unaffected either way.)
- *`quality-engineer`'s lens genuinely covers operational safety* — if reliability/observability/maintainability doesn't stretch to blast-radius/cost, a reviewer-fit gap appears. (Believed true; these are textbook reliability concerns.)
- *The orchestrator's module-inlining mechanism is reusable for a second library as-is* — if it's hard-coded to `security-checklists`, P3 needs a mechanism change. (Believed low-cost; the routing is table-driven — see spike.)
- *Making `security-reviewer` mandatory for infra is the right strength, not overkill* — if most infra changes are trivial config tweaks, a forced multi-module security pass could feel heavy. (Believed correct; the blast radius of the *non-trivial* case — a public bucket, an over-broad role — dominates, and the routing loads only the modules the diff warrants, so a one-line change pulls one module, not five.)

**Drawbacks.**
- Adds a second reference library to maintain, and lengthens `work-loop`'s PLAN/REVIEW prose — real surface-area cost. Justified by the recurring, present pain and the universal reach of P1.
- For adopters who never deploy infra, P2/P3 are dormant weight (mitigated: P1 still earns its place on every task; P2/P3 load only on trigger).

## Evidence & prior art

- **Spike / de-risk result.** The riskiest assumption — that this is a *habit* (in charter) and not duplicative of `security-checklists` — was checked in-repo, no code spike needed. The mechanism P3 requires (an orchestrator that inlines `references/*.md` from a deterministic routing table) **already exists and already fires on IaC/deploy changes**: SKILL.md:555-578 routes "IaC / deploy config" → `config-misconfig`. So P3 is a second lens reusing a proven, table-driven mechanism, not new infrastructure → clears Principle 3. **Inventory diff (the closing method the research named):** `config-misconfig` covers IAM / CORS / secrets / deploy-config from the *security* angle only and contains no idempotency / blast-radius / drift / cost / teardown / observability-and-smoke prose (verified) — so all six `operational-safety` modules are net-new surface, and the reliability-vs-security split is clean → clears Principle 2.
- **Repo precedent.** RFC-0025 (risk triggers already route destructive work to full mode; the byte-identical risk-trigger block across files is an implementation caution for the spec, not a content change here); RFC-0029 + `security-checklists` (the exact depth-library pattern); `work-loop` PLAN verification-mode step (SKILL.md:156-193) and module-routing table (555-578); CONVENTIONS.md:335-337 (the `## Rollout` plan section P2 cross-links); CHARTER Principles 1-4 (the four bars this clears).
- **External prior art.** Distilled in [`0041-notes/research.md`](0041-notes/research.md) (applied-mode survey, per-finding confidence + known-unknowns): preview-then-converge + idempotency (Terraform/Pulumi/CDK); layered verification + smoke tests (Terratest, `terraform test`, policy-as-code); destructive/cost guardrails (Atlantis, GitHub Environments, CDK ConfirmPermissionsBroadening, Infracost); walking-skeleton/tracer-bullet + CD pipeline-first + test-driven-infrastructure (Cockburn, Hunt & Thomas, Humble & Farley, Kief Morris); ReAct/ACI + Anthropic ground-truth + Claude Code hooks/background/async-rewake. The one literature *gap* the survey found — agents driving external deploy CLIs against real infra is under-studied (F5.5) — means this RFC is partly defining the shape, an argument for shipping doctrine and observing, not for waiting.
- **Module-taxonomy resolution.** A focused follow-up (research.md § "Follow-up research") confirms keeping `state-and-idempotency` and `drift-and-rollback` separate, and adding `observability-and-smoke` as a sixth: every major operational taxonomy (AWS Well-Architected, Google SRE, Terraform, Pulumi) splits write-path convergence from divergence-detection/recovery, and treats observability as its own design area.
- **Citation-integrity pass (run, not self-certified).** All load-bearing external citations were fetched and confirmed; 9/12 clean. Three corrected in research.md: (1) the Terraform idempotency no-op claim was re-pointed from the intro page to the apply tutorial (the intro page doesn't state it); (2) Atlantis's `approved` gate is *blanket over all applies* (covers the destructive subset), with CDK `ConfirmPermissionsBroadening` carrying the destructive-scoped claim; (3) Cockburn's walking-skeleton URL is unreachable (expired TLS) and the "deploy to a real environment" emphasis is GOOS's, not Cockburn's canonical definition — downgraded to secondary and re-attributed. `asyncRewake` and `PreToolUse` were confirmed as real, correctly-named Claude Code hook fields.

## Open questions

None remaining. The module-taxonomy question (five vs. merge, plus the observability sixth) was resolved by the focused follow-up research — see the Proposal (Decision 4) and `0041-notes/research.md` § "Follow-up research". Module-prose boundaries are a spec-authoring detail, not an open design question.

## Amendments

- **2026-06-23 (additive, Approver-signed: eugenelim).** Strengthened P1/P5 after a review question — "is `security-reviewer` equipped for every cloud provider's checks?" — clarified the answer: *no, and by design.* (a) P1 now requires a **provider-appropriate policy-as-code/CSPM scanner** as a task-zero mechanism (it holds the per-provider depth; the same scanner feeds P2's static-preflight and P5's security depth). (b) P5 is reframed as a **reviewer + scanner pair** — the standards-grounded reviewer reasons about failure *classes*, the scanner holds per-provider baselines. (c) Added a **URL-free, version-less deferred-authority pointer** (CIS Benchmarks + per-provider well-architected security) in `config-misconfig`, kept evergreen by naming publishers not links and by keeping depth in the self-updating scanner. No reversal of any accepted decision; all additive.

## Follow-on artifacts

Filled in on acceptance.

- **ADR-0031**: record "infra is a verification flavor consumed by `quality-engineer`, not a new reviewer; security on infra is a *mandatory* `security-reviewer` + scanner pair" (the three-reviewer-ceiling + mandatory-security decisions). (ADR-0030 was taken by RFC-0040.)
- **Spec**: `docs/specs/infra-aware-work-loop/` — P1 multi-artifact preflight (incl. the required policy-as-code/CSPM scanner as a task-zero mechanism) + P2 active-end-to-end infra verification flavor + P5 mandatory-security wiring (reviewer + scanner pair) (work-loop SKILL.md edits).
- **Spec**: `docs/specs/operational-safety-checklists/` — P3 six-module reference library + routing-table entries + `quality-engineer` wiring + the URL-free deferred-authority pointer in `security-checklists`' `config-misconfig`.
- **Convention touch**: none expected (the risk-trigger set is unchanged); confirm at spec time.
- **Changelog**: `docs/product/changelog.md` `[Unreleased]` entry for the work-loop behavior change.
- **Pack version**: bump `core` (work-loop edits) and add the new `operational-safety` skill to the catalogue/marketplace manifest at spec time.
