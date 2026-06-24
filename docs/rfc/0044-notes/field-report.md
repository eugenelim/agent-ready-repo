# Field report: real infra builds on the RFC-0041 loop

> **Provenance & scope.** Distilled from **two** independent, multi-day
> infrastructure builds run through `work-loop` (full mode), on **different
> stacks**:
>
> - **Build 1** — a managed cloud agent-runtime platform: managed agent runtime
>   + a tool-function gateway + an auth-fronted API facade + a managed datastore
>   + a CDN-hosted SPA, via typed IaC (CDK-class).
> - **Build 2** — a different stack on the same cloud: a **private-VPC managed
>   graph database** + a **managed vector/search service** + a **containerized
>   ingestion task** + the surrounding network, via the same typed IaC.
>
> All project-, domain-, account-, and resource-identifying details from both
> builds have been scrubbed. What remains is the **failure/▢success pattern**,
> which is platform-agnostic. This is the evidence base for RFC-0044.

## What the loop already did well (RFC-0041 working as designed)

Spec/plan was strong in both: security-critical invariants specified as
acceptance criteria, destructive-op risk trigger routing to full mode,
synth-time assertions written. Build 2 went further on verification — but
**only because the human explicitly demanded a "build a probe" approach**, and
it then carried that pattern across specs. The verification *shape* RFC-0041
defines held; what the loop did *not* do by default is the subject below.

## The cross-cutting pattern

In **both** builds the human had to push for real end-to-end verification
("how are you verifying the install works? are you inserting and then
retrieving?"; "how are you confident everything works? — the primary flow still
times out"). The loop reasons from **model memory or a cheap proxy** instead of
the platform's **ground truth**, at every stage of the infra inner loop. The
two builds together exercise enough surface to make the failure families MECE.

## MECE failure-mode taxonomy (axis: stage of the infra inner loop where the loop substitutes memory/proxy for ground truth)

The infra inner loop is **Author → Provision → Verify → Debug**. Two stages
split into two truth-kinds each (can-it-build vs. will-it-work; cheap-proxy vs.
runtime-ground-truth), giving six collectively-exhaustive families.

### 1. Author · structural grounding — the **contract** [Build 1, dominant]
Is the resource/call legal & buildable per the platform's *structural* contract?
- Invented CLI flags; unknown required project scaffolding; violated a resource
  **naming regex**; wrong tool-schema **shape** + an **unsupported schema
  keyword**; tried to update an **immutable** field (replace-only).
- The human's fix: hand the loop a curated platform-knowledge skill mid-session.
- *Root: built from memory, not the platform's machine-readable contract.*

### 2. Author · behavioral grounding — the **craft** [both builds]
Will it actually *work reliably* given cloud realities the contract doesn't state?
- **Permissions sufficiency.** Least-privilege churned reactively — many
  iterations adding invoke/grant statements until the call path was authorized
  (one build iterated 38+ invoke-permission edits).
- **Eventual consistency / propagation.** A managed feature announced "takes ~10
  minutes to become active"; freshly-created roles/resources aren't immediately
  usable — the loop didn't design for the wait.
- **Timeout / cold-start / retry.** Reactive timeout escalation (read-timeout
  120→300; function timeout 15→30→60s) and ad-hoc `sleep`s instead of designed
  backoff; **no client/frontend cold-start tolerance** — a cold-start gateway
  timeout surfaced raw to the user instead of being retried.
- **Dependency / ordering.** Cross-resource cycles and ordering fixed by trial.
- *Root: the model doesn't apply golden cloud-implementation practice by default.*

### 3. Provision · identity & convergence [both builds]
- **Credentials.** Re-resolved per call until an SSO wrapper timed out; the
  durable fix (resolve **once** into a static session, `unset` the profile,
  reuse) was rediscovered **independently in both builds** — strong signal it
  should be default, not discovered.
- **Convergence.** A stack stuck in a **terminal-failed state**
  (`ROLLBACK_COMPLETE`) can't be updated — must be **destroyed and recreated**;
  non-idempotent creates **collided** on re-run instead of converging.
- **One-off command-spray vs. reusable scripts.** Both builds drove the live
  environment through long streams of **one-off shell commands** — thousands of
  invocations, dozens of ad-hoc log/invoke calls, hand-tuned `sleep`s and
  reactive timeout bumps — that each re-resolved credentials and **left nothing
  reusable behind**. Where the loop instead wrote a **reusable, idempotent,
  credential-reusing script** (deploy/probe/teardown), iteration *converged*;
  where it sprayed commands, it *restarted*. Reusable scripts reusing the
  established session should be the default interaction mode, not the exception.

### 4. Verify · oracle fidelity (static, phased) [both builds]
- The cheap early oracle (synth/validate/lint) **passed while the system was
  still broken** — it does not catch what only **runtime deploy + smoke** catch.
  Treating "synth passes / status: deployed" as done is the **deployed ≠ working**
  fallacy. Oracles are **phased** (lint < plan/preview < runtime smoke) and the
  early ones must not be over-trusted.

### 5. Verify · runtime exercise (the data-plane probe) [Build 2, dominant]
The smoke that actually proves it works has a **different shape** than app-code
verification:
- **In-network if the resource is private.** A private-VPC datastore **cannot be
  probed from the laptop** — the probe must run **inside the network boundary**
  (an in-VPC task/function). The human had to ask for "a secure in-VPC way to
  verify."
- **Data-plane round-trip**, not control-plane health: **write a record → read
  it back**, not "resource exists / status healthy."
- **Readiness-aware**: poll until ready with **bounded backoff**, distinguishing
  **not-yet-ready/propagating** from **actually broken** (Build 2 polled a deploy
  with a readiness predicate; Build 1 thrashed redeploys on what was partly a
  cold-start/propagation delay).
- **The probe is itself infra** and must be **torn down** ("make sure teardown
  includes the probe teardown") — and runs against an **ephemeral, uniquely-named
  environment** so re-runs don't collide (the `defer destroy` / `dev-test-run-uuid`
  pattern from infra-testing practice; see external corroboration).

### 6. Debug · failure localization [Build 1, dominant]
- A gateway-timeout failure was chased in the **backend-runtime log dozens of
  times** when it was emitted by the **facade one hop upstream**. No discipline
  for mapping a symptom (504/timeout → proxy; 403 → authorizer/IAM; 500 →
  handler) to the layer that emits it, nor for bisecting the chain.
- No use of a **failure-signature → likely-cause catalog** — many infra failures
  are well-known patterns with a near-deterministic cause (ImagePullBackOff,
  OOMKilled, `ROLLBACK_COMPLETE`, a cold-start 504, a conditional-write contention error).
  OSS diagnostic agents resolve ~40% of investigations by matching such a
  signature to a runbook before any deep log reading (see external corroboration).

*(Adjacent, not a loop-stage: secrets/PII hygiene — a corporate email/identifier
leaked into IaC parameters and had to be scrubbed from git history. Belongs to
`security-checklists`, noted for completeness.)*

## Root-cause reading

RFC-0041 gave the loop the verification **shape** but assumed the agent **knows
the platform and will exercise the whole chain**. Both builds falsify both
assumptions, across all six families. The unifying cause: **the loop builds,
verifies, and reviews against model memory or a cheap proxy rather than the
platform's actual contract and runtime ground truth.** RFC-0044 grounds all six.

## External corroboration & added items (NOT from the two builds)

To avoid over-fitting to two builds, the taxonomy was cross-checked against
industry research and OSS prior art (full citations in the RFC):

- **MECE cross-check — an empirical IaC defect taxonomy.** A replication study
  (**3,364 defect commits / 285 OSS repos**, plus an expanded 447 OSS + 94
  proprietary projects) confirms **eight defect categories** across PL-IaC tools
  (Pulumi, Terraform CDK, AWS CDK). The abstract names *Configuration Data* (most
  frequent), *Idempotency*, and *Security* among them; these map onto the
  inner-loop families — Configuration Data → families 1–2 (contract + craft);
  Idempotency → family 3 (provision/convergence); Security → adjacent
  (`security-checklists`) — an independent-axis cross-check that the six families
  capture the same failure space, none of the named categories falling outside.
- **The convergence loop is a recognized pattern, not invented.** A research
  system frames LLM-IaC generation as a **"fail → learn → refine → succeed"**
  loop driven by **deployment-simulation feedback** (not static linting alone) —
  external prior art for the runtime-truth-over-cheap-proxy thesis (families 4–5).
  *(Cited for the loop's existence and shape from its title/abstract; the paper's
  internal feedback-signal details were not independently verified.)*
- **OSS prior art for the debug family (6).** CNCF diagnostic agents
  (HolmesGPT, k8sgpt) run a **ReAct loop over live observability**, correlating
  logs/events/status — and **~40% of investigations resolve by matching a known
  failure signature to a runbook** (OOMKilled, ImagePullBackOff). This is the
  evidence for the failure-signature catalog added to family 6.
- **OSS prior art for the probe family (5) and oracle fidelity (4).** Terratest's
  **deploy → verify → destroy** (with `defer destroy` binding teardown to the
  test), **data-plane assertions** (HTTP/API calls, not "resource exists"), and
  **ephemeral uniquely-named environments** are the established shape for V2;
  the standard layered strategy (static/lint < plan + policy-as-code < runtime
  test) grounds V1, and the documented Terraform reality that **`plan` can pass
  while `apply` fails** is the hard evidence that the cheap-early oracle must not
  be over-trusted.

## The key realisation (why "generic prose won't cut it") — applies to families 1, 4, 6

The agent cannot *know* every stack. It must drive the **deterministic oracles
the toolchain already ships**, via a tiered protocol keyed to the **tool, not
the vendor**: T0 detect stack → T1 toolchain oracle (validate/plan/preview/synth
+ a machine-readable schema slice — **heterogeneous**: CFN `createOnlyProperties`
✅ / Pulumi `replaceOnChanges` ✅ / **Terraform force-new NOT in
`providers schema -json`** ❌, read from `plan`+docs) → T2 curated platform skill
for the behavioural surface no schema encodes (detect + **recommend** if absent) →
T3 docs → **final oracle: the runtime data-plane probe** (family 5). Routing on
the tool, not the vendor, makes coverage a **capability spectrum** (strong /
medium / weak oracle) that includes Hetzner / on-prem / bare-metal at whatever
strength their tooling exposes — **not big-three-only** — and obliges the agent
to **declare its oracle tier + confidence** rather than fake coverage.
