# release-engineering

The **SRE/ops outer loop** — deployed end-to-end validation above `work-loop`'s
inner build loop. This pack completes the **company OS**: product (discovery, the
`product-engineering` pack) → engineering (build, `work-loop`) → **SRE/ops
(release, this pack)**.

`work-loop` is the **inner loop** (local build + verification). `release-loop` is
the **outer loop**: it deploys the integrated whole to an **ephemeral
environment**, runs e2e, observes telemetry, feeds deployed findings back to the
inner loop (no human relay), redeploys, and **iterates until the deployed whole
converges** — then stops at the **human consent gate** for the prod ship (G5),
which it surfaces as a **release-readiness record** to ratify, not a bare
go/no-go.

| Primitive | What it does |
| --- | --- |
| `release-lead` (agent) | The SRE/ops outer-loop supervisor — a *peer* of `work-loop`'s supervisor and `discovery-lead`, **not** a `work-loop` mode. Holds the loop state, drives deploy → e2e → converge on ephemeral envs, talks to the human only at the irreversible exits. |
| `release-loop` (skill) | The deployed e2e-validation loop doctrine: the minimum-regret autonomy carve, convergence-by-policy, the inner↔outer feedback seam, the outer round cap + cost budget, and the deploy security/integrity controls. |

## Install

Repo scope, into the **build repo** — the same repo `work-loop` ran in (where the
deploy-ready component lives and `core` is repo-installed):

```bash
agentbundle install release-engineering --scope repo
```

The pack **hard-depends on `core`** and reuses its `operational-safety` modules +
`quality-engineer` + `security-reviewer`. It **detect-and-degrades** on
cloud/platform/contract packs: when a platform pack is present it consumes the
adopter's deploy / smoke / teardown artifacts; when absent it **names the
artifacts it would otherwise use and surfaces the gap** (the "offer to scaffold"
path), never failing silently.

## Why repo scope (and not user scope)

The repo-scope install is **architecturally load-bearing**. `release-lead` reuses
`core`'s repo-scope `quality-engineer` / `security-reviewer` / `operational-safety`
— sound only because it runs **downstream, in the build repo** where `core` is
installed at the same scope. This is the deliberate **scope-inverse** of the
user-scope `discovery-lead`, which ships its *own* reviewers because it runs
*upstream* in non-repo document workspaces that cannot assume a `core` install.
*Scope follows where the work happens* — the company-OS scope boundary falls at
the G3 handoff where shaping becomes a concrete repo.

## The minimum-regret carve

Autonomy is carved by **minimum-regret** — reversible ⇒ autonomous; irreversible
⇒ human:

- **Autonomous (reversible) zone** — the inner loop; the outer loop **on ephemeral
  environments** (deploy / e2e / observe / iterate / teardown); canary in
  non-prod tiers with metric-gated auto-rollback. "Reversible" is conditioned on
  env isolation: ephemeral envs hold no real data, cannot reach prod, and are
  isolated from each other.
- **Human (irreversible) zone** — first real users or data; data migrations; spend
  over a pre-agreed threshold; security / auth-boundary changes; anything
  irreversible beyond MTTR; and the prod ship (G5).

The **reversibility primitives** — ephemeral environments + feature flags +
auto-rollback — are what turn deploy from a one-way door into a two-way door,
which is what lets the outer loop run autonomously up to the human line.

## What's NOT in this pack

- **No runtime engine, daemon, orchestrator, cost-gate, or canary-analyzer** — the
  loop is content + doctrine. It *offers to scaffold* an
  adopter's deploy / smoke / teardown artifacts; it does not ship them.
- **No new reviewer agent** — the operational lens is a *mode* of the reused
  `quality-engineer`; security reuses `security-reviewer`.
- **No fork of the discovery sidecar schema** — it consumes the produced `_state/`
  instances by convention (the schema definition is carried in
  `product-engineering`'s `discovery-loop` skill).
- **The fidelity-ladder / local-infra-equivalents skills** — those are the
  *inner-loop* obligation, a separate concern.
- **The harness** — omnigent supplies ephemeral envs, the human-in-the-loop
  option-card pause, and cost policies; the loop is expressed harness-neutrally.

## Usage

Hand the deploy-ready whole to `release-lead` after `work-loop` reaches G4
("build done"):

> Run the release loop on the integrated whole — deploy to an ephemeral env, run
> e2e, and iterate until it converges, then surface the prod ship for me to ratify.

`release-lead` drives the cycle from the `release-loop` skill, which carries the
full doctrine — the minimum-regret carve, convergence-by-policy, the inner↔outer
feedback seam, and the deploy security/integrity controls.
