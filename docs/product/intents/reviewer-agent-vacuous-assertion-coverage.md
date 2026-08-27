# Reviewer agent vacuous-assertion coverage

- **Status:** Draft
- **Level:** feature

## Outcome

The quality and security reviewers catch the assertion shapes that pass while
proving nothing, so a test that cannot fail is reported rather than counted as
coverage.

## Opportunity

A distillation pass produced twelve topics, five of which are one family:
assertions that report confidence without being able to red. The quality
reviewer already carries the mutation-testing mindset and the tautological-test
shape, but not the four the pass surfaced, and the security reviewer carries no
control-pin obligation at all — the shape with the demonstrated consequence,
where deleting the method a control lived in left two gates green while a
bearer token would have been forwarded across an origin change.

Both reviewers ship to adopters, so the gap travels with the pack.

## Assumptions

- The four shapes are: an empty-set assertion with no positive control; a
  negative case green because a collaborator was left unstubbed; a control
  pinned by substring-matching source text rather than by observing behaviour;
  and a prose enumeration standing in for a captured baseline.
- The security reviewer gains the obligation to verify a control pin by
  deleting the control and confirming the test reds.
- Prose-only change to two agent definitions; no new script or gate.

## Source

- Mode: repo-origin
