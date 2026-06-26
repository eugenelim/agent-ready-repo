# The three loops, the e2e/minimum-regret carve, and the company OS of agents

## Three loops = three company functions

| Loop | Company function | Controller | Loop-scoped agents | Verifier | Autonomy |
| --- | --- | --- | --- | --- | --- |
| **discovery-loop** (shape · upstream) | Product org | `discovery-lead` (product-engineering) | lens-team: research/analyst · product · UX/design · architecture · **security/compliance (design-time)** | none — human-ratified | gated at G0 / G1.5 / G2 |
| **work-loop** (build · **inner loop**) | Engineering | work-loop supervisor | `implementer` (fan-out); reviewers `adversarial-reviewer` · `security-reviewer` (code) · `quality-engineer` | local tests / lint / types + local-infra-equivalents | high — G4 auto |
| **release-loop** (deploy + e2e · **outer loop**) *(new; name provisional, alt `e2e-loop`)* | SRE / ops / QA | `release-lead` (new; provisional) | deploy/e2e driver + observability/reliability lens (`operational-safety` + `quality-engineer`) | deployed telemetry · e2e on ephemeral · canary analysis | high **on ephemeral**; human at prod (G5) |

**The chain:** discovery-loop → (G3 brief→spec) → work-loop (inner; local with
stubs/mocks/local-infra-equivalents) → release-loop (outer; ephemeral deploy + e2e +
observe → findings → back to work-loop → gate → redeploy → **until converge**) → (G5) prod
ship. It mirrors a real company: **product org → engineering → SRE/ops**, each a team with
a lead + specialists, coordinated via the blackboard, execs (humans) at the irreversible
decisions.

## The inner loop (work-loop) — local-infra-equivalents

Fidelity ladder (run as high as a sub-5-min inner-loop budget tolerates; push the rest to
the outer loop): in-process **fakes/mocks** → **consumer-driven contract tests (Pact)** →
**Testcontainers** (real Postgres/Kafka/Redis in-process) → **LocalStack** (AWS API
emulation) → **docker-compose** full-stack. *Packs/skills must produce these equivalents as
part of building* — the build loop is only autonomous because the software runs and
verifies locally without the real deployed infra.

## The outer loop (release-loop) — shift-right, made low-regret

Some findings only appear deployed (~20%, Charity Majors): real traffic, infra drift,
version combinations, emergent behavior. The outer loop exists to surface them. It's
**observability-driven** — instrument every iteration so a deployed finding is
self-explanatory to the agent (no human relay). Cycle: deploy to **ephemeral env** → run
e2e → read telemetry → fix (back to inner loop) → redeploy → converge.

**Convergence (promote):** canary metric analysis passes (success/error/latency SLOs) +
e2e covers the changed surface + flake < 2% — judged by **policy**, not a human, up to the
irreversible gate. **DORA** (deploy freq, lead time, change-fail, MTTR; + 2025 rework rate)
is the health signal.

## The minimum-regret autonomy carve

**Agent runs unwatched** (the reversibility zone):
- inner loop — local build / contract / Testcontainers / LocalStack tests;
- outer loop on **ephemeral environments** — deploy, e2e, observe, iterate, teardown;
- **canary in non-prod tiers** with metric-gated **auto-rollback**.

**Human surfaces** (the irreversible / high-stakes zone):
- first promotion to **real users or real data**;
- **data migrations** (schema / destructive);
- **spend** over a pre-agreed threshold;
- **security / auth-boundary** changes;
- anything **irreversible beyond MTTR**; and the **prod ship** (G5).

**The unlock:** reversibility primitives — **ephemeral environments + feature flags +
auto-rollback** — turn deploy from one-way-door into a two-way door, which is what lets the
outer loop run autonomously. The carve is the autonomy law applied to deploy: *autonomous
where reversible, human where not.*

## The company OS — shared substrate

All three loops run on one substrate (the catalogue ships it as doctrine; the harness runs it):
- **sidecar** — blackboard · open-questions · traceability · decision-log (core schema);
- **gate ladder + surfacing predicate** — G0 · G1 · G1.5 · G2 · G3 · G4 (inner) · **release (outer)** · G5;
- **self-coverage gate** — incl. the resolve-vs-surface lens + scenario-variation;
- **harness** — omnigent (runner/server, ephemeral envs, option-card consent UI), harness-neutral.

So the "company OS of agents" = **three loop-teams (product / engineering / ops) + their
leads, on a shared blackboard, gated by the surfacing predicate, with humans at value,
conflict, and irreversible decisions.** Each loop is loop-scoped (its own roster, its own
verifier, its own autonomy posture); the leads hand off (discovery→work at G3, work→
release at deploy, release→prod at G5).

## Open / provisional
- Names `release-loop` / `release-lead` are provisional (alt `e2e-loop`) — taste call.
- Whether the outer loop needs a *distinct* `release-lead` agent vs. an outer-mode of
  work-loop's supervisor is a child-RFC design call; lean distinct (the inner/outer split
  is real), but it heavily reuses `operational-safety` + `quality-engineer` + RFC-0041's
  infra doctrine — not a new agent zoo.
- This refines/extends RFC-0041 (Accepted): its deploy "flavor" graduates into the outer loop.
