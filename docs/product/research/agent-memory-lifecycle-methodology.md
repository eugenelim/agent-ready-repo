# Agent-memory lifecycle methodology

> Discipline: applied (practitioner-pattern survey)

This survey asks how a repository-installed software agent should learn across
sessions without turning transcripts, stale observations, or hostile content
into standing instructions. It treats memory as a lifecycle and authority
problem first, and a storage or search problem second.

The recommendation is a staged, file-first lifecycle: workflows keep free-form
scratch, triage it at semantic completion gates, and submit worthwhile residue
through a typed capture contract. The repository persists admitted observations
in non-queryable classification/month event journals; distillation later records
a terminal disposition and may reconcile an observation into a narrow,
source-verifiable topic. Enquiry reads only committed topics and retrieves the
smallest task-relevant evidence; use never grants authority. Verification,
contradiction, canonical routing, and retirement keep the corpus current. An
optional multi-project bank may later hold explicitly exported, generalized
guidance behind project namespaces, pending project-local adoption. [high]

# Scope frame

| SIPOC element | Scope for the core pack |
| --- | --- |
| Suppliers | Users, agents, skills, reviewers, repository artifacts, tests, and approved external research |
| Inputs | Corrections, decisions, root causes, non-obvious constraints, successful methods, failed methods, source changes, and retrieval feedback |
| Process | Observe, write scratch, triage, capture, verify, distil, store, index, enquire, use, refresh, route, retire, and evaluate |
| Outputs | Captured-observation events and dispositions, project topics, topic indexes, task-scoped evidence bundles, explicitly exported lessons, and governance artifacts |
| Customers | Future agent runs, maintainers, reviewers, and optional organization-level memory consumers |

The unit of durable project knowledge is not a message or transcript. It is a
narrow claim or practice lesson with a stable topic identity, current
synthesis, lifecycle state, applicable scope, verification basis, and one or
more provenance-bearing occurrences. Session history and workflow checkpoints
remain separate continuity mechanisms. Instructions, policies, and permissions
remain in their governed sources of truth. This separation follows production
frameworks that distinguish thread state from cross-thread stores and research
that separates facts, experiences, summaries, and beliefs rather than treating
all remembered text alike. [high]

Evidence: [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence),
[LangMem core concepts](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/),
[OpenAI Agents SDK agent memory](https://openai.github.io/openai-agents-python/sandbox/memory/),
and [Hindsight](https://aclanthology.org/2026.acl-demo.27/).

The lifecycle covers repository knowledge for the full range of software
repositories into which the core pack may be installed. It does not attempt to
persist complete conversations, replace ADRs or documentation, learn model
weights, or make a committed repository an access-controlled database.

# Stage spine

## Stage 1 — Observe and keep scratch

Any user-facing workflow, skill, reviewer, or ordinary agent session may keep a
free-form note as soon as a potentially reusable lesson becomes clear. The note
needs enough evidence to recover the lesson, its conditions, its source, and a
future question it could answer, but it does not need a schema. Scratch remains
workflow continuity rather than trusted knowledge. [high]

Explicit scratch can also capture verification friction: repeated failed or
redirected attempts, a missing or noisy oracle, or an existing check the agent
could not discover. Mechanical failures do not each create knowledge. The next
semantic gate classifies their accumulated signal and routes it to an existing
loop gate, scoped agent task map, or normal work intake for a new verification
tool. [moderate]

The capture question is broader than speed: would this learning have made a
future approach materially more correct, complete, reliable, recoverable,
secure, privacy-preserving, deterministic, reproducible, operable,
maintainable, reviewable, efficient, or independent of hidden context?

This timing combines immediate note-taking with bounded retrospection at stable
meaning boundaries. Current implementations document the same trade: active
formation is immediate but adds task latency and cognitive load; deferred
formation improves coverage but requires a durable backend. Long-run harness
research also shows that structured handoff state outperforms reliance on
compaction alone. [high]

Evidence: [LangMem formation modes](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/),
[OpenAI Agents SDK two-phase generation](https://openai.github.io/openai-agents-python/sandbox/memory/),
[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
and [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

The harness must not mine every message or tool result into durable knowledge.
Automatic transcript ingestion optimizes capture recall by accepting noise,
privacy leakage, self-reinforcing model output, and persistent prompt-injection
risk. A semantic gate may invite the agent to review only explicit scratch
accumulated since the previous gate; it must not reconstruct observations from
raw context. [high]

## Stage 2 — Triage and shape

At an RFC, ADR, spec, plan, verified-slice, review, handoff, or closeout gate,
the originating workflow rejects current-task state, disproved notes,
unverified incident detail, personal or secret material, source instructions,
duplicates without new evidence, and content fully owned by another canonical
surface. Reusable residue is shaped into a typed capture request carrying
producer, gate, structural scope, source reference and digest where available,
freshness anchor, and competency-question facets. Successful capture persists
an immutable event and returns an idempotent receipt. The event remains
untrusted and is not yet a topic. [high]

Agent-curated, structured saves are preferable to transcript recording, and
stable topic identity is useful for evolving subjects. The portable core should
adopt those ideas while rejecting direct save-to-trusted-memory and automatic
loading. A repository journal is a durable workflow handoff, not a second
queryable memory layer: it holds capture and disposition events until explicit
retention governs closed partitions. Exact replays are idempotent, and exact
duplicates should not create competing current claims. [high]

## Stage 3 — Distil and reconcile

Distillation consumes a bounded pending captured observation, compares it with
existing topics and owning sources, and records at most one terminal
disposition: `promoted`, `duplicate`, `routed`, `rejected`, or `superseded`.
Irreducible judgment remains pending and enumerable rather than receiving an
invented terminal state.
Promotion may create a topic, attach an occurrence, revise the current
synthesis, mark a contradiction, narrow after partial absorption, or retire a
superseded topic. Irreducible merge, split, provenance, or retirement judgment
is surfaced with no topic mutation. [high]

The topic keeps evidence and synthesis distinct. Occurrences retain what was
observed and where; the current synthesis states what practitioners should
believe now. Conflicting evidence does not overwrite history. It marks the
topic `needs_review` until the owning source resolves the conflict. Temporal
memory research and production systems consistently preserve invalidated facts
or historical episodes while distinguishing current validity. [high]

Evidence: [Generative Agents](https://arxiv.org/abs/2304.03442),
[Zep temporal knowledge-graph architecture](https://arxiv.org/abs/2501.13956),
[LangMem collection reconciliation](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/),
and [Hindsight](https://arxiv.org/abs/2512.12818).

Distillation also routes stronger knowledge upward. Current structure belongs
in architecture docs, rationale in ADRs, proposed change in RFCs or specs,
procedure in skills, policy in conventions, and enforceable invariants in tests,
lint, CI, contract probes, or diagnostic tools. Repeated or high-friction
navigation lessons can suggest a task map in the nearest canonical scoped agent
instruction file: authoritative starting point, generated outputs, and closing
verification. Platform-specific projections are not edited directly. Missing
tooling remains tracked work rather than an `AGENTS.md` backlog. The knowledge
corpus holds reusable practice residue and links to the owning destination
instead of duplicating its authority.

## Stage 4 — Store and index

Canonical storage is file-based and Git-published. Capture and terminal
disposition events append through one writer to bounded classification/month
JSONL journals. Reconciled state uses one pretty-printed JSON document per
narrow topic plus a deterministic topic index containing routing metadata
rather than bodies. This avoids one repository-wide hot file, makes one topic
the unit of review, and gives evolving knowledge an explicit update target.
JSONL is appropriate for append-oriented events and migration interchange, but
not for reconciled current-topic state. [moderate]

The portable index is a committed, byte-reproducible topic map with no bodies.
It identifies the expected topic blobs in the same Git tree. A working-tree
topic is an authoring proposal; topic and map become visible to ordinary
enquiry only when one commit publishes the coherent tree. This applies the
established topic-oriented separation between reusable topic units and maps
that select/organize them, while using Git's native snapshot instead of a custom
multi-file transaction. Full-text, embedding, graph, or embedded-database indexes are optional
derived accelerators and stay gitignored. They may be discarded and rebuilt
solely from canonical topic files. FTS5 is a reasonable possible adapter, but
SQLite itself documents that external-content indexes require explicit
consistency management; it should therefore never become a silently competing
source of truth. [high]

Evidence: [OASIS topic-oriented maps](https://docs.oasis-open.org/dita/v1.0/archspec/maps.html),
[ISO Topic Maps identity and merging](https://isotopicmaps.org/sam/sam-model/),
[Git tree snapshots](https://git-scm.com/docs/user-manual),
[Lucene commit points](https://lucene.apache.org/core/10_0_0/core/org/apache/lucene/index/IndexCommit.html),
[JSON Lines format](https://jsonlines.org/),
[SQLite FTS5](https://sqlite.org/fts5.html),
[LangGraph long-term memory storage](https://docs.langchain.com/oss/python/langchain/long-term-memory),
and [Letta context hierarchy](https://docs.letta.com/guides/core-concepts/memory/context-hierarchy).

## Stage 5 — Enquire and assemble evidence

`project-knowledge --enquire` starts with a committed topic-map snapshot, hard filters, then ranking. It resolves the current project
namespace, lifecycle state, path or subsystem scope, source authority, and
freshness requirements before semantic or lexical relevance. It retrieves
topic summaries first and opens occurrences or owning sources progressively
only when the task requires them. The result is a bounded evidence bundle with
topic identity, status, applicable scope, provenance, verification state, and
explicit conflict warnings. It returns a query receipt so a skill-owned call is
visible and attributable rather than ambient context. [high]

Similarity alone is insufficient. Research systems improve recall with
recency, importance, keyword expansion, graph relationships, and temporal
filters; evaluation shows temporal reasoning, knowledge updates, multi-session
reasoning, and abstention are distinct abilities. The first implementation does
not need every signal, but its contract must leave room for lexical relevance,
topic routing, source trust, freshness, and negative feedback. [high]

Evidence: [Generative Agents](https://arxiv.org/abs/2304.03442),
[LongMemEval](https://arxiv.org/abs/2410.10813),
[Hindsight](https://aclanthology.org/2026.acl-demo.27/),
and [LangMem flexible retrieval](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/).

## Stage 6 — Use without authority amplification

Retrieved knowledge is delimited untrusted evidence, never an instruction
layer. It cannot grant permissions, relax confirmations, change policy, or
override canonical repository artifacts. Consequential claims are verified
against their owning source immediately before use. Agents cite topic and
source identity when a memory materially changes an approach, and abstain or
surface uncertainty when evidence is absent, conflicting, or stale. [high]

This boundary is necessary because persistent memory converts a one-session
injection into a cross-session foothold. Security guidance calls for write
validation, segmentation, provenance, retention limits, prevention of automatic
self-reingestion, trust-aware retrieval, quarantine, rollback, and human review
for high-risk uses. Containment research further warns that local files, tool
output, shared agent messages, and persistent state all remain prompt-injection
surfaces. Where the portable core cannot protect a raw quarantine store, it
should refuse the observation body instead. [high]

Evidence: [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/download/52117/),
[AgentPoison](https://arxiv.org/abs/2407.12784),
[How we contain agents across products](https://www.anthropic.com/engineering/how-we-contain-claude),
and [The Instruction Hierarchy](https://arxiv.org/abs/2404.13208).

## Stage 7 — Learn from use

The immediate enquiry receipt records only retrieval-time facts: topics
selected, sources verified, query budget, immutable corpus identity, and
abstention. Whether evidence was ignored, changed the approach, avoided rework,
caused a wrong turn, or revealed a stale topic is known only after use. In the
portable baseline, the caller may add that post-use signal to explicit scratch;
the next semantic gate triages and captures it through the normal lifecycle.
Enquiry remains
read-only and no feedback automatically reinforces or mutates a topic. A later
measurement layer may formalize non-sensitive outcomes only under separate
governance. [moderate]

## Stage 8 — Refresh, route, and retire

Freshness is source-relative, not age-only. A five-year-old lesson whose owning
code and tests are unchanged may be current; yesterday's lesson may be stale
after a refactor. A topic becomes `needs_review` when its source digest changes,
its scope is touched by a conflicting change, a verification deadline tied to
risk expires, enquiry reports contradiction, or the owning canonical artifact
supersedes it. [high]

Ordinary enquiry returns only `active` topics. `needs_review` topics may be
shown in a clearly labelled diagnostic mode and `retired` topics remain in Git
history rather than normal retrieval. Unverified low-trust memory may expire;
verified project knowledge is retired because its applicability or authority
changed, not simply because time passed. This adapts forgetting-curve and
retention ideas without pretending repository truth decays like human recall.
[moderate]

Retirement as `enforced` closes a verification feedback loop: a topic about a
missing or repeatedly missed check remains evidence until the test, lint, CI
rule, contract probe, diagnostic tool, or loop invocation is effective for the
same scope. Only then does the stronger control replace remembered prose.

Evidence: [long-term memory retention study](https://arxiv.org/abs/2305.10250),
[LongMemEval](https://arxiv.org/abs/2410.10813),
[Zep temporal architecture](https://arxiv.org/abs/2501.13956),
and [OWASP ASI06 guidance](https://genai.owasp.org/download/52117/).

# Contingency branches

| Condition | Branch |
| --- | --- |
| No checkpoint or stop hook | Triage at the workflow's next explicit semantic gate; an abrupt end may lose scratch. |
| No durable writable user state or memory service | Persist admitted observations in the repository journal; do not claim to preserve scratch that disappears before capture or uncommitted changes in a deleted worktree. |
| Very small repository | Keep the same topic semantics and direct file path; the body-free index remains a small portable projection. |
| Branch-heavy repository | Use per-topic canonical files so unrelated subjects do not append to one hot file. |
| Large monorepo | Partition topic paths and index routes by project/subsystem namespace; retrieve topic headers before bodies. |
| Regulated or sensitive repository | Refuse indeterminate observation bodies, require stronger provenance and review, and disable cross-project export by default. |
| Local search is slow | Build a gitignored deterministic lexical or embedded index; report index age and corpus digest; rebuild on mismatch. |
| Multiple projects need shared learning | Explicitly export a generalized, redacted topic copy into an optional bank; retain project provenance and never search another project namespace implicitly. |
| Canonical source changes | Mark dependent topics `needs_review`; do not infer that every old topic is wrong or every new topic is current. |
| Contradictory observations | Preserve both occurrences, suppress ordinary retrieval, and require distillation against the owning source. |
| Suspected poisoning | Refuse capture before persistence when detectable; otherwise record a bounded terminal disposition or mark the topic `needs_review`, stop propagation, inspect sources, revert durable changes through Git, and rebuild derived indexes. |

The multi-project bank is an export and adoption target, not the owner of
project truth. Namespaces prevent accidental cross-project bleed; export
requires generalization, privacy review, source references, and an explicit
audience. A bank topic may inform a project, but only project-local validation
can make it active there. Hierarchical namespace patterns are established in
current memory stores, while security guidance makes tenant segmentation and
trust-aware retrieval mandatory for shared stores. [high]

Evidence: [LangMem namespaces](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/),
[LangGraph stores](https://docs.langchain.com/oss/python/langgraph/persistence),
[OpenAI Agents SDK session isolation](https://openai.github.io/openai-agents-python/sessions/),
and [OWASP ASI06](https://genai.owasp.org/download/52117/).

# Maturity ladder

| Level | Capability | Exit signal |
| --- | --- | --- |
| 0 — Loop-bound log | One JSONL corpus, capture only at work-loop closeout, manual curation, no normal retrieval | Valuable learnings are routinely missed outside implementation work or the hot file creates review friction. |
| 1 — Durable capture boundary | Work-loop triages free-form scratch at semantic gates and persists typed observations in non-queryable classification/month journals | Capture survives normal Git handoff without unacceptable noise, privacy exposure, or ceremony. |
| 2 — Topic lifecycle | Terminal dispositions, stable topics, occurrences, reconciliation, lifecycle state, source-relative freshness, and deterministic topic index | Distillation enforces the observation-to-topic contract end to end. |
| 3 — Safe enquiry | Task-scoped progressive retrieval, provenance envelopes, hard trust/freshness filters, abstention, and feedback | Retrieval improves task outcomes without unacceptable false-positive or poisoning rates. |
| 4 — Local acceleration | Replaceable gitignored lexical, full-text, embedding, or graph index selected by observed pressure | Rebuild, drift detection, and fallback to canonical files are reliable. |
| 5 — Optional durable capture and bank | Approved deferred-capture backend and/or explicit export, namespaces, privacy controls, project-local adoption, and policy-aware adapters | Measured loss or reuse justifies new runtime and tenancy boundaries. |

The core pack should implement levels 1 through 3 with file semantics before
standardizing a database. Level 4 is adapter territory; level 5 is a separate
governance and tenancy capability, not a reason to weaken the project model.

# Failure modes

| Failure mode | Cause | Control |
| --- | --- | --- |
| Capture blindness | Only one workflow asks what was learned | Add semantic-gate integrations incrementally after the foundation proves safe |
| Capture flood | Transcript mining or vague “remember this” criteria | Explicit scratch, gate triage, competency questions, and bounded typed input |
| Authority confusion | Observations are loaded beside instructions | No automatic priming; data envelope; canonical-source precedence |
| Persistent injection | Hostile source text reaches durable memory | Refusal on uncertainty, provenance, paraphrased observation, review, no self-reingestion |
| Self-confirming error | Agent output is saved and later treated as evidence | Require independent source references; use feedback only as a review signal |
| Stale truth | Recency substitutes for source verification | Source-relative freshness, change triggers, `needs_review`, abstention |
| Duplicate current claims | Every occurrence becomes a new memory | Stable topic identity with occurrences and one current synthesis |
| Lost history | Upsert overwrites why the topic changed | Preserve occurrences and Git history; record routing and retirement decisions |
| Hot-file conflicts | Every writer appends or edits one repository-wide JSONL file | Classification/month observation journals plus per-topic canonical files |
| Working-tree content leaks into retrieval | Authoring and publication are conflated | Enquiry reads topic and map blobs from one committed Git snapshot |
| Index split brain | Derived database is treated as canonical | Committed body-free topic map, blob identity checks, never commit local DB |
| Verification rediscovery | Agents repeatedly miss or rebuild the same oracle | Capture bounded friction, wire existing checks into the loop, route missing tools to work intake, retire when enforced |
| Cross-project leakage | Global search ignores project or audience | Hard namespace filters before ranking; explicit export and adoption |
| Over-broad topics | Category files recreate the hot file | One independently verifiable claim per topic |
| Premature complexity | A database is added before a capability needs it | File-first levels and pressure-based adapters |
| Benchmark optimism | Recall is measured without freshness or security | Evaluate capture precision/recall, updates, abstention, poisoning, latency, and outcome impact |

# Evidence & confidence

The recommendations are triangulated across peer-reviewed or primary research,
official framework contracts, official security guidance, and this repository's
current implementation. The strongest agreement is on separation of session
state from durable memory, staged consolidation, progressive retrieval,
provenance, namespaces, and explicit trust boundaries. [high]

| Proposition | Evidence convergence | Confidence |
| --- | --- | --- |
| Treat memory as a lifecycle rather than storage plus similarity search | Generative Agents, LangMem, OpenAI agent memory, Hindsight, LongMemEval | high |
| Separate observations from instructions and permissions | LangMem memory types, instruction-hierarchy research, OWASP ASI06, containment guidance | high |
| Combine in-path scratch with semantic-gate capture and later distillation | LangMem formation modes, OpenAI two-phase generation, long-running harness research; portability constraint favors repository-published handoff | moderate |
| Use stable topic identity and preserve occurrence provenance | A-MEM linked notes, temporal architectures, Hindsight evidence/belief separation, local curation needs | moderate |
| Make freshness source-relative rather than age-only | LongMemEval update tests, temporal invalidation systems, repository source-of-truth model | high |
| Prefer topic files plus a committed topic map over one hot JSONL file | OASIS topic/map separation, ISO topic identity and occurrence merging, Git snapshots, Lucene commit-point visibility, JSONL properties | high |
| Keep cross-project sharing explicit and namespaced | LangMem/LangGraph namespaces, session isolation, OWASP tenant segmentation | high |
| Defer a committed or mandatory database | File-based production patterns, storage-neutral memory APIs, heterogeneous core-pack install target | moderate |

The linked-note evidence in the topic-identity row refers to
[A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110),
which dynamically constructs structured notes, links related memories, and
evolves existing representations as new evidence arrives.

The comparison baseline contributes four ideas worth adopting: agent judgment
over what is worth remembering; structured records; duplicate and
evolving-topic semantics; and explicit lifecycle state. Its persistence
topology depends on a binary, writable data directory, or service. The portable
core should instead publish captured observations as non-queryable repository
events, make topics the only queryable project-memory unit, retain Git as the
project audit boundary, and keep retrieval explicit, scoped, and
non-authoritative. [high]

The benchmark literature is useful but not dispositive. LoCoMo evaluates long-
range conversation questions, while LongMemEval adds knowledge updates,
temporal reasoning, multi-session reasoning, and abstention. Neither directly
tests a Git-governed software-repository knowledge lifecycle, capture quality,
or permission amplification. Repository-specific construction and adversarial
evaluations are required before enabling enquiry by default. [high]

Evidence: [LoCoMo](https://arxiv.org/abs/2402.17753),
[LongMemEval](https://arxiv.org/abs/2410.10813),
[AgentPoison](https://arxiv.org/abs/2407.12784),
and [OWASP ASI06](https://genai.owasp.org/download/52117/).

## Known unknowns

- Which semantic gates in non-work-loop skills produce enough useful scratch to
  justify integration without repeated token cost?
- How much useful knowledge is lost to unexpected termination under synchronous
  capture, and does that measured loss justify an optional durable backend?
- What topic granularity minimizes both missed connections and hot-topic merge
  pressure across small repositories and large monorepos?
- Which deterministic lexical ranking is sufficient before embeddings or an
  embedded full-text index materially improve software-repository enquiry?
- What verification triggers and risk-based review intervals minimize stale
  retrieval without turning curation into constant churn?
- What governance boundary should own an optional multi-project bank, and what
  redaction evidence is required before export?
- What false-positive rate is acceptable for privacy and injection scanners,
  given that no semantic scanner can prove arbitrary prose safe?
- Which task-outcome metrics show that retrieved knowledge prevented rework
  rather than merely increasing recall or model confidence?
