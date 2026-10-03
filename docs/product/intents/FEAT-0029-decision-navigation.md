# Decision navigation

- **Slug:** `decision-navigation`
- **Status:** Accepted
- **Accepted:** 2026-10-02 owner ratification
- **Level:** feature
- **Owner:** Platform Core maintainer
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:decision-graph

## Outcome

- **Steerable input:** Reduce the record opens and manual relationship checks needed to find an ADR or RFC, move among list, lineage, guidance-context, and detail views, and reach its rationale.
- **Lagging outcome:** People and agents answer decision-status, constraint, lineage, guidance-context, and rationale questions accurately from canonical records, and can hand the same trustworthy context to an offline reviewer.
- **Guardrail:** Navigation never authors or mutates a decision, invents checked authority from free-form prose or visual placement, turns generated HTML into repository state, or makes record content executable. It never presents a lookup or rendered grouping as the complete policy applicable to an action. ADR and RFC authoring remain separate, and a large export remains useful through an explicit bounded representation rather than an impractical silent payload.

## Opportunity

- **Functional job:** Scan the decision corpus, follow what superseded a record, move from wider decisions to narrower guidance, and inspect why each decision was made without reconstructing the corpus by hand.
- **Emotional job:** Trust that the view distinguishes checked lineage from loose references and that its rationale matches the canonical record.
- **Social job:** Share one reviewable artifact that lets another person trace a decision without first installing repository tooling.
- **Struggling moment:** Decision status, lineage, guidance, and rationale are spread across ADR and RFC files. A flat list cannot show how decisions evolve or where narrower guidance sits in context, while an unqualified graph can make every visual connection look authoritative.

## Boundary

This feature owns the read-only `navigate-decisions` surface defined by [RFC-0105](../../rfc/0105-artifact-derived-navigation-and-workspace-retirement.md):

- lifecycle summaries and bounded lookup across ADRs, RFCs, or both;
- the same bounded metadata and lineage query for humans and agents, so an agent can retrieve a named decision or path without paying whole-corpus body cost;
- checked full and partial supersession lineage, with unresolved `Related` content kept visibly weaker than a checked edge;
- peer list, lifecycle-graph, guidance-context, and record-detail views over the same record population and facts;
- wider-to-narrower guidance navigation when an admitted directional fact or explicit caller assertion supplies direction, with neutral grouping otherwise and visible checked, contextual, caller-supplied, or unresolved trust state rather than a new core relation;
- an explicit route from summary facts to the canonical record body or repository source;
- clean retirement of the public `rfc-status` name while retaining its RFC status and landscape activation coverage;
- an on-demand, single-file HTML artifact whose shell, navigation data, graph data, styles, scripts, and promised offline content are embedded;
- full canonical ADR and RFC bodies in the normal current-corpus export, plus an explicitly labelled bounded representation when the tested portability budget would otherwise be exceeded;
- repository-relative provenance and safe, explicit source links for attachments and optional supporting files.

It does not own ADR or RFC authoring, lifecycle mutation, acceptance or supersession, the intent population, or a hosted decision store. It also does not decide which decisions completely govern a work context, compile policy rules, enforce agent behavior, or turn conflicts and outcomes into automatic evolution. Those uses remain outside navigation. It does not require a new core record shape, shared renderer, component system, build pipeline, payload encoding, compression method, search implementation, layout, interaction model, or fixed size threshold. Later design work is advisory; the implementation team may choose or change those mechanisms while RFC-0105 and the accepted implementation specification remain satisfied.

Generated HTML is disposable scratch output, never an input to linting, derivation, authoring, or lifecycle computation. Record and support content is untrusted: construction must use the repository's confined regular-file helpers, render record content inertly, make no automatic network request, and emit an active source URL only through an allowlisted remote mapping.

## Owner

- Platform Core maintainer. Accountable for the navigation outcome, activation migration, and evidence required before `rfc-status` retires.

## Unresolved questions

- Which tested portability budget triggers the bounded representation on supported desktop browsers.
- Whether representative humans and agents complete lineage and constraint tasks more accurately or quickly than with repository search.
- Which visual treatment makes checked lineage, contextual guidance, and navigation-only grouping unmistakably different.

## Projection

No tracker projection is selected. The human HTML file is a disposable view, not an outbound tracker projection or a second lifecycle home.

## Assumptions

- **Riskiest assumption:** Representative humans and agents will use a read-only decision navigator before context checks are integrated, and at least four of five representative runs will complete lineage and guidance tasks unaided without mistaking an unresolved relation or visual grouping for a checked edge. A fresh corpus task probe supports feasibility and honest trust distinctions; comparative human-and-agent use remains `to-validate`.
- Clean-retiring `rfc-status` into the broader name can preserve current status activation while adding ADR lookup and lineage without diverting authoring prompts from `new-adr` or `new-rfc`.
- A current-corpus export with embedded decision bodies is practical, and an explicitly bounded, source-linked representation remains useful as the corpus grows.
- The deliberately different ADR and RFC metadata shapes can be shown honestly without inventing parity or hiding missing fields.
- **Knowledge surface:** in-repo decision records, RFC-0105, the decision-navigation research survey, and current governance skill contracts.

The feature-level task probe below survived. It establishes that the bounded navigation job is answerable and can preserve the trust boundary; it does not establish adoption, activation compatibility, or browser portability, which remain explicit validation and delivery obligations.

## De-risk record

- **Status:** survived on 2026-10-02; representative human-and-agent use remains `to-validate`
- **Reversibility triage:** two-way door. A read-only query and disposable HTML view can be withdrawn without changing a canonical record, lifecycle, or enforcement boundary.
- **Prototype-approach:** `prototype-led`. A paper query/view over the real corpus is enough to test task usefulness and trust distinctions before selecting implementation architecture.

### Riskiest assumption

A read-only decision navigator is useful before context checks are integrated because people and agents can answer common status, lineage, guidance-context, constraint, and rationale questions with fewer manual record checks while preserving the distinction between checked edges, contextual references, navigation groupings, and missing metadata.

What would have to be true: representative tasks must resolve from canonical metadata plus an explicit body/source action; navigation must reduce rather than merely rearrange the manual work; ADR and RFC shape differences must remain visible; and no task may turn missing applicability or free-form `Related` text into governing policy.

### Kill condition, predeclared 2026-10-02

Kill the standalone navigation feature if a fresh eight-task packet over records not used by the parent probe fails any condition:

1. fewer than six of eight tasks are answerable from bounded metadata plus at most one explicit canonical-body/source action;
2. fewer than five of eight tasks remove at least one manual file discovery, status check, or lineage check compared with direct repository search; or
3. any answer promotes an unresolved relation, missing field, or prose-only applicability claim into checked lineage or governing policy.

The line is recorded before the records and task questions are selected. This desk probe can establish task feasibility, not human adoption.

### Probe

The packet used eight records that were not in the parent capability's ten-record navigation sample: ADR-0001, ADR-0020, ADR-0023, ADR-0042, RFC-0067, RFC-0098, RFC-0099, and RFC-0100. The task questions and results were:

| Task | Bounded answer shape | Manual work removed | Trust result |
| --- | --- | --- | --- |
| Is ADR-0001 current in full? | `Accepted`; D3 is superseded in part by ADR-0020. | One status check and the second endpoint lookup. | Kept partial supersession narrower than whole-record supersession. |
| What replaced ADR-0001 D3? | ADR-0020, whose reciprocal header says it supersedes ADR-0001 D3 in part. | File discovery and the reciprocal-lineage check. | Used the checked pair, not `Related`. |
| Is ADR-0023 live? | No. It is `Superseded` by ADR-0042. | File discovery and status/endpoint checks. | Did not treat the related list as lineage. |
| What current decision replaces ADR-0023, and why? | ADR-0042 is `Accepted`; one explicit body action reaches its decision summary and rationale. | Successor discovery and status check. | Kept metadata separate from canonical rationale. |
| What did RFC-0067 decide, and is it current? | `Accepted`; one body action reaches its session-arc naming decision. | File discovery and status check. | Made no applicability claim from `Related`. |
| What did RFC-0098 admit, and is it current? | `Accepted`; one body action reaches its direct-skill-repository decision. | File discovery and status check. | Made no policy claim beyond the record. |
| What is RFC-0099's lifecycle state? | Surface the exact qualified header: `Accepted (superseded in part by ADR-0111 ...)`; do not coerce it to a bare status token. | File discovery and lifecycle-header lookup. | Preserved an irregular source shape instead of inventing parity. |
| What does RFC-0100 govern, and where is its rationale? | `Accepted`; one explicit body/source action reaches the requested decisions and rationale. | File discovery and status check. | Missing ADR-style summary fields stay missing. |

### Verdict — survived

The packet passed all three predeclared conditions:

- **8 of 8** tasks were answerable from bounded metadata plus no more than one explicit canonical-body/source action, against a threshold of 6.
- **8 of 8** removed at least one manual discovery, status, or reciprocal-lineage check from the direct-search path, against a threshold of 5.
- **0 of 8** promoted `Related`, a missing field, or prose-only applicability into checked lineage or governing policy.

This is a paper navigation prototype over real records, not evidence that a production interaction is faster or preferred. The feature therefore survives into decomposition while the comparative-use hook stays open. Activation compatibility and browser scale are delivery checks rather than reasons to repeat this information-shape probe.

### Validation hook

```yaml
validation_hook:
  assumption: Humans and agents will use read-only decision navigation before context checks are integrated.
  kill_condition: Fewer than four of five representative human or agent runs complete lineage and guidance-context tasks unaided, or any run treats an unresolved relation or visual grouping as checked lineage or complete governing policy.
  activity: to-validate — compare `navigate-decisions` with repository search using five representative maintainer and agent runs across status, lineage, guidance context, rationale, and source-handoff tasks.
```

## Shaping review

The human-and-agent navigation boundary passed an isolated intent-mode shaping review on 2026-10-02 using an attributed packet derived from artifact revision `sha256:d1b83fc97026f7642b9ce6042302dbcfb8534c499b2b7e1cf8aea24be6054849`. Stamping the review date and this binding note is nonmaterial; it changes no outcome, opportunity, assumption, altitude, boundary, or projection.

## Decomposition

**One slice, `decision-navigation`**, handed to `new-spec` as a delivery contract. The bounded query, activation migration, derived lineage, portable view, and scale fallback form one public replacement for `rfc-status`: none is independently valuable or safely releasable without the others. A delivery brief would add coordination structure without creating a second independently shippable feature or repository.

### Why one slice

- A query-only slice would not satisfy the offline human handoff outcome or prove the single-file portability contract.
- An HTML-only slice would create a second activation surface and leave agents without the bounded retrieval path the same feature promises.
- Renaming `rfc-status` before ADR coverage, lineage, and compatibility evidence exist would break rather than migrate current activation.
- The large-corpus fallback is a safety property of the export, not a separate product outcome.

The feature remains one specification with testable increments. That does not require one renderer, component system, data encoding, or implementation module.

### Delivery contract

- **Outcome.** A person or agent names a decision, kind, lifecycle question, guidance question, or checked lineage path and gets an accurate bounded answer from canonical ADR and RFC records; a person can move among list, lifecycle-graph, guidance-context, and detail views in one self-contained, read-only HTML file and follow explicit source links for material that is not embedded.
- **Success signals.** Five representative maintainer and agent comparisons produce at least four unaided completions and no trust-boundary error. Existing RFC-status and RFC-landscape activation cases still route to the replacement. The current corpus produces a full-body artifact, while synthetic 10x, 25x, and 50x corpora complete under a recorded supported-browser size, startup, search-response, and peak-memory budget or select an explicitly labelled bounded representation before writing an impractical file.
- **In scope.** ADR/RFC/both lifecycle summaries; named and bounded lookup; peer list, lifecycle-graph, guidance-context, and record-detail views; checked full and partial supersession; visibly weaker contextual references and navigation grouping; exact source-shape handling for missing or qualified fields; an explicit canonical-body/source action; one generated HTML file with embedded shell and promised offline data; normal current-corpus full bodies; bounded large-corpus fallback; safe support inventory and repository-source links; and the complete `rfc-status` activation and public-name migration.
- **Non-goals.** Authoring or mutating records; accepting or superseding a decision; adding a required ADR/RFC metadata shape; deriving checked lineage from `Related`, scope prose, visual placement, or model judgment; deciding which decisions completely govern a work context; compiling or enforcing policy; embedding every attachment; reading adjacent Markdown from browser disk; persisting generated output; adding a hosted service; or prescribing renderer sharing, components, layout, compression, search, graph library, or other implementation architecture.
- **Dependencies and gates.** RFC-0105 must be accepted before its migration or portability rules become implementation authority. The reshaped parent decision-graph capability must be accepted before implementation dispatch. Implementation uses the repository's blessed confined regular-file helpers for every discovered, measured, embedded, inventoried, or linked file. `new-adr` and `new-rfc` remain separate authoring owners. A safe allowlist and source-remote mapping must exist before active support links are emitted.
- **Advisory design context.** The supplied `rai-azure-adr-review.html` and the existing `explain-diff` HTML informed useful information elements: project context, invariants, corpus counts, filters, compact summaries, reviewer prompts, and progressive access to detail. They are references, not implementation bases or architecture mandates. The research measurement says 237 canonical decision records currently hold 5.43 MiB of Markdown and about 2.62 MiB as per-record gzip plus base64, while a linear 50x body payload is about 130.92 MiB; headers alone remain about 9.77 MiB. Supporting files stay source-linked by default. The implementation team chooses mechanisms and records the tested portability threshold.
- **Delivery questions for the specification.** Which desktop browsers and versions define the benchmark set? Which CLI syntax exposes the accepted versioned query semantics? How are qualified or unknown lifecycle values represented and filtered? Which legacy activation evaluations prove the rename is safe? Which exact hosts enter the implementation-owned source-link allowlist? What threshold and user choice select full-body versus bounded output? Which support-file types may be inventoried, embedded, or only linked?
- **Provenance.** This intent and its surviving 2026-10-02 task probe; RFC-0105; [the decision-navigation naming survey](../research/decision-navigation-naming-survey.md); and the parent [decision graph](CAP-0002-decision-graph.md). Later design work remains non-binding unless its requirement is accepted into the specification or governance record.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md`
- **Authority:** Platform Core maintainer

Framed from RFC-0105 D1, D2, D4, and D5 on 2026-10-02. The RFC fixes the population, trust, portability, and authority boundaries while leaving implementation architecture to later non-binding design and the accepted feature specification.
