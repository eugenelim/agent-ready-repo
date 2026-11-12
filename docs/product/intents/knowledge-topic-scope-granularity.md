# Knowledge topic scope granularity

- **Slug:** `knowledge-topic-scope-granularity`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

A scoped knowledge enquiry returns the topics that bear on the queried area,
rather than an arbitrary slice of a tier too large for the envelope.

## Opportunity

Repairing malformed scopes made every topic matchable, which exposed the next
constraint: the scope vocabulary is coarser than the envelope. In this
repository 17 active topics include the repository root (`.`) in their scopes
and 24 include `tools`; six have exactly `["tools"]`. A broad specificity tier
can exceed the twelve-body envelope, so the tiebreak decides which are seen.

**Current truth 2026-11-12:** the store holds 101 topics: 95 active and six
retired. Of the active topics, 17 include root and 24 include `tools`, with two
in both sets: 39 distinct broad-scope candidates. Only six are tools-only.
Current reachability needs a reproducible before-and-after measurement over a
recorded, fixed query set covering both existing and proposed scopes. The old
query set is absent from the repository and supplies no current baseline.

No ranking rule resolves this: topics tied at one specificity cannot all fit
twelve slots. It is a property of how the corpus is scoped, not of the matcher.

## Assumptions

- The remedy is curation — scoping topics to the region a reader would ask
  about — not a change to matching or to the envelope size.
- Enquiry ordering has no relevance ranking today; adding one is a separate
  and smaller change that does not resolve a tie within a tier.

## Source

- Mode: repo-origin

## Readiness

Route: direct-light curation, one session, no code change. Re-measured 2026-11-12 from `docs/knowledge/topics`: 95 active topics, 17 including root, 24 including `tools`, and six tools-only. Review the 39 distinct broad-scope candidates and narrow only scopes whose applicability supports it; record reasons for retained broad scopes. Agent-only proof: record a fixed query set covering existing and proposed scopes, then run `project_knowledge.py --enquire` with `risk=routine` and the applicable competency questions against the before and after committed snapshots. Enquiry reads committed state, so uncommitted edits are not an after measurement. Compare `receipt.selected_topics`; no previously reachable topic may become unreachable without a recorded reason. Rebuild `docs/knowledge/topics.index.json` with `knowledge_store.rebuild_topic_map(repo_root)` and commit the topics and derived map in the same snapshot. A shared measurement tool is not a prerequisite for this check.

## Non-goals

- Changing the matcher, the envelope size, or adding relevance ranking.
- Deleting or merging topics; only their scopes change.

**Riskiest assumption:** the remedy is curation alone, with no matcher change needed. Test it agent-only by comparing enquiry results over the recorded query set against before and after committed snapshots; that measurement remains required.
