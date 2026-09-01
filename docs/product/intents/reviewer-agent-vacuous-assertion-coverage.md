# Reviewer agent vacuous-assertion coverage

- **Status:** Draft
- **Level:** feature

## Outcome

The quality reviewer catches the assertion shapes that pass while proving
nothing, so a test that cannot fail is reported rather than counted as coverage.

## Opportunity

A distillation pass produced twelve topics, five of which are one family:
assertions that report confidence without being able to red. The quality
reviewer already carries the mutation-testing mindset and the tautological-test
shape, but not the four the pass surfaced. The source-substring control-pin
shape has the demonstrated consequence: deleting the method a control lived in
left two gates green while a bearer token would have been forwarded across an
origin change.

The quality reviewer ships to adopters, so the gap travels with the pack.

## Assumptions

- The four shapes are: an empty-set assertion with no positive control; a
  negative case green because a collaborator was left unstubbed; a control
  pinned by substring-matching source text rather than by observing behaviour;
  and a prose enumeration standing in for a captured baseline.
- Prose-only change to one agent definition; no new script or gate.

## Source

- Mode: repo-origin

## Amendment

Dropped 2026-09-01, before implementation. `docs/CONVENTIONS.md`'s
reviewer-model table, as amended by `9b9d470ef` (released core 2.20.0), gives
`quality-engineer` exclusive ownership of test strength — "whether an assertion
can fail". `quality-engineer.md` states the same exclusivity in its Test design
section. "Delete the control and confirm the test reds" is exactly that lens,
so giving it to `security-reviewer` would put a second owner on an exclusive
one. The substance is not lost: it landed as shape 3, "source-text control
pins", in the agent that owns the lens, carrying the same bearer-JWT incident.
The owner declined a compensating pointer in `security-reviewer.md`.
