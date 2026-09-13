# ADR-0111: Intent review splits into a mechanical well-formedness check and a narrowed assumption attack

- **Status:** Accepted
- **Date:** 2026-09-11
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0099 § 5, ADR-0042, `docs/specs/shaping-review-contracts/spec.md`

## Decision summary

- **Decision:** We will split intent-stage review into two narrow mandates — a near-mechanical
  well-formedness check in `shaping-reviewer` `intent` mode, and a narrowed assumption attack in a
  new `adversarial-reviewer` `intent` mode — each with an output vocabulary that cannot express a
  rewrite.
- **Because:** an intent is too thin to carry a spec-shaped rubric, and a severity-and-fix output
  turns review of a bet into opinion traffic.
- **Applies to:** intent-stage review only. `delivery-brief` and `spec` modes are unchanged.
- **Tradeoff accepted:** intent mode loses `Clean`, so every caller must branch on mode and read
  "no `MALFORMED` lines" as the pass.
- **Revisit if:** intent-mode `MALFORMED` output stops catching the malformations that reach brief or
  spec review, or adversarial intent mode returns empty on intents that later fail on their riskiest
  assumption.

## Context

RFC-0099 § 5 gave `shaping-reviewer` one rubric shape across three modes and one result vocabulary,
`Clean` | `Findings`, across all of them. The shipped implementation grew a failure-mode table
written against spec-shaped artifacts: derivable enumerations, floating citations, unframed
quantities, one-sided contracts, decorative precision.

An intent is thin by construction — an outcome, an opportunity, non-goals, assumptions, an altitude,
and children. Most of those rows cannot fire on it. The rows that do fire ask an intent to carry
spec-grade craft, producing findings about wording on an artifact whose only job is to name a bet.

A severity-ordered list with a `Fix:` per finding also invites the reviewer to rewrite the bet. At
intent altitude there is no contract to measure a rewrite against, and `Clean` on a bet reads as
ratification that no cold reviewer can give.

Two different jobs were riding one rubric: *is this artifact well-formed enough to shape further*, and
*is the bet in it risky in a way nobody has named*.

## Decision

We will split intent-stage review into two narrow mandates, each with an output vocabulary that
cannot express a rewrite.

1. `shaping-reviewer` `intent` mode checks well-formedness, not quality, across six conditions: the
   statement is an outcome and not a solution; non-goals are present; the riskiest assumption is
   named; altitude is consistent with the parent it names; the decomposition partitions the
   artifact's own outcome with no overlap and no gap; the owner is the artifact's own. Two of the
   six are conditional on what the artifact declares, because an artifact that cannot have a
   relation is not malformed for lacking it: the altitude condition applies only to an intent that
   names a parent, a parent being an optional attribution at every level; and where an intent lists
   no decomposition, the children condition fires only above the leaf of the recognized level set
   at `Status: Accepted`, since framing precedes decomposition and this review runs at framing. A
   level the mode cannot place suppresses that absence branch alone. `intent` mode does not run
   the failure-mode table, which stays with
   `delivery-brief` and `spec` mode unchanged. Wrong owner still outranks criterion craft: its token
   is emitted alone and suppresses the other five.
2. Intent-mode output is `MALFORMED(<field>)` per failed condition, or nothing. No severity bucket,
   no `Fix:`, no `Clean`. `delivery-brief` and `spec` modes keep `Clean` | `Findings`. A condition the
   supplied packet cannot settle is not a pass: it emits its own token, so absent evidence fails
   closed.
3. `adversarial-reviewer` gains an `intent` mode whose mandate is to attack the riskiest assumption
   and the non-goals. Its only two outputs are an open question with a named decider, or a validation
   hook — a kill condition plus the real-world activity that would trigger it. No blockers, no
   rewrites, no "consider also". Nothing to say about the riskiest assumption means empty output.
4. Both intent modes run the six-predicate self-check before emission: observation, authority,
   reachability, existing handling, consequence, proposed mechanism.
5. `de-risk-intent` never dispatches `adversarial-reviewer`. That skill authors the kill condition
   itself, so a reviewer emitting validation hooks into it would be marking its own homework.
6. Unchanged: no independent retrieval, the caller-supplied packet stays attributed untrusted data,
   and neither reviewer holds lifecycle authority.

## Decision drivers

- **Fit to artifact thinness** — a rubric row that cannot fire on the artifact under review is noise.
- **An output vocabulary that cannot express a rewrite** — the shape of the output, not reviewer
  restraint, is what keeps a cold reviewer out of the author's bet.
- **One owner per question** — well-formedness and risk are different judgments with different
  stances.
- **Mechanizability** — well-formedness is decidable by reading the artifact; the risk in a bet is
  not.

## Consequences

**Positive:**

- Intent-mode checks are decidable, so two reviewers reach the same verdict on the same artifact.
- An empty adversarial intent result becomes a real outcome rather than a suspicious one.
- Callers gain a cheap gate: any `MALFORMED` line means send it back; no lines means shape on.

**Negative:**

- Two output vocabularies now live in `shaping-reviewer`, so every caller must branch by mode.
- `Clean` disappears from intent mode, so `intake-intent` and `frame-intent` can no longer gate on
  it; each needs its own "no `MALFORMED` lines" reading plus explicit human confirmation.
- Quality problems in an intent — a vague outcome, a decorative metric — go unflagged at intent
  review and surface later, at brief or spec altitude.
- Frozen RFC-0099 § 5 and the shipped `shaping-review-contracts` spec keep the superseded intent rows
  in their bodies; only their `Status` lines point here.

**Revisit if:** intent-mode `MALFORMED` output stops catching the malformations that reach brief or
spec review, or adversarial intent mode returns empty on intents that later fail on their riskiest
assumption.

### The no-new-shaping-surface boundary is mode-scoped

The accepted intent behind RFC-0099 forbids "no common script, separate durable shaping-review
state, generic shaping loop, or fourth `shaping-reviewer` mode", and preserves the three-lens
ceiling on the *code-review* gate. It sets no limit on how many independent reviewers one shaping
artifact passes, and the boundary immediately after it already admits the adversarial reviewer's
full-diff second read as correctness evidence.

That boundary is therefore read as mode-scoped, and this decision conforms to it as built: three
`shaping-reviewer` modes, no shaping state, no shaping loop. The second intent-stage read is
optional, advisory, and establishes nothing — `Accepted` is gated by the well-formedness result plus
explicit human confirmation alone — so it adds a reviewer, not a gate. The owner confirmed this
reading on 2026-09-11, after the adversarial intent mode raised it as an open question on its first
real target.

## Confirmation

- **Mode:** lint/CI
- **Signal:** the core pack's shaping-review contract test asserts intent mode's six well-formedness
  fields, the `MALFORMED`-only output rule, the heading that scopes the failure-mode table to the
  other two modes, and adversarial intent mode's two output types.
- **Owner:** core pack maintainer.

## Alternatives considered

- **Keep one rubric and scope its rows by artifact kind.** Rejected against *one owner per question*:
  row-scoping still leaves one reviewer judging craft and holding the bet's risk, and a
  severity-plus-`Fix:` output still invites rewrites.
- **Drop intent-stage review entirely.** Rejected against *mechanizability*: the six
  well-formedness conditions are cheap and catch real malformations — a solution masquerading as an
  outcome, children that overlap — which cost far more to fix at spec altitude.
- **Give `shaping-reviewer` intent mode the assumption attack too.** Rejected against *one owner per
  question*: an adversarial stance contaminates a mechanical check, and a reviewer that can emit
  either output will emit the interesting one.
- **Emit well-formedness as a normal `Findings` list at blocker severity.** Rejected against *output
  vocabulary*: severity implies a judgment gradient that does not exist here, and `Fix:` reopens the
  rewrite path `MALFORMED` is chosen to close.

## References

- RFC-0099 § 5 — `docs/rfc/0099-cut-before-adding-and-artifact-shaping.md:345-384`, the superseded
  three-mode rubric and single result vocabulary.
- `docs/specs/shaping-review-contracts/spec.md` — Shipped; AC1, AC2, and AC3 carry the superseded
  intent rows.
- `docs/CONVENTIONS.md` § *Superseding a frozen document* — the one-way `Status`-line pointer this
  ADR receives from that spec and its plan.
