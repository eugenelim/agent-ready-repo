# ADR-0081: Canonical project knowledge uses per-topic JSON

- **Status:** Accepted
- **Date:** 2026-08-13
- **Decision-makers:** eugenelim
- **Consulted:** architecture review, security review
- **Supersedes:** none
- **Related:** [RFC-0077](../rfc/0077-distill-knowledge.md),
  [ADR-0082](0082-project-knowledge-modes-separate-authority.md), and the
  [knowledge capture architecture](../architecture/knowledge-capture.md)

## Decision summary

- **Decision:** Reconciled project knowledge is one pretty-printed JSON object
  per stable topic plus a deterministic, body-free `topics.index.json` map.
  Topic and map publication occurs in one Git snapshot.
- **Because:** A topic is mutable current synthesis with occurrences,
  lifecycle, and freshness, while JSONL is better suited to append-oriented
  events than current-state reconciliation.
- **Applies to:** Project knowledge stored under `docs/knowledge/topics/` and
  read by ordinary enquiry.
- **Tradeoff accepted:** The shared topic map is mechanically hot and must be
  rebuilt after branch merges; same-topic conflicts require semantic review.
- **Revisit if:** Measured corpus size, enquiry latency, or write contention
  exceeds the published file-first budgets.

## Context

The shipped corpus is one `docs/knowledge/patterns.jsonl` file. It is easy for
one guarded writer to append, but it mixes independent subjects and provides no
stable current-state target for synthesis, lifecycle, source-relative
freshness, contradiction, or intentional retirement.

Project topics are not immutable events. New occurrences may change one
current synthesis, narrow its scope, mark it `needs_review`, or show that a
stronger artifact has absorbed it. Representing that model as JSONL would
require replay, compaction, and a materialized current view. A committed
database would add a dependency and create another source-of-truth question.

## Decision

1. Each narrow, independently verifiable subject has one stable topic JSON file
   under `docs/knowledge/topics/<namespace>/`.
2. A topic contains current synthesis, structural scope, lifecycle,
   source-relative freshness, provenance-bearing occurrences, and successor
   references where applicable.
3. `topics.index.json` is a byte-deterministic map containing identity, path,
   routing headers, schema version, and expected Git blob identity, but no topic
   or occurrence bodies.
4. Topic files are semantic authority. A map mismatch is an integrity failure;
   a map-only merge conflict is discarded and rebuilt.
5. Ordinary enquiry reads a coherent map and topic blobs from one committed Git
   tree. Working-tree files are authoring proposals, not published memory.
6. Richer lexical, full-text, embedding, or graph indexes are derived local
   accelerators. They are disposable, gitignored, never committed, and
   rebuildable from canonical topics.
7. The legacy JSONL corpus remains migration evidence during cutover. JSONL may
   be used for append-oriented capture events or interchange, but not as the
   reconciled current-topic representation.

## Decision drivers

- Keep the core pack portable from tiny repositories to large monorepos.
- Make stable topic identity, occurrence provenance, lifecycle, and freshness
  directly reviewable.
- Reduce unrelated content conflicts without adding replay machinery.
- Use Git's existing snapshot and review boundary.
- Avoid a database dependency before measurements justify one.

## Consequences

**Positive:**

- Independent topics become independent review and merge units.
- Current state is readable without replay or compaction.
- Occurrences retain evidence history without duplicating current claims.
- Publication is coherent because enquiry reads one Git tree.
- Local acceleration can evolve without changing canonical storage.

**Negative:**

- The committed topic map changes whenever a topic changes.
- Same-topic branch conflicts require semantic reconciliation.
- Multi-file working-tree interruption needs guarded recovery, even though it
  cannot leak partial state into committed-only enquiry.
- Large repositories may eventually need a derived index for acceptable query
  latency.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** construction tests prove deterministic map rebuild, committed-only
  visibility, map/body integrity, topic-level conflict handling, and disposable
  local indexes
- **Owner:** core pack maintainers

## Alternatives considered

- **Keep one JSONL corpus.** Rejected because it remains hot and does not model
  reconciled current state without replay.
- **Use JSONL per topic.** Rejected because immutable revisions still require a
  materialized current view and compaction policy.
- **Commit a database.** Rejected because it adds tooling and binary merge
  costs while obscuring review.
- **Do not commit a topic map.** Rejected because every supported reader would
  otherwise need to enumerate and parse all topic bodies before routing.

## References

- [RFC-0077](../rfc/0077-distill-knowledge.md)
- [Knowledge capture architecture](../architecture/knowledge-capture.md)
