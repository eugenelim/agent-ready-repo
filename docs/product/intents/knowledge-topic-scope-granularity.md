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
repository seventeen topics apply repository-wide and twenty share a single
base, so one specificity tier alone exceeds the twelve-body envelope and the
tiebreak decides which are seen. Measured across the candidate query set,
sixty-nine of seventy-six topics are returned by some query and seven never
are.

Re-counted on 2026-11-04, the store holds 94 active topics: 17 apply
repository-wide and 24 share the `tools` base. The 69-of-76 and 7-never-returned
figures come from the earlier query-set measurement and have not been re-run.

No ranking rule resolves this: twenty topics tied at one specificity cannot fit
twelve slots. It is a property of how the corpus is scoped, not of the matcher.

## Assumptions

- The remedy is curation — scoping topics to the region a reader would ask
  about — not a change to matching or to the envelope size.
- Enquiry ordering has no relevance ranking today; adding one is a separate
  and smaller change that does not resolve a tie within a tier.

## Source

- Mode: repo-origin

## Readiness

Route: direct-light curation, one session, no code change. Re-measured 2026-11-05 from `docs/knowledge/topics`: 94 active topics, 17 scoped repository-wide, 24 on the `tools` base alone. Rescope those topics to the area a reader would ask about. Agent-only proof: run `project_knowledge.py --enquire` for the scope set before and after and compare which topics are reachable; no topic that was reachable becomes unreachable without a recorded reason. The `69 of 76` figure still comes from the earlier query set, which is not in the repository; the before-and-after run replaces it. The shared measurement tool in the closeout brief can reuse this check.

## Non-goals

- Changing the matcher, the envelope size, or adding relevance ranking.
- Deleting or merging topics; only their scopes change.

**Riskiest assumption:** the remedy is curation alone, with no matcher change needed. Tested agent-only by comparing enquiry results over the scope set before and after rescoping.
