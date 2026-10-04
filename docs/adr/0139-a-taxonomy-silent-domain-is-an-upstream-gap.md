# ADR-0139: A taxonomy-silent domain is an upstream gap, never a build-time value

- **Status:** Accepted
- **Date:** 2026-10-04
- **Areas:** experience, packaging
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0130 D2
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0130 (the gap-routed handoff whose gap sources this widens); ADR-0128 (design-system resolves project values); ADR-0132 (visual-target confirmation)

## Decision summary

- **Decision:** We will treat a visual domain the surface needs, on which a resolved token taxonomy is silent — no resolved value and no `unresolved` record — as a third upstream-gap source: the build holds that axis and routes it to whoever produced the taxonomy as `domain-completion-required`.
- **Because:** no rung below a resolved taxonomy may fill the axis (ADR-0130 D3), and no gap source named it either, so the contract left the build with no legal move and it invented values.
- **Applies to:** the frontend-engineering visual-authority rules and the frontend entrypoint; design-system's own rule that a taxonomy addresses every domain is unchanged.
- **Tradeoff accepted:** a surface built from an incomplete taxonomy ships with no author-set value on that axis — the user agent's default applies — until the taxonomy's producer completes it.
- **Revisit if:** adopters routinely receive taxonomies that omit a domain on purpose because the product does not need it, and the hold starts blocking work no one owes.

## Context

ADR-0130 makes the design-to-build handoff gap-routed. D2 names exactly two
gap sources: a resolved direction beside a named-skip taxonomy slot that no
incumbent covers, and a conforming taxonomy that records a needed domain
unresolved. D3 lets a lower rung fill an axis only when it is the accepted
owner of it.

A third case falls between them. A taxonomy resolves, but says nothing about a
domain the surface needs — typography, say. D3 forbids every lower rung from
filling it: the incumbent covers nothing that is absent, the fallback is gated
on no taxonomy resolving, and `local-premise` is standalone-only. D2 does not
name it as a gap. So the contract has no legal outcome, and an implementer
decides alone.

That happened. In a browser-backed golden-path run of the frontend skill, the
taxonomy supplied colour and spacing only; the implementer invented a type
scale, stroke widths and weights, labelled them "flagged for upstream supply",
and shipped them. design-system already treats this shape as a defect —
"Unresolved is not silence" — so the gap is in the consumer's contract, not
the producer's.

## Decision

- **D1:** A domain is **taxonomy-silent** when a resolved taxonomy neither
  supplies a value the surface needs in that domain nor records the domain
  `unresolved`. The test is per value: a domain the taxonomy lists with a rung
  but gives no value for is silent on every value the surface needs.
- **D2:** A taxonomy-silent domain is an upstream gap, joining ADR-0130 D2's
  two sources. The build holds that axis, sets no value for it, and routes it
  to whoever produced the taxonomy — the taxonomy records no owner for a domain
  it never mentions — under the existing operation kind
  `domain-completion-required`.
- **D3:** A surface **needs** a domain when its implementation would
  otherwise set a value in it. A domain the surface does not use — no imagery,
  so no graphic language — is not silent, and holds nothing.

Every other ADR-0130 decision stands unchanged.

## Consequences

- An implementer facing an incomplete taxonomy has one legal move, and it is
  the same move the explicit `unresolved` case already takes.
- The evidence manifest records the held domain, so a reviewer sees an
  incomplete taxonomy rather than invented values passing as resolved.
- A surface can ship with no author-set type, leaving the user agent's
  default in place, until the taxonomy's producer supplies it. That is visible, and
  owned, rather than silently decided.
- Golden eval prompts that extract only some domains now expect a hold for
  the rest, or must supply them.
- **Revisit if:** adopters routinely receive taxonomies that omit a domain on
  purpose because the product does not need it, and the hold starts blocking
  work no one owes.

## Confirmation

- **Mode:** lint/CI
- **Signal:** the roster golden-path walk holds a taxonomy-silent domain as
  `domain-completion-required`, and the frontend pack's upstream-gap tests
  read three gap sources from the installed rule table.
- **Owner:** frontend-engineering pack maintainer.

## Alternatives considered

- **Allow a bounded provisional value, recorded and routed upstream.**
  Rejected: it lets the build decide an axis design owns, which ADR-0130
  exists to prevent; "provisional" values ship and stick.
- **Treat silence as non-conforming and refuse the whole read.** Rejected:
  it throws away every domain the taxonomy did resolve, and a refusal halts the
  mode rather than holding one axis.
- **Leave the contract as is.** Rejected: the browser-backed run showed an
  implementer filling the hole with invented values.

## References

- ADR-0130, ADR-0128, ADR-0132.
- `packs/experience-design/.apm/skills/design-system/SKILL.md` — "Unresolved is not silence".
