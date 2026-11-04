# Architecture

Current repository architecture. Decisions live in [ADRs](../adr/); proposals
live in [RFCs](../rfc/).

- [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) — system model and deeper links.
- [`overview.md`](overview.md) — directory map.
- [`catalogue/`](catalogue/README.md) — catalogue source and resolution, the
  derived catalogue `catalogue init --preset self-hosted` produces, its state
  files, and the published [specification](catalogue/specification.md).
- [`distribution-routes.md`](distribution-routes.md) — the declared routes, build dispatch, and Claude and Agent Plugin publication.
- [`skill-and-pack-format.md`](skill-and-pack-format.md) — skill, pack, and projection formats.
- [`pack-layout.md`](pack-layout.md) — pack source layout.
- [`pack-manifest.md`](pack-manifest.md) — pack metadata projection.
- [`agentbundle.md`](agentbundle.md) — CLI, build, install, and adaptation.
- [`lifecycle-flow.md`](lifecycle-flow.md) — how work moves across the packs from idea to production, and its public projections.
- [`loop-infrastructure.md`](loop-infrastructure.md) — work-loop execution state and controls.
- [`work-loop-execution-supervisor.md`](work-loop-execution-supervisor.md) — the supervisor that owns full-mode procedure.
- [`work-loop-product-ref.md`](work-loop-product-ref.md) — the protected product ref and history-adoption classification.
- [`work-loop-plan-changes.md`](work-loop-plan-changes.md) — the replanning envelope and the TDD guard.
- [`work-loop-supervisor-stages.md`](work-loop-supervisor-stages.md) — how request kinds map to `run.json` stages and event-line stages.
- [`loop-contract.md`](loop-contract.md) — the spec/plan pair the loop runs against: artifact ownership and item identity.
- [`work-intake-and-artifact-routing.md`](work-intake-and-artifact-routing.md) — intake, artifacts, and workspace routing.
- [`workspace-mcp/design.md`](workspace-mcp/design.md) — per-session workspace MCP service.
- [`verification-graph.md`](verification-graph.md) — measured facts: local gate graph, remote workflow fleet, required contexts, and platform classification.
- [`security.md`](security.md) — security-review posture.
- [`runtime-security-primitives.md`](runtime-security-primitives.md) — the confinement libraries, trust boundaries, and supervisor attempt controls.
- [`delivery-content-safety.md`](delivery-content-safety.md) — the content-safety policy, profiles, and writer boundaries for delivery state.
- [`credentials.md`](credentials.md) — brokers, storage, and trust boundaries.
- [`portable-catalogue-authentication.md`](portable-catalogue-authentication.md) — how a remote catalogue fetch picks bearer, JFrog CLI, `.netrc`, or anonymous access.
- [`knowledge-capture.md`](knowledge-capture.md) — capture, distillation, and enquiry.
- [`repository-grounding.md`](repository-grounding.md) — the grounding and exploration skills, their probes, and the optional-provider seam.
- [`code-intelligence.md`](code-intelligence.md) — the optional code-intelligence provider pack and the Core seams it plugs into.
- [`site-publishing.md`](site-publishing.md) — how authored content becomes the published site, and its gates.
- [`telemetry.md`](telemetry.md) — what a pack records about its own execution, and the export boundary.
- [`telemetry-backends.md`](telemetry-backends.md) — which backends can search the loop event line, and the OTLP encoding boundary.
- [`catalogue/upstream-sync.md`](catalogue/upstream-sync.md) — `agentbundle catalogue sync`, the path a derived catalogue takes upstream changes by.
- [`decision-graph.md`](decision-graph.md) — the reference-policy graph and decision navigation; its § 7 context checks are planned.

Architecture docs are a living snapshot. Update them with layout or dependency
changes.

The bundle source-of-truth split lives in
[`pack-layout.md` § The source-of-truth split](pack-layout.md#the-source-of-truth-split).
This directory documents the projected adopter layout; the pack-side authoring
rules live with that split.

## Planned architecture

- **STATUS: PLANNED** — [Binder publishing](binder-publishing/README.md) is
  designed but not implemented. [ADR-0073](../adr/0073-zensical-as-the-v1-binder-renderer.md)
  governs its renderer decision.
- **STATUS: § 1 IMPLEMENTED; §§ 2 AND 3 PLANNED** — [Loop concurrency and plan width](loop-parallelism.md) records
  that the work-loop supervisor dispatches one request at a time and that
  parallel task scheduling belongs to a later slice
  ([ADR-0144](../adr/0144-work-loop-supervisor-owns-procedure.md)).
- **STATUS: PARTLY IMPLEMENTED** — [Acceptance-centered work loop](acceptance-centered-work-loop.md)
  is the parent design for the work-loop refactor. Its rows marked
  `STATUS: PLANNED` (runtime extensions and leases)
  are later slices; the
  [brief](../product/briefs/acceptance-centered-work-loop.md#proposed-delivery-slices)
  owns each slice's status.
- **STATUS: PLANNED** — [Runtime adapter crosswalk](runtime-adapter-crosswalk.md):
  runtime adapters, the selector, and Pi conformance are later slices; the
  supervisor realization it records is current.
- **STATUS: PARTLY IMPLEMENTED** — [Product result integration](work-loop-result-integration.md):
  the sequential protected product ref ships (§ 1a), and its parallel design (§§ 2–8) is Slice 7.
- **STATUS: PARTLY IMPLEMENTED** — [Agent skill engineering](agent-skill-engineering.md)
  records the shipped pack and router; the runtime-package mode and self-host
  adaptation remain planned under
  [RFC-0097](../rfc/0097-agent-skill-engineering.md).
- **STATUS: PARTLY IMPLEMENTED** — [Per-update changelog sources](changelog-fragment-source.md):
  `tools/changelog.py` ships `new`, `render`, `validate`, `compact` and `retract`;
  the month-compaction layout is not yet in use. Contracts and build mapping:
  [reference](changelog-fragment-source-reference.md).
- **STATUS: PLANNED** — [On-demand remote verification](remote-verification.md)
  is the dispatchable composition accepted by
  [`remote-ci-verification-parity`](../product/intents/remote-ci-verification-parity.md).

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
