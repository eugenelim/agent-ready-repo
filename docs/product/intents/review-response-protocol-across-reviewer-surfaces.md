# Review-response protocol across reviewer surfaces

- **Status:** Draft
- **Kind:** outcome
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** work-loop-review-economics — [Work-loop review economics](work-loop-review-economics.md)

## Outcome

- **Steerable input:** Carry the review-response protocol that
  [`docs/specs/acceptance-criteria-set-construction/`](../../specs/acceptance-criteria-set-construction/spec.md)
  ships into `new-spec` out to the other surfaces that produce or receive review
  findings — the `shaping-reviewer` subagent first, then the reviewer and
  adjudication mechanisms across the packs.
- **Lagging outcome:** A sustained finding is answered with the response that
  fits it, and the answer is recorded with its reason, rather than repaired by
  default because repair is the only move the surface names.
- **Guardrail:** No surface gains authority to block on the protocol. Naming the
  available responses is guidance to an author; it never becomes a gate, a
  score, or a refusal. Blocking on a derived review signal is the
  consequence-bound blocking already measured and killed in
  [work-loop review economics](work-loop-review-economics.md).

## Opportunity

A6 established that the eight responses to a sustained finding — repair, narrow
the claim to what its check reaches, cut the item, dismiss with the reason
recorded and re-present, repair the generator rather than the instance, route to
an existing owner, bound out of scope with a named follow-on, and accept with
the reason it is proportionate — are a protocol an author needs stated, because
a surface that names no alternative leaves repair the default by omission. Two
of A6's own criteria were cut, one was narrowed, and one finding was bounded and
deferred, only because the responses were enumerated.

That protocol lands in `new-spec`, which is the authoring side. The receiving
side is unaddressed. `shaping-reviewer` is the first surface to carry it: it
produces the findings a spec author answers, and it has no statement of what a
legitimate answer is, so a finding it sustains reads as an instruction to edit.

A second, distinct obligation belongs on the reviewer side rather than the
author side. **A reviewer must not relitigate a decision the brief records as
settled.** A late finding against a real pre-existing defect is legitimate and
useful; re-opening an owner decision is neither, and the two must be separated
so the author can refuse one without dismissing the other.

## Boundary

- Includes `shaping-reviewer` first, then a survey of the reviewer and
  adjudication surfaces across the packs — `adversarial-reviewer`,
  `quality-engineer`, `security-reviewer`, `design-reviewer`, the
  experience-design and discovery reviewers, and `finding-adjudicator` — and
  whichever of them the survey shows would change behaviour.
- Excludes re-deriving the protocol. A6's spec owns the eight responses and
  their definitions; this intent carries them and never restates them into a
  second home.
- Excludes any blocking, scoring or refusal behaviour on any surface.
- Excludes `new-spec`, which A6 delivers.

## Owner

- eugenelim, Platform Core maintainer.

## Unresolved questions

- Does a reviewer surface need the response list at all, or only the
  no-relitigation rule? The responses are the author's move; a reviewer that
  enumerates them may be writing the author's answer for them.
- Is the settled-decision boundary a reviewer rule, a brief obligation, or both?
  Today it lives only in whatever the brief's author happens to write.
- Which of the pack reviewers have their own finding-response prose already, and
  would gain a second home rather than a first one?

## Source

- Mode: repo-origin
- Locator: docs/specs/acceptance-criteria-set-construction/spec.md
- Authority: repo-origin
