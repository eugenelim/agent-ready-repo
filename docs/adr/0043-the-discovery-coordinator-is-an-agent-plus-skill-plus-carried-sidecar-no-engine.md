# ADR-0043: The upstream discovery coordinator is an agent + a skill + a carried sidecar-schema contract — no new runtime engine, spike-confirmed; the sidecar is the connectedness verifier

- **Status:** Accepted
- **Date:** 2026-06-30
- **Decision-makers:** eugenelim
- **Consulted:** RFC-0053 (the accepted decision this records) and its Decision-7 spike (`docs/rfc/0053-notes/spike/` — the worked example walked G0→G2 as one reasoning context, with the connectedness lint as the only executable); the spec-stage adversarial + secure-design review of RFC-0053 and the `discovery-loop` implementing spec
- **Supersedes:** none
- **Related:** RFC-0053 (the discovery loop — the decision this records); RFC-0041 + ADR-0031 (the doctrine + reference-library + reuse, no-engine idiom this applies one altitude up — the sibling ADR this mirrors); RFC-0048 (the operating model this is child 5 of; D7/D8 spike-confirmed); RFC-0049 (the sibling downstream release-loop coordinator, whose coordinator ADR is the third member of this family); RFC-0051 (the self-coverage gate `discovery-loop` is the full-battery home of); ADR-0042 (reviewer additions keyed to loop + work type — the policy under which the loop-scoped discovery roster is admitted; the CHARTER reviewer ceiling stays a `work-loop`/code-review cap); ADR-0030 / RFC-0040 (the three-tier layout the sidecar paths obey); ADR-0022 (the cross-repo reference-by-version the stable-id traceability reuses)

## Decision summary

- **Decision:** ship the upstream product-discovery coordinator as **content** — a `discovery-lead` **agent** + a `discovery-loop` **skill** + a **carried, versioned sidecar-schema contract** (in the skill, not `core`) — with **no new runtime engine, scheduler, service, message bus, or convergence solver**.
- **Because:** a spike confirmed the loop runs as one reasoning context editing plain typed files plus a ~60-line connectedness lint; the harness an adopter already runs is the runtime. Shipping content is not shipping software (CHARTER Principle 3).
- **Applies to:** the `product-engineering` pack's discovery capability and every downstream consumer that reads the produced sidecar instances (the traceability lint, `work-loop`, the release loop).
- **Tradeoff accepted:** the controller scheduling the recursive walk in-context is a **bet on a shallow tree**, gated by depth/breadth bounds; scheduling many concurrent/parked threads stays the harness's job.
- **Revisit if:** a real recursive walk shows in-context scheduling does not hold at depth, or an adopter harness cannot supply the agent-untokened verdict channel the security contract requires.

## Context

RFC-0048's operating model needs an **upstream** loop that turns a raw idea into a build-ready brief — the peer of `work-loop`'s downstream spec→build loop. The open question (D7/D8) was *how much machinery* to ship: a from-scratch coordinator runtime (an engine that schedules lenses, solves convergence, and drives a state machine), or content the existing harness runs.

The Decision-7 spike walked the worked example G0→G2 as **one reasoning context**, with the two named failure modes (over-scope; an unbacked security-sensitive screen) deliberately injected. Every transition was a **file edit plus, at most, the connectedness lint**. The riskiest assumption — that orchestrating the loop needs a runtime engine — was **refuted**. The recursion pressure-test (does a nested plan-tree force a state-machine engine?) found research *strengthens* the no-engine claim: Hierarchical-Task-Network planning over a blackboard is a plan tree held as **data**, walked by one controller — the opposite choice (a nested finite-state machine) is what fails to scale.

This ADR records the load-bearing, expensive-to-reverse calls — the **form**, the **home**, and the **no-engine line** — so a future maintainer does not re-litigate them. The mechanical detail (the slot field-sets, the gate state machine, the verdict set, the security ACs) is spec-level and lives in the `discovery-loop` implementing spec and the carried schema reference, not here.

Constraints in force when deciding:

- **Principle 3 (a habit, not infrastructure).** The repo ships doctrine and prose the agent reasons from, never a runtime engine, daemon, scheduler, or wrapper. This is the bar that put browser-bridge out of charter.
- **Principle 2 (no duplication).** The sidecar schema lives in exactly one place; no parallel `core` copy and no duplicated prose in `work-loop`.
- **Principle 1 (universal / portable).** The contract is harness-neutral — it must run in whatever harness the adopter uses, including a non-repo store (an Obsidian vault), which is why the schema is carried in the producer pack, not repo-scope `core`.
- **The reviewer ceiling (ADR-0042, superseding ADR-0023).** Agent additions are keyed to loop + work type; the discovery roster is loop-scoped and admitted under that policy, while the core code-review ceiling stays three lenses.

## Decision

> We will ship the upstream discovery coordinator as **content — a `discovery-lead` agent + a `discovery-loop` skill + a carried, versioned sidecar-schema contract — never a runtime engine**, with the typed sidecar as the **connectedness verifier**.

Three sub-decisions, each expensive to reverse:

- **Form & home — agent + skill + carried schema, in `product-engineering`.** `discovery-lead` is an agent definition (the upstream supervisor, a *peer* of `work-loop`'s supervisor — they hand off at G3); `discovery-loop` is the skill carrying the gate state machine, the verdict set, the bounds, the topology, the security controls, and the loop-skill doctrine. The **sidecar schema definition** is a `references/` file carried in `discovery-loop` (the single source of truth), and the **plan-tree** is a carried `assets/` template. This is the ADR-0031 / RFC-0041 idiom — doctrine + reference library + reuse, no new runtime — applied one altitude up.
- **No engine — recursion is data, bounds are counters, verdicts are status edits.** Recursion is `parent_id` nesting walked depth-first by one controller (HTN-over-blackboard, not a nested FSM); the outer cap + cost budget are data counters the controller increments; the typed verdict set is status edits plus a recorded decision-log row. No scheduler, solver, or message bus is ever introduced. **Honest bet:** the controller choosing the next node *is* a form of in-context scheduling the single solo spike did not evidence at depth — so the no-engine win is a defensible bet on a shallow tree, gated by depth/breadth bounds; scheduling many concurrent/parked threads across initiatives stays the harness's job.
- **The sidecar is the connectedness verifier, read by convention — consumers never import the definition.** The prototype's checker read the traceability + open-questions slots and reported orphans pre-recovery and CONVERGED after — connectedness is checkable in ~60 lines, no engine. Every produced instance carries a `schema_version` stamp; downstream consumers (the traceability lint, `work-loop`, the release loop, the self-coverage gate) read the produced `_state/` instances **by slot-name + the stamp**, never importing the definition. A schema bump moves the definition + its producing skill atomically.

Boundaries on the decision:

- **`core` is not bumped for the schema** — it no longer carries it (RFC-0048 § Amendments 2026-06-26). The schema lives in `product-engineering`'s `discovery-loop` skill.
- **The mesh / inter-loop scheduling layer is out of scope** — this contract ships the **stable-id substrate** a company-OS mesh would consume (briefs / `contract@version` ids / backlogs), not the mesh; that is the harness's / platform's (Principle 3).
- **Running validation activities is out of charter** — `plan-validation` scaffolds the instruments and synthesizes transcripts; a human runs the interviews/pilots.

## Decision drivers

- **The spike refuted the engine.** The headline assumption (a coordinator needs a runtime) did not survive the worked example; the cheap content shape is also the *evidenced* one.
- **Portability.** The owning pack is user-scope and must run outside a code repo, so the schema cannot be single-sourced in repo-scope `core`.
- **Charter Principle 3.** A coordinator runtime is exactly the kind of infrastructure the repo declines to ship.
- **Single-owner anti-drift.** A carried, version-stamped, convention-read schema gives one source of truth without cross-pack import coupling — the would-be writers span several packs, so co-location cannot be the guarantee.

## Consequences

**Positive:**

- The capability ships as content runnable by whatever harness an adopter already uses; no engine to build, host, or maintain.
- The sidecar is both the working surface *and* the auditable record (the decision log doubles as an audit trail), and the connectedness lint is a real, cheap conformance check.
- The two-loop split stays honest — discovery and delivery have different inputs, verifiers, and autonomy postures, and meet only at G3.

**Negative:**

- In-context scheduling of a recursive walk is unproven at depth; a deep or wide tree may strain the single controller before the bounds catch it.
- The security contract leans on a **harness-conformance precondition** (an agent-untokened verdict channel + a durable, history-rewrite-protected checkpoint store); an adopter whose harness cannot supply these cannot run the loop unattended safely.
- The schema is carried, not a `contracts/` REST/event surface, so consumers must honor the read-by-convention rule rather than a compiler-checked import.

**Revisit if:** a real recursive (≥2-level) walk shows in-context scheduling does not hold at depth (then the harness must own sub-walk scheduling sooner), or a harness cannot provide the agent-untokened verdict channel (then the unattended posture must change).

## Confirmation

- **Mode:** reviewer-checked + lint/CI.
- **Signal:** the `discovery-loop` implementing spec's validation run forces the cap-pause + the security negative paths on a recursive tree and records the traceability lint's orphan→CONVERGED transition; the traceability lint asserts sidecar conformance (`schema_version` + nodes/edges) on produced instances; the no-engine line is an explicit absence-grep in the implementing spec's tests (no scheduler/daemon/service/bus/solver in the diff).
- **Owner:** the `product-engineering` pack maintainer.

## Alternatives considered

- **A from-scratch coordinator runtime / engine (Option C).** Rejected — Principle 3 forbids the harness, and the spike refuted the need: every transition was a file edit plus a lint. An engine would also re-create the "one big coupled state" anti-pattern the per-initiative forest avoids.
- **Fold the coordinator into `work-loop` (one mega-loop for discovery + build).** Rejected — it conflates two loops with different inputs, verifiers, and autonomy postures (the upstream has no local verifier; the downstream does), and is un-right-sizable (RFC-0048 D8's "must not be conflated").
- **Single-source the schema in `core`.** Rejected — `core` is repo-scope, and the owning pack must run portably (non-repo stores); the schema is carried in the producer skill, read by convention downstream (RFC-0048 § Amendments 2026-06-26).

## References

- [RFC-0053 — the discovery loop](../rfc/0053-the-discovery-loop.md) (the decision this records; the Decision-7 spike in `0053-notes/spike/`).
- [RFC-0041](../rfc/0041-infra-aware-work-loop.md) + [ADR-0031](0031-infra-support-is-doctrine-on-existing-reviewers-not-a-new-reviewer-or-runtime.md) — the no-engine doctrine + reference-library idiom this mirrors.
- [RFC-0048 — the autonomous product-team operating model](../rfc/0048-autonomous-product-team-operating-model.md) (D7/D8 spike-confirmed; the loop-scoped reviewer roster).
- [ADR-0042](0042-agent-additions-keyed-to-loop-and-work-type.md) — the policy admitting the loop-scoped discovery roster.
- The `discovery-loop` implementing spec — `docs/specs/discovery-loop/`.
