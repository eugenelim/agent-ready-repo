---
title: The three loops — the company operating model
summary: Understand why discovery, build, and release are separate supervised loops and how their handoffs form one operating model.
pack: _shared
kind: explanation
---

# The three loops — the company operating model

Shipping software is three jobs: working out what to build, building it, and
getting it into production. They go wrong in different ways, different people
decide them, and some of their mistakes can't be undone. One agent loop can't
run all three well. Give it a single level of caution and it either crawls
through cheap exploration or rushes a production release.

So the catalogue gives each job its own loop. This page shows how work moves
between them and where you make the calls.

## The handoff chain

Follow one piece of work from idea to production and it passes through four
stages. Each stage ends when a person on your team makes a decision. The guides
call the stages *Decide what to build*, *Shape it*, *Build it*, and *Ship it*.

Most work doesn't travel the whole way. A bug fix starts at *Build it*. A small
change to an existing product often goes from a written intent straight to the
build loop. The diagram shows the longest route so you can see where every pack
fits. Dashed lines are the shortcuts.

```mermaid
flowchart TB
    subgraph decide["Decide what to build"]
        direction TB
        D1["desk-research: find out what is true"] --> D2["product-strategy: write-prfaq, run-okr-cascade, define-ux-strategy"]
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
        G2 --> S5["decompose-intent: an ordered backlog"]
        S5 --> G3{{"G3: you commit to build"}}
        SR["Short route: frame-intent, de-risk-intent, decompose-intent"]
        LR["Longer route: frame-situation, identify-opportunities, diverge-solutions, place-bet, map-capabilities"]
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
    D2 --> S1
    D2 -.-> SR
    D2 -.-> LR
    SR -.-> G3
    LR -.-> G3
    G3 --> B1
    B1 -. "small, low-risk change: no spec" .-> B4
    G4 --> L1
    L2 -. "a deployed failure goes back as a build task" .-> B4

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
    class G0,G15,G2,G3,B3,G4,G5 gate
    class G1 autoGate
    class SR,LR shortcut
    style decide fill:#7c3aed14,stroke:#7c3aed
    style shape fill:#2563eb14,stroke:#2563eb
    style build fill:#16a34a14,stroke:#16a34a
    style ship fill:#ea580c14,stroke:#ea580c
```

Read it from the top. Each stage has its own color. The amber hexagons are the
points where the agent stops and waits for you. G1 is pale and round because it
usually passes without you.
When any piece of work finishes, or you abandon it, `close-work` from `core`
tidies it up.

### Three ways through *Shape it*

Every route through *Shape it* ends the same way: you decide the work is ready
and hand it to the build loop. They differ in how much ground they cover first.

- **The short route** is where most teams start. You write the intent, test its
  riskiest assumption, and break it into pieces the build loop can take. Plan on
  about three hours.
- **The longer route** adds a situation, opportunities, options, a bet, and a
  capability map. Take it when you can't yet say what the problem is, or when
  the bet is big enough that someone will ask for the reasoning later.
- **The supervised loop** runs down the middle of the diagram. `discovery-lead`
  walks every gate, brings in design, architecture, and contract work side by
  side, and has two reviewers check for threats and reliability problems before
  you see the brief. Use it for a new product area.

[Shape what to build](../../README.md#p2--shape-what-to-build--3-hours) walks
the short and longer routes. [Walk a discovery end to end](../../product-engineering/tutorials/walk-a-discovery-end-to-end.md)
walks the supervised loop.

### Which pack does what

| Stage | What happens | Pack | What you decide |
| --- | --- | --- | --- |
| Decide what to build | Gather evidence, graded by how much you can trust it | `desk-research` | Whether the evidence is enough to act on |
| Decide what to build | Make the strategic call | `product-strategy` | Which outcome you are committing to |
| Shape it | Frame the intent and test the bet | `product-engineering` | Whether the problem is specific enough |
| Shape it | Map the journey and the screens | `experience-design` | Whether the design is ready |
| Shape it | Sketch the system and its interfaces | `architect`, `contracts` | Whether the concept holds up |
| Shape it | Pull it together into a decision brief and a backlog | `product-engineering` | Whether to commit to build |
| Build it | Write the spec and plan, then build and review | `core` | The spec, the plan, and the merge |
| Ship it | Deploy somewhere safe, test it, and watch it run | `release-engineering` | Whether it goes to production |

A few packs don't belong to one stage. You reach for them whenever the moment
comes up:

- `code-intelligence` when you need to know what the code really does before
  you change it.
- `frontend-engineering` and `iac-terraform` for UI and infrastructure work
  inside the build.
- `atlassian`, `github`, `linear`, and `figma` to pull work in from your team's
  tools and report progress back out.
- `converters` to turn PDFs, slides, and other files into text an agent can read.
- `governance-extras` to write down a decision as an ADR or RFC, at any stage.
- `product-documentation` to document what you shipped.

### If you see a gate code

The agents print a short code when they stop for you. This is what each one is
asking.

| Code | What you're deciding | Product Engineering calls it |
| --- | --- | --- |
| G0 | Is the problem real, and is this the right bet? | Approve the intent |
| G1 | Does the de-risked plan still hold? Usually automatic | |
| G1.5 | What's in the first version, and what's out? | |
| G2 | Is the decision brief good enough to build from? | Approve the decision brief |
| G3 | Are you ready to hand this to the build loop? | Commit to build |
| G4 | Is this merged change ready for release testing? | |
| G5 | Does it go to production? | |

Discovery, build, and release each have their own supervising agent:
`discovery-lead`, the `work-loop` supervisor, and `release-lead`. None of them
runs inside another. They meet at G3 and G4, and nothing crosses either line,
or reaches production at G5, until you say so.

## Why three loops, not one

**Some mistakes are cheap and some aren't.** You can explore five product
shapes in an afternoon and throw four away. A bad production release can't be
taken back as easily. One level of caution is wrong for both: too slow for
exploring, too loose for shipping.

**Different people make the calls.** Whether an idea is worth building is a
business decision. Whether the code compiles is a mechanical check. Whether a
running system meets its service levels is an operations judgment.

**Each loop fails in its own way.** Discovery fails when it settles on the
wrong product. Build fails when the code doesn't work. Release fails when
something breaks in production. Each needs its own checks and its own
reviewers.

## The discovery loop

**Pack:** `product-engineering` | **Agent:** `discovery-lead` | **Scope:** user

Discovery takes a raw product signal and shapes it before anyone writes code.
What you end with is an intent you approved, written at the right size: an
initiative, a capability, or a single feature. Product Engineering doesn't need
`core` installed, and it doesn't write the repository's delivery contract.

How it works:

- **It compares before it chooses.** The agent explores five candidate product
  shapes side by side against the customer and the job they're trying to do,
  so the best one wins on comparison instead of the first idea getting polished.
- **Several specialists work at once.** Product, UX, architecture, and safety
  lenses each write their findings to a shared workspace the agent calls the
  blackboard. They never pass results to each other through chat.
- **Sub-problems stay in the same tree.** A sub-problem you find along the way
  becomes a child of the intent you're working on, and the same loop shapes it.
  It doesn't turn into a separate project.
- **Your decisions can't be rewritten.** Each verdict goes into an append-only
  log, chained by hash, so the agent can't forge or change a decision after you
  made it.

You decide at four points:

- **G0:** the value. Is the problem real, who has it, and is it worth a bet?
- **G1.5:** the MVP boundary. Which features are in the first bet?
- **G2:** the converged intent, including its riskiest assumptions and how
  you'll test them.
- **G3:** the hand-off. Is this ready for the repository's build loop?

→ [Discovery loop guide](../../product-engineering/) · [Walk a discovery end-to-end](../../product-engineering/tutorials/walk-a-discovery-end-to-end.md)

## The build loop

**Pack:** `core` | **Agent:** `work-loop` supervisor | **Scope:** repo

This is the inner loop, and it works on its own. `work-intake` reads what you
describe and picks a route. `intake-intent` records a minimum intent.
`author-delivery-brief create|continue` coordinates work that spans several
specs or repositories. `new-spec` writes one contract for one change you can
ship by itself. An intent from Product Engineering uses the same routes, and
`core` doesn't need that pack installed. Every build then runs plan, execute,
gate, review, and decide.

How it works:

- **The spec is reviewed twice before you see it.** A cold shaping review checks
  that the contract is observable and bounded. Then an adversarial review reads
  the spec and plan together and checks that the plan can deliver the contract.
  Neither replaces the code review that comes after.
- **The ceremony matches the risk.** Small, low-risk work runs in direct-light
  mode, straight from your request, with an adversarial review and no saved
  spec. Full mode writes a spec and plan when something raises the risk: a
  design you can't predict, a new dependency, a compliance surface, work shared
  between people, or a destructive operation. File count doesn't decide it.
- **The gates are real.** Lint, type checks, and tests run as gates. The agent
  can't report success while one of them is red.
- **Three reviewers read every change cold.** The adversarial reviewer looks for
  drift between spec, plan, and code. The security reviewer works from OWASP
  2025, ASVS, and STRIDE. The quality reviewer looks at testability,
  observability, and reliability. Each starts fresh, with no stake in the design.
  The loop keeps fixing until they say `Clean — ready to commit.`
- **Security depth follows the change.** The security checklist loads only the
  sections for the boundaries a change crosses, such as auth, secrets, user
  input, deserialization, file I/O, or LLM code.
- **Lessons stick.** When a run finds a gap in the project's conventions, it
  proposes an edit to the file that owns the rule. The fix stays with the
  project instead of vanishing when the session ends.

In full mode you approve the spec, then the plan, before any code is written.
The merge at the end is yours in both modes. Direct-light mode saves no spec, so
it skips the approval pair. Between those points the loop runs on its own. It
brings blockers to you, and it sorts concerns and nits by whether a tool can fix
them.

→ [Core pack guide](../../core/) · [The `core` pack as a system](../../core/explanation/core-pack.md)

## The release loop

**Pack:** `release-engineering` | **Agent:** `release-lead` | **Scope:** repo

This is the outer loop. It takes the build the inner loop finished and tests it
**deployed**: running in an environment like production, not on a developer's
machine.

How it works:

- **It only deploys to throwaway environments.** The release loop never touches
  production. Its environments hold no real user data, can't reach production,
  are kept apart from each other, and are torn down afterwards. That isolation is
  what makes it safe to leave running.
- **What can be undone runs on its own.** Deploying to a throwaway environment,
  running end-to-end tests, watching telemetry, redeploying, and tearing down
  all run without you. First real users, data migrations, spend over a
  threshold, and the production ship always wait for you.
- **A deployed failure goes back to the build loop.** It arrives in `work-loop`
  as a build task, not as a raw error for you to pass along. The inner loop
  fixes it and the outer loop redeploys.
- **It stops when the evidence says so.** The loop keeps going until the canary
  meets its service levels, the changed areas have end-to-end coverage, flaky
  tests are below the threshold, and the error budget isn't spent.
- **You get a record, not a thumbs-up.** The release-readiness record gives the
  convergence result, the operations and security verdicts, and the cost and
  budget status.

You decide once, at **G5**: does it go to production? No setting, mode, or
flag skips it, and the agent never moves past it on its own.

→ [Release loop guide](../../release-engineering/) · [The release loop explained](../../release-engineering/explanation/the-release-loop.md)

## Where each loop is installed

Each loop installs where its work happens:

- **Discovery installs per person (user scope).** Shaping happens in documents
  like Notion pages, Figma files, and slide decks, not in a repository. That's
  why `discovery-lead` brings its own reviewer agents: it can't count on `core`
  being installed.
- **Build installs per repository (repo scope).** `core` goes into the
  repository that holds the code. Its reviewer agents are available to any other
  pack installed in that repository.
- **Release installs in the same repository as build.** It needs `core` and
  reuses its reviewers, which only works because both live in the same
  repository.

So G3 is where the work moves from your documents into the repository. What it
turns into depends on its size. A single feature can become one spec. A
capability or an initiative can become an RFC, several child intents, or a
delivery brief that coordinates RFCs and specs. A repository without Product
Engineering starts at the same intent, delivery brief, or spec.

## How much the agents do on their own

The more permanent an action, the more the agent waits for you:

| What happens | Examples | How the agent behaves |
| --- | --- | --- |
| Runs on its own | Exploring product shapes, writing and running tests, deploying to throwaway environments, fixing build failures | Keeps going without you |
| Brings it to you | A blocker in the build loop, or the release loop reaching its stop point | Pauses and shows you where things stand |
| Waits for your yes | G0, G1.5, G2, and G3 in discovery, the merge, and G5 in release | Doesn't move until you approve |

## Install the loops

Install them in this order:

```bash
# 1. The build loop. The release loop needs it.
agentbundle install --pack core

# 2. The discovery loop, at user scope so it follows you across repositories
agentbundle install --pack product-engineering --scope user

# 3. The release loop, into the same repository as core
agentbundle install --pack release-engineering
```

Or install the `full-ceremony` profile. It installs `core` with
`governance-extras`, `product-documentation`, and `monorepo-extras` in one
command. Add the other loops as your team needs them.

You only need the loops your team uses. Most teams start with `core`. They add
`product-engineering` once product conversations start happening in documents
instead of in GitHub issues.
