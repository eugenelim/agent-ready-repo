# Amendment 0001 — exempt the H1 title from the damaged-marker scan

- **Status:** Authorized
- **Date:** 2026-09-28
- **Scope owner:** eugenelim
- **Target:** `plan.md` § Design (LLD) → Behavior & rules, the liveness rule
- **Run:** 63804b99-bb0f-4f30-8405-0345af393fa0

## Owner authority

The scope owner was shown the defect, the proposed change, and the full cost of
the controlled amendment procedure — that it returns the run to
`SPEC-PLAN-DRAFTING`, sets both approved artifacts back to `Draft`/`Drafting`,
and re-runs the pre-EXECUTE reviews and both human approval gates — and
directed that the amendment proceed rather than shipping the defect as a
recorded follow-on.

## Why an amendment, and not the verification ledger

`work-loop/references/delivery-contract-lifecycle.md` admits an execution
*observation* to the ledger without amending either approved artifact, but
states that "a falsified settled decision is an error" and that "the
verification ledger is not a route for a settled decision that execution
falsified". Plan approval settled the liveness rule. Review then falsified one
arm of it. So the ledger is closed to this change and the controlled amendment
is the only route.

## The defect

The approved rule refuses `source-unreadable` when a visible preamble line
bears the token `Tombstone` case-insensitively yet does not parse as a
well-formed `Tombstone:` field. An H1 document title is a visible preamble line
that never parses as a field, so a live intent titled, for example,
`# Tombstone migration plan` is refused when a caller asks to rename it.

That is a false refusal of a valid source, against AC-0021's positive path. It
fails closed rather than open — the caller sees a fixed refusal token, not a
silent acceptance — and no file in `docs/product/intents/` triggers it today,
measured across all 157 on 2026-09-28. The exposure is therefore latent rather
than live, which is why shipping it as a follow-on was the alternative offered.

The rule's own next sentence already names the H1 title among the lines that
"is exempt and refuses nothing", so the approved text is internally
inconsistent for a title that bears the token. The adjudication recorded that
resolving that inconsistency in favour of the exemption changes the settled
rule and is the scope owner's decision, not the implementer's.

Two neighbouring cases were implementation drift rather than plan error and
needed no amendment: a line parsing as some *other* well-formed field whose
value contains the word — a `Slug` of `tombstone-migration`, or an annotation
bullet mentioning tombstones — was refused although the approved rule exempts
it. Those are repaired under the ordinary findings-remain path.

## What changes

The damaged-marker scan stops reaching a single leading H1 title. Both
damaged-marker arms otherwise stand unchanged: a token-bearing line that parses
as no field at all still refuses, and a `Reissued as:` or `Retired:` field
parsing while `Tombstone:` does not still refuses.

## Residual risk accepted

A tombstone whose marker is damaged *into* an H1 heading — `# Tombstone:
2026-09-28` — is no longer caught by the token scan. The writer this slice
ships emits `- **Tombstone:** …`, so reaching that state requires hand-editing a
tombstone into a heading, which is the same class of out-of-contract corpus
corruption as deleting a tombstone outright. `## Assumptions` already carries
that residual and no control here detects it.

## Provenance

The finding is F4 of the adjudicated post-gates adversarial review, retained
with the two other lenses' adjudications under
`.context/reviews/63804b99-bb0f-4f30-8405-0345af393fa0/`. That directory is
ignored, so this record — not the report — is the durable reference.
