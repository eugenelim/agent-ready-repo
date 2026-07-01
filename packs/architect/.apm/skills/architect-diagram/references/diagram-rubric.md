# Diagram rubric — the quality bar for `architect-diagram`

Walk this rubric before showing the user a diagram. Each item is a
check, not a suggestion.

> Note: this rubric is intentionally duplicated as
> `references/rubric-c4-diagram.md` and related rubrics in
> `architect-review`. Skill autonomy beats DRY at this scale — see
> the pack README.

## Universal (every diagram)

- [ ] **Fits one screen.** ≤15 nodes. If the system needs more, split
      into multiple diagrams with explicit scope sentences.
- [ ] **Accent restraint.** At most **2** emphasized elements — count one
      `classDef` application (or one coloured / bolded node) as one accent.
      Past two, nothing stands out; the accent stops meaning "look here."
- [ ] **Edge budget.** Roughly **≤20 edges**. A diagram whose edges dwarf its
      nodes is a hairball; split by scope sentence before adding more.
- [ ] **Title or scope sentence** above the diagram tells the reader
      *what they are looking at* without scrolling.
- [ ] **No fabricated names** in document mode. Where a name is
      genuinely missing, label `<unnamed>` or ask.
- [ ] **Renders.** Paste the Mermaid into the live editor and confirm
      it parses before showing the user.
- [ ] **One notation per diagram.** No mixing `sequenceDiagram` blocks
      inside a flowchart.

## Structural (C4 Container, Container-view flowcharts)

- [ ] **Technology label on every Container.** "Service" alone fails.
      "Service [Go 1.22, gRPC]" or `Container(api, "API", "Go 1.22, gRPC")`
      passes.
- [ ] **No bare relation labels.** "uses", "calls", "reads" alone
      fail. Either name the protocol ("gRPC", "HTTPS", "Kafka topic
      orders.v1") or name the *what* ("publishes Order events",
      "reads user profile").
- [ ] **Trust boundaries are visible.** Subgraphs with dashed borders
      for trust-boundary crossings; a comment if subgraphs can't
      represent it.
- [ ] **External actors are visibly external.** Use C4's `Person()` /
      `System_Ext()`, or a distinct shape and the word "external" on
      a flowchart.

## Sequence

- [ ] **Lifelines named at top.** Every participant declared before
      the first arrow.
- [ ] **Synchronous vs. asynchronous arrows are different shapes.**
      Solid for sync, dashed for async; do not mix conventions.
- [ ] **Error / alt paths shown** where the flow has them. A happy
      path with no error handling is a fiction.
- [ ] **No unexplained gaps.** Time skips need an explicit `Note over`
      or a separator.

## State

- [ ] **Initial and terminal states named.** `[*]` start and end where
      relevant.
- [ ] **Transitions labeled** with the event that fires them.
- [ ] **No unreachable states.** If a state has no inbound transition
      and isn't initial, either fix it or document why.

## ER

- [ ] **Cardinality on every relationship.** No bare lines.
- [ ] **Primary key marked** on each entity.
- [ ] **Names match the system.** Match table / collection names
      verbatim in document mode.

## Deployment / infra (flowchart with subgraphs)

- [ ] **Region / cloud / VPC / subnet boundaries** rendered as nested
      subgraphs in the right order — see the matching
      `cloud-<cloud>.md` reference.
- [ ] **Public vs. private subnets** visibly distinct (subgraph label
      or emoji marker).
- [ ] **Trust boundaries dashed**, others solid.
- [ ] **Cross-region or cross-account arrows labeled** with what
      crosses (data, RPC, replication).

## Timeline (`timeline`)

- [ ] **Time-ordered, not comparative.** The axis carries chronology; if the
      point is a side-by-side comparison, it's a table, not a timeline.
- [ ] **Budget: ≤6 periods, ≤3 events each.** Beyond that the axis crowds —
      split into scoped timelines.
- [ ] **Rendering caveat applied.** Offered contingent on the venue rendering
      it; a date→milestone table named as the fallback.

## Quadrant (`quadrantChart`)

- [ ] **Both axes labelled** low→high, and all four quadrants named.
- [ ] **Two dimensions only.** A 2×2 forced onto three axes lies — use a table.
- [ ] **Budget: ≤8 plotted points.** More than eight and the eye can't group
      them; cluster or switch to a table.
- [ ] **Rendering caveat applied.** Offered contingent on the venue; an
      effort/impact table named as the fallback.

## Mindmap (`mindmap`)

- [ ] **A tree, not a graph.** No sideways links, no second parent — if things
      connect across branches it's a `flowchart`.
- [ ] **One distinctive root**; sub-nodes not over-decorated with shapes.
- [ ] **Budget: ≤3 levels deep, ≤5 branches off the root.** Deeper splits into
      a scoped child mindmap.
- [ ] **Rendering caveat applied.** Offered contingent on the venue; a nested
      bullet list named as the fallback.

## Cloud-aware add-ons

- [ ] **Subgraph nesting matches the cloud's boundary hierarchy** —
      AWS: Account → Region → VPC → Subnet. Azure: Subscription →
      Resource Group → VNet → Subnet. GCP: Org → Project → VPC →
      Subnet. Load `cloud-<cloud>.md` if uncertain.
- [ ] **Cloud-specific gotchas applied** (e.g. AWS public-subnet
      vs. private-subnet semantics, Azure private-endpoint vs.
      service-endpoint). Named in `cloud-<cloud>.md`.

## Agentic-platform add-ons

- [ ] **Platform-managed components are visibly distinct** from your
      code (different shape, label, or subgraph).
- [ ] **Session / isolation boundary** named where it materially
      affects the picture (AgentCore microVM-per-session, AI Foundry
      managed identity, Vertex agent identity).
- [ ] **Tool / function-call surface** shown where the user cares
      about who can call what.
