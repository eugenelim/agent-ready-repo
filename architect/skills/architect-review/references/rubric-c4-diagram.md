# C4 / Container-view rubric — for `architect-review`

For critiquing a C4 Context or Container diagram, or a
Container-shaped flowchart.

> Note: intentionally duplicated from `architect-diagram`'s
> `diagram-rubric.md`. Skill autonomy beats DRY at this scale.

## Universal

- [ ] **Fits one screen.** ≤15 nodes.
- [ ] **Title or scope sentence** above the diagram tells the
      reader what they're looking at.
- [ ] **No fabricated names** in document mode.
- [ ] **Renders.** The Mermaid source parses.

## Structural (C4 Container, Container-view flowcharts)

- [ ] **Technology label on every Container.** "Service" alone fails.
- [ ] **Description on every Container** (the 4th C4 arg) — one
      short phrase.
- [ ] **No bare relation labels.** "uses", "calls", "reads" alone
      fail. Either the protocol or the *what* must be named.
- [ ] **Trust boundaries are visible.** Subgraphs with dashed
      borders or explicit comments.
- [ ] **External actors are visibly external.** `Person()` /
      `System_Ext()` or a distinct shape and the word "external".
- [ ] **One system per Container view.** A Container view spanning
      four systems is a Context view in disguise.

## Cloud-aware (when applicable)

- [ ] **Subgraph nesting matches the cloud's boundary hierarchy.**
      AWS: Account → Region → VPC → Subnet. Azure: Subscription →
      Resource Group → VNet → Subnet. GCP: Org → Project → VPC →
      Subnet.
- [ ] **Public vs. private subnets visibly distinct.**
- [ ] **Trust boundaries dashed.**
- [ ] **Cross-region / cross-account arrows labeled** with what
      crosses.
- [ ] **Cloud-specific gotchas applied** — AWS public-vs-private
      subnet semantics, Azure private-endpoint vs. service-endpoint,
      GCP VPC-is-global.

## Agentic-platform (when applicable)

- [ ] **Platform-managed components visibly distinct** from
      customer code.
- [ ] **Session / isolation boundary** named where it materially
      affects the picture (AgentCore microVM, AI Foundry managed
      identity, Vertex agent identity).
- [ ] **Tool / function-call surface** rendered when authorization
      is in scope.
- [ ] **Identity-on-the-edge** for tool calls.

## Severity mapping (typical)

- 🟥 **Blocker** — Trust boundary missing; technology labels
  absent across most Containers; fabricated names presented as
  real; diagram doesn't parse.
- 🟧 **Major** — Bare relation labels; external systems blended
  with internal; one cloud boundary missing.
- 🟨 **Minor** — Edge labels inconsistent in style; one Container
  lacks a description.
- ⚪ **Nit** — Layout direction sub-optimal; emoji marker
  inconsistent with neighbors.
