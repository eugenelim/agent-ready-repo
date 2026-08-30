# Review-and-validation guidance for spec authoring

- **Status:** Draft
- **Level:** feature

## Outcome

`new-spec`'s review guidance names four disciplines that currently exist only as
session practice, so a reviewer's output is triaged rather than absorbed: cheap
measurement is preferred to another review round when the claim is about what
code does or what inputs exist; each finding carries its origin; a spec gate
states what it does not check; and a finding is tested for reachability in the
feature's scope before it is acted on.

## Opportunity

Four disciplines were distilled from a spec review that ran roughly sixteen
rounds, and none is written down in any shipped skill, `docs/CONVENTIONS.md`, or
any ADR or RFC:

- **Measurement over review rounds.** Sixteen rounds found sentence-level
  defects; two spikes found an unimplementable mechanism, a wrong bound origin,
  and a corpus shape gap. One of them took thirty seconds to prove. Eight rounds
  ran against prose describing work nobody had started — zero gates, zero
  compiles, zero measurements.
- **Origin attribution.** Asking whether each finding comes from the artifact or
  from the previous round's fix is what surfaced one round introducing six of its
  own blockers, which was the signal to stop editing prose and spike.
- **Gate-scope disclosure.** A traceability lint passed on acceptance-criterion
  numbering of `1 2 3 4 5 4 5 … 23 25 24` — duplicated and misordered. A green
  gate is evidence about the gate.
- **Finding reachability.** A threat finding real for one install route was inert
  for another; relaying it without checking applicability nearly drove an
  unnecessary RFC amendment.

The same session that distilled these confirmed all four in practice: origin
attribution produced the round-3 stop signal, and reachability checking refuted
five of twelve findings including one whose prescribed remedy would have
contradicted the template's own output-channel rule.

## Assumptions

- These are review-guidance rules for `new-spec` step 6 and its neighbours, not
  criterion-shape rules; the criterion-shape work ships separately in
  `docs/specs/spec-authoring-discipline/`.
- Gate-scope disclosure concerns what `lint-spec-status.py` does and does not
  check; it adds no new lint and ships no lint to an adopter repository.
- No numeric threshold is introduced. Two were proposed by peer sessions during
  the parent work and both were rejected on measurement as calibrated to one
  document.

## Source

- Mode: repo-origin
- Locator: docs/specs/spec-authoring-discipline/spec.md
- Revision: local-2026-08-28
