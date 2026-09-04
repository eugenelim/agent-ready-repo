# Team orientation content inventory

This audit opens the current authored sources only. Generated projections under `web/src/content/journeys/` and `web/src/content/packs/` were skipped because they declare `generated: true`.

## Marketing home

| Section and source | What the reader is told | Single claim | Evidence beside the claim | Reader job and audience | Lifecycle | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Hero — `web/src/components/marketing/Hero.astro` | `core` carries a brief or spec through implementation, gates, and cold review; the catalogue applies that discipline elsewhere. | The product is a supervised build loop that cannot approve its own work. | none; the Claude marketplace link supports only its separate marketplace statement. | Understand the product before evaluation; champion, engineers, budget holder. | Both | Rework — the central claim has no checkable proof. |
| Stat strip — `web/src/components/marketing/StatStrip.astro` | There are three supervised loops, seven adapters, and one pip install. | The system has a small, concrete scope and simple entry. | none | Size the adoption effort; champion, engineers, platform, budget holder. | Both | Rework — all numeric claims ask for trust. |
| Pack catalogue / use cases — `web/src/components/marketing/PackCatalogue.astro` | Choose an outcome, then composable packs; seven cards name users and linked packs. | A team can choose only the workflows needed for its work. | Named `/packs/<pack>/` routes on every card and `/catalogue/`. | Recognize a job before pack names; champion, engineers, platform, budget holder. | Both | Keep — outcome-first routing has inspectable destinations. |
| The problem — `web/src/components/marketing/TheProblem.astro` | Unattended coding loops make and self-certify mistakes; non-bypassable mechanical gates are the answer. | Supervision through non-bypassable gates is necessary for safe agent work. | none | Assess adoption risk; champion, engineers, budget holder. | Both | Rework — the load-bearing risk claim has no artifact or example. |
| Three loops — `web/src/components/marketing/ThreeLoops.astro` | Discovery makes a brief, build makes shipped code, and release makes production; each has a human gate. | Discovery, build, and release form one supervised handoff chain. | `/journeys/product-engineering/`, `/journeys/core/`, and `/journeys/release-engineering/`. | Understand the operating model; champion, engineers, platform, budget holder. | Both | Keep — journey routes provide checkable follow-through. |
| Human control points — `web/src/components/marketing/HumanGates.astro` | Seven handoffs ask a person questions from exploration go/no-go through production ship. | Humans control every consequential handoff. | none; its only `/journeys/core/` link does not substantiate the cross-loop map. | Know retained decisions; champion, engineers, platform, budget holder. | Both | Rework — the complete gate map is unsupported. |
| Adapter matrix — `web/src/components/marketing/AdapterMatrix.astro` | Seven agents receive skills, subagents, and hooks; only Claude Code receives commands; one flag switches layouts. | One installation works across every major coding agent. | none | Check compatibility; champion, engineers, platform, budget holder. | Team adopting | Rework — compatibility claims lack a linked adapter contract. |
| Install terminal — `web/src/components/marketing/InstallTerminal.astro` | Four selectable command sets install `core`, discovery, inception, or solution architect; skill-reading agents inherit the loop. | A team can start its selected workflow with the shown command(s). | `python -m pip install agentbundle`, `agentbundle install --pack core`, and the displayed profile commands. | Begin evaluation or installation; champion, engineers, platform. | Team adopting | Keep — exact commands are testable. |
| Build your organization — `web/src/components/marketing/BuildYourOrg.astro` | Initialize a managed catalogue, select supported packs and profiles, encode conventions, validate, and distribute it without a fork. | An organization can govern its catalogue without a repository fork. | `agentbundle catalogue init` and `/docs/guides/_shared/how-to/create-a-catalogue/`. | Establish team-wide governance; champion, platform, budget holder. | Team adopting | Keep — command and destination are inspectable. |

## Documentation guides

“Marketing link” means a direct marketing-page destination to the area. The global marketing `Docs` link goes only to `/docs/`, so it is not counted as a direct link to each guide area.

| Area and authored path | Kind | First concrete accomplishment | Marketing link | Verdict |
| --- | --- | --- | --- | --- |
| Guides index — `guides/README.md` | Explanation | Follow P1 to install the lifecycle, adapt or start a project, and read its workspace queue. | No direct link. | Rework — it is the cross-catalogue route map but has no direct marketing handoff. |
| Shared guides — `guides/_shared/README.md` | Explanation | Install `agentbundle` from a clone via the first how-to. | Yes — Build your organization links to its create-a-catalogue how-to. | Keep — the only directly connected cross-catalogue entry. |
| Architect — `guides/architect/README.md` | Explanation | Run a read-only repository assessment and receive a correctable current-state map. | No direct link. | Rework — strong first task but no marketing handoff. |
| Atlassian — `guides/atlassian/README.md` | Explanation | Review a Jira backlog and identify stories not ready for engineering. | No direct link. | Rework — operational entry is clear but disconnected. |
| Catalogue curation — `guides/catalogue-curation/README.md` | Explanation | Read the skill standards governing a new or imported skill. | No direct link. | Rework — catalogue ownership bypasses this operator area. |
| Contracts — `guides/contracts/README.md` | Explanation | Generate a validated OpenAPI 3.1 contract from requirements or a domain model. | No direct link. | Keep — focused specialist route. |
| Converters — `guides/converters/README.md` | Explanation | Convert a PDF, Office file, or image to Markdown. | No direct link. | Keep — focused utility route. |
| Core — `guides/core/README.md` | Explanation | Start ordinary-language work and let `work-intake` route it to an artifact and state. | No direct link. | Rework — flagship workflow lacks a direct handoff. |
| Credential brokers — `guides/credential-brokers/README.md` | Explanation | Add a credentialed skill with a broker and declared credentials. | No direct link. | Keep — security-specific authoring start is clear. |
| Desk research — `guides/desk-research/README.md` | Explanation | Run a first research session across four depth modes. | No direct link. | Keep — concrete self-contained start. |
| Experience design — `guides/experience-design/README.md` | Explanation | Map a customer journey from a stated user need. | No direct link. | Keep — job-led specialist inventory. |
| Figma — `guides/figma/README.md` | Explanation | Inspect a Figma file from its URL, including nodes, comments, and renders. | No direct link. | Keep — bounded first task. |
| Frontend engineering — `guides/frontend-engineering/README.md` | Explanation | Choose the page/screen-contract path and produce a contract or explicit no-contract decision. | No direct link. | Keep — task table makes the next step explicit. |
| GitHub — `guides/github/README.md` | Explanation | Intake a GitHub Issue or Milestone as repository work without changing GitHub. | No direct link. | Keep — safe first operation is explicit. |
| Governance extras — `guides/governance-extras/README.md` | Explanation | Propose an open cross-cutting change as an RFC. | No direct link. | Keep — durable decision work is clear. |
| Terraform and OpenTofu — `guides/iac-terraform/README.md` | Reference | Install dependencies and ask the agent to generate IaC for a named cloud workload. | No direct link. | Keep — prerequisite and action are explicit. |
| Linear — `guides/linear/README.md` | Explanation | Set up credentials to read a named Linear project into the repository. | No direct link. | Keep — first action exposes the credential boundary. |
| Monorepo extras — `guides/monorepo-extras/README.md` | Explanation | Scaffold a conventions-complete shared package under `packages/`. | No direct link. | Keep — compact specialist route. |
| Product documentation — `guides/product-documentation/README.md` | Reference | Ask the agent to write a pack README, credential-rotation how-to, or audit missing docs. | No direct link. | Keep — concrete prompts match its reference role. |
| Product engineering — `guides/product-engineering/README.md` | Explanation | Shape a feature intent into a spec-ready piece of work. | No direct link. | Rework — it explains the marketed discovery loop but is not connected. |
| Product strategy — `guides/product-strategy/README.md` | Explanation | Run a SWOT and produce one committed strategy artifact. | No direct link. | Keep — clear upstream specialist start. |
| Release engineering — `guides/release-engineering/README.md` | Reference | Install `core` and `release-engineering`, then run a first release to G5. | No direct link. | Rework — it explains the marketed release loop but is not connected. |

## Duplication

- The three-loop model appears in marketing `ThreeLoops.astro` and `HumanGates.astro`; in `guides/README.md` paths P2, P3, and P5; in `guides/_shared/README.md` as “The three loops as a system”; and in the `product-engineering`, `core`, and `release-engineering` guide introductions.
- Installation and route choice appear in marketing `Hero.astro` and `InstallTerminal.astro`; in `guides/README.md` path P1 and shared list; and in `guides/_shared/README.md` through clone installation, user-scope installation, install routes, and CLI reference.
- Catalogue ownership appears in marketing `BuildYourOrg.astro`; in `guides/README.md` path P6 and role route; in `guides/_shared/README.md` through external-catalogue creation and pack-catalogue explanation; and in `guides/catalogue-curation/README.md`.
- Outcome-to-pack routing appears in marketing `PackCatalogue.astro` and in `guides/README.md` under “Choose what you want to achieve” and “Choose by role.”

## Orphans

No top-level area can be conclusively labelled unreachable from the checked sources. `docs-site/astro.config.ts` imports `docs-site/src/sidebar-config.json`, but that file is absent in this checkout, so the complete rendered sidebar cannot be inspected. Direct entry points establish this gap: marketing links directly only to the shared create-a-catalogue guide; its global `Docs` link reaches `/docs/`, whose authored index links to `core`, `product-strategy`, `experience-design`, `architect`, `atlassian`, `product-documentation`, and shared create-a-catalogue. The remaining areas have no direct route from either checked entry point: catalogue curation, contracts, converters, credential brokers, desk research, figma, frontend engineering, GitHub, governance extras, Terraform and OpenTofu, Linear, monorepo extras, product engineering, and release engineering. The missing sidebar configuration or rendered docs output is required to decide whether any is a true navigation orphan.

## Unevidenced marketing claims

Ranked by adoption load:

1. **Hero:** `core` cannot approve its own work.
2. **The problem:** unattended loops self-certify mistakes and require non-bypassable gates.
3. **Human control points:** the complete seven-gate cross-loop human-control map.
4. **Adapter matrix:** one install works across every major agent, including capability and layout projection.
5. **Stat strip:** three loops, seven adapters, and one pip install.
