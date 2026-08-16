# Guides

Use this catalogue to add repeatable, supervised ways of working to your agent. Start with the outcome you need; the linked pack guides explain what to install, what to ask for, what the agent produces, and where a human decides.

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

- [Get from zero to the three-loop operating model](_shared/explanation/the-three-loops.md).
- [Understand packs, profiles, adapters, composition, and catalogue ownership](_shared/explanation/pack-catalogue.md).
- [Choose an install route](_shared/explanation/install-routes.md) and [check adapter support](_shared/reference/adapter-support.md).
- [Install a curated profile](_shared/how-to/install-a-profile.md), [preview a change](_shared/how-to/preview-install-or-upgrade.md), or [upgrade safely](_shared/how-to/upgrade-packs.md).
- [Create your own catalogue](_shared/how-to/create-a-catalogue.md) and [apply its portable authoring standards](_shared/reference/catalogue-authoring-standards.md).

Claude users can [add this catalogue as a plugin marketplace](_shared/explanation/install-routes.md) and install user-scope packs directly. Repo-scoped packs such as `core` still install with `agentbundle` so their workflow belongs to the project and team.

The public documentation site generates the complete pack and guide navigation from this tree. [Browse the complete generated pack reference](https://eugenelim.github.io/agent-ready-repo/docs/packs/); this page stays a route map rather than duplicating that inventory by hand.

## Writing a guide

Use the [`author-product-docs`](product-documentation/how-to/author-product-docs.md) workflow. It selects the right page contract and destination; the [catalogue authoring standards](_shared/reference/catalogue-authoring-standards.md) define the portable rules.
