# ADR-0089: Decision weight trims the RFC pre-handoff gate: RFC-0054 D1 over its implementing spec

- **Status:** Accepted
- **Date:** 2026-08-19
- **Decision-makers:** eugenelim
- **Consulted:** adversarial review (independent, three rounds to clean)
- **Supersedes:** **AC5 and AC6 only** of
  [`docs/specs/new-rfc-two-humans/`](../specs/new-rfc-two-humans/spec.md) — their
  rule that "No tier drops or weakens a gate check"; every other acceptance
  criterion in that spec stands. Also supersedes the **all-tier scope** of
  refinement 3 in [`docs/specs/new-rfc-fresh-context/`](../specs/new-rfc-fresh-context/spec.md)
  — the no-context readability check itself stands, but it is now
  property-triggered rather than mandatory at every tier; that spec's other
  three refinements stand.
- **Related:** [RFC-0091](../rfc/0091-right-size-rfc-governance.md) D3 (the
  accepted proposal this records); RFC-0054 (the frozen RFC whose D1 text wins);
  RFC-0014 (the frozen RFC that mandated the five gate checks)

## Decision summary

- **Decision:** The RFC `Decision weight` changes what the pre-handoff gate
  obliges, not only how long the draft is. A `light` RFC runs the completeness
  checklist and one adversarial pass; it does not run an iterative
  adversarial loop and does not run an automatic fresh-reader readability
  review. Citation-integrity and verify-before-you-assert apply at every tier,
  scoped to the citations and checkable claims the proposal actually makes.
- **Because:** RFC-0054's own D1 text already specified this, and its
  implementing spec resolved the question in the opposite direction.
- **Applies to:** the `new-rfc` workflow shipped in `governance-extras`, and
  every RFC authored through it.
- **Tradeoff accepted:** a `light` RFC receives one review pass rather than a
  loop, so a defect that a second pass would have caught can reach a reviewer.
- **Revisit if:** `light` RFCs start reaching reviewers with defects that an
  iterative pass would plainly have caught, or if the share of `light` RFCs
  stays near zero after this ships.

## Context

Three accepted authorities disagreed, and the disagreement was invisible until
someone read all three.

- **RFC-0014** (Accepted, Frozen) mandated five pre-handoff gate checks:
  citation-integrity, verify-before-you-assert, per-subpoint backing, the
  completeness checklist, and an `adversarial-reviewer` dispatch re-run until
  clean.
- **RFC-0054** (Accepted, Frozen, and later than RFC-0014, over which it
  explicitly claims partial supersession) introduced
  `Decision weight: light | standard | heavy`. Its D1 text describes light's
  gate as "completeness checklist + one adversarial pass", and it explicitly
  deferred "the exact per-tier gate-trim table … to the implementing spec".
- **`docs/specs/new-rfc-two-humans/` AC5 and AC6** (Shipped) resolved that
  deferred question the other way: "No tier drops or weakens a gate check",
  anchored on RFC-0014's five.
- **`docs/specs/new-rfc-fresh-context/`** (Shipped) then added a **sixth**
  mandatory check at every tier — a second, separate generic-subagent
  dispatch. No RFC authorised it.

The result: a `light` RFC ran six mandatory checks including two separate
subagent dispatches, one of them re-run until mechanically clean. Measured
outcome across the corpus: **3 of 91 RFCs carry `light`** — the tier exists on
paper and is effectively unused, because choosing it bought nothing.

## Decision

Adopt RFC-0054's D1 text as the per-tier obligation set, and define its
proportional form:

| Weight | Obligations |
| --- | --- |
| every tier | citation-integrity and verify-before-you-assert, scoped to citations and checkable claims actually made; neither justifies manufactured research |
| `light` | one focused decision, compact rationale, the completeness checklist, one adversarial pass, no automatic fresh-reader readability review |
| `standard` | full argument, proportionate research, decision-by-decision backing, the completeness checklist, adversarial review re-run until clean |
| `heavy` | `standard`, plus applicable reversal / compatibility / trust-model analysis, a security review when a security boundary or trust model is involved, and validation planning where the uncertainty is empirical |

The fresh-reader readability review runs only when the proposal coins
vocabulary of its own, relies on cross-references to sibling proposals a reader
may not have read, or is written for adopters or contributors who did not take
part in drafting it.

The weight vocabulary stays exactly `light | standard | heavy`. Historical RFC
metadata is not rewritten: 51 of 91 RFCs carry no weight field and 11 carry
free text, including the off-vocabulary `medium` (RFC-0073) and `major`
(RFC-0076). Those bodies are frozen and stay as they are.

## Decision drivers

- **RFC-0054 is the later authority and already said this.** Choosing its D1
  text is not a reversal invented now; it resolves a conflict between two
  accepted documents in favour of the more recent one.
- **A tier that changes nothing is not a tier.** 3-of-91 usage is the evidence
  that the trim was needed for the field to mean anything.
- **The two checks that survive at every tier are the two that protect the
  reader from false claims.** Trimming review *effort* is proportional;
  trimming *truthfulness* is not, so citation-integrity and
  verify-before-you-assert do not scale down.
- **The sixth check was never authorised by an RFC.** Making it
  property-triggered corrects a spec-level addition, and needs no reversal of
  any RFC.

## Consequences

**Positive.** A narrow, reversible proposal costs roughly what it is worth. The
weight field becomes a real signal rather than a label. The two spec-level
rules that outran their authority are corrected at the right altitude.

**Negative.** A `light` RFC gets one adversarial pass, so a defect a second
pass would have caught can reach a reviewer. Authors now choose a weight that
has consequences, which invites under-classification to buy a cheaper gate —
the routing question ("does this need an RFC at all?") and the weight question
are deliberately separate, but a motivated author can still pick `light` for
something that warranted `standard`.

**Residual, accepted.** Someone who greps mid-file in either superseded spec
lands on the old all-tier rule with no pointer in view; per
`CONVENTIONS.md § Superseding a frozen document` rule 4, the frozen bodies are
not patched. The operative instruction lives in the Living skill file at the
point of use.

## Confirmation

- **Mode:** lint/CI — the pack's LLM-judge eval rubric.
- **Signal:** `packs/governance-extras/.apm/skills/new-rfc/evals/evals.json`
  eval 9 asserts that `light` does not mechanically require external research, a
  spike, or two separate subagent reviews; that `standard` re-runs review until
  clean; that `heavy` adds the stronger controls; that citation-integrity still
  applies at every weight; and that weight selection does not itself decide
  whether an RFC is needed.
- **Owner:** eugenelim.

## Alternatives considered

- **Leave the all-tier gate in place** (do nothing). Preserves every check at
  every tier and needs no supersession — but leaves `light` unusable, which is
  the problem. Rejected on the 3-of-91 evidence.
- **Trim only the two spec-level rules**, leaving RFC-0014's five intact at
  every tier. Lowest burden: no RFC-level resolution needed at all. Rejected
  because `light` would still run adversarial-review-until-clean, so the tier
  stays close to `standard` and the usage problem persists.
- **Drop the adversarial pass entirely at `light`**, closer to Rust's and Go's
  posture where a light proposal is just an issue. Rejected: it reverses
  RFC-0014's mandatory-reviewer check outright with no supporting accepted
  text, and one pass is the smallest change that makes the tier real.
- **Remove the weight tiers** and route ceremony from the proposal's shape
  instead. Rejected: it discards an accepted vocabulary that 40 RFCs already
  carry, for no gain this decision needs.

## References

- [RFC-0091](../rfc/0091-right-size-rfc-governance.md) — the accepted proposal,
  decision D3.
- `docs/specs/new-rfc-two-humans/spec.md` AC5, AC6 — the superseded rule.
- `docs/specs/new-rfc-fresh-context/spec.md` refinement 3 — the superseded
  all-tier scope.
- `packs/governance-extras/.apm/skills/new-rfc/SKILL.md` step 6 — where the
  operative per-tier obligations now live.
