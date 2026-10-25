---
title: Guides
summary: Choose the pack and guide that matches your outcome, from supervised delivery loops to research, architecture, integrations, and catalogue operations.
pack: _shared
kind: explanation
---

# Guides

**New here?** [See the operating model](_shared/explanation/the-operating-model.md): four stages, the packs in each, and where you decide.

**Start here:** [the install-to-ship walkthrough](#the-install-to-ship-walkthrough) takes you from installing the catalogue to a merged change you approved, in about ten hours.

## Find your job by stage

Work moves through four stages, and most work skips one or two. Find your stage, then open the job page.

**Set up a repository**

- [Start a project](core/how-to/start-a-project.md) gets a repository ready for your agent.
- [Connect your tracker](_shared/how-to/choose-a-tracker-integration.md) brings Jira, Linear, or GitHub work in.

**Decide what to build**

- [Research a question](desk-research/how-to/run-the-research.md) gives you an evidence-graded answer.
- [Understand the code](code-intelligence/how-to/investigate-a-codebase.md) shows what a codebase does and what a change would break.
- [Analyse the market](product-strategy/how-to/run-a-market-and-competitive-analysis.md) produces a written analysis.
- [Set direction and goals](product-strategy/how-to/set-the-direction.md) turns market knowledge into goals engineers can pick up.

**Shape it**

- [Shape an idea](product-engineering/how-to/frame-the-intent.md) turns a rough idea into a plan ready to build.
- [Design the architecture](architect/how-to/shape-an-architecture-concept.md) agrees a design on half a page.
- [Design the experience](experience-design/how-to/map-the-customer-journey.md) goes from a customer's goal to reviewed screens.
- [Design an API contract](contracts/how-to/generate-an-api-contract.md) gives you a checked contract.

**Build it**

- [Run the build loop](core/how-to/start-the-work.md) takes a change from a request to merged work.
- [Fix a bug](core/how-to/bug-fix.md) finds the cause and fixes it with the smallest change.
- [Review a pull request](core/how-to/review-someone-elses-pr.md) gets an independent review.
- [Build a page or component](frontend-engineering/how-to/page-screen-contract.md) checks accessibility, states, and layout.
- [Record a decision](repo-governance/how-to/new-adr.md) writes down why.
- [Write the docs](product-documentation/how-to/write-a-guide.md) documents a shipped feature.

**Ship it**

- [Release a change](release-engineering/how-to/run-a-release.md) deploys, checks, and ships on your approval.
- [Change infrastructure](iac-terraform/how-to/change-infrastructure.md) turns a request into reviewed Terraform or OpenTofu.
- [Measure delivery](atlassian/how-to/measure-flow-and-dora-metrics.md) reports cycle time and throughput from Jira.

## The install-to-ship walkthrough

This route is an ordered set of guides from installation to a governed, reported release. Each stage names what you need first, roughly what it costs, and which stage comes next.

### P1 · Adopt the catalogue — ~1 hour

**Prerequisite:** none. **For:** anyone, first session. **Stage:** before any of them.

1. [Install packs for your agent](_shared/how-to/install-packs.md)
2. [Install the whole lifecycle](_shared/how-to/install-packs.md#install-a-profile)
3. [Adapt an existing repo](core/how-to/adapt-to-project.md), or [start a new project](core/how-to/start-a-project.md)
4. [Orient at session start](core/how-to/orient-at-session-start.md)

**First value:** `workspace status` answers what to work on next.
**Ends at:** a repository whose queues you can read.

Next: [P2 · Shape what to build](#p2--shape-what-to-build--3-hours).

### P2 · Shape what to build — ~3 hours

**Prerequisite:** P1. **For:** product manager, product engineer, strategist. **Stage:** Shape it.

Start the shaping with the light path: frame an intent, test its riskiest assumption, and break it down. Take the wider path only when the problem is unclear or the bet is large. [The intent tree](product-engineering/explanation/the-intent-tree.md) explains the choice.

1. [Gather evidence](desk-research/) when the answer is not already known
2. [Shape a feature intent](product-engineering/how-to/shape-a-feature-intent.md) with `intent frame`
3. De-risk it with `intent de-risk`
4. [Shape the architecture concept](architect/how-to/shape-an-architecture-concept.md) when the work changes how the system is built
5. Break it down with `intent decompose`
6. [Hand the intent to the build loop](product-engineering/how-to/hand-an-intent-to-build.md)

On the wider path, [frame the situation](product-engineering/how-to/frame-a-situation.md) first. Then [identify opportunities](product-engineering/how-to/identify-opportunities.md), [generate options](product-engineering/how-to/generate-solution-options.md), and [place a bet](product-engineering/how-to/place-a-bet.md). Map the capabilities before you shape the architecture concept.

**First value:** one written intent naming an outcome and the bet behind it.
**Ends at:** Core intake, which picks the route from the content: a spec, a delivery brief, or a minimum repository intent.

Next: [P3 · Build it](#p3--build-it--2-hours). For a wider alternative, see [P2b · the four product disciplines](#p2b--take-the-wider-route-through-the-four-disciplines--4-hours).

### P2b · Take the wider route through the four disciplines — ~4 hours

**Prerequisite:** P1. **For:** product manager, researcher, designer, product engineer. **Stage:** Decide what to build, then Shape it.

This is an alternative to P2, not something you do after it. Take P2 when you change something that exists and need a framed, evidenced bet. Take P2b when the work also needs a strategic choice and a designed surface, such as a new product area or a user-facing flow.

1. [Find out what is true](desk-research/) hands Product Strategy graded evidence.
2. [Decide what to build](product-strategy/) hands Experience Design a committed strategy.
3. [Design how it should feel](experience-design/) hands Product Engineering a per-screen state matrix.
4. [Shape the bet and build it](product-engineering/) ends with a shaped bet and a change you approved.

You can stop after any step and still hold the artifact it produced.

**First value:** graded evidence on your question, before anyone commits to an answer.
**Ends at:** a shaped bet whose evidence, strategy, and design you can point to.

Next: [P3 · Build it](#p3--build-it--2-hours).

### P3 · Build it — ~2 hours

**Prerequisite:** P2, or an existing spec. **For:** engineer, agent. **Stage:** Build it.

1. [Orient at session start](core/how-to/orient-at-session-start.md)
2. [Plan and execute non-trivial work](core/how-to/plan-and-execute-non-trivial-work.md)
3. [Review someone else's PR](core/how-to/review-someone-elses-pr.md)
4. [Close and disposition the work](core/how-to/close-and-disposition-work.md)

**First value:** a spec and plan you approved before any code was written.
**Ends at:** a merged change, and the decision to merge is yours.

Next: [P4 · Decide together](#p4--decide-together--15-hours).

### P4 · Decide together — ~1.5 hours

**Prerequisite:** P1. **For:** tech lead, architect. **Stage:** any. Decisions get written down wherever they are made.

1. [The governance index](repo-governance/how-to/governance-index.md) shows whether you need an RFC, an ADR, or a spec.
2. [Propose an RFC](repo-governance/how-to/new-rfc.md)
3. [Record an ADR](repo-governance/how-to/new-adr.md)

An RFC or ADR is written from the artifacts of P2: an intent, a decision brief, a research survey, or an architecture concept.

**First value:** a circulated proposal with its alternatives written down.
**Ends at:** an accepted decision that outlives the people who made it.

Next: [P5 · Ship and report](#p5--ship-and-report--2-hours).

### P5 · Ship and report — ~2 hours

**Prerequisite:** P3. **For:** delivery lead, SRE. **Stage:** Ship it.

This release and reporting stage takes the build through its human ship gate.

1. [The release loop](release-engineering/explanation/the-release-loop.md)
2. [Run a release](release-engineering/how-to/run-a-release.md)
3. [Project slices out to a tracker](_shared/how-to/project-slices-to-a-tracker.md), or [intake from one](_shared/how-to/choose-a-tracker-integration.md)
4. [Measure flow and DORA metrics](atlassian/how-to/measure-flow-and-dora-metrics.md)

**First value:** a deployed artifact validated in an environment like production.
**Ends at:** a human ratifying the production ship.

## Extend the catalogue

### P6 · Extend the catalogue — ~3 hours

**Prerequisite:** P1 and P3. **For:** AI enablement, catalogue owner.

1. [Why catalogue curation](catalogue-curation/explanation/why-catalogue-curation.md)
2. [Your first skill](catalogue-curation/tutorials/your-first-skill.md)
3. [Build an org stack pack](_shared/how-to/build-an-org-stack-pack.md)
4. [Create a catalogue](_shared/how-to/create-a-catalogue.md)

**First value:** one skill of your own that your agent can run.
**Ends at:** a catalogue your organisation owns.

## Choose by outcome

- **Decide what to build:** [`desk-research`](desk-research/), then [`product-strategy`](product-strategy/), then [`product-engineering`](product-engineering/).
- **Design the product and system:** [`experience-design`](experience-design/), [`architect`](architect/), [`contracts`](contracts/), and [`frontend-engineering`](frontend-engineering/).
- **Build and review software:** [`core`](core/), with [`code-intelligence`](code-intelligence/), [`repo-governance`](repo-governance/), and [`monorepo-extras`](monorepo-extras/).
- **Provision and release safely:** [`iac-terraform`](iac-terraform/), then [`release-engineering`](release-engineering/).
- **Work with team systems and evidence:** [`atlassian`](atlassian/), [`github`](github/), [`linear`](linear/), [`figma`](figma/), [`converters`](converters/), and [`credential-brokers`](credential-brokers/).
- **Document what ships:** [`product-documentation`](product-documentation/).
- **Build and govern a catalogue:** [`catalogue-curation`](catalogue-curation/), with the [catalogue authoring standards](_shared/reference/catalogue-authoring-standards.md).

## Every pack

Each pack has its own guide home with a short list of its job pages.

- [`architect`](architect/): design a system and draw it.
- [`atlassian`](atlassian/): work with Jira and Confluence, and measure delivery.
- [`catalogue-curation`](catalogue-curation/): write, import, and govern catalogue skills.
- [`code-intelligence`](code-intelligence/): query an indexed code graph.
- [`contracts`](contracts/): write API and event contracts.
- [`converters`](converters/): convert documents and publish Markdown.
- [`core`](core/): take work from a request to a merged change.
- [`credential-brokers`](credential-brokers/): keep secrets out of your agent's context.
- [`desk-research`](desk-research/): get an evidence-graded answer.
- [`experience-design`](experience-design/): design reviewed screens.
- [`figma`](figma/): read a Figma file.
- [`frontend-engineering`](frontend-engineering/): build and check a page or component.
- [`github`](github/): bring GitHub work into the repository.
- [`repo-governance`](repo-governance/): record decisions and proposals.
- [`iac-terraform`](iac-terraform/): change infrastructure with review.
- [`linear`](linear/): bring Linear work into the repository.
- [`monorepo-extras`](monorepo-extras/): scaffold a new package.
- [`product-documentation`](product-documentation/): write and check product docs.
- [`product-engineering`](product-engineering/): shape a bet and hand it to delivery.
- [`product-strategy`](product-strategy/): analyse the market and set direction.
- [`release-engineering`](release-engineering/): deploy, verify, and ship.

## Guidance for every pack

[`_shared/`](_shared/) holds the guides that apply whichever packs you install.

- [Install agentbundle](_shared/how-to/install-agentbundle.md), [install packs](_shared/how-to/install-packs.md), [configure it](_shared/how-to/configure-agentbundle.md), and [upgrade packs](_shared/how-to/upgrade-packs.md).
- [Check adapter support](_shared/reference/adapter-support.md) for your agent tool.
- [Start, remember, inspect, or refresh repository work](_shared/how-to/use-work-intake.md), with the [routing and lifecycle reference](_shared/reference/work-intake-routing-and-lifecycle.md).
- [Understand packs, profiles, and catalogues](_shared/explanation/pack-catalogue.md), then [apply the authoring standards](_shared/reference/catalogue-authoring-standards.md).

To write a guide, use the [`author-product-docs`](product-documentation/how-to/author-product-docs.md) workflow.
