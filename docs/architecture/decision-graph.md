# Decision graph architecture

> **STATUS: PLANNED.** This document describes the future-state architecture
> governed by [RFC-0105](../rfc/0105-artifact-derived-navigation-and-workspace-retirement.md)
> and shaped by the accepted [decision-graph capability](../product/intents/CAP-0002-decision-graph.md).
> It is not a statement of current repository behavior. The implementation team
> owns renderer, query, component, and storage choices within the accepted RFC
> and feature contracts. Replace this banner with **CURRENT** only after the
> shipped behavior and its verification agree with this model.

The current baseline is [Governance Extras design](../../packs/governance-extras/DESIGN.md):
`rfc-status` is a read-only RFC lifecycle summary, while `new-adr` and `new-rfc`
own separate authoring flows. This planned architecture replaces the summary
surface with ADR-and-RFC navigation and adds disposable views. It does not
change the authoring owners, canonical Markdown records, or repo-only pack
scope.

## 1. Purpose

The decision graph makes the repository's ADRs and RFCs usable as reference
policy for humans and agents. It preserves canonical records as the authority,
adds checked lifecycle and lineage facts, and supplies several read-only views
for different questions.

The graph does not compile prose into rules or decide which complete policy
applies to an action. It supplies attributable context that a person or agent
checks while planning, implementing, reviewing, or making a future decision.

## 2. Architectural qualities

The design optimizes for three qualities, in order:

1. **Authority and provenance integrity.** A rendered fact remains traceable to
   the canonical record and its exact lifecycle value.
2. **Honest incompleteness.** Checked lineage, contextual references, search
   groupings, conflicts, omissions, and unknowns remain visibly different.
3. **Low ceremony and evolvability.** Navigation and context checks work with
   the records that exist and do not require a policy language or mandatory
   metadata retrofit.

These priorities deliberately trade automatic resolution for trust. A bounded
answer that states its limits is preferred over a confident but inferred rule.

## 3. System context

**Question:** Who uses the decision graph, and where does authority return when
a durable decision changes?

```text
canonical ADR and RFC files
            │
            ▼
navigate-decisions ────────┬──────────── human judgment
                           └──────────── agent judgment
                                          │
                                          ▼
                              existing ADR or RFC lifecycle
                              when a durable decision changes
```

## 4. Navigator subsystem flow

**Question:** How do canonical records become bounded queries and disposable
human views without creating another source of truth?

```text
confined discovery → ephemeral read model → bounded agent query
                              │
                              └───────────→ disposable human projections
                                             ├── corpus list
                                             ├── lifecycle graph
                                             ├── guidance context
                                             └── record detail
```

Every output is a disposable projection over one fact model. The diagram names
observable responsibilities, not required modules or a shared renderer.

## 5. Authority and trust model

The canonical Markdown records remain the only decision authority. Generated
query results and HTML files are snapshots with provenance; neither becomes a
source of truth.

The graph carries five visibly different trust categories:

| Class | Source | What a view may claim |
| --- | --- | --- |
| Checked lineage | Validated reciprocal full or partial supersession metadata | A record replaces all or named parts of another record |
| Canonical record fact | An admitted record field or exact lifecycle value | The record states this value at the exported revision |
| Contextual reference | Explicit but unchecked material such as `Related` | The source record points to this material; the relationship is not validated lineage |
| Caller assertion | An explicit query or view input | The caller asked to inspect this direction; it is navigation-only and non-authoritative |
| Navigation grouping | A query, filter, shared area, or scope reading | These records are shown together for inspection; grouping creates no graph authority |

Free-form prose, filenames, dates, directory proximity, and model judgment do
not create checked edges. A guidance view may present a broad ADR with a more
specific ADR beneath it only when admitted directional metadata or an explicit
caller assertion supplies that direction. Contextual references and
navigation-only groupings may place records in a neutral co-view, never in a
broad-to-narrow hierarchy.

A caller assertion has `trust_class=navigation_only` and
`resolution_state=caller_asserted`; it cannot be promoted to a canonical fact
by rendering. The visual arrangement does not change the core record shape.

Every rendered or queried relationship carries projection metadata separate
from the source record: `basis`, `source`, `direction`, `trust_class`, and
`resolution_state`. These fields describe why the view placed two records
together; they are not written back to ADRs or RFCs.

Directional wider-to-narrower hierarchy is permitted only when an admitted
directional fact or an explicit caller assertion supplies that direction.
Caller-supplied direction is always non-authoritative navigation context. Scope
similarity, search results, and `Related` references otherwise remain neutral
co-view grouping.

A semantic conflict is likewise a caller or reviewer observation unless
canonical metadata records it.

## 6. Read model

For this repository, the admitted population is every confined direct child of
`docs/adr/` or `docs/rfc/` whose basename matches `NNNN-*.md`, excluding
`README.md`, `*-research.md`, and support subdirectories. A candidate-shaped
file that is malformed or duplicates a kind-plus-ordinal identity fails the
corpus; it is not silently reclassified as support material. The accepted
[decision-navigation specification](../specs/decision-navigation/spec.md#corpus-and-query-contract)
owns the complete discovery and bounded-query contract.

The ephemeral read model needs only the facts required by the accepted
navigation contract:

- stable record identity and kind;
- exact recorded lifecycle state, including missing or unfamiliar values;
- repository-relative source and export provenance;
- structured fields already admitted by the ADR or RFC contract;
- canonical body availability and explicit omission state;
- checked supersession lineage, including partial-decision scope;
- contextual references that remain outside the checked edge set; and
- supporting-information inventory and safe source handoff.

The model may expose view-specific indexes in memory. It does not require a
persisted graph, a database, a new ADR/RFC metadata schema, or one internal
representation shared by agent queries and HTML.

## 7. Multi-form navigation

The same corpus supports several peer views because no single form answers all
decision questions well.

### Corpus list

The list is the broad orientation surface. It supports exact lifecycle and kind
filters, search, compact summaries, corpus counts, and fast movement to a
record. It preserves the useful part of the original RFC-status inventory.

### Lifecycle graph

The lifecycle graph answers what replaced what and whether replacement is whole
or partial. It exposes exact lifecycle values and checked edges rather than
deriving one universal “current” answer across partial scopes, branches, cycles,
or unfamiliar statuses. Those cases display `unknown` or `conflict` at the
affected record or decision scope. Superseded records stay available as
explanatory history.

### Guidance context

The guidance view helps a reader inspect a wider decision beside narrower or
more detailed guidance. It is a rendering lens rather than a new graph
contract. Direction comes only from an admitted directional fact or explicit
caller assertion. A caller assertion is labelled navigation-only rather than
record authority. Canonical scope facts, contextual references, and search
similarity can place records in a neutral context neighborhood, but cannot
create a parent or child. Each relationship keeps its trust label, and no
arrangement is presented as automatically applicable policy.

### Record detail

The detail view preserves the complete rationale, decision text, consequences,
supporting-information inventory, provenance, and safe source handoff. It is the
place to inspect the canonical meaning behind a compact node or list row.

A human can switch among these forms without changing corpus membership or
facts. Agent queries receive the same identities, lifecycle, checked lineage,
contextual references, and provenance in a bounded machine-readable result.
Record-controlled values travel as explicitly marked untrusted data beneath
repository and user instructions. Producer encoding prevents structural escape;
the owned skill-consumption rule separately prevents instruction-shaped record
content from changing scope, workflow selection, permissions, or tool use.

## 8. Context-check flow

> **PROVISIONAL.** FEAT-0031 remains Draft and unde-risked. This section fixes
> only the boundary that navigation must preserve; it does not authorize a
> workflow integration or make context checks a delivery dependency for
> decision navigation.

A decision context check is a lightweight use of navigation, not a new policy
layer:

1. The caller supplies explicit anchors such as a record identifier, repository
   area, changed surface, or decision question.
2. Navigation returns a bounded set of canonical records, checked lineage, and
   separately labelled contextual evidence.
3. The result states the anchors, corpus revision, search boundary, omissions,
   conflicts, and unknowns.
4. The person or agent checks the proposed action against the cited record
   content and applies judgment.
5. When the action changes a durable decision, the existing `new-adr` or
   `new-rfc` lifecycle owns the change. Ordinary maintenance remains ordinary
   maintenance.

Absence is not permission. Retrieval relevance is not authority. Context
presence does not prove compliance. A workflow may require a compact receipt
of consulted records, but enforcement remains with that workflow's existing
controls rather than with the graph.

## 9. Runtime and publication boundaries

Record discovery and reading stay within the repository's confined regular-file
boundary. Unsafe, malformed, ambiguous, or duplicate canonical inputs fail
before a successful result or artifact is published.

The human export is one self-contained offline HTML file. It embeds the data,
styles, scripts, and promised content needed for its selected representation.
It does not hydrate from adjacent Markdown or fetch repository content at
runtime. Supporting material that is not embedded is inventoried and handed off
through a safe source reference.

The current corpus may use a full-body representation. Growth beyond the
benchmarked browser budget selects an explicitly labelled bounded form rather
than silently dropping records or creating a hosted dependency. Query and HTML
must agree at the fact boundary even when their internal implementations differ.

## 10. Failure behavior

The architecture fails honestly:

- a missing or unfamiliar lifecycle value remains distinct from an accepted
  value;
- an unresolved or one-sided relationship never becomes checked lineage;
- conflicting accepted records are shown together without selecting a winner;
- a query boundary and omitted content remain visible;
- no result is described as the complete policy applicable to an action;
- record-controlled text stays inert in browser and agent outputs; and
- an unsafe input or destination produces no partial published artifact.

These behaviors make uncertainty inspectable instead of hiding it behind a
clean graph.

## 11. Ownership and evolution

`navigate-decisions` owns read-only discovery, bounded queries, and human views.
`new-adr` and `new-rfc` remain separate authoring owners. Decision-context
checks consume navigation results at selected workflow points without taking
over either responsibility.

The architecture can evolve by adding a new view, query mode, or implementation
strategy without changing the reference-policy model. A future change that
promotes a contextual relationship to checked authority, changes the public
query contract, or adds enforcement crosses a separate governance boundary and
must be decided explicitly. Ordinary rendering improvements do not.
