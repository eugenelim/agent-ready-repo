# Lifecycle flow across the packs

How one piece of work moves through the packs from idea to production, and
where a person decides. This is the maintainer map. The public explanation is
[`guides/_shared/explanation/the-operating-model.md`](../../guides/_shared/explanation/the-operating-model.md).

## Flow

A hexagon is a human decision. G1 is round because it passes automatically
unless a risk trigger fires. Dashed edges are optional routes or shortcuts.

```mermaid
flowchart TB
    subgraph decide["Decide what to build"]
        direction TB
        D1["desk-research: find out what is true"] --> D2["product-strategy: write-prfaq, run-okr-cascade, define-ux-strategy"]
        DA["architect-assess on the area the bet touches, optional"]
    end
    subgraph shape["Shape it"]
        direction TB
        S1["frame-intent"] --> G0{{"G0: you approve the intent"}}
        G0 --> S2["de-risk-intent, then decompose-intent"]
        S2 --> G1(["G1: runs on its own unless a risk shows up"])
        G1 --> S3["explore-options"]
        S3 --> S4["frame-domain"]
        S4 --> G15{{"G1.5: you set the MVP boundary"}}
        G15 --> T1["Product: decompose-intent"]
        G15 --> T2["Experience: journey-mapping, service-blueprint, user-flow, ux-writing"]
        G15 --> T3["Architecture: architect-design, architect-diagram"]
        G15 --> T4["Contracts: api-contract, event-contract"]
        T1 --> RV["Threat and reliability reviewers"]
        T2 --> RV
        T3 --> RV
        T4 --> RV
        RV --> G2{{"G2: you approve the decision brief"}}
        G2 --> S5["decompose-intent: buildable pieces"]
        S5 --> G3{{"G3: you commit to build"}}
        SR["Short route: frame-intent, which may offer one architect-design pass, de-risk-intent, decompose-intent"]
        LR["Longer route: frame-situation, identify-opportunities, diverge-solutions, de-risk-intent, place-bet, map-capabilities"]
        LA["Optional: architect-design at system scope, offered by map-capabilities once the build order is set"]
        LS["Optional: architect-design for subsystems that earn a doc, then architect-review"]
    end
    subgraph build["Build it"]
        direction TB
        B1["work-intake: picks a spec, a delivery brief, or a minimum intent"] --> B2["new-spec: spec and plan"]
        B2 --> B3{{"You approve the spec, then the plan"}}
        B3 --> B4["work-loop: build, gates, three cold reviews"]
        B4 --> G4{{"G4: you merge, and the build goes to release"}}
    end
    subgraph ship["Ship it"]
        direction TB
        L1["define-slo, if you want an error budget"] --> L2["release-loop: deploy to a throwaway environment, test end to end, watch telemetry"]
        L2 --> G5{{"G5: you approve the production ship"}}
    end
    subgraph found["Before any work, once per repository"]
        direction TB
        A1["architect-assess: the current-state map"]
        A2["reference.md, a file: engineering patterns written by adapt-to-project or init-project"]
    end
    A3["close-work: offers to fold the shipped design into the current-state map"]
    D2 --> S1
    D2 -.-> SR
    D2 -.-> LR
    SR -.-> G3
    SR -. "the concept changes the capabilities" .-> LR
    LR -.-> G3
    LR -.-> LA
    LA -. "revise the capabilities and design again" .-> LR
    LA -.-> LS
    LS -.-> G3
    G3 --> B1
    B1 -. "small, low-risk change: no spec" .-> B4
    G4 --> L1
    L2 -. "a deployed failure goes back as a build task" .-> B4
    A1 -.-> DA
    DA -.-> D2
    A2 -.-> LA
    A2 -. "the plan's design follows it" .-> B2
    G4 -. "the work closes" .-> A3

    classDef decideStep fill:#ede9fe,stroke:#7c3aed,color:#1f2937
    classDef shapeStep fill:#dbeafe,stroke:#2563eb,color:#1f2937
    classDef buildStep fill:#dcfce7,stroke:#16a34a,color:#1f2937
    classDef shipStep fill:#ffedd5,stroke:#ea580c,color:#1f2937
    classDef gate fill:#fde68a,stroke:#b45309,stroke-width:2px,color:#1f2937
    classDef autoGate fill:#fef3c7,stroke:#b45309,stroke-dasharray:4 3,color:#1f2937
    classDef shortcut fill:#f8fafc,stroke:#64748b,stroke-dasharray:4 3,color:#1f2937
    class D1,D2 decideStep
    class S1,S2,S3,S4,S5,T1,T2,T3,T4,RV shapeStep
    class B1,B2,B4 buildStep
    class L1,L2 shipStep
    class A1,A2,A3,DA,LA,LS shortcut
    class G0,G15,G2,G3,B3,G4,G5 gate
    class G1 autoGate
    class SR,LR shortcut
    style decide fill:#7c3aed14,stroke:#7c3aed
    style shape fill:#2563eb14,stroke:#2563eb
    style build fill:#16a34a14,stroke:#16a34a
    style ship fill:#ea580c14,stroke:#ea580c
    style found fill:#2563eb0a,stroke:#2563eb,stroke-dasharray:4 3
```

## Gates and their owners

| Gate | Decision | Owner | Source |
| --- | --- | --- | --- |
| G0 | Ratify the value seed | `discovery-lead` | `packs/product-engineering/.apm/skills/discovery-loop/SKILL.md` |
| G1 | Strategy: automatic unless a risk trigger fires | `discovery-lead` | same |
| G1.5 | Ratify the altitude and MVP boundary | `discovery-lead` | same |
| G2 | Ratify the decision brief after the discovery reviewers reconcile | `discovery-lead` | same |
| G3 | Confirm the hand-off through `work-intake` | `discovery-lead` | same |
| G4 | Merge; the deploy-ready build passes to release | `work-loop` supervisor, `release-lead` | `packs/release-engineering/.apm/agents/release-lead.md` |
| G5 | Ratify the production ship | `release-lead` | same |

The short and longer shaping routes are not supervised by `discovery-lead`.
They are the light path and the six-step shaping sequence that P2 in
[`guides/README.md`](../../guides/README.md) walks, and they reach the same
G3 hand-off.

Architecture runs on two rhythms: documents set up once per repository, then
architecture steps at set points in each piece of work. Which skill offers
each step, and how a design reaches a spec, is owned by the "Where
architecture comes in" section of the operating-model guide. No stage gate
waits on any of it.

## Public projections

Three public artifacts restate this flow. Change them together with this page:

- The step-by-step list and the "Where architecture comes in" timeline in the
  operating-model guide, which are the text alternative for both graphics.
- `guides/_shared/explanation/the-operating-model-overview.svg` and
  `the-operating-model-full-map.svg`, generated by
  `python3 tools/render-lifecycle-graphics.py`. Edit the step content in that
  script, not in the SVG files.
- The four-stage strip in `guides/README.md` and the "Where this fits"
  sections in the eight stage-owning pack READMEs.
