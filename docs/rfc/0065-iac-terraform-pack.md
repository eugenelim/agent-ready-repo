# RFC-0065: The `iac-terraform` pack

- **Status:** Open
- **Author:** eugenelim
- **Approver:** eugenelim <!-- repo owner; accepts the D2 charter-boundary
  self-approval flagged by review -->
- **Date opened:** 2026-07-17
- **Date closed:**
- **Decision weight:** heavy <!-- deliberately admits stack-specific content, which the CHARTER's "does NOT" list refuses in general; crosses a charter boundary → explicit Approver sign-off. -->
- **Related:** `core` (work-loop / operational-safety / security-checklists), `governance-extras` (new-adr), packs `atlassian` / `figma` / `credential-brokers` (opt-in tool-specific precedent), profiles (default-profile exclusion)

> **Self-contained for the pack's own content.** Every Terraform-specific artifact
> the pack ships — standards, provider contract, category references, policy,
> pipeline shape, ADR topics — is specified inline here, buildable without any
> external source. The pack *deliberately reuses* `core`/`release-loop` verification,
> operational-safety, and reviewers **by reference**; those are pointed to, not
> restated, so the full capability is "this doc + the named `core` primitives," not
> this doc alone. A coined term is glossed on first use.

## Reviewer brief

- **Decision:** Add a new opt-in, repo-scope pack, `iac-terraform`, that turns a
  plain-language *intent* (a one-line description of infrastructure a user wants)
  into governed, best-practice Terraform/OpenTofu plus a human-gated CI/CD
  pipeline — decision-record-driven and cloud-agnostic.
- **Recommended outcome:** accept.
- **Change if accepted:** (1) new `packs/iac-terraform/` with **two skills** —
  `generate-iac` (author) + `reconcile-iac` (author-side drift audit → propose →
  route; D17) — sharing a **references-heavy** body (per-cloud + per-CI progressive
  references, standards, provider contract, verify/iterate detail), **zero seeds**,
  **zero agents** (reuses `core`'s reviewers; release-loop-compatible by convention);
  (2) it is **not** added to any default profile; (3) **three** tool-neutral habits
  harvested into `governance-extras` (governance-index, extension-contract, and a
  `new-adr` infrastructure-decision starter catalogue).
- **Affected surface:** new pack tree; `governance-extras` (governance-index
  template/convention + `new-adr` infra mode); `architect` (one `architect-review`
  rubric line for the extension-contract pattern); self-host include list; docs/rfc.
  Core is **untouched**.
- **Stakes:** costly-to-reverse (a shipped pack accrues adopters), but each piece
  is individually revertible; the charter-boundary precedent is the one-way part.
- **Review focus:** (a) does an opt-in tool-specific pack erode the charter's
  "not a framework that picks your tech stack" line? (b) is the pack genuinely
  additive over `core`'s existing infra doctrine, or duplicative? (c) is the
  zero-agent, loop-arc reframe (D6/D7) correct — no new reviewer, no lead, apply
  owned by `release-loop`?
- **Not in scope:** changing `core`'s stack-neutral doctrine; shipping this in a
  default profile; supporting non-Terraform IaC engines in v1; **shipping any
  agent** (reviewer or coordinator) or a new loop.

## The ask

- **Recommendation (BLUF):** Approve `iac-terraform` as an **opt-in, repo-scope,
  tool-specific pack** that *reuses* `core`'s infrastructure doctrine and adds
  only the Terraform-specific scaffolding and a thin workflow driver `core`
  deliberately does not carry. Approve harvesting two tool-neutral habits into
  `governance-extras` separately.
- **Why now (SCQA):** *Situation* — the catalogue already carries strong,
  tool-neutral infrastructure doctrine (stop-at-plan, human-gated apply,
  policy-as-code, drift/state/idempotency, ADR authoring). *Complication* — that
  doctrine has no shipped, ready-to-run Terraform scaffolding an adopter can act
  on; teams re-derive the same layered-Terraform + OIDC-pipeline + policy-on-plan
  setup by hand every time. *Question* — where should a reusable, opinionated
  Terraform generator live without contradicting the charter's refusal to pick a
  tech stack?
- **Decisions requested:**

  | ID | Question | Recommendation | Why | Decide by | Reviewer action |
  | --- | --- | --- | --- | --- | --- |
  | D1 | Add `iac-terraform` as an opt-in, repo-scope pack, excluded from every default profile? | Yes | Same posture as `atlassian`/`figma`/`credential-brokers` | this review | Confirm the exclusion + the pack boundary |
  | D2 | Deliberately admit stack-specific content (Terraform + cloud) as a charter exception, opt-in only? | Yes | The value is high and frequently reached; opt-in contains the blast radius | this review | Rule on the charter-boundary precedent |
  | D3 | Reuse `core` (infra-verification, operational-safety, security-checklists) rather than re-ship its doctrine? | Yes — hard requirement | Duplication would drift and violate "substantive not duplicative" | this review | Confirm the pack ships only scaffolding + a thin driver |
  | D4 | Harvest the tool-neutral habits (`governance-index`, `extension-contract`, `new-adr` infra mode) into `governance-extras` as separate items? | Yes — **shapes decided in D16** | They are tool-neutral and belong out of a Terraform pack | this review | Confirm the split (see D16 for the form each takes) |
  | D5 | v1 *validated* provider depth | **AWS + GCP + Databricks** validated (a passing worked example each), **and the AWS example validated on *both* `terraform` and `tofu`** (WA-review Major 2 — else OpenTofu is a headline feature with zero coverage); Azure + the other categories (§6b) contract-complete but unvalidated | Spans two hyperscalers (four-file contract) + one data-platform reference + both engines — proves the taxonomy across *categories* **and** the dual-engine claim | **decided** | ✅ AWS(+tofu) + GCP + Databricks |
  | D6 | Agent topology: does the pack ship any agents (a reviewer, or a "lead" coordinator)? | **No agents at all** — reuse `core`'s forked-context reviewers; be release-loop-compatible, ship no lead | Three-reviewer ceiling; the pack is not a new loop, it is IaC-flavored authoring inside `work-loop` + deploy inside `release-loop` | this review | Confirm zero-agent shape |
  | D7 | Gate/apply model: the pack's own "two human-gated apply boundaries", or the target-repo loop arc? | **The loop arc** — inner-loop `plan` = G4 handoff; `release-loop` owns deploy→converge on ephemeral envs; human owns G5 + minimum-regret consent gates | Follow the repo's loop conventions rather than a bespoke gate model | this review | Confirm the reframe |
  | D8 | Is `generate-iac` one skill that also does verify, or authoring-only? | **Authoring-only** — verify is `core`'s `infra-verification` + reviewers, tapped, not re-shipped | A bundled verify would duplicate exactly what §1b reuses | this review | Confirm the split |
  | D9 | Ship CI generators + provider configs as `seeds/` (copied into the repo) or progressive `references/`? | **Progressive `references/`** — the skill loads only the target cloud + target CI; not all clouds/CIs apply to any one adopter | Seeds would dump 3 clouds × 3 CIs of mostly-irrelevant scaffolding | this review | Confirm packaging |
  | D10 | Ship the 7 template ADRs as `seeds/docs/adrs/`? | **No** — it collides with the adopter's ADRs + the repo's ADR conventions; instead **mine them into `governance-extras`/`new-adr`** as an infrastructure-decision starter catalogue | Reuse the ADR approach we already have; don't ship a rival ADR set | this review | Confirm the mine-not-ship |
  | D11 | Verification modes: specify all four, or specify the inner-loop modes and **refer** to `release-loop` for deploy-time probes? | **Specify** the inner-loop modes it owns (static preflight, `plan`, goal-based policy); **refer + name tooling** for module/contract tests (reused `quality-engineer` test-author mode + `terraform test`/Terratest); **refer** to `infra-verification` for the outer-loop probes it builds | Re-specifying the V2 data-plane probe *or* the reused test tooling duplicates doctrine the pack reuses; IaC uses a *combination* of modes across the loops (§2a) | this review | Confirm the mention-vs-refer boundary |
  | D12 | Engine: Terraform only, or **Terraform + OpenTofu**? | **Both** — engine-neutral baseline that runs on both; OpenTofu differences behind one progressive-disclosure reference + `.tofu` override files (§6a) | OpenTofu is a drop-in HCL fork (not a new language), license-safe/OSI; dual support ≈ one reference file, and staying engine-neutral avoids picking a licensing side | this review | Confirm dual-engine + the not-multi-engine distinction |
  | D13 | Provider coverage: 3 hyperscalers only, or a **category taxonomy**? | **Category taxonomy** (§6b) keyed to the registry's own categories — hyperscalers (four-file contract) + edge/CDN (Cloudflare/Akamai) + secrets (Vault/HCP) + data (Databricks/Snowflake/…) + observability; progressive disclosure, four-file mold only for clouds | Terraform provisions far more than clouds; MECE vs the registry means we don't drop categories; each category gets a fit-for-purpose reference shape | this review | Confirm the taxonomy + v1 provider set |
  | D14 | Kubernetes: excluded, or in scope? | **In scope** — managed-cluster provisioning via each cloud's provider (in the cloud refs) + `kubernetes`/`helm` in-cluster as one Container-Orchestration reference; only **non-Terraform tooling** (Ansible/raw ArgoCD) stays out | Every cloud has a K8s variant; provisioning it is ordinary Terraform; the exclusion is multi-*tool*, not Kubernetes | this review | Confirm the provision-vs-workload line |
  | D15 | Observability + standards adaptability | Ship an **observability/OTEL standard** (§4a) and make **standards extensible** via the governance-index (add a domain row + a reference to add/override a standard) | Every platform has an OTEL capture surface; orgs must be able to adapt/extend standards without forking the pack | this review | Confirm the OTEL standard + the extensibility seam |
  | D16 | `governance-extras` companion shapes | **governance-index** = convention + template + optional lint (NOT a skill); **extension-contract** = convention + `architect-review` rubric line (NOT a skill); **new-adr** = optional infra-ADR mode. The governance-index **template lives in `governance-extras`**, not this pack (used elsewhere) | Pressure-tested against "used often enough to stick": authoring an index / an extension contract is rare → not skills; the ADR fan-out is progressive | this review | Confirm the three shapes + the placement |
  | D17 | Is `reconcile` a second skill, a co-equal mode, or a preflight? | **Two skills — `generate-iac` (author) + `reconcile-iac`** (drift audit → propose → route; triggers: before-change preflight *and* on-demand/scheduled) | Split drift by moment: **runtime telemetry-driven detection = `release-loop`** (ops, when present). But **adopters vary — a real subset causes drift and many lack `release-loop`**, so the author-side `plan`-based reconcile is their only net; it's a **distinct user intent with its own activation surface** ("reconcile my drift" ≠ "provision X"), and skills activate by description → it earns its own skill. Both share references + reviewers; neither owns runtime detection | **decided** | ✅ Two skills |

## Problem & goals

**Problem.** The catalogue can *reason* about infrastructure work well but cannot
*scaffold* it. `core` holds the universal method — verify a deploy by phased
oracles, never autonomously apply, make policy-as-code a prerequisite — but an
adopter who wants "a hardened object store with a private ingestion pipeline"
still hand-writes the layered Terraform, the remote-state backend, the
least-privilege IAM, the OIDC pipeline, and the policy-on-plan gate from scratch.
That scaffolding is real, repeated work; it just isn't stack-neutral, so it has
had nowhere to live.

**Goals.**
- A repeatable *intent → spec → plan → tasks → Terraform → verify* authoring
  workflow whose verified `plan` is the **G4 hand-off** to `release-loop` (the
  apply/deploy is the outer loop's, §1b), reusing the repo's loop conventions
  rather than a bespoke gate model.
- Governance-first: every generated decision cites a decision record (ADR) and a
  standard; no infrastructure is written before the governing records are read.
- Provider coverage as a **category taxonomy** (§6b), MECE against the Terraform
  registry's own categories so we don't drop what Terraform supports: hyperscalers
  via the four-file contract, plus edge/CDN, secrets, data-engineering, Kubernetes,
  and observability via category-appropriate references — loaded per target, never
  all at once.
- Reuse `core`'s verification and operational-safety depth; ship no duplicate
  doctrine.

**Non-goals.**
- Not a default-profile pack — it is opt-in, installed only where an adopter
  wants Terraform generation.
- Not a change to `core`'s stack-neutrality — `core` stays framework-agnostic.
- Not a multi-*language* IaC abstraction (Pulumi/CDK/CloudFormation) in v1 — those
  are different languages needing separate codegen. **OpenTofu is explicitly in
  scope** (D12, §6a): it is the same HCL dialect (a drop-in Terraform fork), so
  dual Terraform/OpenTofu support is nearly free and is *not* what this non-goal
  excludes.
- Not an autonomous applier — no code path in the pack runs `apply`/`destroy`.
- No claim of a *uniform contract* for every provider — the **four-file contract**
  (§6) is hyperscaler-only; other categories (edge/CDN, secrets, data, observability)
  are covered by **category-appropriate references** (§6b), not the four-file mold.
  Multi-provider stacks, on-prem/air-gapped, and sovereign clouds remain v1 edge
  cases handled by the relevant category reference, not a promise of seamless
  support.

## Proposal

### 1. Pack identity and install posture

```toml
# packs/iac-terraform/pack.toml
[pack]
name = "iac-terraform"
version = "0.1.0"
description = "Opt-in Terraform/OpenTofu IaC generator: turn a plain-language intent into governed, best-practice, cloud-agnostic Terraform plus a human-gated CI/CD pipeline. Decision-record-gated; stops at `terraform plan`; reuses core's infra-verification + operational-safety depth."
readme = "README.md"
display_name = "IaC (Terraform)"
license = "Apache-2.0 OR MIT"
categories = ["infrastructure", "governance", "ci-cd"]
keywords = ["terraform", "opentofu", "iac", "policy-as-code", "oidc"]

[pack.adapter-contract]
version = "0.12"   # match the current shipped contract version

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]     # repo-scope: emits generated Terraform/pipeline outputs into
                              # the repo, references the repo's ADRs, and reuses the repo-scope
                              # `core` reviewers (same-scope resolution) — ships zero seeds itself

[[pack.dependencies.required]]
catalogue = "agent-ready-repo"
pack = "core"
version = "^0.1"

[[pack.dependencies.required]]
catalogue = "agent-ready-repo"
pack = "governance-extras"
# Same-PR dependency: this PR adds the governance-index template + `new-adr` infra
# mode + the extension-contract convention to governance-extras, so pin the NEW
# minor those land in (bump governance-extras in the same PR) — never a range that
# can resolve to a version predating them.
version = ">=0.6"

[pack.links]
homepage = "https://github.com/eugenelim/agent-ready-repo"
repository = "https://github.com/eugenelim/agent-ready-repo"
documentation = "https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/iac-terraform/"

[[pack.maintainers]]
name = "eugenelim"
email = "eugenelim@users.noreply.github.com"
```

- `.claude-plugin/plugin.json`: `{name, version, description}` mirroring `pack.toml`.
- **Excluded from all profiles** (`full-ceremony`, `inception`, `solution-architect`)
  — reached only by an explicit `agentbundle install iac-terraform`.
- Depending on a **non-`core` pack** (`governance-extras`) is a compositional
  dependency; each pack's own install gate enforces its direct deps. Flagged here
  as it is a relatively novel dependency shape for the catalogue.

### 1b. Scope, agent topology, and loop integration (follows the target-repo loop conventions)

This is the load-bearing architecture decision, and it follows the repo's own loop
conventions rather than a bespoke gate/reviewer model.

**Scope — repo, not user (D-scope).** The pack installs into the **build repo** —
the same repo `work-loop` runs in, which holds the deploy-ready Terraform and has
`core` **repo-installed**. That co-location is exactly what makes reusing `core`'s
repo-scope reviewers *sound*: they resolve at the **same scope**. This is the
deliberate **scope-inversion** the `release-engineering` pack already documents
(its `pack.toml`): a *user-scope* pack that reached for repo-scope reviewers it
can't assume are present is the `discovery-lead` footgun — avoided here by being
repo-scope. The pre-repo "intent → architecture" need is already served by the
**user-scope `architect` pack**; `iac-terraform` is the repo-co-located *build
realization*, so repo-scope is correct and load-bearing, not incidental.

**Agent topology — zero agents (D6).** The pack ships **no agent of any kind**:

- **No new reviewer.** The three-reviewer ceiling holds. The **cold / forked-context
  review** this work needs is exactly what `core`'s existing forked-context
  reviewers provide — `adversarial-reviewer` (spec/plan/diff), `quality-engineer`
  (the operational lens, with `operational-safety` modules inlined by the
  orchestrator), and `security-reviewer` (with `security-checklists` modules
  inlined). They "do not review their own work" and load conventions + artifacts
  fresh — they *are* the cold-context reviewers. `iac-terraform` reuses them via
  the **existing orchestrator-inlining mechanism**; it adds none.
- **No lead / coordinator either.** `release-lead` and `discovery-lead` are agents
  because they *are* distinct loops with their own inputs, verifiers, and autonomy
  postures. `iac-terraform` is **not a new loop** — it is **IaC-flavored authoring
  inside `work-loop`'s inner loop** plus **deploy inside `release-loop`'s outer
  loop**. So it needs no supervisor. Its correct analogue is `operational-safety`:
  a **depth/scaffold library the loops consume**, not an agent.

**Loop integration — the classic "two apply boundaries" become the loop arc
(D7).** The classic governed-IaC terminal ("the AI stops at `plan`; a separate
pipeline applies after human approval") maps **1:1** onto the existing gate arc —
so the pack adopts the arc instead of defining its own gate model:

| Classic governed-IaC concept | Target-repo loop convention it becomes |
| --- | --- |
| Author Terraform + `fmt`/`validate`/`plan` | `work-loop` **inner loop** — `infra-verification`'s static-preflight + plan/preview GATES layers |
| "AI stops at `plan`" (the deliverable) | the **G4 handoff** — the digest-pinnable, deploy-ready whole; the plan is the *inner verify*, **not** the finish line |
| Deploy → idempotent convergent apply → e2e/smoke → observe → converge | `release-loop` **outer loop**, autonomous on **ephemeral, isolated** envs |
| "Pipeline applies only after human approval" | **G5 + the minimum-regret consent gates** (prod / real data / data-migration / spend / security / one-way-door) — `release-loop`'s carve, not the pack's |
| Policy-on-plan gate | one layer of `work-loop`'s static preflight **and** an input to the `release-loop` **release-readiness record** (the launch PRR) |

**What it takes to make this work with `release-loop` (concrete integration work):**

1. **Retarget `generate-iac`'s terminal** from "stop at plan, done" to "produce the
   **G4 deploy-ready artifact**." The `plan` is the inner-loop verify; the apply is
   `release-loop`'s.
2. **Shape the Terraform skeletons to the `operational-safety` module contract** so
   `release-loop` can drive them — emit the *multi-artifact preflight set*
   `infra-verification` already expects: a **deploy** script, a **verify-status /
   smoke** probe, a **teardown** script, **test-data seeding**, and
   **externalized config** (`*.tfvars` / `TF_VAR_*`), mapping 1:1 to
   `state-and-idempotency`, `cost-and-teardown`, `drift-and-rollback`,
   `observability-and-smoke`, and `environment-isolation`.
3. **Ephemeral-env compatibility:** templates parameterized for a **per-cycle,
   uniquely-named, teardownable** target, with **idempotent convergent apply** as a
   precondition (re-run converges, never collides).
4. **Credential tiering (release-loop control (g)):** the four-file provider
   contract's IAM mapping must express **tier-scoping** — the autonomous/ephemeral
   zone can assume **ephemeral-tier roles only**, never a prod-assumable one. This
   is a concrete addition to §6's provider contract.
5. **Reversibility-class annotations:** the generator tags resource kinds with a
   **reversibility hint** (`reversible` / `costly-to-reverse` / `one-way-door`) —
   e.g. a stateful data store or DNS cutover ⇒ `one-way-door` — so `release-loop`'s
   consent-gate classifier fires correctly rather than guessing.
6. **Policy-on-plan output feeds two consumers** (see the table): `work-loop`
   preflight and the PRR before G5.
7. **Drop the pack's bespoke gate doctrine.** The generated pipeline YAML stays as
   **one emitted realization** of the G5 gate for adopters *without* `release-loop`;
   the *when-to-gate* doctrine is `release-loop`'s minimum-regret carve.

**Composition, not a hard dependency.** `iac-terraform` is **release-loop-compatible
by convention** — it shapes its outputs to the `operational-safety` module contract
(which `core` ships), so it "just works" when `release-engineering` is installed and
**degrades gracefully** to `work-loop` inner-loop + the generated pipeline when it isn't.
It therefore takes **no manifest dependency on `release-engineering`** — mirroring
how `release-loop` consumes the discovery sidecar *by convention*, not by a manifest
edge. (If a future decision wants first-class coupling, that is a follow-on, not v1.)

**Two operating modes — state them plainly (the devil's-advocate pass, Finding 4,
warned against overselling the outer loop as the baseline).** The loop-arc is the
*ceiling*, conditional on `release-engineering` **and** an ephemeral-env harness:
- **Full mode** (`release-loop` + ephemeral envs present + the release-loop
  conformance canary shipping): the iterative outer loop catches the apply-time
  AWS failures — the headline benefit. Absent the canary, degraded mode is the
  only *supported* mode in v1 (WA Major 3 risk).
- **Degraded mode** (the common case today — neither present): the pack is a
  **corrected, loop-conventions-aligned generator** — `work-loop` inner loop +
  the generated human-gated pipeline for apply. Still a real improvement over the
  source (references-not-seeds, the recency corrections, reuse of `core`'s
  reviewers), but **without** the autonomous apply-iteration. The RFC does not claim
  the outer loop as the default.

### 2. The one primitive: the `generate-iac` skill

**One skill, and it is *authoring*, not verify (D8).** `generate-iac` is a single
primitive that produces the deploy-ready Terraform. It does **not** bundle its own
verify step — verification is `core`'s `work-loop` `infra-verification` + the
reviewers, which the skill **taps** (below). "One skill that also does verify"
would re-ship the exact doctrine §1b reuses; the skill *authors and hands off*.

**Two skills — `generate-iac` (author) + `reconcile-iac` — and only two (D17).**
IBM/iac-spec-kit ships ~10 commands and spec-ops ~8 because they re-implement the
whole spec→plan→tasks→implement→verify loop (no `work-loop`); this pack reuses
`work-loop`, so the loop stages are *not* skills. The only Terraform-specific
*habits* are **author** and **reconcile** — two distinct user intents ("provision X"
vs "reconcile my drift") with distinct activation surfaces, so two skills (sharing
references + reviewers), never ten. Drift decomposes by *who owns the moment*:

| Drift moment | Owner |
| --- | --- |
| **Runtime / ops drift** — a *deployed, running* env diverges (telemetry-detected) | **`release-loop`** (`drift-and-rollback`) — ops/SRE, when present |
| **Drift → the code fix** | `release-loop` feedback seam → `work-loop` + **`generate-iac`** (author the fix) |
| **`plan`-based reconcile** — before a follow-on change (preflight) *or* on-demand/scheduled, **with or without `release-loop`** | **`reconcile-iac`** (this pack) — the author-side net |

**But adopters come in all shapes — so `reconcile` is a first-class skill, not just a
preflight.** The recalibration above assumed a governed shop; **the adopter population
is not uniform.** A real subset **will** cause drift (ClickOps / break-glass / partial
IaC coverage / multi-team), and **many will not have `release-loop` installed** — for
them, the runtime-detection owner (release-loop) is *absent*, so the only drift safety
net is an **author-side, independently-invokable `reconcile`** that works standalone:
an **on-demand or scheduled `plan`-vs-live drift audit → proposed disposition →
remediation PR** (the "self-healing = propose-and-approve" loop). This is a **distinct
user intent** ("my infra drifted / reconcile my state") with a **distinct activation
surface** from `author` ("provision X"), and in this catalogue skills activate by
description — so it earns its own skill, **`reconcile-iac`**, sharing `author`'s
references + reviewers. Its two triggers: **before a follow-on change** (the preflight
you named) and **on-demand/scheduled** (the standalone net). The `release-loop` split
still holds: **runtime telemetry-driven** detection is release-loop's when present;
**`reconcile-iac`** is the `plan`-based author-side reconcile that runs **with or
without** release-loop.

**Known blind spot: unmanaged resources.** `terraform plan` computes drift between
state and the live control plane — but resources created entirely outside Terraform
(ClickOps, console actions with *no state entry*) are invisible to `plan`.
`reconcile-iac` inherits this limit; detecting unmanaged resources requires a
separate layer (Snyk IaC / Driftctl lineage, platform-level health checks, or a
`terraform import` discovery pass). The skill body must document this scope
boundary and not imply full drift coverage.

**Does `reconcile-iac` "audit and decide"? Audit + propose + route — never
autonomously decide-and-apply** (that would break the no-autonomous-apply spine). It
emits a **drift audit** (per drifted resource: cause-class + blast-radius against the
standards/records) and a **proposed disposition** — *codify-back into IaC · add
`ignore_changes` · open a remediation PR · block the follow-on change · hand a runtime
case to `release-loop`* — and a **human (or the release-loop consent gate) decides**.

**Why drift recurs (research-grounded).** ClickOps / break-glass are the
*ungoverned-actor* causes — frequent for the ungoverned subset. Others are
**discipline-independent** and recur even in governed shops: **cloud-provider-side
default/patch changes**, **auto-scaling / managed-service self-modification**, the
**Terraform-snapshot-vs-Kubernetes-continuous-reconciliation** conflict, **multi-tool
environments**, **silent pipeline failures**. *Honesty caveats:* frequency evidence is
**vendor-sourced and soft** (Firefly State-of-IaC — ~48% make out-of-band prod changes
weekly — undisclosed methodology; no neutral study; no day-1/day-2 split), and two
circulating stats ("86% of orgs", "67% of incidents") are **fabricated — not cited**.
Net: across the varied population, `reconcile-iac` is a genuine first-class habit, so
**the pack ships two skills — `generate-iac` (author) + `reconcile-iac`** (D17).

**It is a loop, not a straight line.** The stages are the entry ordering, but the
work is **two nested iterative loops**, because IaC fails in ways a linear pipeline
hides:

```
                 ┌───────────── inner authoring loop (work-loop) ─────────────┐
intent → (0) ADR gate → (1) spec → (2) clarify → (3) plan → (4) tasks → (5) write TF
                 │                                                            │
                 │   (6) fmt · validate · terraform plan  ── errors? ─────────┘
                 │        │  (schema/arg hallucination, cycle, missing var)
                 │        ▼  plan CLEAN + digest-pinned  ==  G4 hand-off
                 └────────┼───────────────────────────────────────────────────┘
                          ▼
        ┌──────── outer deploy loop (release-loop, ITERATIVE) ────────┐
        │  deploy to ephemeral env → apply → e2e/smoke → observe       │
        │        │                                                     │
        │        └── AWS apply-time failure? ── feed back to inner ────┘
        │            (IAM propagation, eventual consistency, quota,
        │             dependency ordering, terminal-FAILED states)
        └──── converge → release-readiness record → G5 (human) ────────┘
```

The **inner loop iterates on `plan`** (fix hallucinated args / cycles / missing
vars, re-plan); the **outer loop iterates on `apply`** — and that is where "the
AWS failures we miss" live. A clean `plan` is **necessary but not sufficient**:
apply-time failures (IAM eventual-consistency propagation, service quotas,
dependency ordering, resources that reach a terminal `FAILED` state, cross-region
races) surface **only on `apply` against a real account**, are read by the agent
from the real environment, and feed back as inner-loop build tasks. This is why
the outer loop must be iterative and why the pack is release-loop-shaped, not a
one-shot generator.

**Terraform's oracle model (why `plan` is special — and why it isn't enough).**
Unlike a compile step, `terraform plan` is a **dry-run diff against refreshed
state** — it shows *what the provider will change* before mutation, and doubles as
the **drift detector** (`plan` on unchanged code that shows a diff = drift). But
`plan` evaluates against the provider schema and last-known state, **not** the live
control plane, so it cannot see the apply-time failure classes above; and `apply`
is **not atomic** — a partial apply leaves real resources, so recovery is a
*named re-apply / targeted destroy path* (`drift-and-rollback`), never an "undo".
The pack encodes this: `plan` is the inner oracle; `apply` + smoke is the outer
oracle; neither substitutes for the other.

**It taps `core` directly — `core` is always present (hard dependency), so no
"if available" hedging.** At the verify/review points the skill routes through the
**existing orchestrator-inlining mechanism**:
- **operational depth** → `operational-safety`'s Module index inlines the matching
  modules (`state-and-idempotency`, `drift-and-rollback`, `environment-isolation`,
  `cost-and-teardown`, `observability-and-smoke`, plus `cloud-implementation-craft`
  at EXECUTE — which owns exactly the propagation-wait / terminal-state / dependency
  ordering craft the AWS failures need);
- **operational review** → `quality-engineer` (the operational lens);
- **security** → `security-reviewer` + `security-checklists/config-misconfig`;
- **spec/plan adversarial read** → `adversarial-reviewer`;
- **ADR authoring** → `governance-extras`' `new-adr`.

Apply is the outer loop's act on ephemeral envs, gated by human consent at the
irreversible exits (§1b) — **not** a pack-defined gate.

**Hard rules the skill enforces:**

- **Stage 0 is mandatory.** Before any Terraform, load the repo's *governance
  index* (a manifest mapping each decision domain → the ADR(s) + standard(s) that
  bind it — see §5) and read only those 2–3 files, not the whole repo. The plan
  must list which decision records it satisfies and why.
- **Never invent a decision record.** If an intent conflicts with an existing ADR,
  or no ADR covers a material decision, **stop and surface it** — draft a new ADR
  via `governance-extras`' `new-adr`; do not silently resolve it.
- **Never hardcode a cloud.** The target cloud is an input; provider, backend, and
  module choices resolve from the provider config for that cloud (§6).
- **Vocabulary firewall at SPECIFY (adopted from IBM/iac-spec-kit, §12).** `spec.md`
  names only **generic infrastructure** ("managed database", "object storage",
  "container orchestration") — **no cloud-specific service names**; concrete
  services (RDS, Blob Storage, GKE…) appear only from PLAN onward. Cloud-agnosticism
  by construction.
- **Tier-ordered tasks at TASKS (adopted, §12).** Order `tasks.md` by infrastructure
  tier aligned to the layered layout (Foundation → Network → Compute/Data → App →
  Polish); mark a task `[P]` (parallel) only when it touches disjoint files with no
  resource/data dependency — the same dependency-ordering `release-loop` reasons
  from.
- **Scenario-independence (adopted from spec-ops, §12).** Each infra slice must be
  independently deployable, validatable, and **rollback-able** — which is what
  `release-loop`'s per-changed-surface coverage + `blast-radius` isolation require.
- **Ground every resource in the *live* provider schema — ALWAYS ON (not optional).**
  Before emitting any resource, acquire the provider's live contract via `core`'s
  `contract-acquisition` oracle and reference the cited schema slice — **never guess
  a resource type, argument, or field**. The **ground-truth oracle is the toolchain's
  own `terraform`/`tofu providers schema -json` + `validate`** — the only source of
  full attribute-level schema, immune to model knowledge-cutoff, and **version-current
  by construction** (it reflects whatever provider version the config pins). The
  **HashiCorp Terraform MCP server / Registry API** is an *optional discovery
  accelerant* (module/provider search, rendered docs) — soft, when-present, **never a
  dependency**. This means the pack **never freezes a Terraform spec it must keep in
  sync** for schemas — it acquires the current one at generate-time. It is the
  single best-evidenced defense against the headline failure mode (hallucinated
  Terraform reaching a real account); fires on **every** generation, light mode too.
- **Optional deep-design pass (adopted from IBM `enrichplan`, §12) — offered, not a
  new stage.** For a complex build, deepen PLAN by tapping the **`architect` pack
  when it is installed** (Well-Architected / design-doc lenses) and the
  curated-registry-module-first bias — **any registry module the bias reaches for
  must be version-pinned (exact tag/commit) and routed through the existing
  `security-reviewer`/`security-checklists` supply-chain pass** (WA Minor 5); the
  always-on grounding covers resource schemas, not pulled modules. **Soft
  composition — no manifest dependency on `architect`** (a repo-scope pack may tap a
  user-scope pack's skills where present,
  and degrade cleanly when absent — the reach is safe because absence only removes a
  depth bonus, never a correctness step, which the always-on grounding rule already
  covers); skipped by default.
- **Standards are binding.** The standard references (§3–§4) are law; cite the
  standard applied.
- **Apply is the outer loop's, gated by the loop arc — not by the pack (§1b).**
  The skill's deliverable is a green, digest-pinnable `plan` = the **G4 handoff**.
  Deploy/apply is `release-loop`'s act, **autonomous on ephemeral isolated envs**
  and **human-gated at the irreversible exits** (G5 prod, real data,
  data-migration, spend, security, any one-way-door). Where `release-loop` is not
  installed, the generated pipeline's human-approval gate is the fallback
  realization — but the *doctrine* is the minimum-regret carve, not a pack-defined
  "two boundaries" rule.

**Inputs the skill collects** (ask if missing, else use the documented default):
target cloud (ask — never guess), **engine** (`terraform | opentofu`, default
`terraform`; emit the engine-neutral baseline unless a divergent feature is
requested — §6a), environment(s) (default `dev`), region (ask), decision-record
source (default: the repo's own ADR directory), CI system (default
`github-actions`), state backend (derive from cloud), **account/tenant isolation
model** (ask — shared account + workspaces vs. separate account/subscription/
project per environment; this drives OIDC trust-policy scoping and the state
backend key structure; default: separate account per environment; document the
decision in the state ADR).

**Reuse, do not duplicate.** The skill **references** `core`'s depth rather than
re-stating it:
- Verification method (phased oracle fidelity — a green `validate` is a
  local-typecheck analog, never a done-signal; the plan/preview-before-mutation
  discipline; drive-the-deploy-yourself, no human-as-relay) comes from `core`'s
  work-loop infra-verification mode.
- Operational depth (state & idempotency, drift & rollback, environment
  isolation, least-privilege-but-sufficient IAM, external-config parameterization)
  comes from `core`'s `operational-safety` modules.
- IaC/deploy-config misconfiguration review comes from `core`'s
  `security-checklists`; on infra work that security pass is already mandatory.

The skill's own body carries only what is Terraform-and-cloud-specific and not in
`core`: the stage sequence above, the standards below, and the provider contract.

### 2a. Verification-mode coverage across the loop arc (which modes apply; who owns them; mention vs refer)

`work-loop` defines **four verification modes** — *TDD*, *goal-based*,
*visual/manual-QA*, and *infra/deploy*. IaC work is **a combination of all four**,
split across the **inner (plan-time)** and **outer (deploy-time)** loops. The
governing rule for this RFC: **the pack *specifies* only the inner-loop verification
it owns, and *refers to* — never re-specifies — the deploy-time probe modes
`release-loop`'s `infra-verification` already owns.** Re-specifying a probe the
outer loop builds would duplicate the exact doctrine the pack reuses.

| Verification mode → how it lands for Terraform | Loop / owner | RFC treatment |
| --- | --- | --- |
| **infra/deploy — static preflight** (`fmt`·`validate`·`tflint`·policy-on-plan) | inner / `generate-iac` | **specify** (§3, §7) |
| **goal-based — plan satisfies the stated goals** (the ADR-compliance table + policy-on-plan on plan JSON) | inner / `generate-iac` | **specify** (§5, §7) |
| **infra/deploy — plan/preview** (`terraform plan`, the drift oracle) | inner / `generate-iac` (= the **G4** artifact) | **specify** (§2) |
| **TDD — module/contract tests** (`terraform test` `.tftest.hcl` / Terratest / policy-as-code-as-test; the spec-ops "write validation tests first" discipline, §12) | inner, module-time / **reused** `quality-engineer` (test-author mode) + Terraform-native tooling | **refer + name the tooling** (a thin `references/` note; the *agent* is reused, nothing new shipped). Three tiers the `references/` note must help implementers choose between: **(1) unit** — `.tftest.hcl` with `command = plan` + mock providers (no cloud, no cost, fast); **(2) contract** — consumer-authored interface assertions in plan mode (subnet AZ coverage, output CIDR shape); **(3) E2E/integration** — Terratest or `.tftest.hcl` with `command = apply` against real resources (incurs cloud cost; the only tier that surfaces apply-time failures). Selection criterion: default to unit + contract for module authoring; E2E only when apply-time behavior is the unknown. |
| **infra/deploy — idempotent convergent apply** (re-run converges, never collides) | outer / `release-loop` | **refer** (`infra-verification` GATES layer 3) |
| **visual/manual-QA + goal-based — the data-plane probe** (write→read-back, or drive to the terminal user-visible result; in-network if private; readiness-aware with bounded backoff; self-teardown against a uniquely-named ephemeral target) | outer / **`release-loop` builds the probe** | **refer** (`infra-verification` V2) — the pack's only job is to **shape outputs so the probe is buildable** (§1b item 2) |
| **infra/deploy — rollback** (named re-apply / targeted-destroy path; no atomic undo) | outer / `release-loop` runs; **named at plan-time** in the plan's Rollout | **refer** + the plan names the path |

**The mention-vs-refer answer you asked for, stated plainly:** *if the release-loop
builds a probe to validate, this RFC **refers** to it — it does not mention its
mechanics and does not re-specify it.* The pack contributes the **inputs** the probe
consumes — a `verify-status`/smoke script, seed data, a teardown script, a
uniquely-named ephemeral target, and the `reversibility-class` — not the probe
doctrine (that is `infra-verification`'s V2, owned by the outer loop). This is the
same "shape outputs to the `operational-safety` module contract" obligation as §1b
item 2, viewed through the verification lens.

**Degraded mode (no `release-loop`).** The inner-loop modes (static preflight +
`plan` + module tests) are the **ceiling**; the generated pipeline runs a **reduced
smoke** (a post-apply status check, not the full readiness-aware data-plane probe),
and the **human review at the environment gate** substitutes for the autonomous
probe. The RFC does not pretend the full probe suite runs without the outer loop.

The pack carries one thin reference, `references/terraform-verify-and-iterate.md`,
that (a) specifies the inner-loop modes in Terraform terms (the `plan`-vs-`apply`
oracle split, `terraform test`/Terratest, the drift `plan`) and (b) **points to**
`infra-verification` for everything the outer loop owns — it re-specifies none of it.

### 3. Terraform best-practice standard (progressive `references/`; binding)

- **Layered layout:** `bootstrap → foundation → platform → app` layers, each with
  **isolated remote state**. Deploy layers *compose* reusable modules; they do not
  inline resources.
- **Remote state with locking.** Partial backend config + a per-environment
  `backend.hcl`. Commit the provider lockfile. **Use native lockfile-based
  locking** where the backend supports it (e.g. S3 `use_lockfile = true`, GA in
  Terraform 1.11) — the separate DynamoDB lock table is deprecated; seeds must not
  hardcode it.
- **Reusable modules** live under `modules/`; scaffold from the module skeleton.
- **Pin versions:** `required_version` and provider version constraints; commit
  `.terraform.lock.hcl`.
- **Least-privilege IAM inline per layer** — no god roles.
- **Everything tagged/labeled** per the tagging standard.
- **No secrets in code or state inputs** — reference a secret manager.
  **`sensitive = true` suppresses CLI display only — sensitive output values are
  still stored in plaintext in the state file.** Never output raw credentials;
  output only references/ARNs. Encrypt the state backend at rest (S3 SSE-KMS;
  GCS CMEK; Azure Storage Service Encryption + CMK).
- **`terraform.tfvars.example` committed; `*.tfvars` git-ignored** (except
  `*.tfvars.example`). Supply real values via `TF_VAR_*` from CI vaults or the
  secret manager — never commit a `terraform.tfvars` with real values.
- **`fmt` + `validate` clean; `plan` reviewed** before done.

### 4. Networking standard (progressive `references/`; binding)

Consume a central-team-owned network as an input where one exists; private
subnets; egress-only security groups / NSGs; private service endpoints; **no
public ingress unless the spec explicitly requires it**. A per-cloud mapping table
(network / subnet / firewall / private-service-access / front-door equivalents)
gets a column per supported cloud.

### 4a. Observability standard + standards-are-extensible (D15)

**Observability is a first-class standard, because every platform has an OTEL
capture surface.** The pack ships an `observability-standard.md` reference. Its
binding force is **scoped to the workload class** — a **long-lived
compute/service/data-plane** stack must **emit OpenTelemetry-compatible telemetry**
and provision the carrying pieces; a leaf resource (a lone bucket, a DNS record)
is **not** forced to stand up a collector + backend + dashboards. When it applies,
the pieces are — **(a)** the collector as compute + Helm (there
is no first-party "OTEL Collector" Terraform provider — it deploys as an ECS/EKS
service or Helm chart via the existing infra provider); **(b)** the telemetry
*backend* via the vendor's own provider (hyperscaler-native — CloudWatch/ADOT,
Azure Monitor, GCP Cloud Operations — or Datadog/Grafana/Honeycomb/New Relic); and
**(c)** dashboards/alerts/SLOs as code. This is the **provisioning** side; the
*verification* side (smoke + telemetry reads) is `release-loop`'s
`observability-and-smoke` module, reused not duplicated (§2a). The observability
standard is what a deployed data-plane probe reads against.

**Standards are extensible — the adaptation mechanism you need.** The standards
(`terraform-standard`, `networking-standard`, `security-iam-standard`,
`tagging-standard`, `observability-standard`) are **references keyed to a
governance domain in the governance-index manifest** (§5). An adopter **adapts or
adds** a standard by **adding a manifest domain row + a reference** — e.g. a
`data-residency` domain → their `data-residency-standard.md`, or overriding
`tagging` with their own. The pack ships sensible defaults; the governance-index is
the seam that lets an org **override or extend** them without forking the pack.
This is why the governance-index belongs in `governance-extras` (§9) — extensible
governance is not Terraform-specific.

### 5. The governance index (Stage-0 mechanism — provided by `governance-extras`, consumed here)

A single manifest an assistant **loads first**, mapping each *decision domain* to
the exact record(s) and standard(s) that bind it, so the agent reads 2–3 files
rather than the whole repo. Shape:

```yaml
# governance manifest — the index loaded FIRST
domains:
  state:         { question: "Where does state live and how is it locked?", adrs: [ADR-0001], standards: [terraform-best-practices.md] }
  layout:        { question: "How is Terraform structured into layers/modules?", adrs: [ADR-0002], standards: [terraform-best-practices.md] }
  iam:           { question: "What identity/access model applies?",         adrs: [ADR-0003], standards: [security-iam.md] }
  tagging:       { question: "What tags/labels are mandatory?",             adrs: [ADR-0004], standards: [tagging.md] }
  networking:    { question: "Public or private? Who owns the network?",    adrs: [ADR-0005], standards: [networking.md] }
  pipeline_auth: { question: "How does CI authenticate to the cloud?",      adrs: [ADR-0006], standards: [security-iam.md] }
  remediation:   { question: "Can the system self-heal / auto-apply?",      adrs: [ADR-0007], standards: [] }
clouds: [aws, azure, gcp]
ci_systems: [github-actions, azure-devops, gitlab]
policies_dir: policies/opa
```

**The manifest template ships in `governance-extras`, not in this pack (D16).**
The governance-index is a reusable governance habit used well beyond Terraform (any
governed repo benefits from a domain→record index), so its template + convention
live in `governance-extras` (§9); `iac-terraform`'s Stage-0 **consumes** the
manifest the adopter has, adding the IaC domain rows (`state`, `layout`, `iam`,
`tagging`, `networking`, `pipeline_auth`, `remediation`, `observability`) if absent.
The pack therefore ships **zero seeds** of its own. **The seven decision topics are
NOT shipped as ADR files** (that would collide with the adopter's ADRs and the
repo's ADR conventions — D10); they are offered by `new-adr`'s optional infra mode
(§9). Referencing an ADR by number in the manifest is the adopter's act, not a
shipped `docs/adrs/` tree.

### 6. The provider extension contract — major public clouds by extension (per-cloud `references/`, load target only)

**Providers are progressive references, not seeds — they don't all apply (D9).**
An adopter targets one cloud per generation; shipping `providers/{aws,azure,gcp}/`
as seeds would dump two clouds of irrelevant scaffolding into every repo. Instead
the pack carries one **reference per cloud** (`references/providers/aws.md`,
`…/azure.md`, `…/gcp.md`) plus the tool-neutral **contract**; `generate-iac` loads
only the target cloud's reference and *emits* that cloud's provider files into the
repo. The contract each cloud reference satisfies — the **four-file shape**:

| File | Contract |
| --- | --- |
| `versions.tf` | `required_version >= 1.6`; the cloud's provider pinned with `~>` |
| `provider.tf` | provider block; standard tags/labels (the mandatory keys); region from `var.region`; **OIDC auth, no static credentials** |
| `backend.tf` | empty partial backend block for the cloud's remote-state service |
| `backend.hcl.example` | per-environment backend values template |

**Required mappings** a new cloud must define (one per governance domain): remote-state
service + locking; short-lived workload-identity primitive (no static keys);
tags-vs-labels + naming/charset constraints; network/subnet/firewall/
private-service-access/front-door equivalents; OIDC / workload-federation login
per CI system; **account/tenant isolation model** (shared account + workspaces vs.
dedicated account/subscription/project per environment — drives OIDC trust-policy
`sub` scoping, state key structure, and the `environment-isolation`
operational-safety requirements); **and credential *tiering*** — the ephemeral/
autonomous zone's identity can assume **ephemeral-tier roles only**, never a
prod-assumable one (release-loop control (g), §1b).

**Two acceptance bars — `contract-complete` vs `validated` (the split D5 rests on):**
- **contract-complete** — the four files exist; the networking table has a column
  for the cloud; the tagging notes cover tags-vs-labels + charset; the manifest lists
  it; the provider index lists it. *(No worked example required.)*
- **validated** — contract-complete **plus** at least one worked example that passes
  `terraform init -backend=false && fmt -check && validate`. For AWS, the example
  must additionally pass on **both `terraform` and `tofu`** (D5 — the dual-engine
  claim has zero coverage otherwise).

In v1, **AWS + GCP are `validated`; Azure is `contract-complete` only** (D5) — and
the two are distinct labels, not "done vs half-done."

**Scope of the *four-file contract* (rescoped by the devil's-advocate pass —
Finding 6).** This contract generalizes across the **major public clouds** (AWS /
Azure / GCP, extensible to OCI / AliCloud), which converge on OIDC-shaped federation,
a lockable object-store backend, and a region+tags primitive set. It **deliberately
does not** stretch to non-cloud providers (Cloudflare / Datadog / Kubernetes — no
backend / region / cloud-IAM-federation) — **those are in scope, but via the
category taxonomy's fit-for-purpose references (§6b), not this mold.** Even across
the majors, tags/labels don't losslessly round-trip (GCP labels are lowercase-only)
and network scoping differs (GCP VPC is global, AWS/Azure regional; OCI adds
compartments) — the per-cloud references carry these, they don't paper over them.
On-prem/air-gapped (`local`-backend regime) and sovereign clouds (different auth
endpoints) remain v1 edge cases.

### 6b. Provider coverage as a category taxonomy (progressive disclosure, MECE against the registry — D13)

The four-file contract (§6) is the **hyperscaler-cloud** shape — but Terraform
provisions far more than clouds, and the pack must not silently drop categories
Terraform supports. So provider coverage is a **progressive-disclosure taxonomy
keyed to the Terraform/OpenTofu registry's own category list** (its ~14
user-selectable categories: Public Cloud/IaaS, Container Orchestration, Networking,
Security & Authentication, Data Management, Database, Logging & Monitoring, PaaS,
CI/CD, VCS, Communication & Messaging, …). `generate-iac` loads **only the
reference(s) for the target provider/category**; each category gets a
**category-appropriate reference shape**, *not* forced into the four-file cloud
mold (a SaaS/API provider has no backend/region/OIDC-federation).

| Category (registry) | Leading providers (v1 references) | Reference shape |
| --- | --- | --- |
| **Public Cloud / IaaS** | AWS, Azure, GCP (+ OCI, Linode) | the **four-file contract** (§6) — the only category that uses it |
| **Container Orchestration** | `kubernetes` + `helm` (in-cluster workloads); ArgoCD/Flux *provisioned via the `helm` provider* (in); ArgoCD *as the orchestrator* (out) | **one cloud-agnostic reference** — see the K8s scope note below (D14) |
| **Networking / edge / CDN / DNS / Zero-Trust** | **Cloudflare**, **Akamai** | auth + resource-shape (no backend/region); DNS/WAF/edge/zero-trust resources |
| **Security & Authentication / secrets** | **HashiCorp Vault, Boundary, HCP** | auth + secret/identity resource-shape (Consul/Nomad are modules-first, noted) |
| **Data Management / Database (data engineering)** | **v1 named: Databricks + Snowflake** (`snowflakedb/snowflake` — migrated from `Snowflake-Labs`); Confluent / dbt / Fivetran / Airbyte named as *category members*, added as demand warrants (WA Minor 7 — one reference can't make six heterogeneous providers contract-complete at once) | control-plane resource-shape (workspaces, warehouses, pipelines, jobs) — **not** the four-file mold |
| **Logging & Monitoring / Observability** | hyperscaler-native telemetry (in the cloud refs) + **Datadog, Grafana, Honeycomb, New Relic**; OTEL Collector as a compute+Helm *pattern* | see the observability standard (§4a) |

**Per-category acceptance bar (not just the four-file cloud DoD).** A non-cloud
category reference is `contract-complete` when: the resource-shape reference exists;
the provider's **auth mapping** is documented (SaaS/API providers have no OIDC/backend
— name what they use); a **governance-index domain row** exists; and it appears in the
provider index. It is `validated` when a worked example additionally passes
`init -backend=false && fmt -check && validate`. **Databricks is the v1 `validated`
category reference** (D5); the rest ship `contract-complete`.

**Mark the unvalidated surface — this is the sprawl-containment control (Finding 2).**
Every category reference **not** validated in v1 (Azure, and every provider in
`edge-cdn-dns` / `hashicorp-platform` / `data-platforms` except Databricks /
`observability-vendors` / `kubernetes-workloads`) is stamped **`experimental — not
validated in v1`** in-file *and* in the provider index. So the **shipped** surface
carries an honest maturity label, matching the day-one ownership/deprecation lifecycle
(D2) — the *validated* set (AWS + GCP + Databricks) is right-sized, and the broader
contract-complete surface is opt-in-with-a-warning, not silently blessed.

**MECE + extensible.** Because the taxonomy tracks the registry's own categories,
"we didn't drop a category" is checkable against the registry; a new provider is a
**new reference in its category**, and a new *category* is a new reference + a
governance-index domain row (§4a) — no schema change. **Maturity currency notes for
v1:** Snowflake is `snowflakedb/snowflake` (not the retired `Snowflake-Labs`);
Consul/Nomad are reference-architecture-modules, not resource-rich providers; there
is **no first-party "OTEL Collector" provider** (it deploys as compute + Helm).

**Kubernetes scope (D14) — the line the earlier "not multi-tool" wording blurred.**
Provisioning a **managed cluster is in scope** — it is ordinary cloud infra via the
cloud's own provider (`aws_eks_cluster`, `azurerm_kubernetes_cluster`,
`google_container_cluster`, `oci_containerengine_cluster`), so it lives in each
hyperscaler reference. Managing **resources inside the cluster** via the Terraform
`kubernetes`/`helm` providers is **also in scope**, as the **one** cloud-agnostic
Container-Orchestration reference (every cloud has a K8s variant, so this can't be
excluded). Installing ArgoCD/Flux itself **via the `helm` provider** is in scope;
using **ArgoCD as the runtime orchestrator** (a raw ArgoCD/Cilium GitOps stack, or
Ansible) is **out** — that is the multi-*tool* non-goal (§12), not a ban on
Kubernetes.

### 6c. Relationship to the Terraform agent-tooling ecosystem — don't depend, don't freeze a spec

There **is** a live and partly-converged ecosystem (2026), so "should this pack
depend on a leading Terraform agent-skills library, or become the de-facto one it
must keep in sync?" is a real question. The landscape:
- **HashiCorp Terraform MCP server** (official, GA 2025) — the *discovery pipe*
  (registry/provider-doc/module search). It returns rendered docs, **not** a full
  attribute schema; AWS deprecated its own Terraform MCP in its favor (convergence).
- **HashiCorp Agent Skills** (official, Feb 2026) — the *textbook*: ships **multiple**
  Terraform skills (style-guide, `terraform-test`, verified-modules, search-import).
- **antonbabenko/terraform-skill** (community leader, ~2.2k★) and **TerraShark**
  (diagnostic, module-first) — **no single de-facto *codegen* winner** has emerged.

**Decision: neither depend nor freeze.** (a) **No hard dependency** on an external
skill library — that imports supply-chain + maintenance + charter risk for a
fast-moving, un-converged layer. (b) **We do not become "the skill that knows the
spec and must be kept in sync"** — schemas are **live-acquired** from the CLI oracle
(§2), so the pack carries **no frozen provider spec**. (c) HashiCorp's MCP server and
official Agent Skills are named as **optional, soft companions** an adopter may wire
in (like the `architect` tap) — prior art and accelerants, never required. The
ecosystem confirms the design: **no leading tool freezes a bundled schema; the good
ones acquire it live** (CLI oracle for truth, MCP/registry for discovery).

**The residual currency surface (WA-review Major 4) — bounded and CI-detected.**
Live acquisition grounds resource *schemas* only. It does **not** ground the
currency-sensitive *non-schema* content the references carry — auth mappings,
provider namespaces (e.g. Snowflake's `Snowflake-Labs`→`snowflakedb` migration), CI
OIDC `sub` formats, the §11 currency table. That is a real, bounded maintenance
surface. Mitigation is **mechanical, not "a maintainer notices"**: a **scheduled CI
job re-runs `init -backend=false && fmt -check && validate` for each
contract-complete reference against the latest provider release**, so a
Snowflake-style migration **fails CI** (bounded time-to-detect) rather than surfacing
to an adopter first. Un-mechanizable currency (a `sub`-format change) rides the
named-maintainer + deprecation lifecycle (D2).

### 6a. Engine support: Terraform **and** OpenTofu (dual-target by default; differences by progressive disclosure — D12)

**Yes, one skill emits for both engines — and this is *not* the "multi-engine"
non-goal.** OpenTofu is a **drop-in HCL-compatible fork of Terraform 1.5.x**, not a
different language: it reads `.tf` files and `terraform {}` blocks, keeps the **same
CLI subcommands** and the **same `TF_*` env vars** (no `TOFU_*` prefix), and its
registry mirrors the Terraform registry so `required_providers` shorthand resolves on
both. So the vast majority of what `generate-iac` emits — the layered layout, provider
blocks, modules, tagging, networking, `.tftest.hcl` tests — is **identical HCL that
runs unchanged on both**. (Contrast Pulumi/CDK/CloudFormation, which are different
languages needing separate codegen — *those* remain the non-goal. OpenTofu is the same
dialect, so dual support is nearly free.)

**Why support both (adoption, honestly).** OpenTofu (Linux Foundation, MPL 2.0, CNCF
Sandbox 2025) is **license-safe/OSI-compatible**; Terraform is **BSL/BUSL,
IBM-owned** (acq. Feb 2025) and commercially deepening. OpenTofu is **credible and
growing but not yet dominant** — Terraform still holds the largest overall share; the
higher OpenTofu percentages are vendor-platform telemetry, not neutral surveys
([research note](0065-notes/opentofu-vs-terraform.md)). Enterprises with FOSS-only
procurement policies increasingly *require* OpenTofu — reason enough for a governance
pack to be engine-neutral rather than pick a licensing side.

**The design — engine-neutral baseline + one progressive-disclosure reference:**
- **Engine is an input** (`engine = terraform | opentofu`, alongside target cloud).
  The **default emitted config is the common subset that runs unchanged on both** —
  the skill diverges *only* when a requested feature demands it.
- **Divergences live in one reference, `references/opentofu-differences.md`, loaded
  only when `engine = opentofu` and a divergent feature is in play** — never in the
  baseline templates. The enumerable set: state/plan **encryption**, **early/dynamic
  variable evaluation** (vars in `backend`/`module source`), the **`-exclude`** flag +
  provider `for_each`, **OCI registry** sourcing, `.tofutest.hcl`; and the
  Terraform-only side (**ephemeral/write-only args**, **Stacks**) which the generator
  simply doesn't emit for an OpenTofu target.
- **The `.tofu` override-file escape hatch** (OpenTofu loads `.tofu` and ignores the
  `.tf` twin; Terraform never reads `.tofu`) is how OpenTofu-only syntax is siloed so
  the *same directory* stays dual-compatible — the officially-sanctioned mechanism.
- **CLI/pipeline** parameterize only the binary (`terraform` ↔ `tofu`); verbs, env
  vars, and the §2a verification modes are identical.
- **Lock file** is regenerated **per engine at `init`** (registry origin changes the
  recorded hashes) — the pipeline runs `init` for the target engine, never shares a
  lock across engines.
- **State encryption is a one-way door** (Terraform cannot read OpenTofu-encrypted
  state) — so enabling it is a **`reversibility-class: one-way-door`** action that
  binds to a `release-loop` consent gate (§1b), not an autonomous default.

Net: dual support costs **one reference file + an `engine` input + a binary-name
parameter**, not a second codegen path.

### 7. Policy-on-plan (starter rules in `references/`; enforced in CI)

In CI, `terraform show -json tfplan` → a policy engine (`conftest`/OPA, or
Checkov, or **Trivy** — note `tfsec` was merged into Trivy in 2023; do not cite
tfsec as a live tool) checks the plan JSON against rules that encode the
decision-record compliance table (e.g. **no open ingress**, **mandatory tags
present**). Evaluating the **plan JSON** (not the HCL) is deliberate — HCL values
from vars/modules/dynamic blocks aren't resolved until plan time; the documented
caveat is that some unknown values / dynamic blocks may still be unresolved at
plan time, so rules must tolerate absent fields. **This is a security
false-negative, not just an OPA caveat** (WA Minor 6): a violation carried by a
value unknown at plan time (a CIDR from a module output, a dynamic block) passes the
lenient rule — so a security-relevant unknown-at-plan field gets a **compensating
apply-time re-check** (or the residual false-negative is documented as accepted). A
violation **fails the PR before any apply is possible**. The requirement is **mechanism-level, not tool-level** —
a scanner must exist; the adopter picks it (HashiCorp Sentinel is an option but is
paywalled behind HCP Terraform tiers **and is incompatible with OpenTofu** — for
OpenTofu users, OPA/Conftest is the only supported open-source path).
This dovetails with `core`'s existing requirement that a policy-as-code / CSPM
scanner exist as a preflight task-zero; here the pack ships starter rules.

**Infracost as an optional economic-signal companion.** `infracost diff --path . --format json`
runs against the plan and produces a cost delta — not a blocking gate (cost data
quality varies; thresholds are org-specific), but a named pre-G4 companion for
adopters with a budget-visibility requirement. Surfaces unexpected spend spikes
alongside the policy-on-plan output and wires into the `cost-and-teardown`
`operational-safety` module's blast-radius check. Mechanism-level, not
tool-level — Infracost is the leading open-source option; the adopter picks.

**AI plan-summarisation as a human-review companion.** Platforms including
Spacelift, env0, and ControlMonkey now offer AI that reads `terraform plan` output
and generates a plain-language change summary for human reviewers — addressing the
*review bottleneck* (a human approving a large plan JSON without a summary is
unlikely to catch intent-vs-output drift). Policy checks *whether* a change
complies; plan-summarisation helps a human understand *what* will change. The
pack's G4 handoff is the natural delivery point for this summary. Named here as a
follow-on companion — `generate-iac` should produce a plain-language plan summary
alongside the plan artifact in a later iteration.

### 8. Pipeline generators (per-CI `references/`, load target only — D9)

**CI systems differ and don't all apply** — an adopter uses one. So the generators
are **progressive references** (`references/pipeline/github-actions.md`,
`…/azure-devops.md`, `…/gitlab.md`), not seeds: `generate-iac` loads only the
target CI's reference and emits that pipeline. Common contract across all three:
**on PR** — `fmt`-check → `validate` → `plan` → the policy-on-plan gate; **on merge** —
**human-gated** apply to the environment (GitHub environment protection / Azure
DevOps approval / GitLab manual job — never `-auto-approve` without the gate);
**auth via OIDC / workload federation** (no long-lived cloud keys); **fan out one
job per changed Terraform layer**. This is the only place `apply` runs, and only
after a human approves. **Recency note for the OIDC seeds:** GitHub changed the
Actions OIDC `sub` claim format for repos created on/after 2026-07-15 to an
immutable numeric-ID form; trust policies written against the legacy name-only
`sub` silently fail — the generator must emit `sub` conditions in the current form
and flag this. GitHub Environments protection rules also require Team/Enterprise
on private repos.

**Shops running a Terraform GitOps platform** (Atlantis, Spacelift, env0,
Terrateam) replace the generated CI YAML with their platform's plan/apply flow.
For Atlantis, emit `atlantis.yaml` with per-repo/workspace config instead of a
GitHub Actions workflow; the lock-and-comment-on-PR model differs from the
environment-gate model above. The pack's three references target vanilla CI;
Atlantis compatibility (and commercial platform configs) is a follow-on reference.
The key invariant is identical across all platforms: `plan` before any `apply`,
policy-on-plan as a non-skippable step, human approval before applying to any
persistent environment.

### 9. `governance-extras` companions — and the shape each actually takes (D16)

Three ideas here are **tool-neutral**, belong in `governance-extras`, not this
pack — but each was **pressure-tested for the right form**, and only one is a
skill. The charter test "a habit, not a tool; used often enough to stick" is what
sorts them.

- **`governance-index` → a convention + a template + an optional lint, NOT a
  skill.** The behavior is *(a)* a one-time setup artifact (author the domain→record
  manifest) and *(b)* a read-time habit (load it first). Neither is a reached-for
  workflow: *(a)* is scaffolding, *(b)* is a convention. So it lands as a **seed
  template** (`governance-extras/seeds/governance/manifest.example.yaml`) + a
  **documented convention** ("index your decision domains; load the index first")
  + an **optional lint** that flags a manifest row whose ADR/standard file is
  missing (drift). Forcing it into a skill would fail "used often enough to stick"
  (you author the index roughly once). It *enhances the ADR approach* — the manifest
  is the index over `docs/adr/`, and the extensibility seam standards ride on (§4a).
- **`extension-contract` → a convention + a rubric line in `architect-review`, NOT
  a skill.** The principle is sound (express "any *X* by extension" as a mechanical
  contract — required shape + mappings + definition-of-done — so adding an *X* is a
  checklist, not a guess). But authoring an extension contract happens **rarely**
  (once per extensibility point), which **fails the skill bar** ("used often
  enough"). Pressure-testing the tree: *skill?* no (too rare); *agent?* no;
  *template?* too rigid (each contract's shape differs); *convention + a review
  rubric?* yes — document the pattern as a convention and add an **"extension-contract"
  check to `architect-review`'s design-doc rubric** (does this design express its
  extensibility as a mechanical contract with a DoD?). The four-file provider
  contract (§6) and the category taxonomy (§6b) are *instances* of the pattern; the
  pattern itself is craft guidance, not a shipped tool.
- **`new-adr` infra mode → a progressive, optional fan-out (agreed).** `new-adr`
  gains an **optional infra-ADR mode**: a `references/infra-decisions.md` loaded
  only when the ADR being recorded is infra-flavored, offering the recurring IaC
  decision *topics* as starters — remote-state backend + locking; layered layout +
  isolated state; least-privilege IAM per layer; mandatory tagging;
  private-by-default network; OIDC-only pipeline auth; and **"self-healing is
  propose-and-approve, never autonomous apply"** (which *is* the minimum-regret carve
  as a decision record — detect → analyze → propose → human-approve → apply — so it
  dovetails with `release-loop`, reusable well beyond Terraform). Progressive
  disclosure, never auto-written, no rival ADR tree.

### 10. Pack file layout (re-implementation target)

The pack is **references-heavy, seeds-minimal** (D9): almost everything is
progressive knowledge `generate-iac` loads on demand and *emits into* the adopter
repo, not scaffolding copied wholesale.

```
packs/iac-terraform/
  pack.toml
  README.md
  .claude-plugin/plugin.json
  # NO .apm/agents/ — zero-agent by design (§1b, D6): reuses core's
  # adversarial-reviewer / quality-engineer / security-reviewer for cold-context
  # review, and release-loop for deploy; ships no reviewer and no lead.
  .apm/skills/generate-iac/
    SKILL.md                        # authoring workflow (iterative), hard rules, taps core (§2)
    references/
      terraform-standard.md         # §3 structure/versioning/state/vars/security/anti-patterns
      networking-standard.md        # §4 5 principles + per-cloud table + checklist
      security-iam-standard.md      # identity/access + data-protection + checklist
      tagging-standard.md           # the 6 required keys + per-cloud application
      observability-standard.md     # §4a OTEL emit + collector(compute+Helm) + backend + dashboards-as-code
      terraform-verify-and-iterate.md # §2/§2a: plan-vs-apply oracle, drift, module tests; REFERS to infra-verification V2 (never re-specifies)
      provider-contract.md          # §6 tool-neutral four-file contract + credential-tiering + DoD
      opentofu-differences.md       # §6a — LOADED ONLY when engine=opentofu
      providers/                    # §6b category taxonomy — LOAD TARGET ONLY
        aws.md azure.md gcp.md      #   Public Cloud/IaaS (four-file contract; incl. managed-K8s: EKS/AKS/GKE)
        kubernetes-workloads.md     #   Container Orchestration (kubernetes/helm in-cluster; D14)
        edge-cdn-dns.md             #   Networking/edge — Cloudflare, Akamai
        hashicorp-platform.md       #   Security/secrets — Vault, Boundary, HCP
        data-platforms.md           #   Data — Databricks, Snowflake(snowflakedb), Confluent, dbt, Fivetran, Airbyte
        observability-vendors.md    #   Logging & Monitoring — Datadog, Grafana, Honeycomb, New Relic
      policy-on-plan.md             # §7 approach + starter rego (3 deny rules)
      pipeline/github-actions.md    # §8 per-CI — LOAD TARGET ONLY
      pipeline/azure-devops.md
      pipeline/gitlab.md
      release-loop-integration.md   # §1b — G4 handoff, preflight-set shaping, reversibility-class
      spec-plan-tasks-shape.md      # §11 the ADR-compliance-table plan shape
  .apm/skills/reconcile-iac/        # D17 — the author-side drift skill (with/without release-loop)
    SKILL.md                        # plan-vs-live → drift audit → proposed disposition → route; audit+propose, human decides (§2)
    # references/ are SHARED with generate-iac (same terraform/provider/policy refs) — not duplicated
  # NO .apm/agents/ (zero-agent, D6) · NO seeds/ — the governance-index manifest
  # template lives in governance-extras (§5, D16); this pack emits provider/skeleton/
  # OPA/pipeline files as OUTPUTS, ships zero seeds.
```

Provider files (`versions.tf`/`provider.tf`/`backend.tf`/`backend.hcl.example`),
the layered Terraform skeletons, the OPA rules, and the chosen CI pipeline are
**generated into the adopter repo** from these references — they are outputs, not
shipped seeds.

### 11. Implementation spec — standards, policy, ADR topics, pipeline (first-party)

The concrete substance each `references/` file must carry, specified here in full
so the pack is buildable directly from this RFC.

**Tagging (`tagging-standard.md`).** Six mandatory keys on every taggable
resource: `environment`, `owner`, `cost-center`, `managed-by` (= `terraform`),
`system`, `data-classification` (`public`/`internal`/`confidential`). Apply via a
single `locals { standard_tags = {…} }` block; **AWS** provider `default_tags`;
**Azure** merge into each resource's `tags` + tag the resource group; **GCP**
`labels` (lowercase, hyphen-separated, ≤63 chars). Checklist: all six present;
values conform to each cloud's charset; enforced by policy-as-code where possible.

**Networking (`networking-standard.md`).** Five principles: (1) private by
default — workloads in private subnets, no public ingress unless the spec demands
it; (2) network-as-input — consume central-owned `network_id`/`private_subnet_ids`
via variables, don't create address space unless the spec owns the network;
(3) egress-only least-open — SG/NSG default no ingress, egress restricted to 443 +
named destinations, prefer prefix-lists/service-tags over `0.0.0.0/0`; (4) private
service access — reach storage/secrets/KMS/registry via private/service endpoints;
(5) governed front door only — LB+WAF or API-GW, never a raw public IP.
Per-cloud table: Network = VPC / VNet / VPC network; Segment = Subnet / Subnet /
Subnetwork; Firewall = Security Group / NSG / Firewall rule; Private service
access = VPC Endpoint / Private Endpoint / Private Service Connect+PGA; Front door
= ALB+WAF·API-GW / App-Gateway+WAF·APIM / GLB+Cloud-Armor·API-GW.

**Security & IAM (`security-iam-standard.md`).** Least-privilege inline per layer,
no wildcards without a documented exception. No long-lived cloud credentials —
short-lived identity per cloud (AWS IAM roles via IRSA/assumption; Azure
user-assigned managed identities; GCP service accounts + Workload Identity);
pipelines authenticate via OIDC only. Data protection: CMK encryption at rest for
`internal`/`confidential`, TLS 1.2+ in transit, secrets in a manager (never in
code / committed tfvars / plan output). Guardrails to wire into CI: static
analysis (Checkov/Trivy), policy-as-code (OPA/Conftest or native SCP/Azure
Policy/Org Policy), secret scanning.

**Terraform best-practice (`terraform-standard.md`).** Layered
`bootstrap→foundation→platform→app`, isolated state per layer; reusable modules in
`modules/`, layers only compose. Per-unit files: `main.tf`/`variables.tf`/
`outputs.tf`/`versions.tf`/`backend.tf`(layers)/`README.md`. Every variable typed +
described + `validation` where constrained; sensitive outputs marked `sensitive`;
`name_prefix = <system>-<env>`. Never commit `*.tfstate`/secret tfvars/`.terraform/`.
Anti-patterns to reject: monolithic state, god IAM roles, hardcoded region/account,
`0.0.0.0/0` ingress, inline secrets, agent-run `apply`, `count`-churn where
`for_each` is clearer.

**Policy-on-plan (`policy-on-plan.md`), the three starter deny rules** (Rego,
against `terraform show -json`): (1+2) deny `0.0.0.0/0` ingress on both
`aws_security_group_rule` (ingress + `cidr_blocks`) and
`aws_vpc_security_group_ingress_rule` (`cidr_ipv4`) — ADR-0005; (3) deny any
taggable resource whose `after.tags["managed-by"] != "terraform"` — ADR-0004.
Filter to `create`/`update` actions only. These are *starters* to generalize per
the adopter's compliance table.

**ADR shape + the 7 topics (mined into `new-adr`, §9/D10).** Format:
Context / Decision / Consequences (positive + negative/trade-offs + follow-ups) /
Alternatives considered / Compliance; header `Status` + `Date` + `Applies to`.
Topics: (1) remote state — remote backend, locking, encryption, one state per
layer-per-env, partial backend + `backend.hcl`; (2) layered layout + isolated
state; (3) least-privilege IAM inline per layer; (4) mandatory tagging;
(5) private-by-default network topology; (6) OIDC-only pipeline auth, no static
keys; (7) **self-healing = detect→analyze→propose→human-approve→apply, never
auto-apply** (roadmap: drift→auto-PR, failure-diagnosis→fix-PR, alarm→runbook) —
this is the minimum-regret carve as a decision record.

**Pipeline job shape (`pipeline/*.md`).** GitHub reference: a `plan` job
(`fail-fast: false` matrix over layers foundation/platform/app; `id-token: write`;
OIDC login per cloud; `fmt -check` → `init -backend-config=backend.hcl` →
`validate` → `plan -out=tfplan` → `show -json > tfplan.json`; `conftest test
tfplan.json`; upload plan artifact) and an `apply` job (`needs: plan`; only on
`push` to `main`; `environment: <env>` = the human approval gate;
`max-parallel: 1` to apply layers in dependency order; `apply` runs **only after**
the environment approval — that gate, not the flag, is the human boundary). Azure
DevOps = environment approvals/checks + `ManualValidation`; GitLab = protected
environments + `deployment_approvals`.

**Plan artifact shape (`spec-plan-tasks-shape.md`).** `plan.md` carries a
**mandatory ADR-compliance table** (Decision | Governing ADR | Compliant? | Note),
a standards-mapping table, the layered `terraform/` layout, networking design,
pipeline design, a verification plan, and a human-review-handoff section. Any ❌/⚠️
row must be resolved before tasks.

**Currency requirements — pin the *current* mechanisms (a common failure is
copying older guidance):**

| Area | Do NOT emit (stale) | Emit (current) |
| --- | --- | --- |
| AWS state locking | a **DynamoDB lock table** | **Native S3 lockfile** — `use_lockfile = true` (GA Terraform 1.11); the `state` ADR + AWS backend reference use the lockfile and note DynamoDB only as legacy. |
| Static-analysis scanner | **`tfsec`** | **Trivy** (tfsec was merged into Trivy in 2023) + Checkov; keep `conftest`/OPA for org policy. |
| CI `setup-terraform` version | an old pin (e.g. `1.9.x`) | a current 1.11+ release (needed for the S3 lockfile); adopter-tunable, not frozen. |
| OIDC trust-policy `sub` | legacy name-only `sub` | GitHub's **current immutable numeric-ID form** (repos ≥ 2026-07-15) — a legacy `sub` silently fails (§8). |

These are why standards/providers/policy ship as pack-owned **references** (D9):
they update with the pack, so an adopter tracks the current mechanism.

### 12. Prior-art comparison across the IaC-spec-kit lineage (MECE) + what we adopt

Two public, shipped tools occupy this exact problem shape; comparing them along
**mutually-exclusive, collectively-exhaustive design axes** both justifies the
pack and tells us what to adopt. (Public repos, maturity as of mid-2026:
**IBM/iac-spec-kit** ≈ 80★, v0.0.11, explicitly experimental; **dotlabshq/spec-ops**
≈ 8★, ~3 weeks active, a thin spec-kit skin.)

| Axis (MECE) | IBM/iac-spec-kit | dotlabshq/spec-ops | **`iac-terraform` (this RFC)** |
| --- | --- | --- | --- |
| **Verification boundary** (where the human gate sits) | **stop-at-generated-code** (`validate`+`fmt`; never runs `plan`/`apply`) | stop-at-code; ungated `deploy` | **loop arc** — `plan` = inner verify/G4, `apply` = `release-loop` (ephemeral-auto), human at G5/irreversible |
| **Iteration** | one-shot + static `analyze`/`converge` gap passes | one-shot | **two iterative loops** (plan-iterate inner, apply-iterate outer) |
| **Policy-as-code** | **none** | **none** | plan-JSON policy gate → preflight + PRR |
| **Cloud-agnosticism mechanic** | **vocabulary firewall** — spec forbids service names ("managed database", not RDS); concrete names only from plan on | fixed opinionated stack | **adopt the vocabulary firewall** + the provider category taxonomy (§6b) |
| **Governance model** | semver'd `principles.md` "constitution", Principles Check gated twice, Sync-Impact-Report cascade | placeholder `constitution.md`, semver, MAJOR-bump on tool swap | governance-index (in `governance-extras`) + `new-adr` infra mode (reuse; no rival tree) |
| **Deep-design pass** | **`/iac.enrichplan`** — persisted research/architecture/modules/quickstart + per-cloud Well-Architected mapping + curated-registry-module-first | none | **optional enrich that taps `architect`** (well-architected + design doc) + `contract-acquisition` (curated modules = grounding) |
| **Task decomposition** | **tier-based** (Foundation→Network→Compute/Data→App→Polish), `[P]` if file-disjoint + no data dep | phase-based + "scenario independence" | **adopt tier-based + `[P]` rule**; align tiers to the layered layout |
| **Deploy / iterate loop** | none | `/specops.deploy` (Helm/ArtifactHub→ArgoCD), **ungated** | `release-loop` (gated, iterative, ephemeral) |
| **Multi-tool** | Terraform-first | claims TF+Ansible+ArgoCD+Cilium but **no real abstraction** (dir-convention + prompt only; internally inconsistent) | **Terraform/OpenTofu (same HCL dialect) in v1** — spec-ops is the evidence that multi-*language* tooling without a real abstraction is a trap |
| **Reviewers / agents** | none | none | **reuse `core`'s 3 forked-context reviewers; zero new agents** |

**What we adopt (attributed prior art), folded into §2:**
- **Vocabulary firewall (IBM)** → the SPECIFY stage forbids cloud-specific service
  names; concrete services appear only from PLAN onward. Cloud-agnosticism *by
  construction*, stronger than "cloud is an input."
- **Tier-based tasks + the `[P]` parallelism rule (IBM)** → the TASKS stage orders
  by infrastructure tier aligned to the layered layout; `[P]` only when tasks touch
  disjoint files with no resource/data dependency (this is also how `release-loop`
  reasons about dependency ordering).
- **Optional enrich pass (IBM)** → offered, not built: when a build is complex,
  deepen the plan by **tapping the `architect` pack** (its Well-Architected /
  design-doc lenses) and `contract-acquisition` (curated-registry-module-first =
  the schema-grounding the failure-mode evidence wants). No new stage we author.
- **Scenario-independence contract (spec-ops)** → each infra slice must be
  independently deployable / validatable / **rollback-able** — which is exactly
  `release-loop`'s per-changed-surface e2e coverage + `blast-radius` isolation.

**What we deliberately reject:** IBM's stop-at-code boundary (weaker than the loop
arc — no `plan`/`apply` oracle, no policy gate); both tools' absence of
policy-as-code; spec-ops's multi-tool story (a fixed stack mislabeled as an
abstraction — direct evidence for the Terraform-only v1 non-goal); and every
tool's re-invented constitution (we reuse `new-adr` + the governance-index).

## Options considered

**Two MECE axes.** Axis A: *where does the capability live?* (below). Axis B: *where
does the verification boundary sit?* — enumerated in §12's first row and resolved by
D7 (the loop arc dominates stop-at-plan / stop-at-code / ungated-deploy because it
is the only option with both a `plan` inner-oracle and an iterative `apply`
outer-oracle). The two axes are orthogonal and together cover the design space.

**Axis A:** where does a reusable Terraform-generation capability live in a
catalogue whose charter refuses to pick a tech stack? The axis exhausts to four —
nowhere, in the universal core, bolted onto an adjacent method pack, or a
dedicated opt-in pack.

| Option | Trade-offs vs. goals | Verdict |
| --- | --- | --- |
| **1. Do nothing** (keep only `core`'s tool-neutral doctrine) | Zero maintenance; but adopters keep re-deriving the same layered-Terraform + OIDC + policy-on-plan scaffolding by hand — the frequent, repeated work the catalogue exists to remove. Cost of delay: the capability stays tribal. | Reject |
| **2. Fold into `core`** | Maximum reach; but Terraform + cloud is exactly a tech-stack framework — violates Principle 1 (universal) and the charter's explicit "never of specific frameworks". Pollutes the one pack that must stay neutral. | Reject |
| **3. Bolt onto `architect` / `release-engineering`** | Some conceptual overlap (design; deploy loop); but those are *method* packs that ship no stack scaffolding — adding Terraform seeds bloats them and blurs their boundary. | Reject |
| **4. New opt-in tool-specific pack** ★ | Contains the stack-specificity behind an explicit opt-in; precedented by `atlassian`/`figma`/`credential-brokers` (tool-specific, not in any default profile); reuses `core` doctrine; each primitive still faces the four principles. Cost: a new charter-boundary precedent + provider/CI maintenance. | **Recommended** |

Prior art for option 4 is in-catalogue and load-bearing: `atlassian`, `figma`, and
`credential-brokers` are all tool/vendor-specific, opt-in, and excluded from
default profiles — the exact shape proposed here.

## Risks & what would make this wrong

**Pre-mortem.**
- *Charter erosion.* An opt-in tool-specific pack normalizes stack-specific packs
  and the "does NOT pick your stack" line softens. *Mitigation:* keep it out of
  every default profile; require the four principles of each primitive; make this
  RFC the cited precedent so the next such pack is judged against it, not waved
  through. **The devil's-advocate pass (Finding 2) showed opt-in *alone* is
  insufficient** — Backstage / VS Code extensions / Homebrew / the Terraform
  registry / ESLint all sprawled despite opt-in, because they lacked a
  maintenance-ownership + deprecation lifecycle. *So this pack commits, from day
  one, to:* a named maintainer, a stated support scope (which clouds/CIs are
  *validated* vs *contract-only*), and an **archiving/deprecation path** for a
  provider/CI reference that goes stale — the containment control the precedents
  prove is actually load-bearing.
- *Doctrine duplication drift.* The pack re-states `core`'s infra-verification /
  operational-safety and the two drift apart. *Mitigation:* the skill body
  **references** `core` modules and ships only Terraform-specific scaffolding + a
  thin driver; a lint could assert the skill carries no operational-safety copy.
- *Reference rot.* The per-cloud / per-CI references + skeletons age against
  provider and CI releases. *Mitigation:* the references-not-seeds packaging (D9)
  keeps them out of adopter repos so they update with the pack; keep skeletons
  minimal and push the *live* contract to `core`'s contract-acquisition oracles at
  generate-time rather than freezing it; version-pin doctrine limits blast radius.
- *Hallucinated Terraform lands anyway.* A peer-reviewed failure mode (IaC-Eval,
  NeurIPS 2024): LLMs emit resource/argument identifiers absent from the provider
  schema, and a clean `plan` does not certify intent. (The specific "29% / 42%"
  figures are *unverified* — see the Finding 7 correction — but the *direction* is
  peer-reviewed.) *Mitigation:* the generator **must** ground authoring in the
  provider schema via `core`'s `contract-acquisition` oracle (the best-evidenced
  fix), and the design keeps the human apply-gate precisely because plan-clean ≠
  correct — the pack does not treat a green plan as done.
- *Spec-gate leakage.* Prior art shows spec/plan phase boundaries leak in
  practice and infra reality flows backward (drift). *Mitigation:* Stage-0 +
  record-citation is a hard, non-skippable gate; drift/state handling is delegated
  to `core`'s `operational-safety`, not assumed away.
- *Silent full-mode breakage against `release-loop` (WA-review Major 3).* The
  "compatible by convention, no manifest dependency" seam hard-codes `release-loop`'s
  `reversibility-class` enum, its consent-gate expectations, and the
  `operational-safety` preflight-set shape — pinned to nothing. If `release-loop`
  renames a module or changes the reversibility taxonomy, `generate-iac` keeps
  emitting the old shape and the outer loop can mis-classify a one-way-door action —
  the exact irreversible-action guardrail the arc exists to enforce. *Mitigation:*
  `references/release-loop-integration.md` records the **targeted `operational-safety`
  module-contract + reversibility-enum version**, and a **conformance test / CI canary
  fails when the emitted output shape drifts** from the current `release-loop`
  contract; absent that, degraded mode is the only *supported* mode in v1.

**Key assumptions (falsifiable).**
- Grounding generation in the provider schema materially reduces hallucination for
  *this* pack's outputs. *If false* — grounding doesn't transfer to the layered/
  multi-cloud shapes the pack emits — the contract-acquisition reuse is
  insufficient and the pack needs its own verifier loop. (Evidence is
  AWS-centric, single-lab, un-replicated preprints.)
- Adopters want shipped Terraform scaffolding, not just doctrine. *If false,*
  `core`'s doctrine suffices and this pack is dead weight.
- The workflow is reached often enough to stick (Principle 4). The devil's-advocate
  pass (Finding 5) returned a **do-not-resolve**: *greenfield* authoring is
  front-loaded and rare. The frequent-use mechanism, recalibrated (§2/D17), is that
  **`author` is invoked for *every* infra change** — new work, **the fixes
  `release-loop`'s drift feedback surfaces**, and follow-on changes gated by the
  **reconcile-before-change preflight** — so the pack is reached whenever infra
  evolves, which (given day-2 dominates) is often. **Drift research (§2) supports the
  recurrence** (discipline-independent drivers — cloud-side, autoscaling, k8s
  reconciliation) **but softly** (vendor-sourced frequency data, no neutral study, two
  fabricated stats excluded). Note the *detection* value largely accrues to
  `release-loop`, not here — this pack's Principle-4 case rests on **authoring every
  change + the preflight**, not on owning drift detection. *If false* — adopters
  scaffold once and never evolve the infra — it should be a template repo, not a pack.
- The four-file provider contract generalizes across the **major public clouds** (not
  "any provider" — rescoped per Finding 6). *If false,* even AWS/Azure/GCP need
  bespoke work and the contract is a slogan; the review already shows it does **not**
  extend to non-cloud providers / multi-provider stacks / on-prem / sovereign.

**Drawbacks.** A standing Terraform + multi-cloud + multi-CI surface to maintain;
a charter exception that must be actively defended; seeds that need periodic
refresh. Accepted as the price of removing frequent, repeated setup work.

## Evidence & prior art

An applied (practitioner / grey-literature) research pass grounds the sections
above; the full survey with per-finding confidence, triangulation, and a
known-unknowns section is promoted to
[`0065-notes/agent-driven-iac-survey.md`](0065-notes/agent-driven-iac-survey.md).
Summary of the load-bearing findings:

- **Spike / de-risk (additivity over `core`).** The load-bearing assumption is
  that the pack is additive, not duplicative. Checked by mapping every doctrine
  claim onto existing coverage: stop-at-plan + phased-oracle + drive-deploy →
  `core` work-loop infra-verification; state/idempotency/drift/rollback/isolation
  → `core` `operational-safety`; IaC misconfig → `core` `security-checklists`; ADR
  authoring → `governance-extras` `new-adr`. The uncovered residue —
  layered-Terraform skeletons, the four-file provider contract, policy-on-plan
  rules, OIDC pipeline generators, the intent→Terraform driver — is exactly this
  pack's content. The risk is charter-fit, not feasibility.
- **The workflow shape is validated prior art — and two IaC adaptations were mined
  in full (§12).** The intent → spec → plan → tasks → implement loop is a named,
  shipped methodology (GitHub Spec Kit — "code serves specifications",
  `[NEEDS CLARIFICATION]` markers, a "constitution" compliance gate). `[high]` The
  two IaC forks — **IBM/iac-spec-kit** (80★, experimental) and **dotlabshq/spec-ops**
  (8★, ~3 weeks) — are low-adoption `[moderate]`, but mining them yielded four
  adopted mechanics (vocabulary firewall, tier-based tasks, an optional enrich pass,
  scenario-independence — §12) and one confirmed non-goal (spec-ops's multi-tool
  story is dir-convention, not an abstraction → Terraform-only v1). Independent
  sources (Mamezou, InfoQ, The New Stack) converge on a failure mode: **spec/plan
  phase gates leak in practice and infrastructure flows *backward* (drift) against
  SDD's forward assumption** — *why* the pack enforces Stage-0 structurally and
  reuses `core`'s drift/state depth. Notably **neither fork ships policy-as-code, a
  `plan`/`apply` oracle, an ADR concept, or a deploy loop** — the gaps this pack
  fills by reusing `core` + `release-loop`.
- **The most decision-relevant evidence — schema-grounding beats hallucination;
  `plan` is not a sufficient oracle. `[low]` on the specific numbers, `[moderate]`
  directionally** (downgraded by the devil's-advocate pass —
  [counterpoints](0065-notes/iac-terraform-pack-counterpoints.md), Finding 7). The
  **peer-reviewed anchor is IaC-Eval (Kon et al., NeurIPS 2024 Datasets &
  Benchmarks)** — an **AWS-only** benchmark showing LLMs frequently emit resource/
  argument identifiers absent from the provider schema; **schema/config-grounded
  retrieval is the best-evidenced mitigation** (Nekrasov et al., arXiv 2512.14792,
  raises *technical validation* to 75.3% from a 27.1% *overall-success* baseline —
  two different metrics, not a clean before/after); and `validate`/`plan` are
  argued **insufficient standalone oracles** (TerraProbe, arXiv 2606.26590 —
  non-frontier models). *Caveats the review surfaced:* the widely-quoted "29% /
  46-pp" figures come from an **unverifiable ResearchGate paper (no arXiv, no
  confirmed peer review)** — treat as unverified; **no independent Azure/GCP
  replication exists**; and a follow-on found only **59% of IaC-Eval's own
  ground-truth passes `terraform plan`**, so some "LLM failure" may be oracle
  noise. **The directional claim still holds** (hallucination is a real,
  peer-reviewed failure mode; grounding + `plan` help), and **both mitigations are
  already `core` doctrine** (`contract-acquisition`'s "acquire the contract, never
  guess a schema"; infra-verification's "green validate is never a done-signal") —
  so "reuse `core`" is what even the *conservative* reading recommends, and the
  59%-oracle-noise finding *strengthens* the "don't over-trust one oracle" case for
  keeping the human apply-gate.
- **Best-practice corroboration + two recency corrections.** All six Terraform
  practices in §3 are primary-doc best practice (HashiCorp, AWS Prescriptive
  Guidance, Gruntwork). `[high]` Two currency corrections are baked into the
  references (§11): **native S3 state locking (`use_lockfile`, GA Terraform 1.11)
  supersedes the deprecated DynamoDB table** (§3); and **cite Trivy, not tfsec —
  tfsec was merged into Trivy in 2023** (§7). Policy-on-plan against plan JSON is the recommended mechanism but
  carries an OPA-documented caveat (unknown values / dynamic blocks may be
  unresolved at plan time). OIDC + "environment-as-the-gate" human approval are
  cross-vendor consensus (AWS/Azure/GCP; GitHub/GitLab/Azure DevOps) `[high]`,
  with a live GitHub OIDC `sub`-claim-format change (§6/§8) to flag.
- **Repo precedent.** `atlassian`, `figma`, `credential-brokers` (opt-in
  tool-specific, profile-excluded); `core` infra-verification + operational-safety
  (the reused doctrine); `governance-extras` `new-adr`; the profiles'
  scope-homogeneity lint (which the exclusion respects).
- **Prior-art gap.** The four-file provider abstraction is this proposal's own
  generalization; no in-catalogue or surveyed external precedent states it as a
  contract, which is why §6 specifies it in full. The "engine is the repo, not the
  model" framing is an inference from AGENTS.md/skill mechanics, not a sourced
  principle — no efficacy study exists.

## Open questions

- **Q1 (resolved by D12/§6a).** Engine wording/support is settled: the pack supports
  **both** engines with an engine-neutral baseline, and the emitted references stay
  neutral ("Terraform/OpenTofu"), pinning nothing to a specific distribution.
  **Pack name — DECIDED: `iac-terraform`** (the ecosystem's category name; the HCL
  dialect is still "the Terraform language"; the README states dual-engine support
  explicitly).
- **Q2 (DECIDED — same PR).** The three `governance-extras` companions (§9) ship in
  the **same PR** as the pack, not a follow-up.
- **Q3 (DECIDED — AWS + GCP + Databricks; see D5).** v1 validated examples: **AWS +
  GCP** (four-file contract) **+ Databricks** (data-platform category reference);
  Azure and the remaining categories ship contract-complete but unvalidated.

*All open questions are now resolved.*

## Follow-on artifacts

_All in one PR (Q2 — companions ship with the pack)._
- Scaffold `packs/iac-terraform/` per §10 (via `propose-catalogue-pack`'s shell
  step), authoring the references from the §11 implementation spec; validate **AWS +
  GCP + Databricks** worked examples (D5); validate AWS on **both `terraform` and
  `tofu`** (D5 dual-engine requirement).
- The **three `governance-extras` companions in the same PR** (D16): `governance-index`
  (convention + template + optional lint), `new-adr` infra mode, and the
  `extension-contract` convention + one `architect-review` rubric line.
- Add `iac-terraform` to the self-host recipe include list (declarative config).
- Per-pack guide home `docs/guides/iac-terraform/` + changelog entry.
- Author `references/release-loop-integration.md` against the current `release-loop`
  contract (the seven integration items in §1b), **recording the targeted
  module-contract + reversibility-enum version** (WA Major 3).
- **CI: a scheduled staleness job** re-running `init -backend=false && fmt -check &&
  validate` per contract-complete reference against the latest provider release
  (WA Major 4), + a **`release-loop` conformance canary** (WA Major 3).
- Author both **`generate-iac`** (D8/D17) and **`reconcile-iac`** (D17) skills
  sharing the references tree; `reconcile-iac` accepts both a before-change
  preflight trigger and an on-demand/scheduled trigger (§2).
