# Guides

Documentation for this catalogue, organized to get you to the right place fast — by what you're trying to do, by your role, or by pack.

## What do you want to do?

**Ship a new feature or fix a bug →** [Install `core`](../guides/core/) and run `work-loop`. The build loop handles planning, gating, and adversarial review.

**Turn a product idea into something buildable →** [Install `product-engineering`](product-engineering/) and run `discovery-loop`. Goes from a raw idea to a ratified decision brief in one supervised session.

**Validate and ship to production →** [Install `release-engineering`](release-engineering/) and run `release-lead`. Deploys to an ephemeral environment, runs e2e, feeds back to the build loop, and surfaces a release-readiness record at the prod-ship gate.

**Understand the full picture →** [The three loops as a system](../guides/_shared/explanation/the-three-loops.md) — how discovery, build, and release compose into a complete operating model.

---

## By role

| I work as… | Start here | Also useful |
| --- | --- | --- |
| **Engineer** | [`core`](core/) — the build loop | [`architect`](architect/) for design; [`contracts`](contracts/) for API authoring; [`converters`](converters/) for document handling; [how engineers use the system](core/explanation/role-journeys.md) |
| **Product manager / strategist** | [`product-engineering`](product-engineering/) — intent shaping and the discovery loop | [`desk-research`](desk-research/) for evidence; [`governance-extras`](governance-extras/) for decision trails; [how PMs use the system](core/explanation/role-journeys.md) |
| **AI agent** | [`core`](core/) — the build loop; `workspace-status` + `work-loop` for autonomous execution | [how agents use the system](core/explanation/role-journeys.md) |
| **Designer / UX** | [`experience-design`](experience-design/) — journey mapping, screen flows, service blueprints, design review | [`figma`](figma/) for Figma reads; [`product-engineering`](product-engineering/) for voice and microcopy |
| **Architect** | [`architect`](architect/) — system design and pressure-testing | [`contracts`](contracts/) for API contracts; [`desk-research`](desk-research/) for prior art |
| **SRE / DevOps** | [`release-engineering`](release-engineering/) — the release loop, ephemeral deploy, e2e convergence | [`core`](core/) (required dependency) |
| **Researcher / analyst** | [`desk-research`](desk-research/) — evidence-grounded research with selectable depth | [`converters`](converters/) for document ingestion |
| **Everyone, once** | [`core`](core/) — **install this even if you install nothing else** | — |

---

## The three loops

This repository covers the full software delivery lifecycle through three peer supervisors:

| Loop | Pack | Agent | Scope | What it does |
| --- | --- | --- | --- | --- |
| Discovery | [`product-engineering`](product-engineering/) | `discovery-lead` | user | Raw idea → build-ready decision brief via multi-lens diverge/converge |
| Build | [`core`](core/) | `work-loop` supervisor | repo | Spec → shipped code with hard gates and cold-eyed review |
| Release | [`release-engineering`](release-engineering/) | `release-lead` | repo | Built code → production via ephemeral e2e convergence and G5 prod-ship gate |

Each loop is autonomous where the work is reversible, and surfaces to a human where it isn't. The G3 handoff moves a decision brief from discovery into the build loop; the G4 handoff moves a built artifact into the release loop; G5 is the human prod-ship consent gate.

→ [The three loops as a system](_shared/explanation/the-three-loops.md)

---

## All packs

| Pack | Home | What it ships |
| --- | --- | --- |
| [`core`](core/) | **The flagship.** | The build loop — `work-loop`, `new-spec`, `bug-fix`, `adapt-to-project`, the four reviewer/executor subagents, `pre-pr` + `session-start` hooks, governance seeds. Install this even if you install nothing else. |
| [`product-engineering`](product-engineering/) | [home](product-engineering/) | The discovery loop and intent shaping — `discovery-loop`, `frame-intent`, `de-risk-intent`, `decompose-intent`, `ux-writing`, `align-value-stream`. |
| [`release-engineering`](release-engineering/) | [home](release-engineering/) | The release loop — `release-loop`, `release-lead`; autonomous e2e convergence on ephemeral envs; inner↔outer feedback seam; release-readiness record at G5. |
| [`architect`](architect/) | [home](architect/) | Solution architecture — `architect-design`, `architect-diagram`, `architect-review`, and the read-only `design-reviewer` subagent. |
| [`desk-research`](desk-research/) | [home](desk-research/) | Evidence-grounded research — `desk-research` with selectable depth, plus `source-map`, `compare-hypotheses`, `devils-advocate`, and retrieval subagents. |
| [`experience-design`](experience-design/) | [home](experience-design/) | The full design thread — journey mapping, screen flows, service blueprints, creative direction, design system, design review, and the `experience-reviewer` subagent. |
| [`credential-brokers`](credential-brokers/) | [home](credential-brokers/) | The broker behind credentialed skills — secrets resolve in-process, never reaching the model. |
| [`atlassian`](atlassian/) | [home](atlassian/) | Jira, Confluence, and flow metrics — `jira`, `confluence-crawler`/`-publisher`, `flow-metrics`, `jira-defect-flow`, and more. |
| [`github`](github/) | [home](github/) | GitHub integration — `github-brief-intake` turns a Milestone into a product brief and hands off to `receive-brief`. |
| [`contracts`](contracts/) | [home](contracts/) | Contract-first API design — `api-contract` (OpenAPI 3.1) with a pluggable house standard. |
| [`converters`](converters/) | [home](converters/) | Documents in and out of Markdown — `file-to-markdown`, `markdown-to-docx`/`-pptx`/`-xlsx`, `mermaid-renderer`, `msg-to-markdown`. |
| [`figma`](figma/) | [home](figma/) | The Figma REST primitive — read files, nodes, and comments; render frames; turn FigJam into Mermaid. |
| [`linear`](linear/) | [home](linear/) | Linear Issues and Projects — `linear` credentialed CLI plus `linear-brief-intake` (issue → product brief) and `linear-brief-sync` (delta catch-up). |
| [`governance-extras`](governance-extras/) | [home](governance-extras/) | A written trail for decisions — `new-rfc`, `new-adr`, `update-conventions`. |
| [`monorepo-extras`](monorepo-extras/) | [home](monorepo-extras/) | Monorepo scaffolding — `new-package` and a package template. |
| [`product-documentation`](product-documentation/) | [home](product-documentation/) | Product documentation authoring — create, revise, retrofit, audit, and verify guides, pack READMEs, and journeys using `author-product-docs`. |
| [`product-strategy`](product-strategy/) | [home](product-strategy/) | Answer the committed strategic questions upstream of every initiative — `write-prfaq`, `run-swot`, `run-pestle-analysis`, `run-porters-five-forces`, `run-bcg-matrix`, `run-okr-cascade`, `synthesize-stakeholder-research`, `define-ux-strategy`, `define-content-strategy`. |
| [`frontend-engineering`](frontend-engineering/) | [home](frontend-engineering/) | Build, audit, and ship production-quality web surfaces — `frontend-engineering` (four modes), `token-architecture`, `a11y-engineering`, `fe-performance`, `rendering-strategy`, `component-contract`, `responsive-layout`, `css-architecture`, `fe-status`, and the `frontend-reviewer` agent. |
| [`iac-terraform`](iac-terraform/) | [home](iac-terraform/) | Governed Terraform from plain-language intent — `generate-iac` (ADR gate → spec → plan, stops before apply) and `reconcile-iac` (drift audit). Opt-in, repo-scope. |
| [`catalogue-curation`](catalogue-curation/) | [home](catalogue-curation/) | Grow and maintain a catalogue — `assimilate-primitive`, `assimilate-repo`, `propose-catalogue-pack`, `export-catalogue`. For catalogue maintainers. |

---

## Shared guides

Cross-cutting topics — about the catalogue itself, not any single pack — live in [`_shared/`](_shared/):

- **Install & upgrade** — [from a clone](_shared/how-to/install-agentbundle-from-clone.md), into [Codex](_shared/how-to/install-user-scope-pack-into-codex.md) or [Kiro](_shared/how-to/install-user-scope-pack-into-kiro.md), [preview first with `--dry-run`](_shared/how-to/preview-install-or-upgrade.md), [upgrade an installed pack](_shared/how-to/upgrade-packs.md).
- **Reference** — the [`agentbundle` CLI](_shared/reference/agentbundle.md), the [adapter support matrix](_shared/reference/adapter-support.md), the [tracker vocabulary](_shared/reference/tracker-vocabulary.md) (how brief/spec levels map across GitHub, Linear, Jira, and Jira Align), and the [Catalogue CI contract](_shared/reference/catalogue-ci-contract.md) (publication ordering, exit codes, and responsibility boundaries for CI-driven catalogue releases).
- **Understand** — [the three loops](_shared/explanation/the-three-loops.md), [install routes](_shared/explanation/install-routes.md), [the pack catalogue](_shared/explanation/pack-catalogue.md), [the file-safety contract](_shared/explanation/file-safety-contract.md), and [shaping a new engagement](_shared/explanation/shaping-a-new-engagement.md).
- **Contribute** — [how to author a skill](_shared/how-to/author-a-skill.md) for any pack.
- **Tracker intake** — [choose a tracker integration](_shared/how-to/choose-a-tracker-integration.md) for the right brief-intake skill across GitHub, Linear, Jira, Jira Align, or no tracker.

---

## For guide authors — the four Diátaxis kinds

Each guide has exactly one `kind` — declared as frontmatter metadata, not derived from its directory. Mixing kinds is the most common cause of docs that frustrate everyone.

|  | Practical (you *do* something) | Theoretical (you *understand* something) |
| --- | --- | --- |
| **Learning** (acquiring a skill) | `kind: tutorial` — *lessons.* "Take me through it from the start." | `kind: explanation` — *discussions.* "Help me understand why." |
| **Task** (getting something done) | `kind: how-to` — *recipes.* "Help me solve this specific problem." | `kind: reference` — *information.* "Tell me exactly what this does." |

### Source layout

New guides are **flat by default**:

```
guides/<pack>/<slug>.md
```

Topic-first grouping is permitted where a user perceives a real domain:

```
guides/<pack>/<topic>/<slug>.md
```

Physical quadrant directories (`tutorials/`, `how-to/`, `reference/`, `explanation/`) are a migration-compatible legacy structure — they still work, but **new guides do not require them**. Do not create four empty quadrant directories. Do not create one guide of each type. Let the reader's need determine what you write.

### Required frontmatter

Every new guide needs four fields:

```yaml
---
title: "What this guide is called"
summary: "One sentence for navigation surfaces."
pack: core                  # must match a directory in packs/
kind: how-to                # tutorial | how-to | reference | explanation
---
```

Optional: `slug` (overrides the output path), `aliases` (generates redirect stubs), `journey`, `order`, `status`.

The `author-product-docs` skill applies the correct page contract automatically. The `validate_guides.py` tool checks frontmatter compliance. Navigation in the docs site derives from reader needs and metadata — not from physical folder structure.

### What belongs in `docs/guides/`?

`docs/guides/` is **internal maintainer documentation** — how-tos for repo contributors, not for pack adopters. It is not published as public documentation.

## How this fits with the rest of the repo

These guides are *living* — they must match current behavior, and a PR that changes what users see updates them in the same PR. That's different from [`../specs/`](../specs/) (feature contracts, frozen once shipped), [`../adr/`](../adr/) (architecture decisions), and [`../CHARTER.md`](../CHARTER.md) (the mission). See [`../CONVENTIONS.md`](../CONVENTIONS.md#5c-docsguides--for-users) §5c for the full lifecycle.
