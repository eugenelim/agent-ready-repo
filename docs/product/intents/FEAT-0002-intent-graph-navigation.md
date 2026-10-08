# Intent graph navigation

- **Slug:** `intent-graph-navigation` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:repository-work-graph
- **De-risked:** 2026-10-07
- **Shaping-reviewed:** 2026-10-07
- **Decomposed:** 2026-10-08 brief
- **Accepted:** 2026-10-07 by eugenelim, lifecycle owner. Revision `8014f2622eab1841` (file blob) returned a clean independent intent-mode shaping review after the owner's four delivery decisions were recorded; an earlier revision had also reviewed clean. The riskiest assumption survived `de-risk-intent` against a kill condition predeclared before the probe ran.

## Outcome

- **Steerable input:** Reduce the number of files a reader must open, and the amount of shape they must reconstruct by hand, to learn what intents exist and how they relate.
- **Lagging outcome:** People and agents can inspect intent altitude, status, parent, related edges, direct features, and unclassified legacy intents through a graph derived from artifact headers on demand — an agent through a bounded query, a person through a single-file view — with no persisted graph artifact in the repository.
- **Guardrail:** The graph is derived from artifact headers on demand and never persisted, so it cannot go stale while reading as current and adds no generated file for concurrent work to collide on. Graph metadata stays in preamble fields; artifact bodies are never read to build it. The artifacts stay authoritative, status keeps its single home, and an unclassified legacy intent is shown as unclassified rather than given an inferred altitude.

## Opportunity

- **Functional job:** See the whole body of repository work at once — what exists, at what altitude, under what parent, next to what, and in what state — and find the part that matters now.
- **Emotional job:** Trust the view, because it is derived from the same files that hold the work.
- **Social job:** Hand a maintainer or a reviewer one place to look, instead of a list of files and an explanation of how to read them.
- **Struggling moment:** The shape is mostly unrecorded rather than merely unindexed. Of 130 intent files, 119 carry a `Level:` and only 9 carry a `Parent intent:`, so a reader cannot tell a direct feature from an unclassified legacy intent without reading each file. `lint-traceability.py` already derives a graph from the artifacts — 599 nodes, 85 edges — but it is a structural-orphan lint rather than a navigation surface, and it recognizes an intent as a graph node only when it carries `Kind: outcome`, `Kind: opportunity`, or `Level: capability`.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- the graph over the intent corpus, **derived from artifact headers on demand and never persisted**, and what it must expose: altitude, status, parent, related edges, direct features, and intents that carry no classification;
- the public read-only `navigate-intents` skill defined by [RFC-0105](../../rfc/0105-artifact-derived-navigation-and-workspace-retirement.md), with **two surfaces over the artifact-derived graph**: a bounded query that returns identities, header facts, edges and paths but never artifact bodies, and a human view emitted on demand as a single self-contained HTML file to a scratch location, leaving no repository footprint. The view is a consumer of the derivation, never a second source of truth;
- the portable view's offline core: intent identities, canonical header metadata, and admitted edges. Intent bodies, brief and spec bodies, attachments, and support material remain source-linked unless an implementation deliberately embeds them within its tested portability budget;
- the view's design route — `information-architecture` owns its structure and widget hierarchy through the analytical genre method, `interaction-design` its behaviour, and `frontend-engineering` the single-file build; the workspace genre method in `information-architecture` is the alternative route if it proves to be a sustained-work surface rather than a read-and-act one;
- how a related-intent edge is recorded on the artifact and read into the view;
- how an unclassified legacy intent is surfaced without inventing an altitude for it.

It does not own identity or placement (`intent-identity-and-registration`), the downstream mapping to a brief or spec (`intent-delivery-traceability`), operational coordination state (`workspace-coordination-reorganization`), or rendering the graph into a tracker (`external-tracker-projection`). It never reads `workspace.toml` as its inventory, lifecycle authority, or graph source, and it never mutates an intent or coordination record. It does not require a shared renderer with decision navigation or choose a schema, component system, payload encoding, compression method, search implementation, layout, interaction model, or fixed size threshold. Under RFC-0105 D5, later design work is advisory and may change without RFC errata while the accepted RFC and feature specification remain satisfied.


**Inbound 2026-09-24 — a second consumer already builds part of this graph, and the convergence is recorded here because nothing re-reads that consumer's boundary when this intent is shaped.** [FEAT-0005](FEAT-0005-lifecycle-and-closure.md) § Boundary was amended that day to move eligibility computation into that child, because this intent is `Status: Draft` with `Decomposed:` absent and its closure check could not wait. That child may build an **in-memory descendant set** by inverting declared up-edges, bounded by three conditions that [FEAT-0005](FEAT-0005-lifecycle-and-closure.md) § Boundary states and owns. They are deliberately not reproduced here — read them there, because a copy would drift the moment that section is amended. Persistence, publication and any surface a second consumer reads remain this intent's, undiminished, and **no ordering edge runs in either direction**. When this capability lands, treat that child's per-decision resolution as a candidate consumer to absorb rather than a rival to leave standing — otherwise the repository keeps two independent edge-inversion implementations.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Whether an intent recording neither parent nor altitude is a permanent first-class category rather than a defect to migrate away. On 2026-10-07 the category has 0 members: every live intent carries `Level:`. The open case for the view is an intent with an altitude and no parent (100 of 168). The permanence policy remains the owner's.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Hard dependency

This child depends on the cross-artifact reference grammar owned by [`intent-identity-and-registration`](FEAT-0001-intent-identity-and-registration.md). It is the one real dependency in this family, and it was discovered after the family was cut.

The grammar has shipped. `resolve_endpoint` in `lint-traceability.py` now refuses a bare-slug pointer that suffix-matches more than one node, returning its own `ambiguous` state. Before the grammar, it chose a match by sort order and produced a wrong edge that stayed the same from run to run. Cross-type slug collisions numbered 6 when this intent was written on 2026-09-18 and number 18 on 2026-10-07: 5 between an intent and a brief, 13 between an intent and a spec. One fired during this family's shaping, taking `lint-traceability` to exit 1 on a self-referential brief edge.

Making feature intents graph nodes could turn every collision into a refusal. The 2026-10-07 De-risk record shows it does not. No navigator edge uses a bare slug, and a resolver scoped to each field's target type meets none of the 18.

This dependency is recorded here and in the parent's decomposition log rather than as a `needs` edge, because the intended delivery order already places the grammar first and a blocking edge would add nothing the order does not already give.

## Settled design decisions

Decided 2026-09-18 by the owner, after two independent design passes that disagreed on the central question. Recorded here because they constrain this child and its two siblings; the reasoning that is specific to one sibling sits on that sibling.

### The graph is derived on demand and never persisted

No generated index file is committed, and none is written to disk. The graph is derived from artifact headers each time it is asked for, which is ADR-0112 D1's **absent** branch rather than its generated branch: there is no index, so there is nothing to go stale.

Four reasons, each independently sufficient:

- **Cost is not the constraint.** A header-only derivation over the whole corpus takes well under a second, roughly an order of magnitude cheaper than the existing whole-file walk in `lint-traceability.py`. The argument for persisting rested on the expensive walk's cost, which is an artefact of reading whole files rather than a property of deriving the graph.
- **The runner objection is already settled.** ADR-0006 establishes that adopters have no guaranteed Python runtime, which appears to forbid a derive-on-demand script. ADR-0007 narrowed exactly that: D1 ships such a script to adopters as a skill script, D2 makes it agent-invoked rather than fail-closed, D3 keeps the fail-closed gate inside this catalogue, and D4 states the narrowing explicitly. ADR-0006 constrains hooks and gates, not agent-invoked scripts, and pack skills already ship many of them.
- **A committed index cannot be kept untracked in an adopter repository.** No pack seeds a `.gitignore`, so the disposable-local-accelerator route is unavailable downstream. A generated graph would have to be committed, which makes collision unavoidable rather than mitigable.
- **A committed generated file is a contention surface, and this work exists to remove one.** Concurrent work across multiple worktrees would each regenerate it, so every merge carries a conflict on a file nobody authored. `lint-generated-path-ownership.py` would also require it to declare exactly one producer, on the principle that no generated projection is an authoring dependency.

Two consequences follow and are not separately decided. Status keeps the single home `docs/product/AGENTS.md` gives it, because there is no second generated projection that could own it — a derived answer echoes the artifact's status and never caches it. And there is no index location to choose.

### Graph metadata lives in headers, never in bodies

This is the constraint that keeps the decision above true, so it is a guardrail rather than a preference. Derivation reads each artifact's preamble fields and stops; artifact bodies are more than an order of magnitude larger than their headers and are never read to build the graph. Any future graph metadata — related edges, altitude, area, lifecycle — is added as a preamble field. **If graph metadata ever moves into prose, the cost model inverts and the no-persistence decision has to be reopened.** That is the condition that would falsify it.

### The query and the human view are two surfaces over one derivation

They have different consumers and different shapes, and conflating them makes the agent surface unbounded — an agent asking about one node would pay whole-corpus cost.

- **The query** answers a bounded question and returns node identities, header facts, edges and paths, never bodies; the reader opens the artifact for detail. "Show me every in-flight capability" is a query, not a view.
- **The human view** is a **single self-contained file, emitted on demand** to a scratch location rather than into the repository, so it leaves no tracked or untracked footprint and needs no second distribution surface. It is a consumer of the derivation and never a second source of truth.

The view is a designed surface, not an incidental dump. Its structure and widget hierarchy route through `information-architecture`'s analytical genre method, which owns how a view carries a reader from a status signal to a diagnostic to an action; its interactive behaviour routes through `interaction-design`; and the single-file build is `frontend-engineering`'s, since its primary output is HTML, CSS and JS. If the view turns out to be a sustained-work surface rather than a read-and-act one, the workspace genre method in `information-architecture` is the alternative route — the two methods' scopes overlap here and the call belongs to whoever shapes the view.

### Two hazards the implementation must respect

- **Do not reuse the discovery sidecar's filename or `schema_version` namespace.** `discover_sidecar` in `lint-traceability.py` discovers `_state/traceability.json` through three tiers, the last a bounded tree-wide glob and never a hardcoded path, and `load_sidecar` then treats what it finds as **authoritative**, replacing artifact derivation. A derived graph written to that name anywhere in the tree would make the lint read this capability's own output as authority — a control that cannot fail.
- **Reuse that sidecar's vocabulary, though.** Its node and edge shape is already defined and already consumed, so the derived in-memory graph should speak the same words at a different scope rather than inventing a rival vocabulary.

## Assumptions

- ADR-0112 D1 applies here: an index table over a document corpus is generated from that corpus or does not exist, so a hand-maintained intent index is not an option. This is an accepted decision rather than an open bet, and it constrains the shape rather than needing a test.
- An intent that records no parent and no altitude is a **permanent first-class category**, not a backlog to burn down, so the view must represent unclassified honestly rather than compensate for its absence. This is structural, not a property of today's corpus: ADR-0033 D2 keeps `Level` an open field that no lint closes, and `decompose-intent`'s retroactive-parent affordance is an offer that never blocks, so an unparented intent stays valid indefinitely. On 2026-10-07 the category has 0 members because every live intent carries `Level:`, while 100 of 168 still record no parent. Low parent coverage is not a target to drive to zero. **Untested** is whether a view is useful while that many intents have no parent.
- A related-intent edge can be recorded on the artifact without turning it into a dependency edge that a reconciler reads as blocking. **Survived 2026-10-07:** no shipped reader treats an intent-valued header field as blocking by default; see the De-risk record.
- The typed reference grammar exists before feature intents become graph nodes. **This is a hard dependency on** `intent-identity-and-registration`, not an assumption this child can test on its own. It shipped, and the 2026-10-07 De-risk record shows it is sufficient under field-scoped resolution.
- **Riskiest assumption:** admitting feature intents as nodes leaves every navigator edge resolvable to exactly one node by field-scoped resolution. **Survived 2026-10-07.**
- A generated view can expose altitude and status without restating either, so status keeps the single home `docs/product/AGENTS.md` gives it. **Untested.**
- Intent status and hierarchy prompts can activate `navigate-intents` without diverting decision navigation, authoring, or mutation requests. **Untested.**

The assumptions still marked **Untested** — usefulness while 100 of 168 intents have no parent, status echoed without restating it, and activation routing — are construction-time obligations for the decomposed contract or the validation hook, not open bets on the structure.

## De-risk record — 2026-10-07

- **Level kind:** feature, but the dominant unknown is architectural rather than desirability. The bet is not "do readers want an intent graph" — RFC-0105 D1 already committed the public `navigate-intents` skill — but whether the graph can exist once feature intents become nodes. Human usefulness stays unvalidated and is carried as a validation hook below.
- **Reversibility triage:** one-way door for the edge-resolution rule, two-way for the view. The navigator persists nothing, so a wrong view is cheap to discard. The rule for turning a header pointer into an edge is different: workspace retirement under RFC-0105 D3 and [FEAT-0034](FEAT-0034-workspace-registry-retirement.md) will replace read-only orientation with it, so its semantics become a contract other work depends on.
- **Prototype-approach:** `validate-first`. A read-only, uncommitted corpus walk can fail the bet before any implementation is chosen.

### Why this assumption and not the cost claim

Two candidates had the most risk and least evidence. The evidence on hand before the probe separated them.

- **Derive-on-demand cost.** The `navigate-decisions` precedent shipped 2026-10-05 derives its graph on demand and persists no index, so settled decision 1 holds in practice. A cost overrun would also not kill this bet: settled decision 1 rests on four independently sufficient reasons, and cost is only one of them. Cost is therefore measured below as an owner finding, not as the test target.
- **Collision activation.** Cross-type slug collisions stand at **18** on `origin/main` at `1fe67e8f4` (5 intent/brief, 13 intent/spec), up from 6 when this intent was written on 2026-09-18 and 12 on 2026-10-03. They are not drift. In 12 of the 13 intent/spec collisions, the spec's `Discovery:` points back to the intent of the same slug. Naming a single delivery spec after its intent is the normal convention, so each new one-spec decomposition that follows it adds one. Under the shipped grammar a bare-slug pointer that suffix-matches two nodes refuses as `ambiguous`. If the navigator resolves pointers that way, admitting feature intents as nodes turns each collision into a refusal, and a whole-operation-failure rule like `navigate-decisions`' would turn one refusal into a dead graph.

### Riskiest assumption

Admitting every intent, including feature intents, as a graph node leaves every edge the navigator reads resolvable to exactly one node by its field's admitted target type and the shipped typed grammar alone, without the global bare-slug suffix match.

What would have to be true: each header field the navigator reads must admit a known target type; a typed or path-form value must name one node; a bare slug must be unique within the field's target type; that within-type uniqueness must be enforced by a shipped gate, not by luck; and the delivery mapping consumed from FEAT-0003's resolver must not itself refuse because of a cross-type collision.

### Kill condition, predeclared

There is no traffic for an internal repository contract, so the bar is a count over the real corpus. It was written into this intent before the probe below was run.

**Kill the bet as framed if, over `origin/main` at `1fe67e8f4` with all intents admitted as nodes, any one of the following holds. One case is enough.**

- **K1.** Any navigator edge — an intent's or brief's `Parent intent:`, a spec's `Brief:`, or a spec's intent-valued `Discovery:` — cannot be resolved to exactly one node using only its field's admitted target type, its typed prefix or path, and within-type slug lookup.
- **K2.** Intent slug uniqueness or brief slug uniqueness is not enforced by a shipped gate, so field-scoped resolution would be safe today only by accident.
- **K3.** FEAT-0003's shipped resolver, `intent_delivery_relations.resolve_repository`, emits any `delivery-relation-ambiguous` diagnostic over this corpus whose cause is a cross-type collision rather than a within-type one.

Two narrower lines, also set before the probe, cover the open questions. Neither kills the whole bet.

- **Related edge.** Kill the boundary item "how a related-intent edge is recorded" as framed if any shipped reconciler, lint, or closure reader treats an intent-valued header field as blocking or ordering by default, rather than through a named dependency field. Then no new field could be added without a reader taking it as a dependency.
- **Cost, an owner finding only.** If median in-process header derivation over the navigator's full node set exceeds 1 second, record a finding to the owner that settled decision 1's cost reason is false at this scale. Do not edit the decision.

### Prototype

A throwaway, read-only script outside the repository admitted every live intent, brief, and spec as a typed node. It read each preamble and extracted the four navigator edges named in K1. It resolved each edge twice: once scoped to its field's target type, and once by the global bare-slug suffix match that `lint-traceability.py`'s `resolve_endpoint` uses. Uniqueness enforcement (K2) was tested by planting a duplicate intent slug, then a duplicate brief slug, in a scratch copy of the corpus under the OS temporary directory and running the shipped lints against it. K3 ran FEAT-0003's resolver over the real corpus. Nothing in the repository was written.

### Prototype results

The corpus at `1fe67e8f4` holds 168 live intents, 14 intent tombstones, 22 briefs, and 535 specs.

**K1 did not fire.** The four fields yield 166 edges that name a target. All 166 resolve to exactly one node within their field's target type:

- 65 `Parent intent:` values use `capability:` (57) or `intent:` (8).
- 11 `Parent intent:` values use the traceability chain's `outcome:` or `opportunity:` prefix. Each names one live intent whose `Kind:` matches the prefix.
- 55 `Brief:` values use the `brief:` prefix.
- 35 intent-valued `Discovery:` values use a repository path (31) or `intent:` (4).

No edge uses a bare slug. The global suffix match therefore finds **0 ambiguous edges of 166**, even with 18 collisions in the corpus. The collisions are latent and would stay latent under a field-scoped resolver. A further 278 header values are an explicit `none`, which is no edge. Two of those carry prose after `none` (`none — see Placement`, `none — raised directly, not projected from an intent.`), so the parser must read the leading `none` and not require an exact match.

**K2 did not fire, but the gate is not the one this intent assumed.** The gated `intent_corpus_lint.py` reports `clean` with two live intents claiming the slug `decision-navigation`. `lint-traceability.py` refuses the same corpus with exit 1 and `DUPLICATE ID — intent:decision-navigation`, and refuses a duplicate brief slug the same way. `tools/repo/build_gate_chain.py` runs `lint-traceability` as a script step of `build-check`, which runs on every pull request. Within-type uniqueness is therefore enforced, by `build-check` alone.

**K3 did not fire.** `resolve_repository` returns `complete: True` over 254 artifacts with 0 `delivery-relation-ambiguous` diagnostics. Its 10 diagnostics are 8 `delivery-target-missing` and 2 `delivery-projection-mismatch`. Both are legacy mapping gaps FEAT-0003 already classifies, not cross-type collisions.

**Related edge: did not fire.** Header fields on intents that name another intent are `Parent intent:` (68), `Reissued as:` on tombstones (14), `Depends on:` (3), and `Outcome co-owner:` (1). No shipped reader treats an intent-valued header field as blocking by default. Blocking lives only in named fields: `needs` on a `workspace.toml` entry, and `**Depends on:**` on a plan task read by `loop-cohort.py`. The three intent-level `Depends on:` fields are read by no script; each carries a comment saying its enforceable edge is a `needs` entry on the workspace registration.

**Cost: the owner-finding line fired.** FEAT-0003's resolver reads the same intent, brief, and spec headers through the blessed confinement helper. Over 7 runs it took a median of 1.55 s (1.14 s to 4.34 s). A plain header-only read of the 739 files took 0.42 s, and reading every file whole took 0.40 s. The cost is per file opened, not per byte read. The 245-file `navigate-decisions` corpus shows the same shape: in its profile, 0.32 s of 0.50 s is confined `open` calls and 0.04 s is reads.

**Unclassified intents.** Every live intent now carries `Level:`, so the category "records neither parent nor altitude" has **0 members**. 100 of 168 record no parent: 82 features, 16 capabilities, 1 product strategy, and 1 product vision. 90 of those omit the field, and 10 write `none`. The Struggling moment's figures (130 files, 119 with `Level:`, 9 with `Parent intent:`) describe the corpus on 2026-09-18, not today.

### Verdict — survived

No kill line was crossed. Admitting feature intents as nodes does not activate the 18 collisions, provided the navigator resolves each pointer within its field's target type. The navigator must not resolve them with the global bare-slug suffix match. That resolution rule is the one-way door, and it is now a constraint on decomposition rather than an open bet.

What travels into `decompose-intent`:

- **C1 — Field-scoped resolution.** Resolve `Parent intent:`, `Brief:`, and intent-valued `Discovery:` within their admitted target types, accepting the reference grammar's `intent:`, `capability:`, `outcome:`, and `opportunity:` prefixes, `brief:` for briefs, and repository paths. Refuse a bare slug that is ambiguous within its type, never across types. Consume FEAT-0003's resolver for delivery mappings; do not re-derive them.
- **C2 — Refusal scope must be chosen explicitly.** `navigate-decisions` fails the whole operation on one malformed record. Whether one refused edge fails the intent graph, or is shown as a refused edge, is a contract choice. Today's corpus has no refused edge, so either rule passes on current data. The owner chose on 2026-10-07; see Delivery decisions under Decomposition.
- **C3 — A related edge needs its own field name.** It must be distinct from `Depends on:` and from any name a reconciler reads as blocking. The owner chose `Related intents:` on 2026-10-07; see Delivery decisions under Decomposition.
- **C4 — `Kind:` is a second classifier.** 12 live intents carry `Kind: outcome` or `Kind: opportunity` beside `Level:`, and 11 parent pointers use those prefixes. The view must show both without collapsing one into the other.

Two more were decided by the owner on 2026-10-07, after the verdict:

- **C5 — Navigation needs no `agentbundle`.** Both surfaces run from the skill's own bundled script, with the Python standard library and a co-located projection of the file-safety helper, as `navigate-decisions` does. Installing or invoking the `agentbundle` CLI is never required to navigate the intent graph, and no separate navigator CLI is added.
- **C6 — The query has a plain-text tree format for people.** Beside its JSON output, the query can print a subtree as indented plain text in a terminal. Each line shows the intent's identity, altitude, and echoed status. It is a format of the bounded query, not a third surface: same derivation, same bounds, read-only. A full-screen interactive terminal browser is out of scope; the HTML view covers whole-graph browsing.

### Findings for the owner

These challenge settled design decisions or sit with another intent, so they are recorded here and not acted on.

- **Settled decision 1's cost reason is false at today's scale; the decision still stands.** The reason says header-only derivation is "roughly an order of magnitude cheaper" than a whole-file walk and "well under a second". Measured, header-only and whole-file reads cost the same, and confined derivation takes about 1.5 s. The other three reasons each suffice alone. A 1–4 s agent-invoked query also fits ADR-0007's agent-invoked posture.
- **Settled decision 2's falsifier is weaker than written.** It says the cost model inverts if graph metadata moves into prose. At this scale cost does not depend on bytes read, so that is not the failure mode. The guardrail still stands on its other effect: the query returns no artifact bodies.
- **Slug uniqueness is gated only by `build-check`.** The docs workflow's corpus lint misses a duplicate intent slug. C1 relies on that uniqueness, so this is input for the spec, or for whoever owns `intent_corpus_lint.py`.
- **Dependency edges lose their enforceable home when `workspace.toml` retires.** Three intent `Depends on:` fields defer to `needs` entries on the workspace registration. That is [FEAT-0034](FEAT-0034-workspace-registry-retirement.md)'s state-disposition gate under RFC-0105 D3, not this intent's.

### Validation hook

Desk evidence settles the structural bet. It does not show that people find the view useful.

```
validation_hook:
  assumption: A reader can tell what exists under a capability, where each child stands, and which features have no parent, faster and more accurately with navigate-intents than with repository search, while 100 of 168 intents record no parent.
  kill_condition: Proceed only if at least 4 of 6 representative maintainer or agent sessions answer both "what sits under CAP-0001 and in what state?" and "which feature intents have no parent?" correctly and faster with the navigator than with search, and none mistakes a parentless feature for an unclassified one.
  activity: to-validate — a task-based comparison over the first navigator build, run by a human or scaffolded by plan-validation. Not run.
```

## Decomposition

**Re-cut, 2026-10-08, eugenelim (owner): one coordinating brief, [`intent-navigation-delivery`](../briefs/intent-navigation-delivery.md).** The single-spec cut below was drafted as `docs/specs/intent-navigation/` and ran four spec-mode shaping rounds without converging. The scope had grown to 69 acceptance criteria, and its four parts each had to reconcile with a different shipped component: the delivery resolver, `close-work`'s closure index, the intent-field lint, and the export's browser safety rules. Its Spec map owns the slice set. The text from here to § Delivery contract is the superseded single-spec cut, kept as provenance. Its delivery decisions and both Amendments still apply to the slices.

**One slice, a spec proposed as `docs/specs/intent-navigation/`**, materialized directly as a spec rather than through a delivery brief. The slice is the public read-only `navigate-intents` skill: one header-only derivation of the intent graph, a bounded query with JSON and plain-text tree output, and an on-demand single-file HTML view. That is one independently shippable repository feature, and `navigate-decisions` shipped the same shape as one spec, [`decision-navigation`](../../specs/decision-navigation/spec.md).

The proposed slug follows `decision-navigation`. It also differs from this intent's slug, so it adds no 19th cross-type collision. `new-spec` owns the final name.

### Why one and not several

Four cuts were considered and dropped:

- **Query first, view second, under a brief.** Rejected because both surfaces are settled to be two outputs of one derivation (settled decision 3). Two specs would each restate the derivation and edge-resolution contract, C1, which is the one-way door this de-risk found. The query does ship value alone, and the workspace retirement needs only the query. So the spec's plan should land the query, with its tree output and activation evaluations, before the view. That is an ordering inside one spec, not a second spec.
- **Derivation first, surfaces second.** Rejected as a layer cut. A derivation that no query or view exposes changes nothing for a reader.
- **Related-edge field as its own slice.** Not cut. No intent carries a related edge today, so a navigator could ship without one. But this intent's Boundary owns how the edge is recorded and read, and C3 has to be settled where the reader is built. Splitting it out would leave a field contract with no reader, or a reader for a field nobody can write.
- **Absorbing `close-work`'s parent-edge inversion as a later slice.** Rejected by the owner on 2026-10-07: it converges in this spec. `closure_index.py` still builds its own descendant set from `Parent intent:`. The Boundary's 2026-09-24 inbound note asks that it be absorbed rather than left standing, and a later slice would ship the navigator with the two implementations it was meant to prevent.

No ranking step applies because there is one delivery unit. No tracker projection is added; the Projection section stays unselected because no target is configured.

### Delivery contract

This shaping handoff is retained as provenance. The [delivery spec](../../specs/intent-navigation/spec.md) owns the behavioral contract, and its [plan](../../specs/intent-navigation/plan.md) owns construction and verification; this section is no longer delivery authority. Where the two differ, the spec governs.

**Amendment, 2026-10-07, eugenelim (owner).** The success signal that `close-work`'s "closure verdicts over the corpus do not change" is replaced. Verdicts may change only for two causes, both defects found while authoring the first spec draft: the old ancestor walk skipped every parent written with `capability:`, `outcome:`, or `opportunity:` (68 of 76 typed parents on 2026-10-07), and its slug lookup did not exclude tombstones. A related clarification of delivery decision 3: an ambiguity within one type cannot reach an edge, because a duplicate slug within a type already fails the whole operation as a corpus-integrity fault.

**Amendment, 2026-10-08, eugenelim (owner).** The navigator must find all outstanding work so that `workspace.toml` can retire. The delivery spec therefore adds an outstanding-work view: every non-terminal intent, brief, and spec, placed under its parent intent, refusing rather than returning a partial list. Facts the headers cannot supply, which are captured items with no artifact, `needs` edges, and queue order, stay [FEAT-0034](FEAT-0034-workspace-registry-retirement.md)'s to dispose of.

**Amendment, 2026-10-08, repository owner: intent dependency display.** The coordinating brief gains a proposed slice for read-only intent dependency graphs from `Depends on:` preamble pointers under RFC-0106 D3. This extends the navigation boundary to displaying recorded dependencies. FEAT-0034 retains dependency enforcement and migration of workspace `needs` entries. The brief owns the proposed cut and its review; the slice's spec owns any navigator and export contract amendments. Existing slices 5 and 7 keep their scope.

**Amendment, 2026-10-08, eugenelim (owner): repair over prevention.** Interim states in this repository can be repaired, provided the skills that create intents, briefs, and specs write well-formed graph relationships from now on. Three consequences follow:
- Delivery decision 2 no longer requires `close-work` to converge in the same slice or release as the navigator. A later slice may converge it, and the repository may carry both parent-edge implementations until then.
- The brief gains a slice that makes the authoring skills write typed references and refuses an untyped one in any new or changed artifact. The legacy pointers it would refuse are repaired before feature work, under the next consequence.
- Corpus and reader repairs land before feature work. Correcting how `closure_terminality` reads an annotated status word is one of them, and the `close-work` verdict changes it causes are accepted on the same ground.

- **Outcome:** A person or an agent can learn what intents exist and how they relate without opening intent files one by one. For each intent they see its altitude, `Kind:`, echoed status, parent, children, related edges, and the delivery mapping FEAT-0003 supplies. An agent gets this through a bounded JSON query. A person gets it as an indented plain-text tree in a terminal, or as one self-contained HTML file opened offline. The graph is derived from preamble headers each time and never written into the repository.
- **Success signals:**
  - Over the corpus at decomposition (168 live intents, 22 briefs, 535 specs), every edge that names a target resolves to exactly one node by field-scoped resolution. At de-risk that was all 166, with 0 ambiguous.
  - A planted bare-slug collision across types never refuses. A planted ambiguity within one type refuses with a named state.
  - Intents with no parent, 100 of 168 at de-risk, are shown as parentless at their recorded altitude, never given an inferred one.
  - Status is echoed from the artifact on every call and never cached or restated.
  - Activation evaluations show intent status and hierarchy prompts reach `navigate-intents`, while decision navigation, intent authoring, and mutation requests do not.
  - Running the skill needs neither `agentbundle` nor `workspace.toml`.
  - `close-work`'s closure walk obtains its `Parent intent:` descendants from the shared derivation. No second parent-edge inversion remains on its active path, and its closure verdicts over the corpus do not change.
- **Boundaries:**
  - Read preamble fields only, through the blessed confinement helper or a co-located projection of it.
  - Resolve `Parent intent:`, `Brief:`, and intent-valued `Discovery:` within each field's admitted target type (C1). Admit the reference grammar's `intent:`, `capability:`, `outcome:`, and `opportunity:` prefixes for intent targets, `brief:` for brief targets, and repository paths. Read a leading `none` as no edge, even when prose follows it.
  - Consume `intent_delivery_relations.resolve_repository` for every brief and spec mapping. Display it; never re-derive or infer it.
  - Show `Kind:` beside `Level:` without collapsing one into the other (C4).
  - Ship as a skill with its own bundled standard-library script and no separate CLI (C5).
  - Offer the plain-text tree as a format of the bounded query (C6).
  - Write the HTML view only to a scratch location outside the repository, under RFC-0105 D4's portable-view constraints.
  - Never reuse the `_state/traceability.json` sidecar filename or its `schema_version` namespace; reuse its node and edge vocabulary.
- **Non-goals:**
  - Persisting a graph or index.
  - Reading artifact bodies to build the graph.
  - Reading `workspace.toml` for anything.
  - Mutating any intent, brief, spec, or coordination record.
  - Owning or inferring the intent-to-delivery mapping.
  - Changing intent identity or the reference grammar.
  - Tracker projection.
  - A full-screen interactive terminal browser.
  - Sharing a renderer with `navigate-decisions`.
  - Choosing a fixed size threshold, layout, or interaction model at this level; RFC-0105 D5 leaves those to design.
  - Migrating parentless intents or burning down the parentless count.
- **Dependencies:**
  - FEAT-0001's shipped typed reference grammar.
  - FEAT-0003's shipped resolver, as the source of delivery mappings.
  - RFC-0105 D1–D5 as the governing record.
  - `build-check`'s `lint-traceability` step, which today is the only gate refusing a duplicate intent or brief slug. C1's safety depends on it.
  - No ordering edge to [FEAT-0034](FEAT-0034-workspace-registry-retirement.md). That child consumes this navigator to replace read-only orientation and owns the workspace retirement itself.
- **Design context:**
  - The 2026-10-07 de-risk measurements are the baseline: 18 cross-type collisions, 0 bare-slug pointers, and 12 live intents carrying `Kind:`.
  - Confined derivation over the full node set took 1.55 s median (1.14–4.34 s). Header-only and whole-file reads cost the same, because the cost is per file opened. The spec should set its latency budget against that, not against "well under a second".
  - The view's design route stays as the Boundary names it: `information-architecture`'s analytical genre, `interaction-design`, then `frontend-engineering`.
- **Delivery decisions, owner, 2026-10-07:**
  1. **Pack: `core`.** Intents, `work-intake`, and FEAT-0003's resolver live there. `navigate-decisions` sits in `governance-extras` only because ADRs and RFCs do.
  2. **`close-work` converges in this spec.** Its `Parent intent:` descendant set moves onto the shared derivation. Cross-skill imports are banned, so convergence means a parity-checked projection of the derivation, as FEAT-0003's resolver already has in `close-work/scripts/`.
  3. **Refusal scope (C2): split by fault.** A corpus-integrity fault fails the whole operation, as in `navigate-decisions`: a duplicate identity within a type, an unsafe or unreadable file, or a preamble that cannot be parsed. Node identity cannot be trusted then. An edge fault returns the graph with that edge shown as refused under a named state, never guessed: a dangling target, an ambiguity within one type, or an out-of-type prefix. One bad pointer in one intent should not blind orientation for the whole repository. This also matches FEAT-0003's resolver, which reports per-relation diagnostics beside a `complete` flag.
  4. **Related-edge field (C3): an optional preamble field `Related intents:`.** Its value is a comma-separated list of typed references in FEAT-0001's grammar, such as `intent:<slug>` or `capability:<slug>`, with no bare slugs and no paths, so no collision can reach it. It is written on one side only, and the navigator shows it from both ends, so relating two intents edits one file. `intent_corpus_lint.py` checks that each target is a live intent and not the intent itself, as it already checks `Superseded by:`. The `frame-intent` template lists the field. No reconciler reads it, and a test pins that. The name avoids the ADR and RFC `Related:` field, which RFC-0105 D1 calls free-form and unchecked, and stays distinct from `Depends on:`.
- **Validation hook:** carried from the De-risk record: a task-based comparison over the first build, at least 4 of 6 sessions. It has not been run, and the spec does not run it.
- **Provenance:** This intent, de-risked and decomposed 2026-10-07. The supporting records:
  - [RFC-0105](../../rfc/0105-artifact-derived-navigation-and-workspace-retirement.md)
  - [ADR-0112](../../adr/0112-index-tables-are-generated-or-absent.md) D1
  - [ADR-0007](../../adr/0007-ship-doc-drift-lint-as-work-loop-skill-script.md)
  - The shipped [`decision-navigation`](../../specs/decision-navigation/spec.md) precedent
  - The shipped [`intent-delivery-traceability`](../../specs/intent-delivery-traceability/spec.md) contract

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.

RFC-0105 D1, D3, D4, and D5 narrowed the public skill, workspace-independence, portable-content, and design-authority boundaries on 2026-10-02. It did not waive this feature's de-risk, dependency, or decomposition gates.
