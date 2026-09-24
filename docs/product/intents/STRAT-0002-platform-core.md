# Platform Core

- **Slug:** `platform-core` <!-- canonical identity; independent of the filename ordinal -->
- **Kind:** opportunity <!-- chain rung: the need this strategy addresses on the opportunity-solution tree; orthogonal to Level -->
- **Status:** Fulfilled
- **Accepted:** 2026-09-24 by eugenelim, on an owner waiver rather than an independent shaping review. This strategy was delivered before the recursive intent tree existed, so it never passed `Draft` → `Accepted` and no review could have been recorded against a gate that post-dates it. What the gate exists to establish is nonetheless on the artifact: `## Decomposition` states the partition is closed with no child intents expected and gives the reason, and `### Fulfilment evidence` carries an independent per-action verdict. The owner ratified it directly and waived the intent-mode review, for this one-off migration only. Basis: `docs/specs/lifecycle-transition-contract/notes/migration-record.md`.
- **Fulfilled:** 2026-09-19 by eugenelim, on an independent fulfilment verification against the repository rather than against this artifact's own account of its delivery.
- **Level:** product-strategy
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** outcome:ai-native-ecosystem
- **Decomposed:** no

> **Fulfilled — outcome achieved, verified independently on 2026-09-19.** A separate worker checked the outcome and guardrails against the repository rather than against this body's account of its own delivery, and returned `VERDICT: ACHIEVED`. Achievement was judged on whether the **capabilities exist**, not on whether delivery matched the stated plan — so the one coherent action since superseded in mechanism, the committed work queue, did not count against it.

### Fulfilment evidence

| Coherent action | Verdict | Evidence |
| --- | --- | --- |
| The three loops | **HELD** | Installable skills and supervisors exist in `packs/product-engineering/.apm/skills/discovery-loop/`, `packs/core/.apm/skills/work-loop/`, `packs/release-engineering/.apm/skills/release-loop/`, with supervising agents in `packs/core/.apm/agents/` and `packs/product-engineering/.apm/agents/`. |
| The multi-pack catalogue | **HELD** | `packs/README.md` defines installable packs, distinct manifests exist at `packs/core/pack.toml`, `packs/product-engineering/pack.toml`, and `packs/governance-extras/pack.toml`, while `packages/agentbundle/agentbundle/commands/install.py` and `packages/agentbundle/tests/integration/test_multi_pack_install.py` implement and exercise composition. |
| The shaping room | **HELD** | `packs/product-engineering/.apm/skills/` contains the six-step sequence from `frame-situation` through `map-capabilities`, while `frame-intent` and `decompose-intent` support multiple and recursively lower altitudes. |
| The governance machinery | **HELD** | The live `docs/adr/`, `docs/rfc/`, and `docs/specs/` corpora are governed by spec-status, ADR-shape, record-index, ordinal, brief-coverage, and traceability gates registered in `tools/repo/build_gate_chain.py`. |
| The declared-intent work queue | **HELD** | `workspace.toml` carries shaping, brief, and work queues with lifecycle collections and inline `needs`, and `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` parses and reconciles them programmatically. |
| The guardrails | **HELD** | `packages/agentbundle/agentbundle/_data/adapter.toml` projects skills across Claude Code, Codex, Copilot, Cursor, Gemini, and Kiro, `packs/release-engineering/.apm/skills/release-loop/SKILL.md` requires no service or engine, and `packs/core/.apm/skills/work-loop/SKILL.md` preserves mechanical gates and the human merge decision. |

**Verifier's stated confidence.** High confidence: I directly inspected the pack sources, manifests, installer and integration tests, queue data and parser, governance corpora and gate chain, and multi-host adapter contract. I did not execute test suites because the permitted command set excluded the repository’s test runner.

The superseded mechanism is recorded under Succession below and does not qualify this verdict: [Graph-powered SDLC](STRAT-0001-graph-powered-sdlc.md) replaces the work queue's answer while the outcome it served stands.

## Outcome

- **Steerable input:** How much of its operating model a team has to invent for itself before it can deliver.
- **Lagging outcome:** An engineering layer carries work from raw idea to deploy-ready change without first inventing the process to do it, and that process survives the people and sessions that ran it.
- **Guardrail:** No team is locked into a tracker, harness, runtime or CI system to participate, and nothing requires a service to run. Rigour is not traded for speed: the gates that catch something stay, and human merge authority is untouched.

## Opportunity

- **Functional job:** Know, at the start of any session, what this repository intends, what is queued, what is running and what to pick up.
- **Emotional job:** Stop re-establishing context that was established last week and evaporated with the session.
- **Social job:** Show a team that coordination is declared and inspectable rather than carried in one person's head.
- **Struggling moment:** The loops can run a spec end to end, but there is nothing above the spec. Strategic context lives in session logs that expire, and no structured mechanism exists to queue what is shaped, what is ready, and what is running.

## Product-strategy fields

- **Central challenge (diagnosis):** Models are capable enough to do sustained engineering work, but every team invents its own operating model around them — its own loops, its own review discipline, its own coordination — and that model lives in people's heads and dies at the session boundary.
- **Guiding policy:** Ship the operating model as something a team installs: a multi-pack catalogue of loops, skills and coordination, delivered as doctrine and portable markdown rather than as a runtime, committed to the repository and locked to no tool.
- **Coherent actions:** The **three loops** — discovery (raw idea to ratified brief), work (spec to verified change), release (verified to shipped). The **multi-pack catalogue** and its core, product-engineering and governance packs. The **shaping room**, applying six-step product thinking at each altitude. The **governance machinery** of ADRs, RFCs and specs with traceability. And the **work queue**: a standard tracker-mappable vocabulary, a three-queue split, an explicit lifecycle status, an inline dependency model, and a git pattern updating coordination in the same diff.
- **Problem / segment sequence:** This repository first, as the only corpus able to falsify the design, then adopters seeded from their own RFC or roadmap.
- **Horizon:** Delivered. M1–M5 shipped; the remaining milestone is adoption rather than construction.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this strategy and for its closure.

## Unresolved questions

- Whether a vocabulary maps to every major tracker without adopting any tracker's hierarchy. Untested, and inherited by `STRAT-0001`.
- Adoptability was never settled: delivery proved the loops buildable, not that a team with its own habits adopts them.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Boundary

Includes the installable operating model for the engineering layer: the three loops, the multi-pack catalogue, the shaping room, the governance machinery, and the declared-intent work queue above the spec.

Excludes the **model** of work that the loops act on, which is [Graph-powered SDLC](STRAT-0001-graph-powered-sdlc.md)'s: this strategy owns the loops and the machinery, that one owns the graph they read and write. Excludes the non-engineering layers ([Autonomous product-team operating model](STRAT-0003-autonomous-product-team-operating-model.md)) and distribution ([Trustworthy organisation-owned catalogues](STRAT-0004-trustworthy-org-owned-catalogues.md)). RFC-0064 is **one milestone delivery within this strategy**, not its whole charter — the ecosystem overview records it as such — so this strategy's scope is not bounded by that RFC's goals.

## Succession

[Graph-powered SDLC](STRAT-0001-graph-powered-sdlc.md) inherits the work queue's diagnosis and replaces its answer. The other coherent actions are unaffected. The coordination artifact this strategy chose is a single committed file, now 1,626 lines, holding 135 entries for this strategy alone and conflicting on 20 of 51 rebases that had to replay an edit to it over 30 days. The successor derives the same answers from artifact headers on demand and persists nothing, and [Workspace coordination reorganization](CAP-0003-workspace-coordination-reorganization.md) carries the migration.

Two of this strategy's coherent actions are being retired rather than inherited: shaping artifacts in a dedicated folder, and the initiative-keyed queue as an ownership boundary. [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md) records the second, and [Single-ladder migration](FEAT-0004-single-ladder-migration.md) carries both.

## Decomposition

Closed. This strategy decomposed into delivery rather than into child intents: its coherent actions were carried by milestone deliveries and closed as specs under the `ini-002` queue, 108 of them Shipped. It predates the recursive intent tree, so it has no child intents and none is expected.

The two actions that are **not** closed are being retired rather than delivered, and are carried by other intents: shaping artifacts in a dedicated folder and the initiative-keyed queue as an ownership boundary both belong to [Single-ladder migration](FEAT-0004-single-ladder-migration.md). Its successor's work is [Graph-powered SDLC](STRAT-0001-graph-powered-sdlc.md)'s, not a continuation of this one.

### Decomposition decisions

- **The partition is closed, not empty.** A strategy delivered before the intent tree existed has its decomposition in shipped specs. Recording no children is the accurate state; inventing child intents retrospectively would fabricate a tree that never existed and imply work that is not coming.
- **Accretion under this strategy's queue is not its decomposition.** 135 entries accumulated in `ini-002`, of which roughly 15% match this charter. The rest arrived because a delivered strategy's queue becomes the default home for work needing one, and they re-home through the migration rather than defining this strategy retrospectively.

## Riskiest assumption

**An operating model can be installed rather than invented, and a team that already has its own will adopt it.**

This is the bet the whole strategy rests on: every coherent action below assumes a team will take a shipped loop over its own habit. If it is wrong, the packs are a reference implementation nobody runs rather than a platform.

It is the one assumption that delivery did **not** settle. The loops, packs and shaping room are demonstrably usable — this repository runs on them — but self-hosting tests buildability, not adoptability. The repository's own adopter research points the other way: installation friction inside a short activation window is named as the binding constraint for the solo-engineer segment, and self-service deployments reach roughly a fifth of the automation that specialist-mediated ones do.

## Assumptions

- The riskiest assumption above. **Unsettled by delivery** — buildability is demonstrated, adoptability is not.
- A vocabulary can map to every major tracker without adopting any tracker's hierarchy. **Untested** at adopter scale.
- **Knowledge surface:** in-repo doc set. The strategy's scope is taken from the INI-002 description in [`ecosystem-overview.md`](../shaping/ecosystem-overview.md); the work-queue action's diagnosis and seven decisions come from [RFC-0064](../../rfc/0064-ini-001-ai-native-ecosystem.md), one milestone delivery within it.

**Not de-risked as an intent.** Its bets were taken and largely settled by delivery rather than by a predeclared test, and one is refuted by later measurement. Re-enter `de-risk-intent` only if it is reopened rather than closed.

The single-coordination-file assumption is no longer listed here. It was refuted by measurement, and **Succession** owns that record and the successor it hands the diagnosis to.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/rfc/0064-ini-001-ai-native-ecosystem.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Extracted 2026-09-18 from [`docs/rfc/0064-ini-001-ai-native-ecosystem.md`](../../rfc/0064-ini-001-ai-native-ecosystem.md), which is one milestone delivery inside this strategy rather than its charter, and from the delivered `ini-002` queue.
