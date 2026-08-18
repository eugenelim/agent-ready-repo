# Guide metadata decisions

- **Status:** Accepted
- **Owner:** eugenelim
- **Spec:** [`spec.md`](spec.md)
- **Decision date:** 2026-08-17

This ledger is the approved editorial input to implementation. It is not a
generated source-of-truth substitute: each row was reviewed as content, and
implementation must copy it exactly unless the spec is amended first. For the
four files owned by `guide-title-clarity`, that spec's approved replacement is
the final `title`; the title recorded here is the reviewed pre-change baseline.

## Backfill inventory and exceptions

The incomplete-metadata inventory contains exactly 125 affected public content
pages. Exactly five additional validator findings are structural or
non-content Markdown and receive no guide metadata:

- `guides/AGENTS.md` — agent authoring instructions, not reader content;
- `guides/_shared/tutorials/README.md` — tutorial-quadrant authoring template;
- `guides/_shared/how-to/README.md` — how-to-quadrant authoring template;
- `guides/_shared/reference/README.md` — reference-quadrant authoring template;
- `guides/_shared/explanation/README.md` — explanation-quadrant authoring
  template.

`guides/README.md` is affected public content and is owned by `_shared` with
kind `explanation`. Public guides that already satisfy the metadata contract
are outside this backfill ledger; global validator and emitted-route coverage
must continue to include them.

## Approved move and compatibility

Move `guides/_reference/catalogue-format.md` to
`guides/_shared/reference/catalogue-format.md`. It remains `_shared` reference
content. Preserve its public route as
`/docs/guides/_reference/catalogue-format/` through an explicit slug, and
remove the empty `_reference` group only when the generated navigation and
route checks prove that is safe.

## Title and content findings

- Titles remain the current H1 except for the four changes owned by
  `guide-title-clarity`; that spec supplies the final title to source and
  emitted-output assertions.
- The approved corpus has no normalized duplicate titles.
- Potentially broad titles such as “Guides,” “Shared guides,” “Frontend
  Engineering guides,” the “About…” titles, and the “Reference…” titles are
  retained. Their summaries supply the missing information scent, and there is
  no contradictory evidence that warrants reopening the fixed title scope.
- As one same-page content correction, replace the false opening in
  `guides/_shared/how-to/pack-journey-authoring.md` with: “Use this when you
  maintain a catalogue whose packs publish canonical journey pages. This guide
  defines the source, metadata, migration, and projection contract for a
  pack-owned `JOURNEY.md`.”

## Review batches

1. Root, shared, and catalogue-format content — 23 pages.
2. Architect, Atlassian, and Catalogue Curation — 23 pages.
3. Contracts, Converters, and Core — 24 pages.
4. Credential Brokers, Desk Research, Experience Design, Figma, Frontend
   Engineering, and GitHub — 22 pages.
5. Governance Extras, Linear, Monorepo Extras, Product Documentation, and
   Product Strategy — 17 pages.
6. Product Engineering — 16 pages.

For each batch, apply only the rows below, compare all four fields (using the
`guide-title-clarity` replacement for its four owned titles), run the
scoped schema validator and the global normalized-title scan, and make no other
body edits. After all batches, enumerate all 125 affected pages in emitted-
output tests across both sites, then run complete public-guide coverage so
pre-existing compliant pages cannot disappear. Verify titles, descriptions,
routes, aliases, links, and fragments.

## Approved metadata

| Batch | Final source path | `title` | `summary` | `pack` | `kind` |
| ---: | --- | --- | --- | --- | --- |
| 1 | `guides/README.md` | Guides | Choose the pack and guide that matches your outcome, from supervised delivery loops to research, architecture, integrations, and catalogue operations. | `_shared` | `explanation` |
| 1 | `guides/_shared/README.md` | Shared guides | Find cross-catalogue guidance for installing, upgrading, authoring, integrating, and understanding packs regardless of which packs you use. | `_shared` | `explanation` |
| 1 | `guides/_shared/explanation/pack-catalogue.md` | The pack catalogue | Understand how packs, profiles, adapters, catalogues, and `agentbundle` compose into an organization-owned workflow distribution system. | `_shared` | `explanation` |
| 1 | `guides/_shared/explanation/pack-workflow-design.md` | Pack workflow design | Design a coherent pack by classifying its workflow, mapping its session arc, naming skills, choosing storage paths, and registering lifecycle state. | `_shared` | `explanation` |
| 1 | `guides/_shared/explanation/shaping-a-new-engagement.md` | Shaping a new engagement: product intent and the architecture concept | Understand how product intent and architecture concepts constrain and inform one another at the start of an engagement. | `_shared` | `explanation` |
| 1 | `guides/_shared/explanation/the-three-loops.md` | The three loops — the company operating model | Understand why discovery, build, and release are separate supervised loops and how their handoffs form one operating model. | `_shared` | `explanation` |
| 1 | `guides/_shared/how-to/browser-automation-skill.md` | How to author a browser-automation skill | Build a browser-driving skill with persistent sessions, robust authentication handoff, durable probes, and maintainable selectors. | `_shared` | `how-to` |
| 1 | `guides/_shared/how-to/build-an-org-stack-pack.md` | How to ship your organization's standard stack as a reusable pack | Package organizational architecture, conventions, and framework knowledge into a reusable pack and one-command profile. | `_shared` | `how-to` |
| 1 | `guides/_shared/how-to/choose-a-tracker-integration.md` | Choose a tracker integration for work intake | Select the appropriate tracker intake route while keeping tracker object types separate from repository artifact routing. | `_shared` | `how-to` |
| 1 | `guides/_shared/how-to/configure-adapter.md` | Configure your agent adapter | Pin or override the target adapter so installations consistently project into the intended agent environment. | `_shared` | `how-to` |
| 1 | `guides/_shared/how-to/configure-catalogue-enterprise-distribution.md` | How to configure a catalogue for enterprise distribution | Configure catalogue distribution coordinates and generated defaults so managed installations use the approved internal channel automatically. | `_shared` | `how-to` |
| 1 | `guides/_shared/how-to/create-a-self-hosted-catalogue.md` | How to create a self-hosted catalogue | Derive, brand, validate, and package an owned catalogue from an existing source without losing provenance or safety rails. | `_shared` | `how-to` |
| 1 | `guides/_shared/how-to/design-a-profile.md` | How to design a profile | Define a persona-specific pack profile that passes the catalogue’s cohesion, scope, dependency, and validation tests. | `_shared` | `how-to` |
| 1 | `guides/_shared/how-to/install-a-profile.md` | How to install a curated set of packs in one command | Install a role or governance profile at the correct scope without invoking each constituent pack separately. | `_shared` | `how-to` |
| 1 | `guides/_shared/how-to/pack-journey-authoring.md` | How to author a pack-local JOURNEY.md | Author a canonical pack-owned journey with validated metadata, gates, state transitions, and projection-safe migration. | `_shared` | `how-to` |
| 1 | `guides/_shared/how-to/run-a-full-inception.md` | Run a full inception for a new project | Sequence research, product, architecture, and core workflows from a raw idea to a build-ready walking-skeleton spec. | `_shared` | `how-to` |
| 1 | `guides/_shared/reference/agentbundle.md` | `agentbundle` — reference | Look up the supported install, inspection, preview, configuration, source-resolution, networking, and failure behavior of `agentbundle`. | `_shared` | `reference` |
| 1 | `guides/_shared/reference/agentskills-io-standard.md` | agentskills.io specification — applied reference | Apply the external skill specification together with this catalogue’s additional layout, description, security, and enforcement rules. | `_shared` | `reference` |
| 1 | `guides/_shared/reference/catalogue-format.md` | Catalogue format | Use the authoritative directory, marker, schema, adapter-artifact, and validation contract when creating or checking a catalogue. | `_shared` | `reference` |
| 1 | `guides/_shared/reference/output-rendering.md` | Output rendering directives | Select and declare the canonical rendering shape, columns, status vocabulary, and omission rules for structured skill output. | `_shared` | `reference` |
| 1 | `guides/_shared/reference/skill-script-conventions.md` | Skill script conventions | Apply the catalogue’s common flags, usage documentation, shortcut, shared-library, setup, and operation-logging conventions to helper scripts. | `_shared` | `reference` |
| 1 | `guides/_shared/reference/skill-ux-patterns.md` | Skill UX patterns | Apply the detailed alignment, truncation, command-bar, confirmation, card, and progress patterns used by structured skill output. | `_shared` | `reference` |
| 1 | `guides/_shared/reference/tracker-vocabulary.md` | Tracker intake vocabulary | Distinguish tracker objects and profile hints from the repository artifacts and lifecycle routes selected by `work-intake`. | `_shared` | `reference` |
| 2 | `guides/architect/README.md` | `architect` — guides | Choose the architecture workflow for shaping a concept, drawing a system, reviewing an artifact, or establishing a repository reference architecture. | `architect` | `explanation` |
| 2 | `guides/architect/explanation/architect-diagram-skill-design.md` | Why the architect-diagram skill works the way it does | Understand the notation, layout, visual-encoding, grounding, and portability decisions behind the architecture-diagram workflow. | `architect` | `explanation` |
| 2 | `guides/architect/how-to/diagram-a-system.md` | Diagram a system | Produce a self-checked Mermaid diagram in the notation appropriate to a system, flow, state model, data model, or deployment. | `architect` | `how-to` |
| 2 | `guides/architect/how-to/establish-reference-architecture.md` | Establish your repo's reference architecture | Create a normative `reference.md` from settled repository decisions so later designs and reviews follow a real golden path. | `architect` | `how-to` |
| 2 | `guides/architect/how-to/review-an-architecture-artifact.md` | Review an architecture artifact | Obtain a severity-ranked architecture verdict, concrete findings, and an independent review for a finished-enough design artifact. | `architect` | `how-to` |
| 2 | `guides/architect/how-to/shape-an-architecture-concept.md` | Shape an architecture concept | Agree a bounded Stage 0 concept, alternatives, provider, constraints, and key tradeoff before committing to a full design document. | `architect` | `how-to` |
| 2 | `guides/architect/reference/reference-architecture.md` | `reference.md` sections and the stack-pack contract | Look up the required reference-architecture sections and the contract by which an optional stack pack supplies them. | `architect` | `reference` |
| 2 | `guides/architect/tutorials/architect-first-session.md` | Your first architecture session | Produce a first plain-language architecture snapshot of an existing codebase in a guided session. | `architect` | `tutorial` |
| 2 | `guides/architect/tutorials/create-your-reference-architecture.md` | Create and use your `reference.md` | Commit one real architecture standard and use it immediately to steer a design decision. | `architect` | `tutorial` |
| 2 | `guides/atlassian/README.md` | `atlassian` — guides | Choose the workflow for tracker intake, story improvement, team status, publishing, flow metrics, or adoption reporting. | `atlassian` | `explanation` |
| 2 | `guides/atlassian/explanation/ai-adoption-measurement.md` | Measuring AI adoption with flow metrics | Understand what delivery-flow comparisons can and cannot establish about AI-assisted engineering adoption. | `atlassian` | `explanation` |
| 2 | `guides/atlassian/how-to/crawl-and-publish-confluence.md` | Crawl and publish Confluence | Mirror a documentation space to Markdown, publish reviewed Markdown back, or complete a controlled round trip. | `atlassian` | `how-to` |
| 2 | `guides/atlassian/how-to/measure-flow-and-dora-metrics.md` | Measure flow and DORA metrics | Produce scoped delivery-flow and DORA measurements from tracker history, with cohort comparison when requested. | `atlassian` | `how-to` |
| 2 | `guides/atlassian/how-to/report-ai-adoption-as-a-delivery-lead.md` | Report AI adoption as a delivery lead | Turn consistent cohort or before-and-after flow measurements into a caveated stakeholder-ready adoption report. | `atlassian` | `how-to` |
| 2 | `guides/catalogue-curation/README.md` | `catalogue-curation` — guides | Choose the operator workflow for authoring, surveying, assimilating, governing, or redistributing catalogue primitives. | `catalogue-curation` | `explanation` |
| 2 | `guides/catalogue-curation/explanation/catalogue-operator-journey.md` | Catalogue operator journey | Understand how catalogue authors, maintainers, and organizational stack owners use the curation workflows at different operating altitudes. | `catalogue-curation` | `explanation` |
| 2 | `guides/catalogue-curation/explanation/skill-standards.md` | Skill standards | Understand the safety, portability, and craft standards applied to every authored or assimilated skill. | `catalogue-curation` | `explanation` |
| 2 | `guides/catalogue-curation/explanation/the-convergence-model.md` | The convergence model | Understand why safe assimilation reviews and reshapes external primitives instead of copying them directly. | `catalogue-curation` | `explanation` |
| 2 | `guides/catalogue-curation/explanation/why-catalogue-curation.md` | Why curation is its own pack | Understand why catalogue growth, adoption, and reproduction require a governance layer distinct from ordinary repository governance. | `catalogue-curation` | `explanation` |
| 2 | `guides/catalogue-curation/how-to/survey-a-repo.md` | Survey a repo for what to adopt | Inventory an external repository, classify every candidate, and produce a resumable adoption RFC. | `catalogue-curation` | `how-to` |
| 2 | `guides/catalogue-curation/reference/ledger-and-guard.md` | Reference: the ledger and the engine guard | Look up the append-only assimilation ledger, progress model, confinement guard, and recovery behavior. | `catalogue-curation` | `reference` |
| 2 | `guides/catalogue-curation/tutorials/first-assimilation.md` | Your first assimilation | Safely review, reshape, verify, and adopt one external skill into the catalogue. | `catalogue-curation` | `tutorial` |
| 2 | `guides/catalogue-curation/tutorials/your-first-subagent.md` | Your first subagent assimilation | Safely review, reshape, verify, and adopt one external subagent definition into the catalogue. | `catalogue-curation` | `tutorial` |
| 3 | `guides/contracts/README.md` | `contracts` — guides | Choose the contract-first workflow for synchronous APIs, asynchronous events, and pluggable organizational standards. | `contracts` | `explanation` |
| 3 | `guides/contracts/explanation/contract-first-design.md` | Contract-first design | Understand why versioned API or event agreements precede implementation and govern producers, consumers, tests, and tooling. | `contracts` | `explanation` |
| 3 | `guides/contracts/how-to/author-an-event-contract.md` | Author an event contract | Produce a validated AsyncAPI contract with channels, operations, messages, envelopes, and schemas ready for consumers. | `contracts` | `how-to` |
| 3 | `guides/contracts/how-to/generate-an-api-contract.md` | Generate an API contract | Produce a validated OpenAPI 3.1 contract from requirements or a domain model under the active design standard. | `contracts` | `how-to` |
| 3 | `guides/contracts/reference/contract-skills.md` | The contract skills | Look up each contract skill’s inputs, stages, emitted document shape, validation, and standard-selection mechanism. | `contracts` | `reference` |
| 3 | `guides/converters/README.md` | `converters` — guides | Choose a conversion workflow for extracting Markdown, rendering diagrams, publishing HTML, or filling branded Office templates. | `converters` | `explanation` |
| 3 | `guides/converters/how-to/convert-documents-to-markdown.md` | Convert documents to Markdown | Extract readable Markdown from documents or images with explicit fidelity warnings and conversion statistics. | `converters` | `how-to` |
| 3 | `guides/converters/how-to/convert-markdown-to-html-and-email.md` | Convert Markdown to HTML, and email to Markdown | Produce self-contained HTML from Markdown or structured Markdown from an email file. | `converters` | `how-to` |
| 3 | `guides/converters/how-to/publish-markdown-to-office.md` | Publish Markdown as a branded Office file | Fill an approved branded template with Markdown content to produce a Word document, presentation, or workbook. | `converters` | `how-to` |
| 3 | `guides/converters/how-to/render-mermaid-diagrams.md` | Render Mermaid diagrams to images | Convert Mermaid fences into PNG or SVG assets and optionally rewrite the Markdown to reference them. | `converters` | `how-to` |
| 3 | `guides/converters/reference/converter-skills.md` | Converter skills | Look up each converter’s accepted inputs, outputs, options, dependencies, and operational limitations. | `converters` | `reference` |
| 3 | `guides/core/README.md` | `core` — guides | Start durable work through one intake route, then carry approved work through planning, execution, verification, independent review, and merge. | `core` | `explanation` |
| 3 | `guides/core/explanation/foundation-vs-map.md` | About foundation vs. map | Understand why normative architecture standards and the descriptive codebase map belong in separate documents. | `core` | `explanation` |
| 3 | `guides/core/explanation/token-economy.md` | The token economy of the loop | Understand where the supervised loop spends context and why independent planning and review are worth their cost. | `core` | `explanation` |
| 3 | `guides/core/explanation/walking-skeleton-vs-throwaway.md` | About the walking skeleton | Understand why a greenfield project keeps a minimal end-to-end slice instead of discarding a prototype. | `core` | `explanation` |
| 3 | `guides/core/explanation/why-the-plan-owns-the-lld.md` | About the plan owning the low-level design | Understand why implementation design belongs in the mutable plan while the spec remains a behavioral contract. | `core` | `explanation` |
| 3 | `guides/core/how-to/bug-fix.md` | How to fix a bug | Diagnose the root cause, constrain the change, prove the regression, and deliver a reviewed fix. | `core` | `how-to` |
| 3 | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | How to plan and execute non-trivial work | Turn an approved spec into a locked plan, checked implementation, independent review, and merge-ready change. | `core` | `how-to` |
| 3 | `guides/core/how-to/record-your-foundation-during-inception.md` | Decide and record your foundation during inception | Select a stack, record the rationale, and seed the normative reference architecture before the walking skeleton. | `core` | `how-to` |
| 3 | `guides/core/how-to/review-someone-elses-pr.md` | Review a branch or PR you didn't write | Run an independent, severity-ranked review of another author’s change and return actionable findings. | `core` | `how-to` |
| 3 | `guides/core/how-to/run-headless-session.md` | Run a headless session with workspace-mcp | Drive unattended sessions through structured queue discovery, state observation, scoped Git operations, and explicit gate handling. | `core` | `how-to` |
| 3 | `guides/core/how-to/start-a-project.md` | How to start working on a project | Orient to an existing governed repository and identify the first ready work item without bypassing lifecycle state. | `core` | `how-to` |
| 3 | `guides/core/reference/spec-shape-and-lld.md` | Spec `Shape:` and the plan's `## Design (LLD)` | Look up the feature-shape classification, plan design sections, stack derivation, and boundary between behavioral and implementation decisions. | `core` | `reference` |
| 3 | `guides/core/tutorials/start-a-new-project.md` | From idea to a walking skeleton: start a new project | Create a new governed repository with a recorded foundation and an approved first walking-skeleton spec. | `core` | `tutorial` |
| 4 | `guides/credential-brokers/README.md` | `credential-brokers` — guides | Understand and select the credential setup and broker interfaces that keep cleartext secrets out of agent context. | `credential-brokers` | `explanation` |
| 4 | `guides/credential-brokers/reference/credbroker-sso-api.md` | `credbroker` SSO API | Look up the supported in-process API for checking, capturing, and using brokered SSO sessions without handling subprocess details. | `credential-brokers` | `reference` |
| 4 | `guides/desk-research/README.md` | `desk-research` — guides | Choose the appropriate episodic depth or sustained-project workflow for an evidence-grounded research question. | `desk-research` | `explanation` |
| 4 | `guides/desk-research/explanation/episodic-vs-project-research.md` | Episodic vs project research — the two axes | Understand when a question deserves one research session and when it requires a durable project corpus. | `desk-research` | `explanation` |
| 4 | `guides/desk-research/explanation/research-methodology.md` | Research methodology — the why behind the pack | Understand the pack’s source, depth, confidence, citation, perspective, and counter-evidence design choices. | `desk-research` | `explanation` |
| 4 | `guides/desk-research/how-to/research-pipelines.md` | How to run the research pipelines | Run the survey, competing-hypotheses, or decision-archaeology pipeline appropriate to a bounded research question. | `desk-research` | `how-to` |
| 4 | `guides/desk-research/how-to/run-a-research-project-into-an-rfc.md` | Run a research project and feed it into an RFC | Carry a multi-session corpus into a confidence-graded synthesis and preserve its evidence when opening an RFC. | `desk-research` | `how-to` |
| 4 | `guides/desk-research/reference/desk-research-pack.md` | Desk Research pack — reference | Look up every research skill and subagent, its inputs, outputs, depth, consumers, and lifecycle role. | `desk-research` | `reference` |
| 4 | `guides/desk-research/tutorials/desk-research-first-session.md` | Your first research session | Produce and compare research outputs at each episodic depth in a guided first session. | `desk-research` | `tutorial` |
| 4 | `guides/desk-research/tutorials/your-first-research-project.md` | Your first research project | Build a durable source corpus and finish with a cited, confidence-graded brief ready for a decision-maker. | `desk-research` | `tutorial` |
| 4 | `guides/experience-design/README.md` | `experience-design` — guides | Move from an understood need through journeys, screens, service evidence, design decisions, and independent review. | `experience-design` | `explanation` |
| 4 | `guides/experience-design/explanation/the-experience-thread.md` | The experience thread | Understand how journey, flow, service, content, visual, interaction, and review artifacts form one traceable design thread. | `experience-design` | `explanation` |
| 4 | `guides/experience-design/how-to/author-design-intent.md` | Thread a feature from journey to screens | Produce the durable journey, screen-flow, service, design-intent, and review artifacts needed to implement a feature. | `experience-design` | `how-to` |
| 4 | `guides/experience-design/how-to/copy-boundary.md` | Choose the right copy skill | Route a copy task to copy direction, tone of voice, content design, or product microcopy without duplicating work. | `experience-design` | `how-to` |
| 4 | `guides/experience-design/reference/experience-design.md` | `experience-design` — skill and reviewer reference | Look up each design skill and reviewer’s inputs, outputs, write boundary, routing rules, and artifact contract. | `experience-design` | `reference` |
| 4 | `guides/figma/README.md` | `figma` — guides | Understand the read, render, comment, history, and diagram-conversion capabilities exposed through the credentialed design-file primitive. | `figma` | `explanation` |
| 4 | `guides/figma/how-to/inspect-a-figma-file.md` | Inspect a Figma file | Retrieve and report the requested design-file structure, nodes, metadata, comments, history, renders, or connector graph. | `figma` | `how-to` |
| 4 | `guides/figma/reference/figma-skill.md` | The `figma` skill | Look up the design-file skill’s commands, supported resources, output forms, permissions, and API limitations. | `figma` | `reference` |
| 4 | `guides/figma/tutorials/figma-first-session.md` | Your first Figma session | Establish a credentialed connection and inspect the page and frame structure of an accessible design file. | `figma` | `tutorial` |
| 4 | `guides/frontend-engineering/README.md` | Frontend Engineering guides | Find the create, retrofit, audit, verification, contract, and evidence workflows used to deliver a frontend surface. | `frontend-engineering` | `explanation` |
| 4 | `guides/github/README.md` | `github` — guides | Understand the fixed-host, read-only intake workflow that turns selected repository work into canonical local work. | `github` | `explanation` |
| 4 | `guides/github/how-to/intake-a-github-milestone-as-a-brief.md` | Intake GitHub work into the repository | Read selected issue or milestone content and route it through `work-intake` without writing back to the tracker. | `github` | `how-to` |
| 5 | `guides/governance-extras/README.md` | `governance-extras` — guides | Choose the governed workflow for proposing a cross-cutting change, recording a decision, or updating repository conventions. | `governance-extras` | `explanation` |
| 5 | `guides/governance-extras/how-to/extension-contract.md` | How to define an extension contract | Document an intentional extension hook’s shape, guarantees, exclusions, ownership, and verification method. | `governance-extras` | `how-to` |
| 5 | `guides/governance-extras/how-to/new-rfc.md` | How to propose a cross-cutting change (RFC) | Produce and progress a researched RFC for a cross-cutting, prior-decision, or consensus-requiring change. | `governance-extras` | `how-to` |
| 5 | `guides/governance-extras/tutorials/governance-extras-first-session.md` | Your first governance session | Install the governance pack and record one reviewed architecture decision through its confirmation gate. | `governance-extras` | `tutorial` |
| 5 | `guides/linear/README.md` | `linear` — guides | Understand the boundary between first-time repository intake and approval-gated synchronization of an existing brief. | `linear` | `explanation` |
| 5 | `guides/linear/how-to/linear-brief-intake-and-sync.md` | Choose Linear intake or brief sync | Choose first-time intake or controlled brief synchronization and receive the corresponding validated route or update preview. | `linear` | `how-to` |
| 5 | `guides/monorepo-extras/README.md` | `monorepo-extras` — guides | Understand the repository-scoped package scaffolding workflow and the conventions carried by its shared-library template. | `monorepo-extras` | `explanation` |
| 5 | `guides/monorepo-extras/how-to/scaffold-a-new-package.md` | Scaffold a new package | Create a conventions-complete shared library, wire it into the workspace, and verify its placeholder test and architecture entry. | `monorepo-extras` | `how-to` |
| 5 | `guides/monorepo-extras/reference/new-package.md` | `new-package` reference | Look up the generated package tree, template contents, post-scaffold steps, and boundaries of the package workflow. | `monorepo-extras` | `reference` |
| 5 | `guides/product-documentation/how-to/use-author-product-docs.md` | How to create and maintain product documentation | Create, revise, retrofit, audit, or verify the correct reader-facing documentation artifact against canonical product behavior. | `product-documentation` | `how-to` |
| 5 | `guides/product-strategy/README.md` | `product-strategy` — guides | Set the committed market, product, objective, experience, and content direction upstream of individual initiatives. | `product-strategy` | `explanation` |
| 5 | `guides/product-strategy/explanation/why-strategy-is-its-own-seat.md` | Why strategy is its own seat | Understand why market analysis, portfolio direction, objectives, and experience governance require a distinct upstream role. | `product-strategy` | `explanation` |
| 5 | `guides/product-strategy/how-to/cascade-okrs-into-the-shaping-queue.md` | Cascade OKRs into the shaping queue | Convert objective gaps into ranked, traceable strategy entries ready for product shaping. | `product-strategy` | `how-to` |
| 5 | `guides/product-strategy/how-to/run-a-market-and-competitive-analysis.md` | Run a market and competitive analysis | Produce the specific internal, competitive, macro, or portfolio analysis needed for a strategic decision. | `product-strategy` | `how-to` |
| 5 | `guides/product-strategy/how-to/set-ux-and-content-strategy.md` | Set UX and content strategy | Commit the experience vision and content-governance system before journeys and screens are designed. | `product-strategy` | `how-to` |
| 5 | `guides/product-strategy/reference/frameworks-and-artifacts.md` | Reference: frameworks and artifacts | Look up every strategy skill, its framework, emitted artifact, owning pillar, and configurable output location. | `product-strategy` | `reference` |
| 5 | `guides/product-strategy/tutorials/run-your-first-swot.md` | Run your first SWOT | Produce a grounded four-quadrant strategic position from a guided first analysis. | `product-strategy` | `tutorial` |
| 6 | `guides/product-engineering/README.md` | `product-engineering` — guides | Shape a raw product signal through intent, risk, alternatives, capability decomposition, and delivery-ready briefs. | `product-engineering` | `explanation` |
| 6 | `guides/product-engineering/explanation/the-discovery-loop.md` | The discovery loop — from a raw idea to a build-ready brief | Understand how divergence, specialist lenses, validation hooks, human gates, and reconciliation produce a build-ready decision brief. | `product-engineering` | `explanation` |
| 6 | `guides/product-engineering/explanation/the-intent-tree.md` | The intent tree — level-agnostic product shaping | Understand how vision, strategy, capability, and feature intents reuse one recursive frame–de-risk–decompose model. | `product-engineering` | `explanation` |
| 6 | `guides/product-engineering/how-to/create-a-lean-canvas.md` | How to create a Lean Canvas for an initiative | Elicit and commit a concise or full initiative brief grounded in an existing bet and capability map. | `product-engineering` | `how-to` |
| 6 | `guides/product-engineering/how-to/frame-a-product-vision.md` | How to frame a product vision | Test a product-existence bet, record a de-risked vision intent, and decompose it toward a product strategy. | `product-engineering` | `how-to` |
| 6 | `guides/product-engineering/how-to/frame-a-situation.md` | How to frame a situation | Classify a raw signal, assess capability maturity, and select the correct entry point into product shaping. | `product-engineering` | `how-to` |
| 6 | `guides/product-engineering/how-to/identify-opportunities.md` | How to: identify opportunities | Identify and rank functional, emotional, and social jobs before committing to a solution direction. | `product-engineering` | `how-to` |
| 6 | `guides/product-engineering/how-to/map-capabilities.md` | How to map capabilities | Convert a committed bet into a dependency-aware capability map with maturity, criticality, disposition, and build order. | `product-engineering` | `how-to` |
| 6 | `guides/product-engineering/how-to/run-a-capability-across-a-value-stream.md` | How to run a capability across a value stream (many component repos) | Coordinate a cross-repository capability through a meta-repository, shared contracts, per-component briefs, and AND-completion rollup. | `product-engineering` | `how-to` |
| 6 | `guides/product-engineering/how-to/run-a-discovery.md` | How to run a discovery end-to-end | Run the complete divergence-to-validation discovery loop and obtain a ratified, build-ready decision brief. | `product-engineering` | `how-to` |
| 6 | `guides/product-engineering/how-to/shape-a-feature-intent.md` | How to shape a feature intent in an app repo | Turn an application-scale idea into a de-risked feature intent and a delivery-ready core brief. | `product-engineering` | `how-to` |
| 6 | `guides/product-engineering/how-to/shape-a-product-strategy.md` | How to shape a product strategy | Turn a survived vision into a tested strategic path and decompose it into capability intents. | `product-engineering` | `how-to` |
| 6 | `guides/product-engineering/how-to/write-product-microcopy.md` | How to write a product's voice and microcopy | Establish a reusable voice chart and write actionable, consistent errors, empty states, labels, and calls to action. | `product-engineering` | `how-to` |
| 6 | `guides/product-engineering/reference/discovery-sidecar-and-roster.md` | Reference — the discovery sidecar, plan-tree, and roster | Look up discovery state slots, statuses, plan-tree shape, verdicts, specialist roster, gates, and bounds. | `product-engineering` | `reference` |
| 6 | `guides/product-engineering/reference/intent-fields-and-modes.md` | Reference — intent fields, modes, and projection profiles | Look up intent fields, level-specific additions, risk modes, output locations, contract maturity, and tracker projections. | `product-engineering` | `reference` |
| 6 | `guides/product-engineering/tutorials/walk-a-discovery-end-to-end.md` | Walk a discovery end-to-end | Follow a complete discovery through divergence, human gates, rejection recovery, reviewer coverage, and delivery handoff. | `product-engineering` | `tutorial` |
