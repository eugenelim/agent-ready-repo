# Graph-powered SDLC — applied survey

> Discipline: applied (practitioner-pattern survey, agent-run desk research)

- **Run date:** 2026-09-18
- **Repository evidence observed at:** `d53759325`. In-repository citations are relative paths and resolve against the working tree, not that revision.
- **Shapes:** [STRAT-0001 Graph-powered SDLC](../intents/STRAT-0001-graph-powered-sdlc.md), and through it [CAP-0001 Repository work graph](../intents/CAP-0001-repository-work-graph.md) and [CAP-0002 Decision graph](../intents/CAP-0002-decision-graph.md).
- **Two passes:** Part 1 covers enterprise ontology and lineage platforms. Part 2 covers delivery-side graphs — decision graphs for coding agents, code and repository graphs, traceability in regulated engineering, monorepo affected-set computation, and header-derived graphs. Both were agent-run on 2026-09-18.

## Question

Not *whether* modelling work as a graph is worth it. The delivery-tracker market settles that: organisations already pay for hierarchical work models and cross-level orchestration, and every major tracker ships one. The open questions are narrower and both are mechanism questions.

1. **Which unlocks survive the constraints?** This repository has no server, no daemon, no hosted runtime, and no guaranteed adopter runtime beyond Python. Which capabilities that graph platforms demonstrate actually transfer to a derived, file-based graph, and which are inseparable from infrastructure we have ruled out?
2. **Which edges stay true?** A graph is only as good as its edge set. What predicts whether an edge type stays accurate over years, versus rotting into confident nonsense?

## Headline

Across every platform surveyed, the graph is never itself the unlock. Three separable things are, and they have very different transferability:

| | What it is | Transfers here? |
| --- | --- | --- |
| **Reverse traversal** | Given a node, enumerate everything affected | **Yes** — the only unlock evidenced in every domain surveyed |
| **A write path** | The graph is how you change the world, so every effect is typed, validated and logged | **No** — needs a transactional runtime |
| **A grounding boundary** | An agent gets a typed bounded interface instead of a corpus | **Partly**, and the evidence is mixed-to-negative |

And one predictor dominates the durability question: **an edge survives when producing it is a byproduct of work someone had to do anyway, and dies when it is a separate act of documentation.** Every success below derives edges from something already required. Every failure asks a human to author an edge whose benefit accrues to someone else, later.

## Prior-art matrix

| System | Node / edge | Edges declared or derived | Persisted? | The unlock | What it costs |
| --- | --- | --- | --- | --- | --- |
| Palantir Foundry / AIP | Object types, link types; action types as the kinetic half | Hand-declared by mapping pipeline output onto object types | Materialised in a dedicated object store | Operational write-back: an edit validates against rules, propagates to source systems **attributed to the named human**, and lands in an immutable action log. Scenario forking. Agent tools *are* action types, so humans and agents share one permission and audit model | Continuous manual modelling; forward-deployed engineers are structural. NHS FDP whole-life cost revised £330m → **£1.1bn** against £808m forecast benefit |
| Databricks Unity Catalog | Tables, columns, notebooks, jobs, dashboards | **Derived automatically** by parsing Spark execution plans as queries run | System tables, 1-year window; UI indefinitely but only post-2024-09-01 | Column-level impact analysis with `job_id`, `created_by`, `statement_id` on every row — "this column is about to be dropped, list every downstream dashboard and its owner" | Coverage is **perfect inside the runtime and zero outside it**. The manual fallback is capped, not written to system tables, and has no freshness guarantee |
| Backstage software catalog | Component, System, Domain, API, Group | **Generated from declared spec fields** — `spec.owner` → `ownedBy`/`ownerOf` | Catalog is explicitly "a caching mechanism" over YAML in repos | Spotify reports new-engineer time-to-10th-merged-PR **60 days → under 20** across 280 teams | ~10% adoption outside Spotify; documented catalog rot — *"you learn about it in a post-mortem"*; 6–12 months and a dedicated team |
| DataHub / Atlan | URN entities, versioned aspects | Producers **push** at write time; LinkedIn abandoned crawler-pull as "a nightmare" | Polyglot: MySQL + Elasticsearch + graph index | Pre-merge impact analysis on the dbt PR; GDPR deletion propagation across every dataset a subject ID reached | DataHub Lite (single-file DuckDB, no server) keeps entities and search but **explicitly loses graph traversal** — the vendor's own split tells you where the server is load-bearing |
| Bazel / Nx / Turborepo / Buck2 | Build targets | **Declared** deps; a missing dep is a build error, never a silent miss | Files define the graph; daemons are caches | `rdeps` gives an exact affected set. 383 projects, 102,232 experiments, **4.22–4.71× median** incremental speedup | BUILD-file maintenance is the recurring complaint; 31% of adopters never invoke it in CI |
| CodeQL | AST, dataflow, call graph | Derived from source | Database built per analysis | Transitive closure and joins — taint source-to-sink across files and aliases. No composition of regexes expresses this | Heavyweight; but the unlock is the *relational model*, not the persistence |
| Requirements traceability | Requirement ↔ test | Hand-authored | Varies | Change-impact analysis, the field's dominant use case | **No rigorous ROI study exists** — the field says so itself. Survives only where an external regime mandates it |
| GUAC | SBOM, attestation, CVE | Derived from artifacts the build already emits | Yes | Reachability over a narrow, well-typed query class | The encouraging counter-case: narrow and typed works |

## Findings

### Finding 1 — the daemon is latency, not correctness [high]

Bazel's server, Nx's daemon and Buck2's `buckd` are optimisations over a graph the files alone define; Nx ships `NX_DAEMON=false` and Turborepo needs none at all. Correctness never depends on the daemon; interactive speed at hundred-thousand-target scale does.

**So what:** this repository's derivation runs in well under a second over ~600 nodes. `CAP-0001`'s no-persistence decision is externally corroborated and can stop being hedged.

### Finding 2 — coverage is binary at the observer boundary [high]

Unity Catalog's lineage is perfect for work executed on its compute and absent for everything else, with a manual fallback that is capped, unrefreshed and trusted anyway. There is no gradual middle.

**So what:** our observer is the shaping skill that writes the header. Inside that boundary coverage is near-total and free; outside it — a hand-edited header, a record predating the skill, an adopter who installs the packs and never runs the loop — the graph **looks populated and is wrong**. `CAP-0001`'s assumption that such an adopter "is not harmed" is the first thing to test, because the evidence says the out-of-boundary case is not neutral.

### Finding 3 — the closest structural analogue already exists, and half of it rots [moderate]

Backstage is this design minus the server: entities declared in files inside repositories, relations generated from spec fields, catalog as a cache. Its orientation result is the same outcome `STRAT-0001` claims. Its failure is equally instructive: co-locating the record with the code fixes discoverability and does **nothing** for rot.

Evidence caveat: the loudest Backstage cost figures come from Port, Cortex and Riftmap, all direct competitors. The Spotify self-report and the Earthly critique are the two worth relying on.

### Finding 4 — the repository is already running this experiment, and it has already returned a result [high, in-repo]

Supersession edges are gate-checked by ADR-S008/S009/S010: **46, clean**. `Related` edges have a parser and no rule: **444, unvalidated**, sometimes naming no record at all. Ten to one. Separately, 9 of 130 intents carry a `Parent intent`.

**So what:** traceability decay is reproducing here *before the graph exists*, and it split exactly along the gated/ungated line the literature predicts. `CAP-0002` already carries `Related` on the node as unresolved text rather than as an edge; that is the right call and the local evidence is the reason.

### Finding 5 — agent grounding is the weakest-evidenced opportunity, not the strongest [moderate]

Microsoft's GraphRAG paper scopes its claim to global multi-hop sensemaking. A February 2026 evaluation — *UnWeaving the knots of GraphRAG — turns out VectorRAG is almost enough* — reports that **plain VectorRAG beats standard GraphRAG** and nearly matches SOTA graph approaches for a fraction of the cost, arguing graph indices carry orders-of-magnitude complexity. Verified against the primary source on 2026-09-18.

**So what:** the graph's value here rests on orchestration and traversal, not on retrieval augmentation. Do not lead with "agents read the graph instead of the corpus", and measure what sessions actually ask before building for it.

### Finding 6 — four properties separate the successes [moderate]

1. The edge is a **byproduct** — Databricks parses a plan it already built; Bazel reads a dep the compiler required; Backstage generates `ownedBy` from an owner the deploy pipeline needed.
2. **Something fails** when the edge is missing — build error, or no certification. The only mechanism found that keeps a link set honest over years.
3. The query class is **narrow, typed and compositional** — reverse dependency, taint reachability, supersession lineage. Not "explain this".
4. The answer arrives **where the work happens** — a PR check, a diff annotation, a CI step. A graph you must go and visit is a catalogue, and catalogues go unvisited.

## What transfers, and what does not

**Transfers:** derivation from declared header fields with reciprocal edges generated rather than authored; no daemon; reverse traversal as the primary capability; making a missing edge fail something; narrow typed queries over open-ended sensemaking.

**Does not transfer, and should be named as out of reach rather than degraded:** write-back actions with atomic multi-system effects and an immutable action log; runtime-evaluated permissions; scenario forking; push notification to consumers on upstream change; any always-current or incrementally-maintained index. The degraded local version of each is precisely Unity Catalog's manual external lineage — capped, stale, and trusted anyway.

## Known-unknowns

- **Is the out-of-boundary adopter harmed?** Finding 2 says a partially-populated graph is worse than an absent one. Unresolved for the case where an adopter installs the packs and never runs the shaping loop. Would be closed by: deriving the graph over an adopter-shaped corpus with headers written by hand and measuring what fraction of edges resolve.
- **Does a forcing function survive contact with authoring?** Finding 6's second property is the strongest durability mechanism found, but a gate that fires on the common path gets disabled. Would be closed by: instrumenting how often a dangling-edge gate would have fired over the last quarter of real commits.
- **Which query class do sessions actually ask?** The whole opportunity ranking assumes traversal questions dominate. Would be closed by: sampling real session transcripts and classifying questions as single-fact lookup versus multi-hop traversal.
- **No published evaluation of a repository-artifact graph exists** for any of these unlocks. Every transferable finding here is an analogy from an adjacent domain, not a measurement of this one.

## References

**Primary, high confidence.** Palantir docs — [Ontology overview](https://www.palantir.com/docs/foundry/ontology/overview), [Why create an Ontology?](https://www.palantir.com/docs/foundry/ontology/why-ontology), [Action types](https://www.palantir.com/docs/foundry/action-types/overview), [action log](https://www.palantir.com/docs/foundry/action-types/action-log); [FY2025 10-K](https://investors.palantir.com/files/2025%20FY%20PLTR%2010-K.pdf). Databricks — [Lineage in Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage), [lineage system tables](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/lineage), [external lineage](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/external-lineage). Backstage — [Creating the catalog graph](https://backstage.io/docs/features/software-catalog/creating-the-catalog-graph/), [Well-known relations](https://backstage.io/docs/features/software-catalog/well-known-relations/), [Measuring Backstage success at Spotify](https://backstage.spotify.com/discover/blog/measuring-backstage-success-at-spotify/). DataHub — [metadata model](https://docs.datahub.com/docs/metadata-modeling/metadata-model), [impact analysis](https://docs.datahub.com/docs/act-on-metadata/impact-analysis), [DataHub Lite](https://docs.datahub.com/docs/datahub_lite). Build graphs — [Bazel query guide](https://bazel.build/query/guide), [arXiv:2405.00796](https://arxiv.org/abs/2405.00796), [Nx daemon](https://nx.dev/docs/concepts/nx-daemon), [Turborepo graph](https://turborepo.dev/docs/core-concepts/package-and-task-graph). Prior art — [Nygard on ADRs](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions), [When Traceability Goes Awry (arXiv:2206.04462)](https://arxiv.org/abs/2206.04462), [Grand Challenges of Traceability (arXiv:1710.03129)](https://arxiv.org/abs/1710.03129), [GraphRAG (arXiv:2404.16130)](https://arxiv.org/abs/2404.16130), [UnWeaving the knots of GraphRAG (arXiv:2603.29875)](https://arxiv.org/abs/2603.29875) — verified against the primary source, [GUAC](https://openssf.org/projects/guac/).

**Secondary, medium confidence.** [Thoughtworks: why ontologies matter, why they fail](https://www.thoughtworks.com/en-us/insights/blog/data-strategy/why-ontologies-matter-fail-build-anyway); [Cagle: why knowledge graph projects fail](https://ontologist.substack.com/p/why-knowledge-graph-projects-fail); [Earthly: Backstage is at peak hype](https://earthly.dev/blog/backstage-is-at-peak-hype/); [NHS FDP business case under scrutiny](https://www.computing.co.uk/news/2026/government/nhs-palantir-platform-s-business-case-under-scrutiny-as-costs-rise-and-benefits-fall); [traceability mapping study (arXiv:2108.02133)](https://arxiv.org/abs/2108.02133).

**Flagged as motivated.** Backstage FTE and upgrade-pain figures originate with Port, Cortex and Riftmap, all competitors. Unity Catalog limitation framing originates with Atlan and Decube, also competitors. Nx's percentage claims are vendor marketing. Enterprise knowledge-graph adoption figures are survey-grade and vendor-adjacent.

---

# Part 2 — delivery-side graphs

One framing result governs this half: the graphs that survive are those where **either a machine derives the edges from something it can parse, or a small editorial authority enforces them at publication time.** Graphs depending on voluntary, distributed, unenforced human upkeep decay everywhere they have been studied.

## Finding 7 — the strongest number in either pass needs no graph at all [high]

**ContextCov** (arXiv 2603.00822, Feb–May 2026) compiles constraints out of `AGENTS.md`-style files into AST queries, shell shims and architectural validators, intercepts agent actions, and returns reproducible violation traces. On SWE-bench Lite — 12 repositories, 300 tasks — it reports **88.3% constraint compliance against 67.0% prompt-only and 50.3% LLM-reflection, at 3.4× lower feedback cost**, with functional correctness maintained.

Three things follow, and they cut in different directions.

- **Passive instruction text is honoured about two-thirds of the time.** The compliance problem is real and measured.
- **An LLM asked to self-check does worse than plain instructions.** Deterministic interception is the mechanism that works, not reflection.
- **ContextCov achieves this with zero graph structure.** No parentage, no altitude, no supersession.

Alongside it: **Agentless** (arXiv 2407.01489) reports **32.00% on SWE-bench-Lite at $0.70/instance** with no graph, no index and no agentic loop, beating several graph-augmented systems on accuracy and cost simultaneously.

**So what:** the compliance gap justifies enforcement, not a hierarchy. Any claim that our four altitudes improve agent behaviour is unsupported by the best available evidence, and the honest framing is that the hierarchy is human-facing.

## Finding 8 — the decision-graph category is real, young, and entirely unevidenced [high]

Three shapes have emerged. A hook-based tool installs `PreToolUse` interception into Claude Code and Codex, scoping decisions to code by **path glob plus dependency match**, returning PASS/WARN/FAIL with FAIL exiting 2, and deliberately exposing an MCP surface with **no accept, supersede or bypass authority** — the agent may propose and query; only a human may change what governs. A second, doctrinal, ranks **deterministic signals above semantic ones** (path, service, language, dependency, ownership, lifecycle status first; task text only as discovery afterwards) and surfaces conflicts rather than resolving them. A third is service-backed with seven node types and six edge types.

**No published outcome evidence exists for any of them.** One publishes a methodology with pre-registered thresholds and 324 planned runs, and states results publish later. Adoption figures are undisclosed everywhere.

**So what:** treat the category as a design source, not as evidence. Its best design move — agents propose, humans decide — is directly applicable and costs nothing to adopt.

## Finding 9 — our design has a stdlib-only precedent that already works [high]

**adr-kit** is stdlib Python 3.10+, no build step, no service, no API key on any default path. Frontmatter carries `id`, `status`, `binding`, `gate`, `supersedes`, `superseded_by`. It generates two deterministic index views from those headers, regenerable and `--check`-verifiable, prints inbound and outbound edges per reference kind, and **flags dangling links**. Enforcement is a pre-commit hook with file:line citations.

Alongside it, the header-derived graphs that have survived longest: **IETF `Obsoletes`/`Updates`** (verifiable live — RFC 2616's info page states it is obsoleted by RFC 7230–7235) and **PEP `Superseded-By`/`Replaces`**, whose cross-reference index is a Sphinx build-time render, not a database.

**So what:** every sparsity-tolerant unlock we want is reachable with stdlib Python and no daemon, and the precedents are decades old.

## Finding 10 — ADRs are the closest precedent and they show a pilot-then-abandon signature [high]

Buchgeher et al., IEEE Access 2023, mining ADR use on GitHub: adoption is rising, but **~50% of repositories with ADRs contain only 1–5 records, and fewer than 2% sustain more than 25.**

The previous generation explains why. Jansen & Bosch coined "architectural knowledge vaporization" in 2005; Capilla's ten-year retrospective names six barriers — no motivation, inadequate tools, high capture effort, not knowing what to capture, disruption of design flow, no long-term-investment mindset — and records that **dedicated architecture-knowledge-management tool development stopped around 2015**, with industry drifting to bare decision logs. Heavyweight, schema-rich, server-backed repositories lost to lightweight git-native files.

**Why IETF did not decay, and ADRs did:** a small centralized editorial function enforces the metadata at publication time. It is not self-service. **A CI gate is our substitute for the RFC Editor** — and it is the only substitute available.

## Finding 11 — build-graph payoff does not transfer, and this is the most tempting bad analogy available [high]

Affected-target computation pays because of a **conjunction of four properties**, not because it is a graph:

1. **Cheap mechanical derivation** — parse an import statement.
2. **Self-reporting failure** — a wrong edge breaks a build within minutes, on every change, free.
3. **Extreme query frequency** — thousands of times a day, amortizing maintenance.
4. **A fungible cost unit** — compute-minutes, directly comparable to the graph's cost.

A work graph of intents, decisions, specs and delivery has **none of the first three and only weakly the fourth.** There is no import statement for prose; a wrong "affected specs" edge fails nothing and silently mis-notifies a human, removing the feedback loop that makes build-graph errors self-correcting; and it is queried once per change by one person.

Facebook's own conclusion reinforces this: they **rejected static change-impact analysis** as impractical at their scale and language spread, and replaced it with a statistical selector — Predictive Test Selection halves test cost, runs ~1/3 of transitively-dependent tests, and catches >99.9% of regressions.

**So what:** Facebook's 2×, Ekstazi's 32% and the monorepo vendors' 30–70% are **not transferable evidence** for a work graph. The nearest analogue that does earn its keep is CODEOWNERS — narrow ambition, path-glob derivation — and it rots silently with no drift detection.

## Finding 12 — sparsity splits the unlocks cleanly, and half are silently wrong when incomplete [high]

This matters most for us, because the corpus is largely unclassified and will be for a long time.

| Tolerates sparsity — honest at 20% coverage | Requires completeness — silently wrong when sparse |
| --- | --- |
| Governing-decision lookup (per-node; empty is a correct answer) | Impact analysis — returns a **confident, short, wrong** answer |
| Supersession refusal (per-edge) | Coverage and orphan reporting — "no orphans" over 30% coverage reads as assurance |
| Ancestry walk from a classified leaf | Any merge gate on graph-derived completeness |
| Dangling-link detection (useful from the first link) | |
| Negative decisions (purely additive) | |

**So what:** ship the sparsity-tolerant unlocks first, and never render a completeness-requiring query without a denominator. A classified-versus-total count on every impact answer is the difference between a tool and compliance theatre.

## Finding 13 — agent value and human value concentrate in different edges [moderate]

**The agent gets** retrieval it cannot do for itself (it starts every session with nothing; a six-month engineer carries the graph in their head), mechanical interception (an agent can be *stopped* at `PreToolUse`; a person can only be asked), and **negative knowledge** — "we tried this and it failed" is the single most valuable node type for an agent and nearly worthless to a human who already remembers.

**The human gets** rationale as narrative, judgement about whether a decision still applies under conditions that have changed, onboarding orientation, and audit standing.

**So what, sharply:** agent-facing value concentrates almost entirely in **scope** (which decision governs this path) and **supersession** (which record is live). Human-facing value concentrates in **parentage** (the four altitudes) and **rationale**. These are different products sharing a file format. **Parentage buys an agent very little and costs real maintenance.** Rank accordingly, and do not sell the hierarchy as an agent capability.

## Finding 14 — intent-to-code mapping, extracted for organizational use [low evidence, high strategic pull]

Owner-raised on 2026-09-18 and **the least evidenced opportunity in either pass**, recorded because it is where the strategy's organizational value would come from if it lands.

The capability: a durable chain from a shipped change back through spec, feature, capability and strategy to the outcome it serves — and then extracting that upward for organizational consumption, so a portfolio view, an investment question or a compliance answer is derived from delivery reality rather than re-gathered by hand.

What the two passes say about it:

- **The shape exists at the top end.** Palantir's pitch is literally "a digital twin of the organization", and its value is that operations and analysis share one object model. That is this opportunity with a runtime we do not have.
- **The mechanism has a precedent at the bottom end.** Provenance — a merged change citing the record IDs and commit it was reviewed against — is specified in the decision-graph doctrine and is emitted **at the time of the change**. Reconstruction at audit time is the documented failure mode, and it is exactly how requirements traceability became theatre.
- **Nobody has measured it.** No study in either pass links intent-to-code traceability to an organizational outcome. The regulated analogue is mandated rather than chosen, and practitioners who *believe it pays* still do not maintain it, for lack of time, staff and clear ownership.
- **It is completeness-requiring**, which puts it on the wrong side of Finding 12. A portfolio view over a partly-mapped corpus does not read as partial; it reads as the answer.

**So what:** this is the opportunity most worth wanting and least safe to assume. Its precondition is Finding 6's first property — the mapping must be a byproduct of shipping, cited at merge, never reconstructed. If it is ever assembled retrospectively for a report, it has already failed.

## Finding 15 — the scale argument, which neither pass tested and which defeats half the steelman [high, in-repo]

Owner-raised on 2026-09-18, and it reframes the question. Every measured comparison in both passes was run at **one agent**. At that scale the steelman holds: a capable model can read the prose directly, and a second representation is a sync liability.

The argument does not survive scale. At Level 4 of the maturity ladder the vision names — intent-steered, monitored by exception, 1000+ agents — the binding constraint is not agent capability and not retrieval quality. It is **the volume of work the loop itself proposes.** Every session ends by emitting follow-ons, findings, deferred scope, discovered defects and candidate specs. That output compounds, and prose has two properties that make it fail here: reading cost scales linearly with volume, and it supports no traversal, no deduplication and no prioritisation. A backlog nobody can traverse is not a backlog; it is an archive.

**The local evidence is this repository, at roughly one agent.** Measured 2026-09-18: 484 specs, 434 plans, 338 spec notes files, 140 intents, 119 ADRs, 102 RFCs, 45 research documents. Coordination state holds **165 open backlog entries** — 24 of which explicitly cite a review round, a pre-flight or a shaping discovery as their origin — plus **184 entries across the initiative queues**. Alongside that sit the 444 unvalidated `Related` edges from Finding 4.

That is the generated-work problem appearing at single-agent scale, before any multiplication. Two orders of magnitude of agents do not make it two orders of magnitude worse in reading cost alone; they make the corpus one no human reads and no agent can traverse, which is the same end state the ADR and traceability corpora reached for a different reason.

**What this does to the steelman.** It concedes the capability half and defeats the scale half. The steelman's strongest move is that a model can read the prose — true, and it stays true per-artifact at any scale. What it cannot do is answer *across* a corpus that grows faster than anyone reads it: which of these 165 items are the same item, which are superseded by work already shipped, which are downstream of a decision that just changed, and which can be closed without reading them. Those are traversal and set questions, and they are exactly the class Finding 12 marks sparsity-tolerant — per-node and per-edge, honest when incomplete.

**What it does not license.** It is an argument for the graph as a *management* substrate, not for the four altitudes as an agent capability — Finding 13 stands. And it is an argument whose evidence is a projection: no study in either pass measured work-management cost at high agent counts, because no corpus exists at that scale yet. It is the most strategically important claim in this survey and the least externally evidenced, which is a reason to instrument it here rather than to assert it.

**The falsifier:** measure whether generated-work volume in this repository is growing faster than the rate at which items are closed or deduplicated. If open backlog and queue entries are flat or shrinking per unit of delivery, the management problem is not yet real and the graph is early. If they compound, the argument is measured rather than projected.

## The steelman against all of this

Recorded in full because it uses this survey's own evidence and should not be softened.

*A work graph is metadata whose only consumer is a process that could have read the prose directly, and every comparable graph depending on voluntary human upkeep has decayed.* Fewer than 2% of repositories with ADRs sustain more than 25 records. AKM tooling development stopped in 2015. Mandated requirements traceability still fails in the field, and practitioners who believe it pays still do not do it. SBOMs are generated under mandate and, on available evidence, not queried. CODEOWNERS rots silently. Backstage catalogs orphan.

The only graphs that did not decay had **mechanical derivation** or **a centralized editorial gatekeeper**. A four-altitude intent graph has neither: its edges are human assertions about prose, with no import statement to infer from and no execution that falsifies a wrong edge. And the strongest agent-side result available needed no graph at all.

The cost is not the build. It is the permanent tax on every subsequent change: every spec placed, every retirement reciprocated, every gate satisfied or exempted — and every exemption compounds.

**The rebuttal, and its limits.** Two things survive. The compliance gap is real and measured, and some of the residual is plausibly scope-resolution, which needs edges. And supersession is cheap, tolerates sparsity completely, and has a working multi-decade precedent. But both survivors are narrow: they justify **scope and lifecycle attributes on decision records, enforced at a hook and a CI check** — not a four-altitude hierarchy. **If the strategy is sold on the hierarchy, this argument wins. If it is sold on scope-plus-supersession with the hierarchy as a human-facing byproduct, it does not.**

## Consolidated ranking after both passes

Ranked on evidence strength. Note that Finding 15 reorders the *strategic* case without reordering the evidence: the management substrate is the reason to build, while the items below remain the order in which to build it.

1. **Governing-decision injection at the agent's write boundary** — the only unlock with a strong measured number behind its problem statement.
2. **Supersession refusal** — cheapest real capability, sparsity-proof, multi-decade precedent.
3. **Dangling and non-reciprocal edge detection as a CI gate** — our substitute for the RFC Editor, and the only durability mechanism found.
4. **Derive every edge from a field the author already writes** — the property that separates the half of Backstage that works from the half that rots.
5. **Negative decisions** — total agent/human asymmetry; needs a discriminating trigger or it is inert prose.
6. **Generated index projection with `--check`** — precedented by adr-kit and PEP; needs a token budget.
7. **Answer at the point of authoring, not in a view** — catalogues go unvisited.
8. **Intent-to-code mapping for organizational use** — highest strategic pull, lowest evidence, completeness-requiring; only viable as a byproduct of shipping.
9. **Ancestry navigation across the four altitudes** — real human value, no agent evidence; do not sell it as an agent capability.
10. **Affected-spec impact computation** — rank last, gate behind a visible denominator, and do not import build-graph numbers.

## Part 2 references

**Primary, high confidence.** [ContextCov (arXiv 2603.00822)](https://arxiv.org/abs/2603.00822); [Agentless (arXiv 2407.01489)](https://arxiv.org/abs/2407.01489); [RepoGraph, ICLR 2025 (arXiv 2410.14684)](https://arxiv.org/abs/2410.14684); [LocAgent, ACL 2025 (arXiv 2503.09089)](https://arxiv.org/abs/2503.09089); [Predictive Test Selection, ICSE-SEIP 2019 (arXiv 1810.05286)](https://arxiv.org/abs/1810.05286); [Buchgeher et al., ADRs on GitHub, IEEE Access 2023](https://ieeexplore.ieee.org/document/10186293); [Jansen & Bosch, WICSA 2005](https://ieeexplore.ieee.org/document/1544207); [Ruiz, Hu & Dalpiaz, "Why don't we trace?", Requirements Engineering 2023](https://link.springer.com/article/10.1007/s00766-023-00408-9); [adr-kit](https://github.com/rvdbreemen/adr-kit); [adr-tools](https://github.com/npryce/adr-tools); [Bazel query reference](https://bazel.build/query/language); [Pants dependency inference](https://www.pantsbuild.org/docs/how-does-pants-work); [PEP 1](https://peps.python.org/pep-0001/); [RFC 2616 info page](https://www.rfc-editor.org/info/rfc2616); [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners); [GitHub stack-graphs (arXiv 2211.01224)](https://arxiv.org/abs/2211.01224); [Meta Glean incremental indexing](https://glean.software/blog/incremental/).

**Medium confidence.** [Mäder & Egyed, EMSE 2015](https://link.springer.com/article/10.1007/s10664-014-9314-z) — 24% faster / ~50% more correct, corroborated across secondaries but the primary text was not read; [Rempel & Mäder, IEEE TSE](https://ieeexplore.ieee.org/document/7469859) — correlational; [Ekstazi, ISSTA 2015](https://dl.acm.org/doi/10.1145/2771783.2771784); [When Traceability Goes Awry (arXiv 2206.04462)](https://arxiv.org/abs/2206.04462) — abstract only.

**Vendor or unevidenced — flagged.** The decision-graph products publish mechanism and methodology but **no results**. Monorepo customer stories (Nx, Vercel) are survivorship-filtered with no disclosed baselines; the adopter's own engineering blog is the more credible variant. Retrieval-recall and token-reduction claims from coding-agent vendors have no independent corroboration.

**Gaps, stated as gaps rather than findings.** No software-specific quantified trace-link staleness rate. No defensible cost-per-requirement figure. No controlled three-arm comparison of agentic-grep versus persisted-embeddings versus structural-graph on one split with one model. No study linking intent-to-code traceability to an organizational outcome. No production system treats documentation or spec dependencies as a build-cacheable action graph. Part 2's web-search budget was exhausted before reaching Rust RFC supersession mechanics, Kubernetes KEP metadata, and service-catalog adoption figures.

---

# Part 3 — where the constraint lands when execution is automated

Run 2026-09-18 to de-risk [VISION-0001](../intents/VISION-0001-ai-native-ecosystem.md)'s restated bet. Deliberately **not** sourced from agentic prior art, which is too young — an earlier probe failed precisely by using a too-new, wrong-population evidence base. Sources are organisational and operational: aviation flight deck, air traffic control, aircraft certification, radiology screening, content moderation, financial-crime surveillance, code review, statistical quality control, audit and nuclear oversight, plus the queueing literature.

**Method limitation, stated first.** The web-search budget was exhausted before work began, so everything came from direct URL and API fetch. That yielded full primary text for Bainbridge 1983, the FAA's 279-page 2013 automation report, the BEA AF447 final report, the House 737 MAX report, Sandia SAND2012-8590, DORA 2019 and four ICSE/FSE papers. Three gaps remain and are gaps, not findings: **applied Theory-of-Constraints case studies naming the post-automation constraint** (the single most wanted item, unreached), **Galbraith 1974's actual text**, and Toyota's 2014 automation reversals.

## Finding 16 — the constraint does relocate onto human decision time, but not universally [moderate]

Independent domains show it. Radiology screening: the MASAI RCT (105,934 women randomised) cut human screen-reading workload **44.3%** while raising detection from 5.1 to 6.1 per 1,000, so reading was the binding load. Content moderation: 100% human review was never affordable, and the Oversight Board reviews **53 of 398,597 appeals — 0.013%**. Queueing theory predicts it mechanically: Little's Law caps throughput at the slowest station, and Kingman's formula shows a high-variance human decision step suffers the utilisation penalty harder than a machine.

**The counter-case is decisive and must be carried.** Google runs ~20,000 changes a workday at a **median of one reviewer** and **under four hours** end-to-end, with reviewers spending a mean 3.2 hours a week. Review need not become the constraint.

**Gustafson's objection is unrefuted and gives a cheap test.** Amdahl bounds speedup by the un-automated fraction at fixed problem size; Gustafson observes that people grow the problem to fit the capacity. So: **does the human decision step's work scale with the *number* of items or the *scope* of the batch?** Constant review time per batch regardless of size means growing the unit is the answer, not raising the altitude. Review time scaling with item count means the ceiling is real. This is answerable with our own instrumentation and nobody has measured it.

A second discipline the literature ignores: **separate queueing time from service time.** "Approval took eleven days" can mean eleven days of work or ten days of sitting plus one of review — opposite remedies.

## Finding 17 — raising the altitude of human attention is refuted, including by statute [high]

Two documented reversions, both by regulators holding the best data in their domains.

**Aircraft certification.** FAA delegation rose from **28 of 87 tasks in 2013 to 79 of 91 by November 2016**, with safety-critical items reclassified downward mid-project; the Boeing oversight office held 45 FAA staff against over 1,500 Boeing delegates. After two hull losses, the Aircraft Certification, Safety and Accountability Act (Pub. L. 116-260, Div. V) legislated the altitude back down: a **non-delegable safety-critical class**, FAA **personnel authority over delegates**, and **embedded reviewers**. Note what was *not* done — the FAA did not resume reviewing everything.

**Flight deck.** With manual-handling error implicated in over 60% of in-scope accidents and pilots "out of the control loop" in over 50%, FAA SAFO 13002 told operators to **promote manual flying in normal operations**, deliberately foregoing automation's benefit to preserve capability. AF447's recommendations *add* a manual action to re-engage the flight director.

**The failure shape is the ratchet, not the level.** No single delegation step failed; the share crept up over three years. The countermeasure the evidence endorses is a structurally non-delegable class, not a periodically-reviewed percentage.

**Bainbridge refuted the mechanism by name in 1983**, and the field's 2017 review is titled "Still Unresolved After All These Years":

> "There is therefore no way in which the human operator can check in real-time that the computer is following its rules correctly. One can therefore only expect the operator to monitor the computer's decisions at some meta-level… The human monitor has been given an impossible task."

Her mechanisms, verified in the primary text: monitoring capability is produced by the doing that automation removes; the residual job needs *more* skill and *less* load; **succession is the bomb** — the first cohort of high-altitude reviewers learned by doing, and the second will not exist; and oversight is added load, not removed load.

Her own remedy is to raise the altitude **for machines** — "alarms on alarms" — with the regress flagged immediately: "who notices when the alarm system is not working properly?"

## Finding 18 — the attention limit is not linear, and reliability makes it worse [high]

Vigilance decrement: mean sensitivity effect size **0.73** across 42 studies and 138 conditions, onset around 20–30 minutes, reproduced on public roads in 2024 across four production level-2 vehicles.

**The mechanism is multi-tasking, not boredom, and this is the most design-relevant result in the survey.** Parasuraman, Molloy & Singh (1993): failure detection was substantially worse for constant-reliability automation after ~20 minutes — *but* "when system monitoring was the only task, detection was very efficient and was unaffected by variations in automation reliability." A human watching one stream with nothing else to do performs well. "Raise the altitude" almost always arrives bundled with "and supervise N parallel streams", which is the documented failure condition.

**Higher reliability makes oversight worse**, and it compounds: constant-reliability automation degraded detection, and human detection independently degrades as defects get rarer (Harris 1968, 16% → 0.25% defect rate). The better execution gets, the faster oversight rots.

**Training does not fix it.** Complacency "cannot be overcome with simple practice"; automation bias "cannot be prevented by training or instructions." **Adding reviewers does not fix it either** — Google median 1, Rigby & Bird median 2 with "only a minimal increase" in comments from more.

**Full human review was never the control it is imagined to be.** Sandia SAND2012-8590 field detection under 100% inspection: 67% piston rings, 76% acoustical tile, 68% aircraft visual, 53% subsea pipelines, **52% routine highway bridge inspection**, with accuracy still improving to ~six independent passes. "Sampled review is worse than full review" is not a safe premise.

## Finding 19 — the mechanism that works, in every domain that worked [high]

> **The human looks at full detail on a much smaller, better-selected unit, while a machine carries the detection load — and the machine's liveness is deliberately tested.**

Radiology contains both outcomes in one domain. **CAD decorated unchanged human reading and made it worse** — recall 10.1%→13.2%, AUC 0.919→0.871, invasive cancer detection down 12% across 222,135 women. **MASAI's AI replaces one of two human readers**; the remaining human reads at full detail. The distinguishing variable is whether the machine carries real load, not the sampling rate.

Google's version: 110 automated analyzers holding the mechanical floor, a **24-line median change**, explicit directory ownership deciding routing, and per-language readability certification encoding standing judgement **once** rather than re-deriving it per review. Jidoka's version: the machine "makes independent judgments about abnormality" and stops itself. PCAOB's version: when full-population inspection became cheap, the standard-setter moved *toward* full population and began governing it.

Onnasch et al. locate the damage precisely: it jumps when automation crosses from **analysing information** to **selecting the action**. Policy-level oversight sits on the expensive side by construction. (Vote-counting meta-analysis — the sign is solid, no quantitative curve is defensible.)

**On structured representations of work specifically**, ranked by evidence: authority-and-routing structure first, standing judgement encoded once second, automated detection with tested liveness third, batch-size reduction fourth — and **queues, kanban and exception dashboards last**, because they make the queue visible without making the human faster. The warning is FCA *Market Watch 79*: three banks' surveillance detectors were **dead for over three years** while the firms believed they were covered because other models produced true positives. A control emitting plausible output is indistinguishable from a working one without injected-fault testing.

## Corrections — four claims that must not enter any artifact

1. **"80% effective 100% inspection"** attributed to Harris & Chaney is untraceable folklore. Use the Sandia field table above.
2. **"90–95% AML false positive rate"** traces only to circa-2017 consultancy analysis recycled through vendor marketing.
3. **CMS did not withdraw CAD coverage on effectiveness grounds** — codes 77051/77052 were bundled into CPT 77065–77067 effective January 2018.
4. **Judge & Piccolo found management by exception "inconsistently related to the criteria,"** not worst; laissez-faire carries the −.37. Using that meta-analysis against exception-based governance is a construct-validity error.

Also: **Deming's kp rule is all-or-none** and argues *against* sampling. He supports "inspection is too late", not "sample it". And the Cisco/SmartBear code-review numbers are vendor-published, never peer-reviewed, with "LOC per review" and "LOC per hour" routinely conflated.
