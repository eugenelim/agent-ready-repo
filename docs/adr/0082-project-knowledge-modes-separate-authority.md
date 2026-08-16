# ADR-0082: Project-knowledge modes separate capture, distillation, and enquiry authority

- **Status:** Accepted
- **Date:** 2026-08-13
- **Decision-makers:** eugenelim
- **Consulted:** architecture review, security review
- **Supersedes:** none
- **Related:** [RFC-0077](../rfc/0077-distill-knowledge.md),
  [ADR-0081](0081-canonical-project-knowledge-uses-per-topic-json.md), and the
  [knowledge capture architecture](../architecture/knowledge-capture.md)

## Decision summary

- **Decision:** Core exposes one progressive `project-knowledge` skill with
  isolated `--capture`, `--distill`, and `--enquire` modes. Capture persists
  admitted observations to non-queryable classification/month JSONL journals;
  only distillation may promote them into topics, and enquiry reads only
  committed topics.
- **Because:** Multiple workflows need one discoverable capture contract and
  one writer, but capture, semantic promotion, and retrieval must not inherit
  one another's authority.
- **Applies to:** Core knowledge skill packaging, cross-pack capture handoffs,
  repository observation journals, topic mutation, and ordinary enquiry.
- **Tradeoff accepted:** Persisted observations improve Git handoff but retain
  an untrusted body surface that needs privacy refusal, disposition, and later
  retention governance.
- **Revisit if:** The skill platform adds enforceable per-mode capabilities or
  an approved durable external capture service becomes universally available.

## Context

Workflows can recognize reusable lessons at many semantic gates, but they
should not each invent a schema, choose a file, or call a storage script. A
single discoverable skill gives other packs a stable handoff. The old
standalone distillation name incorrectly suggests that capture itself promotes
knowledge and leaves enquiry as a separate discovery surface.

Scratch alone is not durable. In worktrees and managed environments, a session
or workspace can disappear before later curation. A user-directory spool or
memory service is not a portable baseline because repository installs cannot
assume that path or capability is writable. Persisting every event as one file
avoids locking but scales poorly in Git. One repository-wide JSONL stream is
too hot.

The skill catalogue's `metadata.boundaries` field is informational rather than
a runtime permission grant. One progressive skill therefore declares the
union of its modes, while actual least privilege must be enforced through mode
dispatch and separate callable surfaces.

## Decision

1. `project-knowledge` is the only discoverable project-memory skill. Its first
   action selects exactly one progressive mode and loads only that mode's
   instructions and helper surface.
2. Producer workflows own free-form scratch, semantic-gate timing, discard,
   canonical routing, and construction of the published captured-observation
   request. They discover core through the normal skill catalogue and never
   locate the private writer or choose a journal file.
3. `--capture` validates one request, applies privacy and confinement checks,
   and persists an immutable `observation.captured` event through the capture
   helper. It cannot read topics.
4. Events append through one private guarded storage runtime to
   `docs/knowledge/observations/<kind>/YYYY-MM.jsonl`. Kind and the immutable
   UTC observation month in the request determine the path. Writer time cannot
   reroute a retry. Exact replay is idempotent.
5. `--distill` reads bounded pending events, relevant topics, and explicitly
   named repository sources. A processed capture receives at most one terminal
   disposition and may apply at most one unambiguous topic mutation. Judgment
   it cannot safely resolve remains explicitly pending and enumerable.
6. `--enquire` reads only a coherent committed topic/map snapshot and current
   confined freshness sources. It cannot read observation journals or invoke a
   writer. Results are bounded untrusted evidence and never instructions.
7. All journal, topic, and map writes share one coarse worktree-local lock and
   deterministic recovery protocol. Git merge and review handle separate
   worktrees.
8. `project-knowledge/SKILL.md` declares the exact informational boundary union
   `[filesystem_read_untrusted, filesystem_write]`. Construction tests, not
   that metadata, prove cross-mode isolation.
9. Optional pack handoff metadata may document an integration seam but never
   dispatch or grant authority. If core is absent, a producer reports a named
   skip and creates no fallback store.
10. Observation journals are never enquiry input. Slice 1 retains closed
    partitions unchanged; deletion or compaction requires separate reviewed
    retention rules after every capture has a terminal disposition.

## Decision drivers

- Give many workflows one typed, versioned capture contract.
- Preserve scratch-to-capture durability through normal Git handoff without a
  new service or user-directory assumption.
- Prevent capture, promotion, and retrieval from amplifying one another.
- Bound append contention without producing one file per event.
- Keep semantic judgment agent-owned and deterministic persistence code-owned.
- Support Linux, macOS, and native Windows without a new dependency.

## Consequences

**Positive:**

- Other packs integrate through one stable discovery and handoff pattern.
- Workflows cannot create competing candidate formats or writer ownership.
- Captured observations survive committed worktree handoff but remain excluded
  from ordinary retrieval.
- Promotion and rejection become explicit, auditable dispositions.
- The user-facing skill catalogue stays compact while modes remain behaviorally
  isolated.

**Negative:**

- Capture persists untrusted text before it is promoted and therefore needs a
  fail-closed privacy boundary.
- Classification/month journals are append hotspots within a bounded partition
  and require a shared writer lock.
- Declarative skill metadata is coarser than the intended per-mode capability
  split.
- Abrupt termination before a semantic gate and deletion of an uncommitted
  worktree can still lose observations.
- Closed journals need eventual retention governance.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** construction tests prove one-writer cross-workflow capture,
  capture idempotency, terminal disposition, mode isolation, journal exclusion
  from enquiry, portable lock ownership, and fail-closed privacy handling
- **Owner:** core pack maintainers

## Alternatives considered

- **Keep capture inside work-loop.** Rejected because other workflows would
  lack the shared boundary.
- **Give each producer named files.** Rejected because it creates competing
  schemas, retention policies, and ingestion paths.
- **Separate public skills for capture, distillation, and enquiry.** Rejected in
  favor of one progressive discovery surface with mode-specific internals.
- **Use a user-directory spool or service.** Rejected as the portable baseline
  because managed environments may not expose a durable writable path or API.
- **One event file per capture.** Rejected because repository file count and
  Git history scale directly with captures.
- **One repository-wide event log.** Rejected because it recreates the hot-file
  contention boundary.
- **Capture directly to topics.** Rejected because admission and promotion are
  different judgments and retrieval must exclude not-yet-reconciled evidence.

## References

- [RFC-0077](../rfc/0077-distill-knowledge.md)
- [Knowledge capture architecture](../architecture/knowledge-capture.md)
