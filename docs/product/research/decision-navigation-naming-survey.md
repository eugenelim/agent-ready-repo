# Decision navigation naming — applied survey

> Discipline: applied (practitioner-pattern survey)

- **Run date:** 2026-10-02
- **Question:** What should this repository call a skill and a generated, self-contained HTML surface that let people scan ADRs and RFCs, follow trusted decision edges, open a record, and move into supporting material without turning the projection into a second source of truth?
- **Local frame:** [Graph-powered SDLC](../intents/STRAT-0001-graph-powered-sdlc.md), [Decision graph](../intents/CAP-0002-decision-graph.md), [Repository work graph](../intents/CAP-0001-repository-work-graph.md), and [Intent graph navigation](../intents/FEAT-0002-intent-graph-navigation.md).
- **Reference surface:** the provided `rai-azure-adr-review.html`, inspected as source outside the repository. No browser runtime was available, so interaction and rendered-layout claims about that file remain unverified.

## Verdict

Rename and widen `rfc-status` into **`navigate-decisions`** instead of adding a new `decision-workspace` or `adr-rfc-explorer` skill.

Keep **`new-adr`** and **`new-rfc`** separate. They have different admission questions and activation phrases. Combining their authoring flows would make discovery worse and erase the repository's settled distinction between a durable decision and an unresolved proposal.

Give `navigate-decisions` two output modes over one decision-corpus derivation:

- `summary` — the current read-only landscape in chat or machine-readable form;
- `html` — a generated, read-only, single-file **Decision Explorer** with an overview, filters, trusted decision lineage, full record reading, and source-linked supporting material.

Both modes should accept `kind=adr|rfc|all`. The shared navigation skill does not merge ADR and RFC authoring. It exposes two record kinds already grouped by the local `Decision graph` capability.

Do not absorb intent navigation. A later **`navigate-intents`** skill should use the same renderer and interaction grammar but a different derivation, schema, and trust contract. The repository explicitly made the decision graph a sibling of the work graph because the populations have different completeness and edge reliability.

Treat `workspace-status` as a transitional facade, not a permanent naming family. `navigate-intents` can replace its orientation surface once repository artifacts carry or make derivable every fact needed for orientation. Full retirement is possible, but not from the current corpus without first relocating or removing the non-derivable queue, dependency, priority, cooling, and dispatch state that still lives only in `workspace.toml`. Keep the navigator read-only; mutation belongs in the workflow that owns the affected artifact.

## Naming evidence

### Finding 1 — “workspace” denotes a durable work container, not a disposable projection [high]

Across independent products, a workspace contains ongoing state, scope, configuration, membership, or editable models:

- Visual Studio Code defines a workspace as one or more open folders plus restorable UI state, settings, tasks, and debug configuration ([VS Code workspaces](https://code.visualstudio.com/docs/editing/workspaces/workspaces)).
- Structurizr defines a workspace as the wrapper around an architecture model and its views, not as one exported view ([Structurizr workspace](https://docs.structurizr.com/dsl/cookbook/workspace/)).
- Linear calls a workspace the home and container for an organization's issues, teams, and interactions ([Linear workspaces](https://linear.app/docs/workspaces), [Linear conceptual model](https://linear.app/docs/conceptual-model)).
- Notion uses workspace for the persistent home that contains pages, databases, members, permissions, settings, and security controls ([Notion workspace introduction](https://www.notion.com/help/intro-to-workspaces), [Notion workspace settings](https://www.notion.com/help/workspace-settings)).

The local repository is even more specific: `workspace.toml` owns non-derivable operational coordination state, while generated graph views must leave no repository footprint. Calling a scratch HTML projection a workspace would collide with both market meaning and local meaning.

**Applied consequence:** reserve `workspace` for a durable container or coordination boundary. Do not use `decision-workspace`, and do not establish `<domain>-workspace` as the cross-pack name for generated HTML.

### Finding 2 — “explorer” is a good surface label for relation-aware browsing [moderate]

Three independent implementations use explorer or an equivalent viewer for interactive movement through a connected corpus:

- Structurizr calls its ADR graph the **Decision explorer**; it shows connections and opens a decision from the graph ([Structurizr decisions](https://docs.structurizr.com/ui/decisions/)).
- ADR Explorer combines graph and timeline views, opens records, and analyzes supersession and related edges ([ADR Explorer](https://github.com/janmohammadi/adr-explorer)).
- Backstage's catalog graph plugin provides a viewer that navigates entities and filters relation types ([Backstage catalog graph plugin](https://backstage.io/api/stable/modules/_backstage_plugin-catalog-graph.html)).

`adr-viewer` shows that **viewer** also works when the value is mainly readable static publication ([adr-viewer](https://github.com/mrwilson/adr-viewer)). The proposed surface goes beyond viewing because it supports search, filtering, lineage traversal, and supporting-document navigation. Explorer is therefore the better UI noun.

**Confidence limit:** this is a small, self-selected tool sample. Product names are not controlled evidence of user comprehension, so the finding is moderate and carries **survivorship bias**.

### Finding 3 — “catalogue” implies an inventory with ongoing registration or governance [high]

Backstage describes its software catalog as a centralized system that tracks ownership and metadata; even when repository files remain authoritative, the catalog is a maintained cache and discovery service ([Backstage Software Catalog](https://backstage.io/docs/features/software-catalog/), [Backstage catalog graph](https://backstage.io/docs/features/software-catalog/creating-the-catalog-graph/)). DataHub's catalog depends on ingested entity metadata for search and discovery ([DataHub search](https://docs.datahub.com/docs/how/search)). OpenMetadata aggregates assets into a catalog for cross-system discovery ([OpenMetadata data discovery](https://docs.open-metadata.org/v1.12.x/how-to-guides/data-discovery)). Databricks catalogs are registered governance namespaces with access and lifecycle meaning ([Databricks catalogs](https://docs.databricks.com/aws/en/catalogs), [Unity Catalog governance](https://docs.databricks.com/aws/en/data-governance)).

A generated HTML file is a point-in-time projection. It has no registration flow, owner, synchronization process, access-control model, or independent lifecycle. Calling it a catalogue would overstate its authority and revive the stale-index risk the local intents prohibit.

**Applied consequence:** use `catalogue` for published or governed inventories, not for an on-demand file that can be deleted and regenerated.

### Finding 4 — “dashboard” promises at-a-glance state, not corpus reading [high]

Grafana defines a dashboard as panels that provide an at-a-glance view of related information, while its Explore surface is for detailed query and analysis ([Grafana visualizations](https://grafana.com/docs/grafana/latest/visualizations/), [Grafana Explore](https://grafana.com/docs/grafana/latest/visualizations/explore/)). Linear likewise separates high-level initiative health and progress from the project overview where descriptions, documents, links, and milestones are read ([Linear initiatives](https://linear.app/docs/initiatives), [Linear project overview](https://linear.app/docs/project-overview)).

The supplied Azure ADR review HTML has dashboard-like strengths: platform context, invariants, counts, filters, and compact review cards. Those are useful as the explorer's landing state. The complete product is not a dashboard because its primary job also includes opening full records, walking lineage, and reading support notes.

**Applied consequence:** keep a dashboard-like overview inside the Decision Explorer, but do not use `dashboard` as the skill or artifact name.

### Finding 5 — skill names and surface names should not be forced to match [moderate]

OpenAI's public skill guidance prefers short, verb-led skill names and says the description is the main trigger surface ([OpenAI skill creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md)). Anthropic's public guidance likewise treats the description as the activation mechanism and supports routing variants behind one top-level skill ([Anthropic skill creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)). Public ADR skills use many competing nouns — `adr`, `architecture-decision`, `architecture-decision-records`, `adr-create`, and `decision-memory` — with no stable convention beyond making the artifact or action discoverable ([skills.sh ADR examples](https://www.skills.sh/arrudadev/skills/adr), [architecture-decision](https://www.skills.sh/jwynia/agent-skills/architecture-decision), [adr-create](https://www.skills.sh/flitzrrr/opencode-processing-skills/adr-create)).

That makes the clean split:

- skill: `navigate-decisions` — an action, aligned with the repository's own “navigable graph” language;
- generated page title: **Decision Explorer** — a recognizable surface noun;
- trigger description: explicitly name “ADR,” “RFC,” “decision graph,” “RFC status,” “decision index,” and “self-contained HTML.”

**Confidence limit:** agent-skill naming is young and fragmented. The recommendation is an inference from two platform guides and a convenience sample, with **stale prior art** likely as registries change.

## Fit with the repository's intent graph

### Finding 6 — intent navigation and decision navigation must stay separate [high, in-repo]

The local intent architecture already decides the population boundary:

- `Repository work graph` owns intent identity, parentage, status, and delivery mapping.
- `Intent graph navigation` owns a bounded query and a single self-contained human view over intent headers.
- `Decision graph` owns ADRs and RFCs, trusted supersession lineage, and unresolved `Related` text.
- `Repository work graph` says widening intent navigation to decisions would merge populations with different trustworthiness under one bet.

This is stronger than a naming preference. A combined `decision-workspace` or `repository-navigator` would hide separate derivations, different edge semantics, and different completeness claims behind one activation point.

The two navigation skills may share code without sharing authority:

```text
canonical intent headers  -> intent derivation   -> navigate-intents
                                                     | summary
canonical ADR/RFC headers -> decision derivation -> | html
                                                     v
                                              shared HTML renderer
```

The shared renderer owns only presentation mechanics: shell, filters, hash routing, panels, graph drawing, print rules, and accessibility behaviour. Each navigator owns discovery, parsing, schema, validation, and claims about trusted edges.

### Finding 7 — `rfc-status` is the right skill to evolve [moderate, in-repo]

`rfc-status` is already the read-only activation point for “show RFCs,” “RFC dashboard,” and “RFC landscape.” Adding a separate HTML skill would duplicate those triggers and make users choose based on output format before the task is understood. Renaming it to `navigate-decisions` and adding modes preserves the route while extending the population to the decision corpus defined by `CAP-0002`.

This is a design recommendation, not evidence that the migration will be harmless. Trigger evaluations must test at least:

- “what RFCs are open?” -> `navigate-decisions`, `summary`, `kind=rfc`;
- “make me a single-file ADR browser” -> `navigate-decisions`, `html`, `kind=adr`;
- “show the ADR and RFC decision graph” -> `navigate-decisions`, `html`, `kind=all`;
- “write an ADR” -> `new-adr`, never the navigator;
- “draft an RFC” -> `new-rfc`, never the navigator;
- “show the intent hierarchy” -> `navigate-intents`, never the decision navigator.

**Confidence limit:** no activation evaluation has been run, so the migration remains moderate confidence.

### Finding 8 — `navigate-intents` can replace orientation now, but not all workspace coordination yet [high, in-repo]

The direction is consistent with the accepted repository-work-graph intent: artifacts are the authoritative inventory, lifecycle status has one home in each artifact, and graph views are derived on demand. The current files already carry most orientation facts. Across 174 intent files, every file has `Slug`, 160 have `Status` and `Level`, and 70 declare `Parent intent`.

`workspace.toml` still carries a different class of facts. Measured on 2026-10-02, it is 2,432 lines and 279,188 bytes, with 370 entries across 42 lifecycle collections. Of those entries, 345 use the canonical shape and 25 remain legacy. The canonical entries contain 88 `needs` edges; `backlog.open` alone contains 177 entries. The intent headers expose only three `Depends on` fields, and they do not encode queue membership, active-initiative selection, dispatch eligibility, cooling, or repair/prune state.

This yields a staged replacement:

1. **Replace `workspace-status status` with `navigate-intents summary`.** Derive identity, altitude, lifecycle, parentage, related intents, and delivery mappings from artifact headers. This removes the duplicated inventory/status read path.
2. **Stop treating queue membership as inventory.** Discover intents, briefs, and specs from their canonical directories. A record absent from a queue remains visible rather than silently disappearing.
3. **Decide the fate of each non-derivable fact.** Move a durable dependency or priority into the owning artifact header, derive dispatch eligibility from the artifact lifecycle and the existence of its approved plan, or explicitly retain a much smaller coordination record for facts that are genuinely operational.
4. **Move mutations out of the navigator.** Reconcile, repair, rollback, prune, cooling, and closeout actions belong to `work-loop`, `close-work`, or the lifecycle owner that writes the canonical artifact. `navigate-intents` reports; it never repairs.
5. **Retire `workspace-status` and `workspace.toml` only when the residual set is empty.** The 25 legacy entries and 88 workspace-only dependency edges are concrete migration work, not reasons to preserve the broad registry forever.

A graph can calculate which nodes are eligible. It cannot infer which of several eligible nodes humans want next. Full removal of `workspace.toml` therefore requires one explicit answer for prioritization: make priority a canonical artifact field, delegate selection to an external tracker projection, or accept an unordered eligible set. Hiding that choice inside graph traversal would turn a view into an authority.

## Cross-pack ontology

Use the same grammar across packs:

| Name shape | Meaning | Examples |
| --- | --- | --- |
| `new-<artifact>` | Author one canonical artifact with its own admission rules | `new-adr`, `new-rfc`, `new-spec` |
| `navigate-<population>` | Read-only derived query or human view over canonical artifacts | `navigate-decisions`, future `navigate-intents` |
| `<domain>-status` | Read-only cold-start orientation over durable state; no mutation | `experience-status`, `fe-status` |
| `navigate-<population>` with `summary` | Preferred replacement when orientation is derivable from canonical artifacts | `navigate-intents summary`, `navigate-decisions summary` |
| `<verb>-workspace` | Operate a durable workspace/container only when irreducible workspace state remains | not an HTML export and not a default pack pattern |
| `<Population> Explorer` | Human-facing interactive surface title | Decision Explorer, Intent Explorer |
| `<Population> view` | A projection or mode, not a source or top-level domain | summary view, graph view, timeline view |

This makes one current inconsistency visible: `workspace-status` now includes repair, apply, rollback, and prune modes. Those operations are broader than “status.” It should not be copied or renamed into a new cross-pack pattern yet. The stronger target is to let `navigate-intents` absorb read-only orientation, move mutation to its owning workflow, and retire the workspace skill if no irreducible coordination state survives.

## Single-file delivery architecture

### Finding 9 — a shipped `file://` page cannot silently hydrate from repository Markdown [high]

Modern browsers usually treat local `file:` URLs as opaque origins, so adjacent files are not reliably same-origin and local `fetch()` commonly fails ([MDN same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Same-origin_policy), [MDN local-file CORS guidance](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSRequestNotHttp)). Browser filesystem APIs require explicit user permission, and important parts are limited to secure contexts ([MDN File System API](https://developer.mozilla.org/en-US/docs/Web/API/File_System_API), [MDN File API](https://developer.mozilla.org/en-US/docs/Web/API/File_API)).

The reliable default is therefore **build-time embedding**, not runtime disk hydration:

1. Discover and validate repository records with the decision derivation.
2. Read canonical record bodies plus the paths and metadata of allowed support files for the `html` presentation projection.
3. Sanitize and render the Markdown during generation.
4. Embed metadata, canonical record bodies, styles, icons, and JavaScript in one HTML file. Link attachments and optional support files to their repository source instead of embedding them by default.
5. Store each body as inert text or a compressed data chunk, then materialize only the selected record into the reading pane. This is island-like lazy rendering, but it hydrates from payload already inside the file, not from Markdown on disk.

Do not use one `<template>` per rendered record at large scale. Template contents are parsed into `DocumentFragment` nodes even though they are not displayed ([MDN `HTMLTemplateElement.content`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLTemplateElement/content)). Chrome warns around 800 body nodes and reports an excessive DOM around 1,400; its guidance is to create nodes only when needed ([Chrome DOM-size guidance](https://developer.chrome.com/docs/lighthouse/performance/dom-size)). MDN and Microsoft likewise tie larger DOMs to longer construction, layout, memory, and forced-layout costs ([MDN critical rendering path](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Critical_rendering_path), [Microsoft Edge performance guidance](https://learn.microsoft.com/en-us/microsoft-edge/devtools/rendering-tools/)). Keep the initial DOM to the shell plus a virtualized result window and one record pane.

An optional **Open repository snapshot** control may let a person select files or a directory and rebuild the in-memory view. It is an explicit import session, not automatic hydration, and it should not be required for the shippable artifact to work.

### Finding 10 — the current corpus fits easily; a full-text 50× corpus does not remain “easily shippable” [high for size, moderate for portability]

The corpus was measured from regular files in the working tree on 2026-10-02. Counts exclude README/template files from canonical record counts. The compressed estimate gzips each canonical record separately and base64-encodes it so a single HTML file can decode one selected record without inflating every body. `DecompressionStream` has broad browser availability and supports gzip streams ([MDN `DecompressionStream`](https://developer.mozilla.org/en-US/docs/Web/API/DecompressionStream)).

| Payload | Current population | Current size | At 50× |
| --- | ---: | ---: | ---: |
| ADR + RFC header regions | 237 records | 0.20 MiB | 9.77 MiB |
| ADR + RFC canonical bodies, raw Markdown | 237 records | 5.43 MiB | 271.34 MiB |
| Canonical bodies, per-record gzip + base64 | 237 records | 2.62 MiB | 130.92 MiB |
| RFC support Markdown, linked rather than embedded | 69 files | 1.79 MiB avoided | 89.51 MiB avoided |
| Intent header regions | 174 intents | 0.07 MiB | 3.50 MiB |
| Intent bodies, per-record gzip + base64 | 174 intents | 0.64 MiB | 32.06 MiB |
| Intent + brief + spec header regions | 716 work nodes | 0.51 MiB | 25.74 MiB |

The present Decision Explorer should land near 3–5 MiB after adding its shell, metadata, and search fields if canonical bodies are compressed and support files are linked. That is comfortably shippable for ordinary file transfer and local opening, subject to a browser benchmark.

At 50×, the same full-record design is roughly 131 MiB before the shell, metadata index, and search structures. It may still open on a capable desktop if the DOM is virtualized and records decompress on selection, but it is no longer a small artifact. It would also exceed GitHub's 100 MB single-object limit if someone tried to commit the generated file, which reinforces the existing rule that it is scratch output rather than repository state ([GitHub repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits)). The browser must retain the large document text and encoded payload, so runtime memory will exceed the file size; the exact multiplier is browser- and encoding-dependent and must be benchmarked rather than asserted. Chrome also notes that larger HTML takes longer to parse ([Chrome transfer-size guidance](https://developer.chrome.com/docs/lighthouse/performance/resource-summary)).

The thin graph/index remains viable at 50×. Decision headers are under 10 MiB, intent headers are about 3.5 MiB, and the wider intent-to-brief-to-spec header graph is about 26 MiB under linear growth. This is the key architectural split:

- `navigate-intents html` should embed **header-derived graph metadata only** and link every artifact body to its source. Its own intent already says queries return identities, header facts, edges, and paths rather than bodies. It scales to 50× without `workspace.toml` becoming a read dependency.
- `navigate-decisions html` may embed canonical ADR/RFC bodies at today's scale, because reading the rationale is central to the job. It should link attachments and support material to the source repository.
- The generator must calculate projected output size before writing. Above a tested portability budget, it should require an explicit choice between a full portable artifact and a linked-body index rather than silently emitting a very large file.

The 50× figures are a linear projection of today's measured corpus. They do not assume repeated text compresses better, because future records will be novel. They also exclude images and binaries, which is why linking attachments is part of the default contract.

### Navigation and supporting material

Use hash-addressed routes so a copied file still supports deep links:

- `#overview`
- `#decision/ADR-0117`
- `#decision/RFC-0083`
- `#decision/RFC-0083/support/<relative-path>`

The build should classify support material before representing it:

- list supporting Markdown, notes, and attachments in the support pane with type, size, and repository-relative path;
- link every support item to its canonical repository source by default;
- optionally embed a small support note only when the generator's explicit size budget allows it;
- rewrite links between embedded records and notes to hash routes;
- inventory unsupported or oversized binaries with path, type, size, and omission reason;
- never execute scripts, HTML event attributes, or active content found in records.

Every record should expose two provenance actions when a repository remote is available:

- **Open source at snapshot** — a commit-pinned URL matching the generated artifact;
- **Open latest source** — the default-branch URL, clearly labelled as potentially newer.

Each support item should use the same pair when both URLs are available, with the snapshot link as the primary action. GitHub documents that a commit identifier creates a permanent link to the exact file version, while a branch link can change ([GitHub file permalinks](https://docs.github.com/en/repositories/working-with-files/using-files/getting-permanent-links-to-files)). For a non-GitHub remote, the generator should use a configured source-link adapter or show the repository-relative path without inventing a URL. The explorer shell, index, graph, and embedded canonical records remain usable offline; opening an attachment requires repository access by design.

Keep graph construction and body rendering separate. The graph reads headers only. The HTML payload may include bodies and support notes for reading, but prose never creates an edge. That preserves the local guardrail even though the finished file contains more than the graph derivation consumed.

### Interaction model

The strongest elements from the supplied Azure review HTML should survive: project context, decision invariants, corpus counts, status and area filters, compact record summaries, and reviewer-oriented prompts. The generalized surface also needs:

- global search across title, identity, status, area, and rendered text;
- list, lineage, and optional timeline lenses over the same selected population;
- a persistent detail route with back/forward history;
- visible distinction between trusted supersession edges and unresolved related text;
- an adjacent support-material drawer or split pane;
- keyboard navigation, focus restoration, `aria-expanded`/`aria-controls`, and non-pointer activation;
- print rules that include selected or all records by an explicit print choice.

Use a normal click or Enter to open a record. Structurizr uses double-click in its force graph, but double-click is a poor primary web action because it is undiscoverable, touch-hostile, and unnecessary here. It may remain a nonessential shortcut.

The supplied file is not the implementation base without changes. It imports React, Babel, and Tailwind from CDNs, hard-codes one review packet, has no deep-link routing or support-document model, and therefore is neither self-contained nor a corpus browser. It is useful as an information-design reference.

## Recommended skill contract

```text
navigate-decisions
  mode: summary | html
  kind: adr | rfc | all
  content: full | linked
  root: repository root (default: current repository)
  output: scratch path for html mode only

summary
  lifecycle counts
  active/resolved lists
  candidate counts where repository policy defines them
  bounded record lookup and lineage answers

html
  one self-contained Decision Explorer
  embedded canonical records in full mode
  header/decision summaries plus source links in linked mode
  attachments and optional support material linked to the source repository
  no repository output or generated index
  graph derived only from checked header relations

navigate-intents
  mode: summary | html
  content: linked
  derived intent/work graph metadata only
  source links for full artifacts and attachments
  no workspace.toml read once residual coordination state is retired
```

The HTML file is an explicit scratch artifact and may be deleted at any time. It never becomes an input to `new-adr`, `new-rfc`, linting, status computation, or future graph derivation.

## Known unknowns

- **Whether the view is worth shipping before a decision gate.** This is already the open assumption in `CAP-0002`. A usability test can measure whether people answer lineage and “what constrains this?” questions faster and more accurately than with repository search.
- **Whether `navigate-decisions` triggers more reliably than `rfc-status`.** Requires activation evals across ADR authoring, RFC authoring, status, HTML export, and intent navigation prompts.
- **How the measured payload behaves in supported browsers.** The byte sizes are known, but startup time, peak memory, search-index cost, and the practical threshold for a “small” shippable artifact still need benchmarks.
- **What portability budget should force `content=linked`.** The measured 50× payload shows the need for a threshold, but only synthetic 10×/25×/50× browser benchmarks on supported desktop targets can set it.
- **Which `workspace.toml` facts should survive.** The current file contains 88 dependency edges and explicit prioritization/queue choices. Each needs a disposition: canonical artifact metadata, derivation, external projection, or deliberate removal.
- **Whether an unordered eligible set is sufficient.** If it is not, removing `workspace.toml` still needs an authoritative priority signal somewhere other than the navigator.
- **Whether full-text search should include support notes by default.** Including them improves recall but can swamp canonical records. This needs query examples from maintainers.
- **Whether RFC support directories contain sensitive or unsuitable files.** A safe allowlist and size inventory are required before the first generator run.
- **Whether ADR and RFC status vocabularies can share one filter control without confusion.** The surface can group by kind, but this needs a prototype with the real corpus.
- **Whether the supplied Azure review surface's card density works at corpus scale.** It was inspected only as source and appears designed for a small curated packet.

## Unknowables at this stage

- Future browser changes to local-file origin and filesystem APIs cannot be relied on for a portable artifact.
- Runtime memory for a 131 MiB encoded HTML payload cannot be inferred exactly from file size; browser string representation, source retention, and garbage collection differ.
- Naming research cannot prove activation quality; model versions and skill registries change.
- Public tool repositories do not reveal abandoned internal tools, so the explorer-name sample has survivorship bias.
- No external precedent can decide the local trust boundary between checked supersession and free-form related text; repository gates remain the authority.

## Moderator pass

Every material naming claim above is linked to primary product documentation or the tool's own repository, and each high-confidence market-semantics claim has at least three independent product families. The source sample is strongest for `workspace`, `catalogue`, and local-file constraints. It is weaker for agent-skill naming and the word `explorer`; both are marked moderate with the downgrade reason stated.

The most important contradictory evidence is Structurizr: it uses both a durable **workspace** and a **Decision explorer** inside that workspace. That does not support `decision-workspace`; it supports the proposed separation between container and view. Backstage also calls its catalog a cache rather than a source of truth, but it still has registration, ingestion, APIs, plugins, and an ongoing service lifecycle that the generated HTML does not.

The scale pass changes one earlier implementation detail: `<template>` is suitable for a small reusable component skeleton, not as the storage container for hundreds or thousands of fully rendered records. The measured corpus plus browser DOM guidance favors compressed inert text, virtualized lists, one materialized record, and source links for attachments.

A final high-signal search for public skills named `navigate-decisions`, `decision-explorer`, `decision navigator`, or `ADR explorer` returned no exact skill-name examples. That weak negative result suggests the proposed name is not copying an established skill convention; it does not prove uniqueness across registries and does not raise the naming recommendation above moderate confidence.
