# Architecture

Current repository architecture. Decisions live in [ADRs](../adr/); proposals
live in [RFCs](../rfc/).

- [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) — system model and deeper links.
- [`overview.md`](overview.md) — directory map.
- [`catalogue/`](catalogue/README.md) — catalogue source and resolution, the
  derived catalogue `catalogue init --preset self-hosted` produces, and its
  state files.
- [`skill-and-pack-format.md`](skill-and-pack-format.md) — skill, pack, and projection formats.
- [`pack-layout.md`](pack-layout.md) — pack source layout.
- [`pack-manifest.md`](pack-manifest.md) — pack metadata projection.
- [`agentbundle.md`](agentbundle.md) — CLI, build, install, and adaptation.
- [`loop-infrastructure.md`](loop-infrastructure.md) — work-loop execution state and controls.
- [`loop-contract.md`](loop-contract.md) — the spec/plan pair the loop runs against: artifact ownership and item identity.
- [`work-intake-and-artifact-routing.md`](work-intake-and-artifact-routing.md) — intake, artifacts, and workspace routing.
- [`workspace-mcp/design.md`](workspace-mcp/design.md) — per-session workspace MCP service.
- [`verification-graph.md`](verification-graph.md) — measured facts: local gate graph, remote workflow fleet, required contexts, and platform classification.
- [`security.md`](security.md) — security-review posture.
- [`credentials.md`](credentials.md) — brokers, storage, and trust boundaries.
- [`knowledge-capture.md`](knowledge-capture.md) — capture, distillation, and enquiry.
- [`telemetry.md`](telemetry.md) — what a pack records about its own execution, and the export boundary.

Architecture docs are a living snapshot. Update them with layout or dependency
changes.

The bundle source-of-truth split lives in
[`pack-layout.md` § The source-of-truth split](pack-layout.md#the-source-of-truth-split).
This directory documents the projected adopter layout; the pack-side authoring
rules live with that split.

## Planned architecture

- **STATUS: PLANNED** — [Upstream sync](catalogue/upstream-sync.md) designs
  `agentbundle catalogue sync`, the path a derived catalogue takes upstream
  changes by.
- **STATUS: PLANNED** — [Binder publishing](binder-publishing/README.md) is
  designed but not implemented. [ADR-0073](../adr/0073-zensical-as-the-v1-binder-renderer.md)
  governs its renderer decision.
- **STATUS: § 2 IMPLEMENTED; §§ 1, 3 AND 4 PLANNED** — [Durable transitions and within-wave parallelism](loop-parallelism.md)
  ships the cohort-state identity check that serialises a transition commit
  against a concurrent cohort mutation (§ 2), and
  proposes a `pending_transition` replay marker generalising the shipped
  `amendment_pending` marker to every event that needs one,
  and treats serialising the wave-exit verdict and raising plan width as the two
  dependent changes behind concurrent execution. It introduces one unified
  transition history and a `schema_version` bump that refuses in-flight state.
  § 4 specifies the read-only wave decision contract: a JSON verdict naming,
  per wave, which tasks are candidates for concurrent dispatch, with a coded
  reason for every refusal and the colliding peer and glob where one exists.
  [ADR-0061](../adr/0061-loop-infrastructure-phase-1.md) D8 defers the schema,
  and D5 defers parallel-wave orchestration — it is D5's *Revisit if* clause,
  not D5 itself, that names the bounded round cap.
- **STATUS: PLANNED** — [Agent skill engineering](agent-skill-engineering.md)
  describes the portable workflow, compiled knowledge-provider, runtime-profile,
  and self-host migration architecture accepted by
  [RFC-0097](../rfc/0097-agent-skill-engineering.md).

## What belongs here

How the code is *currently* organized. Not why — that is a decision record; not
what we want — that is a proposal. What is.

`overview.md` is the map: what lives where, and how the parts relate. One file
per non-trivial subsystem describes its structure and entry points, and links to
the decisions that explain why it took that shape.

This directory holds current state. A designed-but-unbuilt subtree is admitted
only when its index carries a `STATUS: PLANNED` marker and links to the decision
governing it.

When a page carries a `Last verified against commit` marker, it records a
deliberate whole-page re-verification against that commit, not merely an edit.
Update it only after re-reading the whole page against the tree at that commit.
An unchanged marker means the page has not had that audit; it is provenance, not
a freshness requirement.

Decision records accumulate, and reconstructing current state from them means
reading every one in order. This directory is the rolled-up snapshot instead.
