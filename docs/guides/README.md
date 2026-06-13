# Guides

The user-facing documentation for the catalogue, organized **by pack**. You install `core`, maybe `research`, maybe `atlassian` — each pack has its own guide home with the four [Diátaxis](https://diataxis.fr/) kinds inside it. Find your pack, start at its home page.

> The adopter-facing `user-guide-diataxis` seed scaffold stays organized by quadrant, not by pack — see [ADR-0020](../adr/0020-per-pack-diataxis-hierarchy-for-guides.md).

## Find your pack

| Pack | Start here | What it ships |
| --- | --- | --- |
| [`core`](core/) | **The flagship.** | The loop — `work-loop`, `new-spec`, `bug-fix`, `adapt-to-project`, the reviewers, the hooks. Install this even if you install nothing else. |
| [`architect`](architect/) | [home](architect/) | Solution architecture — `architect-design`, `architect-diagram`, `architect-review`, and the `reference.md` golden path. |
| [`research`](research/) | [home](research/) | Evidence-grounded research — `research` with selectable depth, plus the pipeline skills (`source-map`, `compare-hypotheses`, `devils-advocate`, …). |
| [`product-engineering`](product-engineering/) | [home](product-engineering/) | Shape product intent into shippable specs — the recursive `intent` tree (`frame`, `de-risk`, `decompose`, `align-value-stream`). |
| [`credential-brokers`](credential-brokers/) | [home](credential-brokers/) | The broker behind credentialed skills — secrets resolve in-process and never reach the model. |
| [`atlassian`](atlassian/) | [home](atlassian/) | Jira, Confluence, and flow metrics over the REST APIs — `jira`, `confluence-crawler`/`-publisher`, `flow-metrics`, `jira-defect-flow`, and more. |
| [`contracts`](contracts/) | [home](contracts/) | Contract-first design — `api-contract` (OpenAPI 3.1) and `event-contract` (AsyncAPI), with a pluggable house standard. |
| [`converters`](converters/) | [home](converters/) | Get documents into Markdown and back out — `file-to-markdown`, `markdown-to-html`, `mermaid-renderer`, `msg-to-markdown`. |
| [`figma`](figma/) | [home](figma/) | The Figma REST primitive — read files, nodes, and comments; render frames; turn FigJam into Mermaid. |
| [`governance-extras`](governance-extras/) | [home](governance-extras/) | A written trail for decisions — `new-rfc`, `new-adr`, `update-conventions`. |
| [`monorepo-extras`](monorepo-extras/) | [home](monorepo-extras/) | Monorepo scaffolding — `new-package` and a package template that ships its own conventions. |
| [`user-guide-diataxis`](user-guide-diataxis/) | [home](user-guide-diataxis/) | The docs skeleton you're reading right now — Diátaxis quadrants plus `new-guide`. |

## Not tied to one pack

Some guides are about the catalogue itself — installing it, upgrading it, seeing what each agent tool supports — rather than any single pack. They live in [`_shared/`](_shared/):

- **Install & upgrade** — [from a clone](_shared/how-to/install-agentbundle-from-clone.md), into [Codex](_shared/how-to/install-user-scope-pack-into-codex.md) or [Kiro](_shared/how-to/install-user-scope-pack-into-kiro.md), [preview first with `--dry-run`](_shared/how-to/preview-install-or-upgrade.md), [upgrade an installed pack](_shared/how-to/upgrade-packs.md).
- **Reference** — the [`agentbundle` CLI](_shared/reference/agentbundle.md) and the [adapter support matrix](_shared/reference/adapter-support.md).
- **Understand** — [install routes](_shared/explanation/install-routes.md), [the pack catalogue](_shared/explanation/pack-catalogue.md), and [the file-safety contract](_shared/explanation/file-safety-contract.md) (your edits are never silently overwritten).
- **Contribute** — [how to author a skill](_shared/how-to/author-a-skill.md) for any pack.

## The four kinds

Within every pack (and within `_shared/`), guides are sorted into the four Diátaxis kinds. Each piece of content belongs in **exactly one** — mixing kinds is the most common cause of docs that frustrate everyone.

|  | Practical (you *do* something) | Theoretical (you *understand* something) |
| --- | --- | --- |
| **Learning** (acquiring a skill) | **tutorials/** — *lessons.* "Take me through it from the start." | **explanation/** — *discussions.* "Help me understand why." |
| **Task** (getting something done) | **how-to/** — *recipes.* "Help me solve this specific problem." | **reference/** — *information.* "Tell me exactly what this does." |

The discipline that makes it work is **link out**: when a tutorial wants to explain *why*, it links to an explanation instead of digressing; when a how-to wants to list every option, it links to the reference. Each quadrant's writing rules live in the per-quadrant READMEs under [`_shared/`](_shared/) — read the matching one before you write a guide (or just run `new-guide`, which walks you there).

## How this fits with the rest of the repo

These guides are *living* — they must match current behavior, and a PR that changes what users see updates them in the same PR. That's different from [`../specs/`](../specs/) (feature contracts, frozen once shipped), [`../adr/`](../adr/) (architecture decisions), and [`../CHARTER.md`](../CHARTER.md) (the mission). See [`../CONVENTIONS.md`](../CONVENTIONS.md#5c-docsguides--for-users) §5c for the full lifecycle.
