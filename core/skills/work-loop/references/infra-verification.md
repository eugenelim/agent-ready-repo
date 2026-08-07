# infra-verification — the infra/deploy verification mode (full doctrine)

> **Loaded when:** the work is **infra-flavored** — the destructive/irreversible
> risk trigger routed it to full mode *and* it provisions, mutates, deploys, or
> tears down infrastructure (the `security-checklists` Module index's IaC /
> deploy-config entry).
> **What this is:** the progressive-disclosure depth behind `work-loop`'s
> infra/deploy verification mode. `SKILL.md` keeps the load-bearing one-liners
> (the mode entry in the PLAN verification-mode list, the EXECUTE
> contract-grounding gate, and the reviewer-dispatch bullets that route against
> the two depth libraries' Module indexes — the boundary→module routing
> authorities now live in `security-checklists` and `operational-safety`, not in
> a `SKILL.md` table); the full doctrine —
> the layered GATES sequence, the multi-artifact preflight, contract grounding,
> the EXECUTE craft load, the reusable-script discipline, phased oracle fidelity
> (V1), the readiness-aware data-plane probe (V2), and the reviewer wiring —
> lives here. Tool-neutral throughout (Terraform / Pulumi / CDK / CloudFormation
> / Kubernetes / hand-rolled scripts alike); any tool named is illustrative,
> never normative. (The other three verification modes' depth — the manual-QA
> "exercise the real artifact" doctrine — lives in
> [`verification-modes.md`](verification-modes.md).)

## PLAN — the layered GATES sequence

The infra/deploy mode's contract is a **layered GATES sequence**, not a single
check — because a deploy is slow, stateful, costs money, and is partially
irreversible. The layers, in order:

1. **static preflight** — validate / lint / policy-as-code, run through the
   provider-appropriate scanner the preflight obligation (below) requires as a
   task-zero (the lint+typecheck analog);
2. **plan / preview** — a dry-run diff, reviewed before any mutation;
3. **idempotent convergent apply — the precondition the rest rests on**:
   re-running after a fix must *converge, not collide*, so iteration is safe; an
   imperative, non-idempotent script is the retry-collision root cause, and the
   thing to fix first rather than work around;
4. **active end-to-end smoke** — not a single status check but a multi-hop
   probe, and the direct extension of the visual/manual-QA "exercise the real
   built artifact" doctrine to a deployed system: seed test / mock users → load
   the real CDN / site URL → assert it actually renders → on failure pull the
   access / error logs and debug → tear down;
5. **rollback** — *before* the first apply, confirm a known-good re-apply path
   is named (it belongs in `## Rollout`), since no atomic rollback exists for a
   partially-applied deploy.

This mode names *how we verify* a deploy; it does **not** author *deployment
sequencing*, which the plan template's `## Rollout` section already owns —
cross-reference it, don't duplicate it.

### Phased oracle fidelity (V1)

These layers are **phased and of increasing fidelity** — static (lint /
validate / policy-as-code) < plan / preview < runtime deploy + smoke — and the
cheap-early oracle is **necessary but not sufficient**: a green `synth` /
`validate` is the **local-typecheck analog**, never a done-signal, and "deployed
≠ working." Do not over-trust it. This carves cleanly against the
[`contract-acquisition`](../../contract-acquisition/SKILL.md) gate
(A1): **A1 owns *did the agent consult the oracle to ground authoring before
generating the resource?*; V1 owns *is a green early oracle being mistaken for
"works" at verify?*** — the same oracle output, two different jobs
(ground-before-authoring vs. don't-mistake-cheap-for-done).

### Readiness-aware data-plane probe (V2 — refines layer 4)

The active end-to-end smoke (layer 4) has a specific shape, distinct from app
verification: **in-network if private** (probe from *inside* the network
boundary, not the operator's machine, when the resource isn't publicly
reachable); a **data-plane round-trip** — **write a record → read it back**, or
for a request path drive it to the **terminal user-visible result** — never
"resource exists / status healthy"; **readiness-aware** — poll until ready with
**bounded backoff**, distinguishing *not-yet-ready / propagating* from *broken*;
and **self-teardown against an ephemeral, uniquely-named target** (the `defer
destroy` / `dev-test-run-uuid` shape), the teardown rolled into the P1 teardown
artifact. This **refines** P2 and cross-links the plan template's `## Rollout`
(which owns sequencing); it does **not** re-author the GATES layer sequence
above.

## PLAN — read recorded coordinates first, then cold oracle discovery

Before enumerating the multi-artifact preflight below and before the
contract-grounding gate, do one cheap thing first: **check recorded
coordinates → acquire via oracles**. The adopter may already have written down
where they deploy and how they verify, in files they own:

- the **`AGENTS.md` "Commands you'll need"** optional infra/verification block —
  the `<deploy>` / `<smoke / verify-status>` / `<teardown>` / `<seed-test-data>`
  one-liners; and
- the **`reference.md`** platform/verification slots — the
  **managed-runtime / platform target** under *Constraints*, the
  **framework-/library-level contract** under *Solution strategy → Key
  technology decisions*, and **where the verification tooling lives** under
  *Crosscutting → Observability / Testing standards*.

**Every one of these reads is presence-checked — read-if-present, degrade
honestly if absent.** A repo that recorded nothing runs exactly as it does
today: absence lowers only the *starting information* the preflight begins from,
it **never fails the loop**, and it is **not enforced by any CI gate**. There is
**no new config file** for this — no `grounding.toml`, no schema; the surface is
the two adopter-owned files above. State which coordinates you found (or
"none"), the same way `architect-design` states the surface it detected.

**A recorded coordinate seeds acquisition; it never replaces it.** A found
`<deploy command>` or platform target *seeds* the multi-artifact preflight and
the contract-grounding gate — it tells you where to start — but the agent still
derives the **live** contract from the toolchain's oracles
([`contract-acquisition`](../../contract-acquisition/SKILL.md)) and
still smokes the **real** deployed system. When a recorded value **contradicts**
the oracle (the `reference.md` names a runtime the `plan` output disputes, a
recorded smoke command targets an endpoint the deploy no longer exposes), that
contradiction is a **surfaced drift signal**, not a fact to trust — exactly the
AGENTS.md *"When this file is wrong"* posture: flag the drift, don't silently
work around it.

## PLAN — the multi-artifact preflight (each its own task-zero)

For infra/deploy the mechanism is rarely one artifact; the preflight enumerates
it as a **multi-artifact set, each its own task-zero**: (a) a **verify-status**
script (does the deploy report healthy?), (b) a **teardown** script (clean down
a failed or ephemeral run), (c) **test-data / mock-user seeding** (so the smoke
probe has something to exercise), (d) a **provider-appropriate policy-as-code /
CSPM scanner**, and (e) a **durable credential session** — establish credentials
**once** (resolve into a static session via the toolchain's own export
mechanism), assert with a **single identity check**, **reuse** it for the whole
loop, and resolve **profile-vs-static precedence up front**. The field report
found credentials re-resolved per call until an SSO wrapper timed out — the
"establish once, reuse" fix was rediscovered independently in *both* builds,
which is why it is a named preflight artifact, not an afterthought.

The scanner is the load-bearing one: it is the **per-provider-depth source**,
its vendor-maintained rulesets holding the per-service config checks the
standards-grounded reviewers cannot and should not carry — and the **same**
scanner feeds two layers, *operational* misconfig → the infra/deploy mode's
static preflight (layer 1) and *security* misconfig → the mandatory security
pass (REVIEW). The requirement is **mechanism-level, not tool-level**: a scanner
must exist; the adopter picks Checkov / tfsec / a cloud-native CSPM, exactly as
the loop requires "tests exist" without mandating a framework. The loop names
these as prerequisite tasks and offers to scaffold them; it does not ship them
as executable tooling.

## EXECUTE — drive the deploy yourself

Implement the change (one task may span several GATES layers), then **drive the
deploy yourself and read the real environment output**: run the apply, the smoke
probe, the log pull, and the teardown, and read their *actual* output rather
than reasoning about what they would say. The **human-as-relay** pattern — a
human running the deploy command and pasting the error back into the session by
hand — is the anti-pattern this removes; the agent reads ground truth from the
environment at each step. This is **harness-agnostic doctrine** — do it by hand
on any agent. In Claude Code, background tasks (for long applies), `asyncRewake`
(to wake on a background deploy's exit with stderr surfaced), and `PreToolUse`
(to gate a destructive command before it runs) are an **accelerant only, never a
dependency** — matching how `/verify` and `/simplify` are treated; adapters
without them lose the shortcut, not the doctrine.

## EXECUTE contract-grounding gate (infra flavor — universal across light and full mode)

This section is the **infra-flavor detail** of the gate; the gate itself spans
**two surfaces** (`SKILL.md` § EXECUTE contract-grounding gate). The **software**
surface's full tiered protocol (T0 version → T1 type-checker / compiler +
API-surface oracle → T2 curated skill → T3 versioned docs → runtime probe) lives
in [`contract-acquisition`](../../contract-acquisition/SKILL.md)
itself — not in this infra-depth reference, which is loaded only on
infra-flavored work.

Before generating a CLI invocation, an IaC resource, **or application code that
runs on a managed runtime** (e.g. a function handler whose packaging / import
model the platform dictates) **against an unfamiliar platform**, acquire that
platform's contract via the
[`contract-acquisition`](../../contract-acquisition/SKILL.md) skill —
never guess a flag, a schema shape, a field constraint, or a packaging /
entrypoint assumption. This is the infra flavor of the **generalization of
AGENTS.md's "Grep to verify a function exists before importing it"**: the
toolchain's own deterministic oracles (validate / plan / synth + a
machine-readable schema slice) are the grep, and a guessed contract is the broken
import. The gate's
output is a **cited contract slice the generated resource references** (the
schema field, the plan line, the doc) — not a bare "contract acquired: yes"
flag; that citation is what lets `quality-engineer` re-derive independently. The
gate is **universal** — grounding is cheap and a guessed contract is expensive —
so it
fires in light mode too; the heavier infra-flavor layers (the
`cloud-implementation-craft` craft load at EXECUTE, the V2 data-plane probe, the
`quality-engineer` infra wiring) fire only on the **infra-flavored signal** (the
destructive/irreversible trigger + the `security-checklists` Module index's IaC /
deploy-config entry).

## EXECUTE — `cloud-implementation-craft` loaded into the implementer's brief

On infra-flavored work, the orchestrator inlines the
[`cloud-implementation-craft`](../../operational-safety/references/cloud-implementation-craft.md)
module — least-privilege-**but-sufficient** permissions derived from the
contract in one pass, eventual-consistency / propagation readiness waits,
timeouts-to-real-latency + bounded backoff + client cold-start tolerance,
dependency ordering, terminal-failed-state handling, the managed-runtime
packaging / entrypoint-import model, and externalized script configuration —
into the **implementer's EXECUTE brief**, via the
[`operational-safety` Module index](../../operational-safety/SKILL.md#module-index)
(the routing authority). This is the **deliberate EXECUTE-consumer extension** of
`operational-safety`: by default a REVIEW-only depth library for
`quality-engineer`; here the **same module, on the same routing mechanism**, is
pointed at the implementer so the craft shapes the build, not only the review.
Loading is **orchestrator-driven** (the subagent's `tools:` carries no Skill
tool), never subagent self-discovery — exactly as the REVIEW-side
`operational-safety` and `security-checklists` inlining works.

## EXECUTE — reusable-script corollary (a discipline sharpening, not a new failure family)

**Every** live-environment interaction — deploy, smoke probe, **log pull, debug
step** — goes through a **reusable, idempotent, credential-reusing script** that
accumulates into the verify / probe / teardown harness (the P1 task-zero
artifacts), **not** a stream of one-off shell commands that leaves nothing
behind. These scripts are **externally parameterized**: resource name prefixes,
region / account, tags, stage, and naming-convention tokens live in **external
config** — *illustratively (never normative, Principle 1)* `*.tfvars` /
`TF_VAR_*`, a sourced env file, CDK context / `cdk.json` — **never hardcoded
inline**. That lets the harness **honour an organization's naming + tagging
conventions** without editing script bodies, and **port across accounts to stand
up like-for-like environments** — the property V2's ephemeral, uniquely-named
probe target and `environment-isolation`'s per-PR ephemeral harness both rest
on. This is a **discipline sharpening agent-drives-verification**,
not a new failure family.

## REVIEW — mandatory, multi-module security on infra-flavored work

When the change is **infra-flavored** — the **destructive/irreversible risk
trigger** routed it to full mode *and* its diff matches the `security-checklists`
Module index's IaC / deploy-config entry — the `security-reviewer` pass is
**non-skippable** and
runs at **both the spec stage** (the pre-EXECUTE secure-design step) **and on
the diff**, not via the discretionary security-boundary trigger. Because
"infra-flavored" keys on the existing classifier rather than a per-diff
judgement, the pass **cannot be silently skipped** on an infra diff. The
orchestrator force-loads from the infra-relevant **candidate set** —
`config-misconfig` (the IaC / deploy-config entry — IAM, CORS, deploy config —
present on any infra diff) plus `access-control` (when the change alters the
authorization *model*: role bindings or resource policies that change *who can
call what*), `secrets-and-crypto` (secrets in state or env, keys),
`outbound-ssrf` (public exposure, CDN / origin egress), and `supply-chain`
(provider / module pinning) — each pulled in when the diff trips *that module's
own* `security-checklists` Module-index entry, so the Module index stays the
single deterministic authority and the set loads only what the diff trips, never a blanket load of the whole candidate set (a one-line
config tweak pulls one; a new public-facing stack pulls several). This adds **no
new reviewer and no new module**: it makes the *existing* security pass
mandatory and multi-module. The **Profile-A opt-out still applies wholesale** —
a project that uses no reviewer at all opts out of the loop entirely — but where
`security-reviewer` *is* in use the infra pass is **not individually skippable**,
and a missing `security-reviewer` subagent on infra-flavored work is a **loud
blocker in the final summary, not a silent proceed** (the one place the
select-or-note fallback hardens to a blocker, given the blast radius).

**Security on infra is a reviewer + scanner *pair*; neither substitutes for the
other.** `security-reviewer` is **not** the per-provider depth source — it
reasons from cross-cutting standards (OWASP / ASVS / CWE + STRIDE / LINDDUN) and
catches failure *classes* (over-broad IAM, public exposure, unencrypted-at-rest,
secrets in state, metadata SSRF, missing audit logging) and
control-completeness. The **per-provider secure-config depth** comes from the
policy-as-code / CSPM scanner the PLAN preflight requires as a task-zero (its
vendor-maintained rulesets *are* the provider baselines). Run both: the scanner
for per-provider breadth, the reviewer for failure-class reasoning.

## REVIEW — `quality-engineer` independent contract re-derivation (Delivery — no new agent)

The re-derivation trigger keys on **a contract slice having been cited at the
EXECUTE gate — infra *or* software** — not on the infra-flavored signal (that
signal only adds the infra-specific extras below). On infra-flavored work the
orchestrator additionally inlines
[`contract-acquisition`](../../contract-acquisition/SKILL.md)
(alongside `cloud-implementation-craft`, routed via the `operational-safety`
table in `SKILL.md`) into the `quality-engineer` brief, and the reviewer
**re-derives the platform contract independently from the oracles** — running
the validate / plan / synth + schema-slice acquisition itself — **never trusting
the implementer's own contract evidence**, which would reproduce the
field-report blind spot (a build that authored against model memory, then
"verified" against the same memory). **A cited *software* slice gets the same
independent re-derivation** — the reviewer re-runs the type-checker / API-surface
oracle (or reads the curated skill / versioned docs) itself, never trusting the
implementer's citation; this fires on any software-contract-citing diff, not
only an infra-flavored one, so the broadened EXECUTE software surface ships with
its matching REVIEW half. This adds **no new reviewer or agent** (the
three-reviewer ceiling): contract-conformance rides the **existing**
`quality-engineer`, already the infra reviewer in spirit. The
**auth-flow-contradiction class** (a spec whose auth design contradicts itself)
is caught **earlier, at spec stage, by `design-reviewer`** where the architect
pack is installed — otherwise it falls to the spec-stage adversarial pass. A
**dedicated `infra-contract-reviewer` is deferred** behind a named evidence
trigger (a spike showing oracle-execution traffic — large
`plan` / `synth` output — measurably degrades `quality-engineer`'s other lenses);
fetching the contract in *slices* softens the isolation case meanwhile.
