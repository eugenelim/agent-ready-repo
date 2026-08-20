# Architecture

Current repository architecture. Decisions live in [ADRs](../adr/); proposals
live in [RFCs](../rfc/).

- [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) — system model and deeper links.
- [`overview.md`](overview.md) — directory map.
- [`catalogue.md`](catalogue.md) — catalogue source and resolution.
- [`skill-and-pack-format.md`](skill-and-pack-format.md) — skill, pack, and projection formats.
- [`pack-layout.md`](pack-layout.md) — pack source layout.
- [`pack-manifest.md`](pack-manifest.md) — pack metadata projection.
- [`agentbundle.md`](agentbundle.md) — CLI, build, install, and adaptation.
- [`loop-infrastructure.md`](loop-infrastructure.md) — work-loop execution state and controls.
- [`work-intake-and-artifact-routing.md`](work-intake-and-artifact-routing.md) — intake, artifacts, and workspace routing.
- [`workspace-mcp/design.md`](workspace-mcp/design.md) — per-session workspace MCP service.
- [`security.md`](security.md) — security-review posture.
- [`credentials.md`](credentials.md) — brokers, storage, and trust boundaries.
- [`knowledge-capture.md`](knowledge-capture.md) — capture, distillation, and enquiry.

Architecture docs are a living snapshot. Update them with layout or dependency
changes.

The bundle source-of-truth split lives in
[`../CONVENTIONS.md` § Pack source-of-truth split](../CONVENTIONS.md#pack-source-of-truth-split).
This directory documents projected adopter layout; pack authoring rules live in
CONVENTIONS.

## Planned architecture

- **STATUS: PLANNED** — [Binder publishing](binder-publishing/README.md) is
  designed but not implemented. [ADR-0073](../adr/0073-zensical-as-the-v1-binder-renderer.md)
  governs its renderer decision.
