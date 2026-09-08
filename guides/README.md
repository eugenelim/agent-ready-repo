---
title: Guides
summary: Choose the pack and guide that matches your outcome, from supervised delivery loops to research, architecture, integrations, and catalogue operations.
pack: _shared
kind: explanation
---

# Guides

Use this catalogue to add repeatable, supervised ways of working to your agent. Start with the outcome you need; the linked pack guides explain what to install, what to ask for, what the agent produces, and where a human decides.

## Follow a path

A path is an ordered set of guides that ends at a handoff, not at a document.
Each names what you must already have and roughly what it costs. Start at the
front door and work down; the two tables after this one are alternate ways in
once you know the shape.

### P1 · Adopt the catalogue — ~1 hour

**Prerequisite:** none. **For:** anyone, first session.

1. [Choose an install route](_shared/explanation/install-routes.md)
2. [Install the whole lifecycle](_shared/how-to/install-the-whole-lifecycle.md)
3. [Adapt an existing repo](core/how-to/adapt-to-project.md) — or [start a new project](core/how-to/start-a-project.md)
4. [Orient at session start](core/how-to/orient-at-session-start.md)

**First value:** `workspace status` answers what to work on next.
**Ends at:** a repository whose queues you can read.

### P2 · Shape what to build — ~3 hours

**Prerequisite:** P1. **For:** product manager, product engineer, strategist.

The **light path** is the default: frame an intent, test its riskiest
assumption, break it down. Reach past it to the **robust path** — situation,
opportunities, options, bet, capability map — only when the problem itself is
unclear or the bet is large enough to need a recorded rationale. [The intent
tree](product-engineering/explanation/the-intent-tree.md) explains the choice.

1. [Gather evidence](desk-research/) when the answer is not already known
2. [Shape a feature intent](product-engineering/how-to/shape-a-feature-intent.md) — `frame-intent`
3. De-risk it and break it down — `de-risk-intent`, then `decompose-intent`
4. [Shape the architecture concept](architect/how-to/shape-an-architecture-concept.md) against it
5. [Hand the intent to the build loop](product-engineering/how-to/hand-an-intent-to-build.md)

On the robust path, [frame the situation](product-engineering/how-to/frame-a-situation.md)
first, then [identify opportunities](product-engineering/how-to/identify-opportunities.md),
[generate options](product-engineering/how-to/generate-solution-options.md), and
[place a bet](product-engineering/how-to/place-a-bet.md) before step 4.

**First value:** one written intent naming an outcome and the bet behind it.
**Ends at:** Core intake, which selects the route from the content — a spec, a
delivery brief, or a minimum repository intent.

### P3 · Build it — ~2 hours

**Prerequisite:** P2, or an existing spec. **For:** engineer, agent.

1. [Orient at session start](core/how-to/orient-at-session-start.md)
2. [Plan and execute non-trivial work](core/how-to/plan-and-execute-non-trivial-work.md)
3. [Review someone else's PR](core/how-to/review-someone-elses-pr.md)
4. [Close and disposition the work](core/how-to/close-and-disposition-work.md)

**First value:** a spec and plan you approved before any code was written.
**Ends at:** a merged change, and the decision to merge is yours.

### P4 · Decide together — ~1.5 hours

**Prerequisite:** P1. **For:** tech lead, architect.

1. [The governance index](governance-extras/how-to/governance-index.md) — which of RFC, ADR, or spec you need
2. [Propose an RFC](governance-extras/how-to/new-rfc.md)
3. [Record an ADR](governance-extras/how-to/new-adr.md)

P4 draws on P2's artifacts: an intent, a decision brief, a research survey, or
an architecture concept is what an RFC or ADR is written *from*.

**First value:** a circulated proposal with its alternatives written down.
**Ends at:** an accepted decision that outlives the people who made it.

### P5 · Ship and report — ~2 hours

**Prerequisite:** P3. **For:** delivery lead, SRE.

1. [The release loop](release-engineering/explanation/the-release-loop.md)
2. [Run a release](release-engineering/how-to/run-a-release.md)
3. [Project slices out to a tracker](_shared/how-to/project-slices-to-a-tracker.md) — or [intake from one](_shared/how-to/choose-a-tracker-integration.md)
4. [Measure flow and DORA metrics](atlassian/how-to/measure-flow-and-dora-metrics.md)

**First value:** a deployed artifact validated in an environment like production.
**Ends at:** a human ratifying the production ship.

### P6 · Extend the catalogue — ~3 hours

**Prerequisite:** P1 and P3. **For:** AI enablement, catalogue owner.

1. [Why catalogue curation](catalogue-curation/explanation/why-catalogue-curation.md)
2. [Your first skill](catalogue-curation/tutorials/your-first-skill.md)
3. [Build an org stack pack](_shared/how-to/build-an-org-stack-pack.md)
4. [Create a catalogue](_shared/how-to/create-a-catalogue.md)

**First value:** one skill of your own that your agent can run.
**Ends at:** a catalogue your organisation owns.

## Choose what you want to achieve

| I need to… | Start with | Continue with |
| --- | --- | --- |
| **Decide what to build** | [`product-strategy`](product-strategy/) for strategic choices | [`desk-research`](desk-research/) for evidence, then [`product-engineering`](product-engineering/) to shape a build-ready bet |
| **Design the product and system** | [`experience-design`](experience-design/) for journeys and surfaces | [`architect`](architect/), [`contracts`](contracts/), and [`frontend-engineering`](frontend-engineering/) for the system, interfaces, and implementation |
| **Build and review software** | [`core`](core/) to route work into a durable artifact and supervised loop | [`governance-extras`](governance-extras/) for durable decisions and [`monorepo-extras`](monorepo-extras/) for package scaffolding |
| **Provision and release safely** | [`iac-terraform`](iac-terraform/) for reviewable infrastructure plans | [`release-engineering`](release-engineering/) for deployed validation and the human production gate, supervised by [`core`](core/) |
| **Work with team systems and evidence** | [`atlassian`](atlassian/), [`github`](github/), [`linear`](linear/), or [`figma`](figma/) | [`converters`](converters/) for source material and [`credential-brokers`](credential-brokers/) for credential-safe access |
| **Document what ships** | [`product-documentation`](product-documentation/) | [`converters`](converters/) and the guide for the pack whose behavior you are documenting |
| **Build and govern a catalogue** | [`catalogue-curation`](catalogue-curation/) | [`governance-extras`](governance-extras/), [`product-documentation`](product-documentation/), and the [catalogue authoring standards](_shared/reference/catalogue-authoring-standards.md) |

The [`core`](core/) build loop is the catalogue's flagship and its strongest standalone product: a spec-driven implementation loop with mechanical gates, cold independent review, stasis detection, and a human merge decision. Start there when you want the most rigorous coding-agent workflow; the rest of the catalogue applies the same supervised-work principle to other jobs.

## Choose by role

- **Product manager or strategist:** [decide what to build](product-strategy/), [gather evidence](desk-research/), then [shape the bet](product-engineering/).
- **Platform, infrastructure, or SRE team:** [design the system](architect/), [author its contracts](contracts/), [plan infrastructure](iac-terraform/), and [validate the release](release-engineering/).
- **Software engineer:** start with the [`core` work loop](core/), then add the design, contract, frontend, infrastructure, or governance pack your change needs.
- **Designer or UX practitioner:** start with [`experience-design`](experience-design/) and connect the result to [`product-engineering`](product-engineering/) or [`frontend-engineering`](frontend-engineering/).
- **Researcher or analyst:** start with [`desk-research`](desk-research/) and add the relevant team-system or conversion pack.
- **AI enablement or catalogue owner:** start with [the pack catalogue](_shared/explanation/pack-catalogue.md), then use [`catalogue-curation`](catalogue-curation/) to evolve your organization-owned collection.

## Shared and pack-specific guidance

Pack directories contain task guidance for that pack. [`_shared/`](_shared/) contains cross-catalogue guidance that applies regardless of which packs you install:

- [Start, remember, inspect, or refresh repository work](_shared/how-to/use-work-intake.md), then use the [routing and lifecycle reference](_shared/reference/work-intake-routing-and-lifecycle.md) when you need the exact boundary.

- [Get from zero to the three-loop operating model](_shared/explanation/the-three-loops.md).
- [Understand packs, profiles, adapters, composition, and catalogue ownership](_shared/explanation/pack-catalogue.md).
- [Choose an install route](_shared/explanation/install-routes.md) and [check adapter support](_shared/reference/adapter-support.md).
- [Install a curated profile](_shared/how-to/install-a-profile.md), [preview a change](_shared/how-to/preview-install-or-upgrade.md), or [upgrade safely](_shared/how-to/upgrade-packs.md).
- [Create your own catalogue](_shared/how-to/create-a-catalogue.md) and [apply its portable authoring standards](_shared/reference/catalogue-authoring-standards.md).

Claude users can [add this catalogue as a plugin marketplace](_shared/explanation/install-routes.md) and install user-scope packs directly. Repo-scoped packs such as `core` still install with `agentbundle` so their workflow belongs to the project and team.

The public documentation site generates the complete pack and guide navigation from this tree. [Browse the complete generated pack reference](https://eugenelim.github.io/agent-ready-repo/docs/packs/); this page stays a route map rather than duplicating that inventory by hand.

## Writing a guide

Use the [`author-product-docs`](product-documentation/how-to/author-product-docs.md) workflow. It selects the right page contract and destination; the [catalogue authoring standards](_shared/reference/catalogue-authoring-standards.md) define the portable rules.
