---
title: The three loops — the company operating model
summary: Understand why discovery, build, and release are separate supervised loops and how their handoffs form one operating model.
pack: _shared
kind: explanation
---

# The three loops — the company operating model

Software delivery has always had three distinct jobs: shaping what to build, building it, and getting it to production. Those three jobs have different failure modes, different decision authorities, and different reversibility profiles. A single loop can't govern all three well — and an agent that tries will either move too slowly (treating every change as a prod ship) or too recklessly (treating a prod ship as just another change).

This catalogue makes all three loops concrete.

## The handoff chain

```
product-engineering              core                    release-engineering
───────────────────              ────                    ───────────────────
discovery-lead                   work-loop supervisor    release-lead
Raw signal → Intent  ─G3─▶ Intent/brief → Spec → Code ─G4─▶ Built → Production
   (user scope)                  (repo scope)               (repo scope)
```

Each loop is a **peer supervisor** — not a mode of another, not a sub-phase. Each has its own agent, its own skill doctrine, and its own consent gates. The handoffs between them (G3: discovery → build; G4: build → release; G5: release → prod) are explicit gates where a human ratifies the decision before the next loop begins.

## Why three loops, not one

**Different reversibility profiles.** Exploring product shapes is cheap and reversible — you can explore five candidates in parallel and discard four. Deploying to production is expensive and often irreversible. Treating them with the same autonomy level is wrong in both directions: too much caution on exploration, too little on shipping.

**Different decision authorities.** Whether a product shape is worth building is a business decision. Whether code compiles is a mechanical gate. Whether a deployed system meets its SLOs is an operational judgment. These decisions belong to different people and different loops.

**Different failure modes.** The discovery loop fails when it converges on the wrong product shape. The build loop fails when it ships code that doesn't work. The release loop fails when it promotes something that breaks in production. Each failure mode requires a different set of checks, reviewers, and escalation paths.

## The discovery loop

**Pack:** `product-engineering` | **Agent:** `discovery-lead` | **Scope:** user

The upstream loop takes a raw product signal through structured shaping before
code is written. Its durable output is a ratified intent at the appropriate
altitude: initiative, capability, or feature. Product Engineering may de-risk
and decompose that intent, but it does not require Core and does not own the
repository delivery contract.

**Key mechanics:**

- **Diverge before converging.** Five candidate product shapes are explored in parallel against the customer segment and job-to-be-done. The goal is to surface the best shape by comparison, not to optimize the first idea.
- **Multi-lens convergence.** Product, UX, architecture, and safety lenses run simultaneously against a shared blackboard — results posted to slots, never relayed through chat. Each lens is a distinct specialist reviewer, not a re-run of the same one.
- **Recursion is data.** Sub-problems discovered during discovery become child nodes in an intent tree, not separate projects. The same loop governs every level of scope.
- **Hash-chained decision log.** Every human verdict is recorded append-only and hash-chained — the agent cannot forge or retroactively alter a ratified decision.

**Human gates:**
- **G0** — Ratify the value seed: the problem statement, the customer segment, and the existence bet.
- **G1.5** — Ratify the MVP boundary: which features are in scope for the initial bet.
- **G2** — Ratify the converged intent, including riskiest assumptions and validation hooks.
- **G3** — Ratify a feature-level handoff ready for repository admission or spec authoring.

→ [Discovery loop guide](../../product-engineering/) · [Walk a discovery end-to-end](../../product-engineering/tutorials/walk-a-discovery-end-to-end.md)

## The build loop

**Pack:** `core` | **Agent:** `work-loop` supervisor | **Scope:** repo

The inner loop. Core can operate alone: `intake-intent` admits a minimum
repository intent, `author-delivery-brief create|continue` coordinates work that
needs multiple specs or repositories, and `new-spec` owns one independently
shippable engineering contract. An upstream Product Engineering intent can use
the same routes without making that pack a repo-level dependency. Every build
then goes through plan, execute, gate, review, and decide.

**Key mechanics:**

- **Two contract reviews before approval.** `new-spec` first sends the drafted
  contract to a cold shaping review, then sends the complete spec-plan pair to
  adversarial review. The first checks whether the contract is observable and
  bounded; the second checks whether the construction plan can deliver it.
  Shaping review is distinct from the later adversarial, security, and quality
  code-review lenses; neither replaces code review after implementation.
- **Risk-scaled modes.** Eligible low-risk work runs direct-light from the current request with adversarial review and no persisted spec. Full mode uses a durable spec and plan when a risk trigger fires — unfamiliar territory, new dependency, compliance surface, multi-person work, destructive operation. The mode is chosen by the work's risk profile, not by file count.
- **Hard gates.** Lint, typecheck, and tests run as mechanical gates. No path through the loop lets the agent claim success on a red gate.
- **Cold-eyed review.** Three specialist reviewers — adversarial (spec/plan/impl drift), security (OWASP 2025 + ASVS + STRIDE), quality (testability, observability, reliability) — each read every diff in a fresh context with no sunk cost in the design. The loop iterates on findings until reviewers say `Clean — ready to commit.`
- **Progressive disclosure.** The security checklist pulls only the depth relevant to the boundaries a change crosses — current without bloating the prompt. Depth is added on demand per security boundary type (auth, secrets, user input, deserialization, file I/O, LLM code).
- **Capture what was learned.** Gaps in project conventions discovered during a run land as proposed `CONVENTIONS.md` edits — mistakes become the project's memory instead of evaporating between sessions.

**Two human approvals in full mode, and one at the exit.** Full mode runs the G-plan sequence: you approve the spec, then you approve the plan, before any implementation write. The merge decision at the end is yours too. Direct-light mode persists no spec and so has no approval pair. Beyond those gates the loop is autonomous: blockers surface to the human, and the agent routes concerns and nits by whether they're mechanical.

→ [Core pack guide](../../core/) · [The `core` pack as a system](../../core/explanation/core-pack.md)

## The release loop

**Pack:** `release-engineering` | **Agent:** `release-lead` | **Scope:** repo

The outer loop. Takes the locally built, deploy-ready artifact and validates it **deployed** — not as it runs on the developer's machine, but as it runs in an environment that resembles production.

**Key mechanics:**

- **Ephemeral environments only.** The outer loop never touches prod. It deploys to purpose-built ephemeral environments: no real user data, cannot reach production, isolated from each other, teardown on completion. The isolation guarantee is what makes unattended operation safe.
- **Minimum-regret autonomy carve.** Reversible operations (deploy to ephemeral, run e2e, observe telemetry, redeploy, teardown) run autonomously. Irreversible operations (first real users, data migrations, spend over threshold, the prod ship) always surface to a human.
- **Inner↔outer feedback seam.** When the outer loop surfaces a deployed failure, it feeds it back to `work-loop` as a build task — not a raw error message to the human. The inner loop fixes it; the outer loop redeploys. No human relay needed for build-level fixes.
- **Convergence by policy.** The loop iterates until: canary passes SLOs, changed-surface e2e coverage is met, flake rate is below threshold, and the error budget is not exhausted. When convergence is reached, it stops and surfaces a release-readiness record — not a bare go/no-go.
- **Release-readiness record.** The convergence output is a structured assessment: convergence result, operational verdict, security verdict, and cost/budget status. The human ratifies this at G5 — the only gate between convergence and the prod ship.

**Human gates:**
- **G5** — Ratify the prod ship. The only autonomous-to-irreversible transition. Never bypassed, never auto-advanced.

→ [Release loop guide](../../release-engineering/) · [The release loop explained](../../release-engineering/explanation/the-release-loop.md)

## The scope boundary

The scope model follows where the work happens:

- **Discovery runs at user scope.** Product shaping happens in document workspaces — Notion, Figma, presentation decks — not in a repo. `discovery-lead` ships its own specialist reviewer agents because it can't assume a `core` repo-scope install is present.
- **Build runs at repo scope.** Code lives in repos. `core` installs into the repo where the code is, and its reviewer agents are available to anything installed at repo scope in the same repo.
- **Release runs at repo scope.** The release loop runs in the same repo as the build loop, downstream of it. It hard-depends on `core` and reuses its reviewers — this is architecturally sound only because both are at repo scope in the same repo.

This makes G3 a scope boundary, not a fixed artifact conversion. A
feature-level intent may become one spec directly; an initiative or capability
may become an RFC, several child intents, or a delivery brief coordinating one
or more RFCs and specs. Repositories without Product Engineering can begin at
the same Core intent, delivery-brief, or spec owners.

## The autonomy model

Each loop enforces autonomy proportional to the reversibility of what it's doing:

| Tier | Operations | Autonomy |
| --- | --- | --- |
| Fully autonomous | Exploring product shapes; writing and running tests; deploying to ephemeral; iterating on build failures | Runs unattended |
| Surfaces to human | Blockers in the build loop; convergence reached in the release loop | Pauses and presents the situation |
| Requires human consent | G0, G1.5, G2, G3 (discovery); G5 (release) — all irreversible exits | Never proceeds without explicit ratification |

The G5 prod-ship gate is always in the "requires human consent" tier. There is no configuration, mode, or flag that removes it.

## Installing the operating model

Install all three loops in dependency order:

```bash
# 1. The build loop — always first; the other loops depend on it
agentbundle install --pack core

# 2. The discovery loop — at user scope (follows you across all repos)
agentbundle install --pack product-engineering --scope user

# 3. The release loop — at repo scope (into the same repo as core)
agentbundle install --pack release-engineering
```

Or install the `full-ceremony` profile to get `core` plus governance in one command, and add the others as your team adopts them.

Each loop is independent — install only what your team uses. Most teams start with `core` and add `product-engineering` when the product-shaping conversations start happening in Notion docs instead of GitHub issues.
