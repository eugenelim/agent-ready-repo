# Mermaid flowchart — the architecture workhorse

The right default for *deployment*, *infrastructure*, *integration*, and
*topology* diagrams. Renders cleanly in GitHub, Confluence, Azure DevOps
Wiki, and GitLab.

## Skeleton

````
```mermaid
flowchart TB
    Client[Client]
    Service[API service]
    DB[(Datastore)]
    Client --> Service --> DB
```
````

`flowchart TB` is top-to-bottom — best for deployment hierarchies.
`flowchart LR` is left-to-right — best for anything with a reading
order: request flows, and **pipelines / ETL / CI-CD stages /
data-flow** where the eye should track stages start-to-finish. Pick one
and stick with it within a diagram.

## Title and accessibility metadata

Give the diagram an in-source title with Mermaid's **config frontmatter**
(a YAML block fenced by `---` at the very top of the Mermaid source,
Mermaid ≥ 10.5) — it renders as a heading above the diagram:

````
```mermaid
---
title: Order ingestion pipeline
---
flowchart LR
    Ingest --> Validate --> Ledger
```
````

This is the portable version of a diagram title — it renders in current
Mermaid (`mmdc` and the repo's `render-proof` / `markdown-to-html`
renderers pin `mermaid@11`). It is still a version-dependent feature, so
carry the same venue caveat the skill applies to `architecture-beta` /
`timeline` and friends: **the prose scope sentence above the diagram
stays the always-portable baseline** — the frontmatter title augments it,
it doesn't replace it. Do **not** reach for a `%% title:` comment: `%%`
is Mermaid's comment marker and is dropped by every renderer.

For screen-reader accessibility, add `accTitle` (short) and `accDescr`
(longer) inside the diagram body — they emit to the SVG's `<title>` /
`<desc>` and are supported across diagram types (flowchart, sequence,
state, er, …), not just flowcharts:

````
```mermaid
flowchart LR
    accTitle: Order ingestion pipeline
    accDescr: Ingest validates each order, then writes it to the ledger.
    Ingest --> Validate --> Ledger
```
````

Recommended for any diagram that will ship in a docs page or wiki; it is
the diagram analogue of alt text. Renderers vary in whether they expose
it, so treat it as reinforcement, never the sole carrier of meaning.

## Node shapes (architecture-relevant)

| Shape | Mermaid | Use for |
| --- | --- | --- |
| Rectangle | `A[Label]` | Service, component, generic |
| Rounded | `A(Label)` | External actor, person |
| Stadium | `A([Label])` | Start / end / boundary marker |
| Subroutine | `A[[Label]]` | Queue, topic, channel |
| Cylinder | `A[(Label)]` | Database, persistent store |
| Trapezoid | `A[/Label/]` or `A[\Label\]` | Object store, blob, file system |
| Diamond | `A{Label}` | Decision, conditional routing |
| Hexagon | `A{{Label}}` | External system, third-party |
| Circle | `A((Label))` | Junction, fan-in / fan-out |

Be consistent across the diagram — pick one shape per *category* of
thing and never mix.

## Edges

| Mermaid | Meaning |
| --- | --- |
| `A --> B` | Synchronous call, A initiates |
| `A -.-> B` | Asynchronous call, fire-and-forget |
| `A --o B` | Observation / read-only |
| `A --x B` | Failure path / terminates |
| `A === B` | Strong / heavy coupling (used sparingly) |
| `A -->|"label"| B` | Labeled edge — name the protocol or payload |

**Always label edges** that cross a trust boundary or carry data.
"HTTPS" alone is fine; "gRPC orders.v2" is better; "uses" is wrong.

## Subgraphs — for boundaries

Subgraphs are the workhorse for cloud boundary nesting. Nest them
inside-out for visual clarity.

````
```mermaid
flowchart TB
    subgraph region["us-east-1"]
        subgraph vpc["vpc-prod"]
            subgraph public["🌐 public subnet"]
                ALB[ALB]
            end
            subgraph private["🔒 private subnet"]
                APP[App service]
                DB[(Postgres)]
            end
        end
    end
    Internet[(Internet)] --> ALB --> APP --> DB
```
````

Use a dashed border for *trust* boundaries — Mermaid renders this via
the `classDef` mechanism:

```
classDef trust stroke-dasharray: 5 5
class accountA,accountB trust
```

## Styling — use sparingly

Stick to defaults. The exception is the trust-boundary `classDef`
above. Heavy theming rots fast and doesn't reproduce across wiki
renderers.

## Common architecture pitfalls

- **Top-down flowchart used as a request flow.** Switch to
  `flowchart LR` or use a `sequenceDiagram`.
- **One mega-flowchart with 30 nodes.** Split by scope sentence.
- **All edges unlabeled.** A diagram without labeled edges is
  abstract art.
- **Mixing shapes inconsistently** — `[Service A]` and `(Service B)`
  for two services that play the same role. Pick one.
