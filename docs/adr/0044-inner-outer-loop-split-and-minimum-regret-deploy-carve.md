# ADR-0044: Split the build loop from a deployed-validation outer loop, and carve deploy autonomy by minimum-regret

- **Status:** Accepted
- **Date:** 2026-06-30
- **Decision-makers:** eugenelim
- **Consulted:** RFC-0049 (parent), RFC-0048 (foundation), RFC-0041 (infra-aware work-loop), the release-loop spec + its spec-stage adversarial and security reviews
- **Supersedes:** none
- **Related:** [RFC-0049](../rfc/0049-the-release-loop-and-company-os.md) · [RFC-0048](../rfc/0048-autonomous-product-team-operating-model.md) · [RFC-0041](../rfc/0041-infra-aware-work-loop.md) · [ADR-0031](0031-infra-support-is-doctrine-on-existing-reviewers-not-a-new-reviewer-or-runtime.md) · [ADR-0043](0043-the-discovery-coordinator-is-an-agent-plus-skill-plus-carried-sidecar-no-engine.md) · [release-loop spec](../specs/release-loop/spec.md)

## Decision summary

- **Decision:** We split the operating model into an **inner loop** (`work-loop` —
  local build + verification) and a **deployed-validation outer loop**
  (`release-loop` — ephemeral deploy + e2e + iterate-to-converge), and carve deploy
  autonomy by **minimum-regret**: reversible (ephemeral) ⇒ autonomous; irreversible
  (prod / data / spend / security) ⇒ human.
- **Because:** a deployed, integrated system surfaces failures no pre-deploy
  testing replicates, and only the inner/outer split lets an agent iterate the
  *deployed* whole to convergence without a human relaying findings — while
  ephemeral-env reversibility is what makes that autonomy low-regret.
- **Applies to:** the company-OS gate arc from G4 (build done) to G5 (human prod
  ship); the `release-engineering` pack; not the inner loop's local-build contract
  and not the live-service operate/incident loop (a future sibling RFC).
- **Tradeoff accepted:** the outer loop requires real adopter infrastructure
  (ephemeral envs + reversibility primitives) the inner loop does not, so the
  capability is opt-in, not a `core` default.
- **Revisit if:** ephemeral-env reversibility stops holding as the autonomy
  predicate (e.g. envs cannot be proven isolated cheaply), or a harness emerges
  that makes prod deploy itself cleanly reversible — either would move the
  agent/human line the carve draws.

## Context

RFC-0048 takes the catalogue from product vision to **locally-built,
deploy-ready code** (G0–G4). But two things remain. First, the inner loop is only
autonomous if the software *runs locally* without real deployed infra — an
inner-loop obligation (local-infra-equivalents), separate from this decision.
Second, and the subject here: a deployed, integrated, distributed system surfaces
failures that **no pre-deploy testing replicates** (the irreducible shift-right —
real traffic, infra drift, version combinations, emergent behavior). RFC-0041 made
`work-loop` infra-aware but kept deploy as a *flavor* of the inner loop — no
ephemeral-env outer loop, no iterate-until-converge — so a human became the relay
for deployed findings, the very anti-pattern RFC-0041 named.

The question RFC-0049 put: **how far into deploy + e2e can an agent go
autonomously, with minimum regret?** The answer rests on a reversibility claim —
ephemeral environments, feature flags, and auto-rollback turn deploy from a
one-way door into a two-way door — which is the same logic RFC-0048 already uses
for tests-as-verifier, applied to deploy.

## Decision

1. **The inner/outer split.** `work-loop` is the **inner loop** (local build +
   verification via the fidelity ladder). A new `release-loop`, run by a distinct
   `release-lead` agent, is the **outer loop**: deploy the integrated whole to an
   **ephemeral environment** → run e2e → observe telemetry → feed findings back to
   the inner loop → redeploy → **converge** → assemble a release-readiness record →
   **G5** human ship. `release-lead` is a **peer** of `work-loop`'s supervisor and
   `discovery-lead`, not a `work-loop` mode — different inputs, verifiers, and
   autonomy postures.

2. **The minimum-regret carve.** The agent runs the inner loop **and** the outer
   loop **on ephemeral envs** unwatched; the human is present only at the
   **irreversible exits** — first real users or data, data migrations, spend over a
   pre-agreed threshold, security/auth-boundary changes, anything irreversible
   beyond MTTR, and the prod ship (G5). "Reversible" is **conditioned on env
   isolation**: a deploy target that cannot be proven isolated is itself a
   consent-gate crossing.

3. **Convergence by policy.** Promotion up to the human gate is judged by
   **automated policy** — canary metric analysis + e2e coverage of the changed
   surface + flake < 2% — not by a human; **DORA** is the health signal, not a
   per-promotion gate.

4. **Reuse, not rebuild (the ADR-0031 idiom).** The outer loop reuses `core`'s
   `operational-safety` modules (via `quality-engineer`, orchestrator-inlined per
   ADR-0018) + `security-reviewer`, and consumes the RFC-0053 discovery sidecar by
   convention. It ships **no new runtime engine** and **no new reviewer agent** —
   every transition is a file edit plus a policy check.

## Decision drivers

- **Shift-right is irreducible** — some failure classes appear only in a deployed,
  integrated environment, so an outer loop is necessary, not gold-plating.
- **Reversibility unlocks autonomy** — ephemeral envs + flags + auto-rollback make
  the outer loop low-regret, so the agent can run it unwatched up to the
  irreversible line.
- **No-relay** — the agent reads the real environment output itself; a human
  relaying deploy errors is the RFC-0041 anti-pattern this removes.
- **Reuse-not-rebuild** — the company-OS substrate already carries the reviewers,
  the sidecar, and the harness; a new seat is content + doctrine, not a runtime.

## Consequences

- **Positive:** the autonomous product team is complete end-to-end on one
  substrate (discovery → build → release); deployed findings converge without a
  human relay; the irreversible line is explicit and credential-enforced.
- **Negative / tradeoff:** the outer loop is an opt-in capability with a real
  adopter prerequisite (ephemeral-env infra + reversibility primitives), so it is
  not a `core` default; fidelity gaps mean some findings appear *only* in the
  outer loop (which is *why* it exists).
- **Revisit if:** ephemeral-env reversibility stops being the cheap, provable
  autonomy predicate, or prod deploy itself becomes cleanly reversible under a new
  harness — either moves the agent/human line.

## Confirmation

The carve and the split are realized as **`release-loop` skill doctrine + the
`release-lead` agent** (not a CONVENTIONS edit — RFC-0048 § Amendments
2026-06-29), verified by the release-loop spec's acceptance criteria: the
inner/outer split and peer-not-mode framing (AC1), the two carve zones (AC3/AC4),
convergence-by-policy (AC6), the reuse-no-engine posture (AC9), the security &
integrity controls (AC10), and the no-engine worked-example trace (AC12). The
expensive-to-reverse part — deploy-to-prod autonomy doctrine on a security +
irreversibility boundary — is what warrants recording it as an ADR rather than
leaving it implicit in the skill.

## Alternatives considered

- **Do nothing (stop at G4).** Humans relay deployed findings — the RFC-0041 relay
  anti-pattern. Rejected.
- **Deploy as a flavor inside `work-loop` (RFC-0041 as-is).** Conflates fast/local
  with slow/stateful/deployed; no ephemeral-env iterate-until-converge.
  Insufficient — this ADR graduates that flavor into a proper outer loop.
- **Full autonomous prod deploy.** The agent ships to prod unwatched. Crosses the
  irreversible line; violates the minimum-regret carve. Rejected.
