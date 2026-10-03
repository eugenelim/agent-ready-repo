# RFC-0105: Artifact-derived navigation and workspace retirement

- **Status:** Accepted
- **Author:** Platform Core maintainer
- **Approver:** Platform Core maintainer
- **Date opened:** 2026-10-02
- **Date closed:** 2026-10-03
- **Decision weight:** heavy
- **Related:** [RFC-0064](0064-ini-001-ai-native-ecosystem.md), [RFC-0067](0067-session-arc-conventions-and-pack-workflow-guide.md), [RFC-0099](0099-cut-before-adding-and-artifact-shaping.md), [Decision graph](../product/intents/CAP-0002-decision-graph.md), [Intent graph navigation](../product/intents/FEAT-0002-intent-graph-navigation.md), [Workspace coordination reorganization](../product/intents/CAP-0003-workspace-coordination-reorganization.md), [decision-navigation naming survey](../product/research/decision-navigation-naming-survey.md)

## Reviewer brief

- **Decision:** Establish separate read-only navigation skills for the decision and intent populations, evolve `rfc-status` into decision navigation, and adopt gated retirement of `workspace-status` and `workspace.toml`.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - `navigate-decisions` becomes the read-only entry point for ADR and RFC summaries, lookup, multi-form graph navigation, bounded reference context, and portable human views; `new-adr` and `new-rfc` remain separate authoring skills.
  - `navigate-intents` becomes the read-only entry point for the intent graph and must derive its answers from canonical artifact metadata rather than `workspace.toml`.
  - `workspace-status` and `workspace.toml` enter a gated retirement path that cannot complete until every non-derivable coordination fact and every reader or writer has an explicit disposition.
- **Affected surface:** core and governance skill names, activation routing, pack guidance, decision and intent navigation, generated HTML exports, workspace coordination, and adopter compatibility.
- **Stakes:** Costly and compatibility-sensitive. This proposal changes published skill names and targets an accepted persistent coordination format for retirement, but it requires staged migration and preserves current behavior until replacement gates pass.
- **Review focus:** Population boundaries, the evidence required to retire workspace state safely, activation compatibility, and whether the portable-view requirements are strong enough without selecting an implementation design.
- **Not in scope:** Renderer architecture, shared code, component boundaries, payload encoding, compression, virtualization, search implementation, layout, interaction details, or fixed performance thresholds.

## The ask

**Recommendation:** Adopt artifact-derived navigation as two separate skills, reserve authoring for the existing artifact-specific skills, and make `workspace-status` plus `workspace.toml` transitional compatibility surfaces rather than permanent repository infrastructure.

**Why now:** The repository now has separate intent and decision graph contracts. Both derive views from canonical record metadata on demand, while `workspace-status` still presents a second inventory assembled from a large shared registry and also owns repair, rollback, migration, and prune operations. At the same time, the current RFC-only status skill is too narrow for the decision graph and cannot produce the portable human view the graph work calls for. Without a new boundary, adding HTML export risks creating more skills, calling a disposable projection a workspace, or making a navigator depend on the registry it is meant to replace.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Which navigation skills should exist? | Establish separate `navigate-decisions` and `navigate-intents` skills. Keep `new-adr` and `new-rfc` separate. Treat list, graph, guidance-context, detail, and HTML output as views or modes of the relevant navigator. | Decisions and intents are different populations with different edge trust and completeness. Views answer different questions without becoming new skills or record shapes. Authoring ADRs and RFCs also has different admission rules. | 2026-10-09 | Confirm the skill and population boundaries. |
| D2 | What happens to `rfc-status`? | Clean-retire the name into `navigate-decisions`, preserving its status use cases as one navigation mode. | A separate HTML or ADR-status skill would duplicate activation. The broader name matches the decision graph without merging authoring. | 2026-10-09 | Confirm the rename and compatibility plan. |
| D3 | What happens to `workspace-status` and `workspace.toml`? | Adopt full retirement as the target state, gated by a complete inventory and disposition of residual coordination state and consumers. | Canonical artifacts can own the inventory and graph, but current workspace-only dependency, priority, cooling, dispatch, repair, and prune behavior cannot be discarded or inferred. | 2026-10-09 | Confirm the target and retirement gates. |
| D4 | What must a portable human view guarantee? | Both navigators produce a read-only, single-file HTML artifact whose promised offline content works without installation. Decision navigation exposes list, lifecycle-graph, guidance-context, and record-detail forms over one corpus; attachments and optional support material link to repository source files. | This makes relationships navigable rather than decorative while keeping the artifact easy to ship and the rendering forms separate from the canonical record shape. | 2026-10-09 | Confirm the portability, provenance, view, and trust-boundary constraints. |
| D5 | How binding is later design work? | Treat later design artifacts as advisory implementation input, not as amendments to this RFC. | Teams need room to choose mechanisms after benchmarking. Only this RFC's accepted outcomes and constraints require RFC amendment or errata when changed. | 2026-10-09 | Confirm the authority boundary. |

## Problem & goals

### Problem

The current skill vocabulary mixes three different jobs:

- `new-adr` and `new-rfc` author canonical records;
- `rfc-status` reports one slice of the decision corpus;
- `workspace-status` orients from `workspace.toml` and also reconciles, repairs, migrates, rolls back, and prunes coordination state.

That mixture creates two forms of expansion pressure. Decision navigation could become a new skill for each output format or record kind. Intent navigation could become another consumer of `workspace.toml`, preserving the duplicated inventory and status paths that the artifact-derived graph is meant to remove.

The generated-view problem has a second constraint. A portable HTML file cannot rely on silently reading adjacent Markdown from disk. Embedding every canonical record and attachment works at today's scale, but linear growth makes it an increasingly large delivery artifact. The experience needs a stable contract that permits source-linked support material and a large-corpus fallback without freezing a renderer design before it has been tested.

### Goals

1. Give decision and intent navigation distinct, discoverable activation surfaces.
2. Keep ADR and RFC authoring separate.
3. Reduce the skill footprint by making summaries and HTML views modes of the relevant navigator rather than separate skills.
4. Make canonical artifacts and their checked metadata the navigation authority while preserving weaker contextual relationships as visibly weaker evidence.
5. Retire `workspace-status` and `workspace.toml` only after their remaining operational duties have safe owners.
6. Make generated HTML portable, provenance-aware, multi-form, and bounded at large corpus sizes.
7. Leave implementation mechanisms to the teams that design and build each navigator.

### Non-goals

- Selecting or requiring a shared renderer between the two navigators.
- Defining a UI component system, visual design, information architecture, or interaction model.
- Fixing an encoding, compression algorithm, search index, virtual-list implementation, or byte threshold.
- Combining `new-adr` with `new-rfc`.
- Making decision and intent records one graph population.
- Removing `workspace.toml` before its compatibility and state-migration gates pass.
- Making the generated HTML an input to linting, authoring, navigation derivation, or lifecycle computation.

### Terms used by this RFC

- A **navigator** is a read-only skill that derives answers from the canonical records in its population. It neither authors records nor mutates lifecycle or coordination state.
- **Canonical artifact metadata** is a preamble or header field whose owning artifact contract makes it authoritative. Prose in a record body is not graph metadata.
- A **checked** or **trusted edge** is one admitted and validated by the governing population contract and its repository gate. A navigator does not promote free-form prose into an edge.
- A **navigation view** is a disposable arrangement of canonical facts and labelled contextual evidence for a particular question. A list, lifecycle graph, guidance context, or record detail does not create a new record field or relationship merely by rendering it.
- A **bounded query** names a node, filter, or path question and returns only the identities, metadata, and edges needed to answer it. It does not return every record body.
- A **bounded representation** preserves navigation and provenance while limiting embedded bodies or support material under a benchmarked portability budget.
- A **scratch output** is a disposable generated file at an explicit user-selected or temporary location. It is not an index, authority, or required tracked file, and the default location is outside the repository worktree.
- A **recognized remote mapping** is a configured forge adapter that maps one validated repository identity, revision, and repository-relative path to an allowlisted URL scheme and host. Without one, the view shows an inert repository-relative path.
- **Clean retire** means the replacement and all operative references move together, the old public skill name is removed without a permanent alias, and frozen historical records remain unchanged.

## Proposal

### D1 — Separate navigation by canonical population

Create two read-only navigation skills:

- **`navigate-decisions`** reads the ADR and RFC decision population. It owns lifecycle summaries, bounded lookup, checked decision lineage, bounded reference context, and on-demand list, lifecycle-graph, guidance-context, and record-detail views. It may filter to ADRs, RFCs, or both without changing the population boundary.
- **`navigate-intents`** reads the intent-node population admitted by the intent identity and intent graph contracts. It owns bounded queries and on-demand human views over intent identity, altitude, lifecycle, parentage, and related edges. It may display brief or spec mappings only after the accepted intent-to-delivery traceability contract supplies them, and then only as a consumer; it never owns or infers those mappings.

The skills are separate because their claims differ. Decision supersession is checked; free-form `Related` text is not. A guidance-context view may arrange wider and narrower decisions only when an admitted directional fact or an explicit caller assertion supplies direction. A caller assertion is a non-authoritative view input, not a source-record fact, and must remain labelled as navigation-only. Contextual references, scope similarity, search, and navigation grouping remain neutral co-view context. Every relationship preserves its basis and trust class, and visual hierarchy is never presented as checked applicability. Intent edges use the work graph's typed identity and lifecycle rules. A single skill would either hide those differences or require one activation surface to explain two trust models.

This RFC does not require the implementations to share code, a renderer, a schema, or a build pipeline. Each implementation team may select its own architecture.

`new-adr` and `new-rfc` remain separate. Navigation never creates, edits, accepts, rejects, or supersedes a record.

### D2 — Evolve `rfc-status` without adding format skills

Clean-retire `rfc-status` into `navigate-decisions`. The new skill description must retain activation coverage for existing requests such as “RFC status,” “show open RFCs,” and “RFC landscape,” while adding ADR, lineage, guidance-context, decision-index, and portable-view language.

Summary output and generated HTML are modes of `navigate-decisions`, not separate skills. The exact argument names and command grammar belong to implementation design. Activation evaluations must prove that:

- RFC status and landscape requests reach decision navigation;
- ADR lookup, decision-lineage, broader-or-narrower guidance, and decision-view requests reach decision navigation;
- ADR and RFC authoring still reach `new-adr` and `new-rfc` respectively;
- intent hierarchy and intent-status requests reach `navigate-intents` rather than decision navigation.

The rename follows RFC-0067's clean-retire convention: operative references move in the same delivery change, historical frozen records remain historical, and no permanent compatibility alias is added. The implementation may stage publication if packaging requires it, but the final public roster contains `navigate-decisions`, not both names.

### D3 — Make workspace retirement a gated target

`navigate-intents` must derive navigation from canonical artifact metadata. It must not read `workspace.toml` as its inventory, lifecycle authority, or graph source.

That rule permits `navigate-intents` to replace the read-only orientation part of `workspace-status`; it does not authorize immediate deletion of the workspace system. The current registry still carries non-derivable operational choices and supports mutation workflows. Retirement therefore proceeds through four gates:

1. **Consumer inventory:** identify every reader, writer, projection, fixture, seed, guide, and adopter-facing promise that depends on `workspace.toml` or `workspace-status`.
2. **State disposition:** classify every workspace-only fact as canonical artifact metadata, derived state, externally owned projection, temporary migration state, or deliberate removal. A deliberate removal of accepted behavior must cite an accepted RFC, ADR, or errata entry with authority over that behavior. Priority and human selection cannot be presented as graph derivation unless a canonical source actually records them.
3. **Behavioral equivalence:** preserve required reconciliation, dependency, provenance, dispatch, lifecycle, cooling, repair, rollback, and prune safety until each responsibility has a named replacement or an accepted removal decision.
4. **Compatibility closure:** migrate or explicitly retire legacy entries, remove operative references and seeds, pass activation and corpus gates, and only then delete the old skill and registry contract.

Until all four gates pass, `workspace-status` and `workspace.toml` remain supported compatibility surfaces. New navigation work must not add further dependencies on them.

The workspace-retirement specification must contain the consumer inventory, the per-fact disposition record, the equivalence evidence, and the compatibility-closure checklist. The Platform Core maintainer named as this RFC's Approver certifies completion of all four gates in that specification and the retiring change. Advisory design work cannot authorize deletion, declare the inventory complete, or accept removal of existing behavior.

Mutation does not move into `navigate-intents`. A navigator reports. A workflow that owns the affected artifact or lifecycle performs any authorized edit, repair, closeout, rollback, or destructive cleanup.

### D4 — Define portable-view constraints without choosing a renderer

Each navigator must be able to emit one self-contained HTML file to a scratch location. “Self-contained” means its shell, navigation data, graph data, styles, scripts, and required offline content are present in that file and require no local server or installation.

The minimum offline content differs by population:

- `navigate-decisions` embeds the canonical ADR and RFC bodies in its normal current-corpus export so a recipient can read rationale and move among list, lifecycle-graph, guidance-context, and record-detail forms. Every form uses the same corpus membership and preserves the distinction between checked lineage, contextual references, and navigation-only grouping. When a benchmarked portability budget would be exceeded, it may emit an explicitly labelled bounded representation that keeps decision metadata, graph navigation, and source provenance offline while linking record bodies.
- `navigate-intents` embeds the intent graph's identities, canonical header metadata, and admitted edges. Intent bodies, brief and spec bodies, attachments, and support material remain source-linked unless an implementation chooses to embed them within its tested budget.

The exact profile names, threshold, encoding, and selection interface belong to the accepted implementation specification and may differ between the navigators.

It does not mean every attachment must be embedded. The default support-material contract is:

- attachments and optional supporting files are listed with repository-relative provenance and link to their repository source when a safe remote mapping exists;
- a commit-pinned source link is the stable reference when the forge supports it;
- a latest-branch link may also be offered when clearly identified as potentially newer;
- the view remains useful offline, while opening source-linked material requires repository access and is disclosed as such.

Generated HTML is a disposable projection. It is never committed as repository state, never becomes an input to another workflow, and may be deleted and regenerated at any time.

The generator must handle a corpus that is too large for the selected export without silently producing an impractical file. It must estimate or measure the payload before completion and offer or select a bounded representation that preserves navigation and provenance. The implementation team sets the threshold from supported-browser benchmarks; this RFC does not set a byte limit or mandate full versus linked mode names.

Record content and support paths are untrusted input. Before discovery, reading, size measurement, provenance display, embedding, or source-link generation, every selected record and support file must be confined to an allowed regular-file root beneath the repository. The read must reject traversal, symlinks, junctions, reparse points, special files, multiple hard links, root escape, and identity change between validation and use. Implementations must use the repository's blessed filesystem-confinement helpers rather than a string-prefix or `..`-stripping check.

Rendered Markdown must be encoded for its HTML context and must not execute scripts, event handlers, active HTML, styles, frames, or other record-provided executable content. Trust-bearing source text must refuse or visibly represent bidirectional and other non-printing controls that could spoof lifecycle, identity, relationship, or provenance cues, and generated trust labels must remain structurally separate from record-controlled text. Opening the generated file must cause no automatic network request from record or support content; remote images and other external resources render as inert links or placeholders. External navigation is an explicit user action and is allowed only for schemes and hosts admitted by the implementation specification.

Generated source links are emitted only through a recognized remote mapping. The specification must name the allowed scheme and the trusted source of its exact host allowlist; repository records, query input, environment values, and Git remote text cannot extend that allowlist. A mapping must match both a validated repository identity and an allowlisted host. The default scheme is `https`. `file:`, `javascript:`, `data:`, unrecognized hosts, and other unapproved mappings degrade to inert repository-relative provenance rather than an active URL.

### D5 — Keep design advice non-binding

Information architecture, interaction design, frontend engineering, and implementation design may produce recommendations, prototypes, benchmarks, and construction notes for either navigator. Those artifacts guide the implementation team but do not become part of this RFC's contract merely because this RFC links to them.

An implementation may depart from a later design without an RFC amendment or errata when it still satisfies D1–D4 and the accepted follow-on specification. Update, supersede, or discard the advisory design artifact through its own lifecycle. A requirement that exists only in an accepted specification changes through that specification's own lifecycle; it requires RFC amendment or errata only when the change also alters D1–D4.

An RFC amendment or post-acceptance errata entry is required only when changing an accepted decision or constraint in this RFC, such as merging the navigation populations, making a navigator mutate canonical state, retaining `workspace.toml` as a required navigation authority, or dropping the portable-view provenance and safety requirements.

## Options considered

### Navigation boundary

Axis: number and meaning of public activation surfaces.

| Option | Benefit | Cost |
| --- | --- | --- |
| **Separate `navigate-decisions` and `navigate-intents`** | Preserves population and trust boundaries while keeping output formats behind modes | Two navigation skills remain in the roster |
| One repository or workspace navigator | One apparent entry point | Hides two trust models, overloads activation, and revives the ambiguous workspace label |
| Keep `rfc-status` and add ADR/HTML skills | Minimal rename disruption | Grows the skill roster around record kinds and output formats |
| Do nothing | No migration | Leaves the decision graph without its intended navigation surface and preserves duplicated intent orientation |

### Workspace transition

Axis: treatment of accepted coordination behavior.

| Option | Benefit | Cost |
| --- | --- | --- |
| **Gated retirement** | Removes duplicated inventory while preserving behavior until replacements exist | Requires a consumer inventory and staged migration |
| Immediate deletion | Fastest simplification | Loses workspace-only dependencies, priority, lifecycle, repair, and dispatch behavior |
| Permanent registry | No migration cost | Keeps the shared hot file, duplicated status paths, and broad overloaded skill |

### Portable content

Axis: where non-canonical support material is read.

| Option | Benefit | Cost |
| --- | --- | --- |
| **Portable core with source-linked support** | Small enough to ship, provenance remains visible, attachments stay canonical | Some support material requires repository access |
| Embed every record and attachment | Maximum offline completeness | Unbounded file size and active-content handling surface |
| Metadata-only for every population | Smallest artifact | Decision readers cannot inspect rationale offline even at today's manageable scale |
| Hosted application only | No single-file limit | Adds deployment and service dependencies contrary to the requested portable artifact |

## Risks & what would make this wrong

### Compatibility and reversal risks

- **A workspace-only fact is lost.** Retirement is blocked until the consumer inventory and state-disposition record are complete and every required behavior has equivalence evidence or an accepted removal decision.
- **Activation gets worse after the rename.** The implementing spec must include positive and near-miss evaluations for RFC status, ADR lookup, decision authoring, and intent navigation before the old name is retired.
- **The new skills remain overloaded.** Output forms may be modes, but mutation, authoring, and cross-population traversal remain outside the navigators.
- **The portability contract is interpreted as “embed everything.”** The source-link rule and large-corpus fallback explicitly permit a smaller bounded artifact.
- **Advisory design is treated as frozen governance.** D5 states that mechanisms are non-binding and may change without RFC maintenance when the accepted outcomes still hold.

### Trust and safety risks

- Markdown and support files may contain active HTML or unsafe links. The view treats record content as untrusted presentation input, never executes embedded active content, and validates source-link paths and remote mappings.
- A latest-branch link may no longer match the exported record. The snapshot link is the stable reference, while any latest link must disclose that it may differ.
- A linked attachment may be unavailable to an offline recipient. The export must distinguish embedded content from repository-required content before activation.

### Falsifiable assumptions

- **Canonical artifact metadata can replace workspace orientation.** Supported for identity, lifecycle, altitude, and parentage; falsified for immediate full replacement by the current workspace-only dependency, priority, cooling, and mutation state. That is why retirement is gated.
- **A portable decision view is useful at current scale.** Untested with users. It fails if representative readers cannot answer lineage and constraint questions faster or more accurately than with repository search.
- **A bounded representation remains useful at 50× growth.** Supported by payload measurements, not by browser interaction tests. It fails if the linked representation cannot support useful search and navigation within an agreed startup and memory budget.

### Drawbacks

- The clean rename breaks callers that invoke `rfc-status` by exact skill name until they update.
- A recipient can read the portable core offline but may need repository access for attachments and support material.
- Gated retirement temporarily leaves both the workspace compatibility surface and the new intent navigator in the catalogue.
- Implementation teams must benchmark and choose mechanisms instead of receiving a prescribed renderer design from this RFC.

## Evidence & prior art

The [decision-navigation naming survey](../product/research/decision-navigation-naming-survey.md) is the promoted evidence source for this RFC. This RFC imports only its naming evidence, supplied-HTML observations, local corpus measurements, browser constraints, and source-link evidence. Any renderer-sharing, interaction, component, or implementation recommendation in that survey is advisory under D5 and is not part of this RFC's contract.

Repository authority establishes why this is a new RFC rather than a design note:

- [RFC-0064](0064-ini-001-ai-native-ecosystem.md) accepted `workspace.toml`, queue coordination, and `workspace-status`. Retiring them changes an accepted persistent representation and published workflow.
- [RFC-0067](0067-session-arc-conventions-and-pack-workflow-guide.md) accepted the `*-status` naming family and the `workspace-status` name. The `navigate-<population>` convention narrows that accepted taxonomy where orientation is derived from canonical artifacts.
- [Decision graph](../product/intents/CAP-0002-decision-graph.md) keeps accepted ADRs and RFCs separate from the intent corpus and trusts checked supersession more than free-form related text.
- [Intent graph navigation](../product/intents/FEAT-0002-intent-graph-navigation.md) already requires a bounded query and a single self-contained human view derived from headers without a persisted graph.
- [Workspace coordination reorganization](../product/intents/CAP-0003-workspace-coordination-reorganization.md) owns the non-derivable operational state and requires an inventory of every reader, writer, projection, fixture, and adopter before reorganization.

Measured on 2026-10-02:

- 237 canonical ADR and RFC records contain 5.43 MiB of raw Markdown and about 2.62 MiB when individually gzipped and base64-encoded;
- a current full Decision Explorer is therefore expected to be roughly 3–5 MiB after shell and metadata overhead;
- at linear 50× growth, canonical decision bodies reach about 130.92 MiB in the same encoded form, while decision headers remain about 9.77 MiB;
- intent headers reach about 3.50 MiB at 50×, and intent, brief, and spec headers together reach about 25.74 MiB;
- 69 RFC support files account for another 1.79 MiB today and 89.51 MiB at linear 50× growth, which supports linking rather than default embedding;
- `workspace.toml` currently contains 370 entries across 42 lifecycle collections, including 25 legacy entries, 88 canonical `needs` edges, and 177 `backlog.open` entries.

The size result supports a portable full decision view today and a bounded large-corpus fallback. It does not select compression, data layout, rendering, or a threshold.

## Experiment / validation

Before a navigator ships, its implementing specification must define and run:

1. **Activation evaluation:** representative positive prompts and near misses across decision navigation, intent navigation, ADR authoring, RFC authoring, and existing status language.
2. **Corpus construction and view-parity test:** headers, status, identifiers, and trusted edges in every view match the canonical files; free-form relations and visual grouping are not promoted to checked edges; and switching views does not change corpus facts.
3. **Portability test:** the generated file opens from local disk with no server; its required offline content, list, graph, guidance-context, detail, and history navigation work without network access; and opening it triggers no automatic external request.
4. **Input and source-link test:** traversal, link, special-file, multiple-hard-link, identity-change, root-escape, unsafe-scheme, unrecognized-host, snapshot, latest, fallback-path, and missing-remote cases are exercised without reading outside allowed roots or executing record-provided active content.
5. **Scale test:** synthetic 10×, 25×, and 50× corpora measure generated size, startup time, search response, and peak memory on supported desktop browsers. The implementation team records the tested threshold and fallback behavior in the specification or implementation documentation.
6. **Workspace-equivalence test:** before retirement, a frozen corpus compares every required reconciliation, dependency, provenance, dispatch, lifecycle, cooling, and cleanup outcome between the accepted old behavior and its replacement or accepted removal decision.

The decision-view bet fails if representative maintainers cannot answer “what constrains this?”, “what superseded this?”, and “what broader or narrower guidance should I inspect?” more accurately or quickly than with repository search, or if they mistake a visual grouping for checked authority. Workspace retirement fails closed if the consumer inventory is incomplete or any required old outcome lacks a replacement or accepted removal decision.

## Follow-on artifacts

Acceptance creates these required follow-ons:

- **At RFC acceptance:** add errata to RFC-0064 naming RFC-0105 as the authority for the workspace retirement target while preserving RFC-0064 behavior until the gates above pass, and add errata to RFC-0067 naming RFC-0105 as the authority for artifact-derived `navigate-<population>` naming while leaving other durable-state `*-status` skills unchanged.
- **Before implementing decision navigation:** accept the reshaped decision-graph capability and an aligned specification for the `rfc-status` to `navigate-decisions` migration, activation evaluations, decision derivation, multi-form portable view, supported browser set, and benchmark plan. RFC-0105 does not waive that intent lifecycle.
- **Before implementing intent navigation:** close the intent graph navigation intent's required de-risk and decomposition gate, satisfy its intent-identity dependency, and then accept a specification. Any brief or spec mapping also waits for the accepted intent-to-delivery traceability authority and remains a display-only consumption of that mapping. RFC-0105 does not waive either dependency or the governing intent lifecycle.
- **Before retiring workspace coordination:** close the workspace coordination reorganization intent's required de-risk and decomposition gate, then accept a workspace-retirement specification containing the compatibility inventory, every residual fact and consumer, the required authority for any removal, and the four gate proofs. RFC-0105 sets the retirement target but does not waive that governing intent lifecycle.
- **When each public migration ships:** update authoring guidance, pack manifests, user guides, and changelog entries.

Advisory experience and implementation design is optional and explicitly non-binding under D5.

No ADR is required merely to repeat this RFC. A later architectural choice warrants an ADR only if it settles a durable implementation decision not already made here.
