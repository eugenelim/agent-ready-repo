# Knowledge topic scope granularity

- **Status:** Draft
- **Level:** feature

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

No ranking rule resolves this: twenty topics tied at one specificity cannot fit
twelve slots. It is a property of how the corpus is scoped, not of the matcher.

## Assumptions

- The remedy is curation — scoping topics to the region a reader would ask
  about — not a change to matching or to the envelope size.
- Enquiry ordering has no relevance ranking today; adding one is a separate
  and smaller change that does not resolve a tie within a tier.

## Source

- Mode: repo-origin
