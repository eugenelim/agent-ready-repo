# Agent-memory lifecycle methodology

> Discipline: applied (practitioner-pattern survey)

This survey asks how a repository-installed software agent should learn across
sessions without turning transcripts, stale observations, or hostile content
into standing instructions. It treats memory as a lifecycle and authority
problem first, and a storage or search problem second.

The recommendation is a staged, file-first lifecycle: agents may signal
low-trust candidates from any workflow; a shared gate distils accepted
observations into narrow, source-verifiable topics; enquiry retrieves only the
smallest task-relevant evidence; use never grants authority; verification,
contradiction, promotion, and retirement keep the corpus current. Project-local
topics remain scoped evidence; canonical project artifacts remain
authoritative. An optional multi-project bank holds explicitly promoted,
generalized guidance behind project namespaces and a replaceable local index,
pending project-local validation before use. [high]

# Scope frame

| SIPOC element | Scope for the core pack |
| --- | --- |
| Suppliers | Users, agents, skills, reviewers, repository artifacts, tests, and approved external research |
| Inputs | Corrections, decisions, root causes, non-obvious constraints, successful methods, failed methods, source changes, and retrieval feedback |
| Process | Signal, triage, verify, distil, store, index, enquire, use, refresh, promote, retire, and evaluate |
| Outputs | Pending candidates, project topics, topic indexes, task-scoped evidence bundles, cross-project promoted lessons, and governance artifacts |
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

## Stage 1 — Observe and signal

Any user-facing workflow, skill, reviewer, or ordinary agent session may emit a
typed candidate as soon as a potentially reusable lesson becomes clear. A
session or pre-compaction checkpoint also performs a bounded retrospective over
agent-authored outcomes and already-referenced evidence. Both paths create
candidates only; neither writes trusted knowledge. [high]

The capture question is broader than speed: would this learning have made a
future approach materially more correct, complete, reliable, recoverable,
secure, privacy-preserving, deterministic, reproducible, operable,
maintainable, reviewable, efficient, or independent of hidden context?

This hybrid timing combines the immediacy of in-path memory formation with the
coverage of post-run consolidation. Current implementations document the same
trade: active formation is immediate but adds task latency and cognitive load;
background formation increases coverage without slowing the response. Long-run
harness research also shows that structured files and explicit handoff state
outperform reliance on compaction alone. [high]

Evidence: [LangMem formation modes](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/),
[OpenAI Agents SDK two-phase generation](https://openai.github.io/openai-agents-python/sandbox/memory/),
[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
and [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

The harness must not mine every message or tool result into durable knowledge.
Automatic transcript ingestion optimizes capture recall by accepting noise,
privacy leakage, self-reinforcing model output, and persistent prompt-injection
risk. A checkpoint may remind the agent to finish or persist already-signalled
candidates and may invite a bounded retrospective; it must not silently
promote raw context. [high]

## Stage 2 — Triage and quarantine

The shared capture gate rejects current-task state, unverified incident detail,
personal or secret material, source instructions, duplicates without new
evidence, and content owned by another canonical surface. Accepted candidates
remain low-trust and repo-scoped until distillation. Candidate metadata records
producer, repository identity, source reference and digest where available,
time, scope, and decision history. Unknown or malformed states quarantine.
[high]

This is where the external comparison baseline is strongest: agent-curated,
structured saves are preferable to transcript recording, and stable topic
identity is useful for evolving subjects. The core pack should adopt those
ideas at the candidate and topic layers, while rejecting direct save-to-trusted-
memory and automatic loading. Exact-duplicate accounting is useful as evidence
of recurrence; it should not create multiple competing current claims. [high]

## Stage 3 — Distil and reconcile

Distillation converts one or more candidates or occurrences into a project
topic. It compares the proposed claim with the existing topic and its owning
sources, then chooses one of: discard, attach an occurrence, revise the current
synthesis, mark a contradiction, split an over-broad topic, promote to a
canonical artifact, or retire the topic. [high]

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
procedure in skills, policy in conventions, and enforceable invariants in tests
or lint rules. The knowledge corpus holds reusable practice residue and links
to the promoted destination instead of duplicating its authority.

## Stage 4 — Store and index

Canonical storage is file-based and Git-reviewed. The scale target is one
pretty-printed JSON document per narrow topic plus a deterministic topic index
containing routing metadata rather than bodies. This reduces the merge and
rewrite pressure of a single hot JSONL file, makes one topic the unit of review,
and gives evolving knowledge an explicit update target. JSONL remains a valid
portable interchange and small-repository compatibility format. [moderate]

The index may start as a committed, byte-reproducible topic catalogue or a
generated local manifest. Full-text, embedding, graph, or embedded-database
indexes are derived accelerators and stay gitignored. They may be discarded and
rebuilt solely from canonical topic files. FTS5 is a reasonable local adapter,
but SQLite itself documents that external-content indexes require explicit
consistency management; it should therefore never become a silently competing
source of truth. [high]

Evidence: [JSON Lines format](https://jsonlines.org/),
[SQLite FTS5](https://sqlite.org/fts5.html),
[LangGraph long-term memory storage](https://docs.langchain.com/oss/python/langchain/long-term-memory),
and [Letta context hierarchy](https://docs.letta.com/guides/core-concepts/memory/context-hierarchy).

## Stage 5 — Enquire and assemble evidence

Enquiry starts with hard filters, then ranking. It resolves the current project
namespace, lifecycle state, path or subsystem scope, source authority, and
freshness requirements before semantic or lexical relevance. It retrieves
topic summaries first and opens occurrences or owning sources progressively
only when the task requires them. The result is a bounded evidence bundle with
topic identity, status, applicable scope, provenance, verification state, and
explicit conflict warnings. [high]

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
surfaces. [high]

Evidence: [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/download/52117/),
[AgentPoison](https://arxiv.org/abs/2407.12784),
[How we contain agents across products](https://www.anthropic.com/engineering/how-we-contain-claude),
and [The Instruction Hierarchy](https://arxiv.org/abs/2404.13208).

## Stage 7 — Learn from use

Enquiry records non-sensitive operational feedback: topics surfaced, selected,
ignored, contradicted, verified, or found stale; query latency and evidence
volume; and whether retrieved knowledge avoided rework or caused a wrong turn.
Use is evidence, not automatic truth reinforcement. Repeated successful use may
raise utility; it must not raise instruction authority or erase the need for
source verification. Negative feedback creates a review candidate. [moderate]

## Stage 8 — Refresh, promote, and retire

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

Evidence: [MemoryBank](https://arxiv.org/abs/2305.10250),
[LongMemEval](https://arxiv.org/abs/2410.10813),
[Zep temporal architecture](https://arxiv.org/abs/2501.13956),
and [OWASP ASI06 guidance](https://genai.owasp.org/download/52117/).

# Contingency branches

| Condition | Branch |
| --- | --- |
| No checkpoint or stop hook | The shared capture command still works from any agent or skill; the next explicit curation run discovers pending candidate files. |
| Very small repository | Keep the same topic semantics; JSONL may remain the physical representation until an observed pressure justifies migration. |
| Branch-heavy repository | Use per-candidate spool files and per-topic canonical files so unrelated writers do not append to one hot file. |
| Large monorepo | Partition topic paths and index routes by project/subsystem namespace; retrieve topic headers before bodies. |
| Regulated or sensitive repository | Shorter candidate retention, stronger scanners, mandatory human promotion, stricter provenance, and no cross-project export by default. |
| Local search is slow | Build a gitignored deterministic lexical or embedded index; report index age and corpus digest; rebuild on mismatch. |
| Multiple projects need shared learning | Explicitly promote a generalized, redacted topic copy into an optional bank; retain project provenance and never search another project namespace implicitly. |
| Canonical source changes | Mark dependent topics `needs_review`; do not infer that every old topic is wrong or every new topic is current. |
| Contradictory observations | Preserve both occurrences, suppress ordinary retrieval, and require distillation against the owning source. |
| Suspected poisoning | Quarantine the candidate or topic, stop propagation, inspect source and promotion history, revert durable changes through Git, and rebuild derived indexes. |

The multi-project bank is a projection and promotion target, not the owner of
project truth. Namespaces prevent accidental cross-project bleed; promotion
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
| 1 — Shared capture | Any workflow can emit typed repo-scoped candidates; checkpoints persist already-signalled candidates; promotion remains explicit | Capture coverage is measurable and candidate precision is acceptable. |
| 2 — Topic lifecycle | Stable topics, occurrences, reconciliation, lifecycle state, source-relative freshness, and deterministic topic index | Distillation and enquiry can enforce the topic contract end to end. |
| 3 — Safe enquiry | Task-scoped progressive retrieval, provenance envelopes, hard trust/freshness filters, abstention, and feedback | Retrieval improves task outcomes without unacceptable false-positive or poisoning rates. |
| 4 — Local acceleration | Replaceable gitignored lexical, full-text, embedding, or graph index selected by observed pressure | Rebuild, drift detection, and fallback to canonical files are reliable. |
| 5 — Multi-project bank | Explicit promotion, namespaces, privacy controls, project-local adoption, and policy-aware adapters | Multiple projects demonstrate recurring transferable lessons and governance can own the new boundary. |

The core pack should implement levels 1 through 3 with file semantics before
standardizing a database. Level 4 is adapter territory; level 5 is a separate
governance and tenancy capability, not a reason to weaken the project model.

# Failure modes

| Failure mode | Cause | Control |
| --- | --- | --- |
| Capture blindness | Only one workflow asks what was learned | Shared capture command plus bounded session/checkpoint retrospective |
| Capture flood | Transcript mining or vague “remember this” criteria | Typed signals, quality attributes, hard caps, and explicit promotion |
| Authority confusion | Observations are loaded beside instructions | No automatic priming; data envelope; canonical-source precedence |
| Persistent injection | Hostile source text reaches durable memory | Candidate quarantine, provenance, scanners, paraphrased observation, review, no self-reingestion |
| Self-confirming error | Agent output is saved and later treated as evidence | Require independent source references; use feedback only as a review signal |
| Stale truth | Recency substitutes for source verification | Source-relative freshness, change triggers, `needs_review`, abstention |
| Duplicate current claims | Every occurrence becomes a new memory | Stable topic identity with occurrences and one current synthesis |
| Lost history | Upsert overwrites why the topic changed | Preserve occurrences and Git history; record promotion decisions |
| Hot-file conflicts | Every writer appends or edits one JSONL file | Per-candidate spool files and per-topic canonical files |
| Index split brain | Derived database is treated as canonical | Corpus digest, rebuildable index, fallback to files, never commit local DB |
| Cross-project leakage | Global search ignores project or audience | Hard namespace filters before ranking; explicit promotion and adoption |
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
| Combine in-path signals with background/checkpoint consolidation | LangMem formation modes, OpenAI two-phase generation, long-running harness research | high |
| Use stable topic identity and preserve occurrence provenance | A-MEM linked notes, temporal architectures, Hindsight evidence/belief separation, local curation needs | moderate |
| Make freshness source-relative rather than age-only | LongMemEval update tests, temporal invalidation systems, repository source-of-truth model | high |
| Prefer topic files plus a derived index over one hot JSONL file | JSONL properties, Git line-level conflict behavior, SQLite index consistency duties, local writer shape | moderate |
| Keep cross-project sharing explicit and namespaced | LangMem/LangGraph namespaces, session isolation, OWASP tenant segmentation | high |
| Defer a committed or mandatory database | File-based production patterns, storage-neutral memory APIs, heterogeneous core-pack install target | moderate |

The linked-note evidence in the topic-identity row refers to
[A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110),
which dynamically constructs structured notes, links related memories, and
evolves existing representations as new evidence arrives.

The external comparison baseline contributes four ideas worth adopting:
agent judgment over what is worth remembering; structured records; duplicate
and evolving-topic semantics; and explicit lifecycle state. The core pack
should change their placement. Saves first become quarantined candidates;
topics, not individual saves, are the durable current unit; Git remains the
project audit boundary; and retrieval remains explicit, scoped, and
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

- Which supported harnesses expose reliable stop, compaction, and session-close
  events, and which can only support explicit capture calls?
- Can a bounded retrospective achieve useful capture recall without reading
  untrusted raw transcript content or retaining sensitive detail?
- What topic granularity minimizes both missed connections and hot-topic merge
  pressure across small repositories and large monorepos?
- Which deterministic lexical ranking is sufficient before embeddings or an
  embedded full-text index materially improve software-repository enquiry?
- What verification triggers and risk-based review intervals minimize stale
  retrieval without turning curation into constant churn?
- How should repository identity survive clones, remotes, forks, and monorepo
  subprojects without embedding personal or organization-specific identifiers?
- What governance boundary should own an optional multi-project bank, and what
  redaction evidence is required before promotion?
- What false-positive rate is acceptable for privacy and injection scanners,
  given that no semantic scanner can prove arbitrary prose safe?
- Which task-outcome metrics show that retrieved knowledge prevented rework
  rather than merely increasing recall or model confidence?
