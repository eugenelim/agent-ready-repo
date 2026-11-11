# ADR-0140: Shaping entry point: one verb-mode `intent` skill with a stateless route mode

- **Status:** Accepted
- **Date:** 2026-10-10
- **Areas:** shaping
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0107 (the proposal this records — D1 and D2); RFC-0099 (its generic-shaping-skill exclusion, superseded in part by RFC-0107's erratum); RFC-0053 (the discovery loop that becomes the supervised route)

## Context

- Hosts preload every installed skill's name and description into a fixed listing
  budget.
  - Codex allows 8,000 characters when it cannot size the context window. Over budget,
    it shortens descriptions and then drops skills.
  - The 14 shaping skills in `product-engineering` used 8,401 description characters on
    2026-10-10.
- Three of those skills share the verb *frame*.
- The choice between the short, longer, and supervised shaping routes existed only as
  prose, copied in five places.
- A forced-choice probe over 146 eval queries found that one verb-mode description
  selects as accurately as the narrow skills: 99% on Opus and 98% on Sonnet, against 98%
  and 99% for today's listing.

## Decision

We will reach the shaping stage through one `intent` skill whose verb modes each load
only when chosen, with a read-only route mode and `discovery-loop` kept as the
supervised route.

- **D1:** `intent` replaces the separate shaping skills. Its body lists every mode, and
  each mode's procedure loads only when that mode is chosen.
- **D2:** With no verb, `intent` runs a read-only route mode. It picks a route from
  observable facts in the request, names the first mode, and asks one question when the
  facts conflict.
- **D3:** Route mode holds no run state, retries, or gate control. It selects guidance
  and stops.
- **D4:** `discovery-loop` stays a separate skill and is the supervised route. Route mode
  hands it a raw whole-product idea. Its gates call `intent` modes.
- **D5:** `align-value-stream` stays a separate skill, because it coordinates delivery
  across repositories rather than shaping.

## Decision drivers

- Listing cost within host budgets.
- Selection accuracy no worse than the narrow skills.
- No return of an overloaded, stateful controller.

## Consequences

**Positive:**
- The shaping listing falls from 8,401 to about 2,640 description characters.
- The route choice has one owner that runs.
- Mode names are unique, which removes the *frame* collision.

**Negative:**
- Twelve skill names retire with no alias, which breaks adopters' prompts and scripts
  that name them.
- Selection now has a second step: the model picks `intent`, then a mode.
- Five modes start with no trigger evidence.

**Revisit if:** the held-out activation run in RFC-0107 fails its threshold on a
required host, or a change gives route mode state, retries, or gate control.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** the activation run meets RFC-0107's threshold, and route mode's
  procedure writes no state and invokes no gate.
- **Owner:** eugenelim

## Alternatives considered

- **Do nothing:** over a host budget on its own, which fails the listing-cost driver.
- **Trim descriptions only:** the verb collision and the copied route prose remain.
- **Fold `discovery-loop` into `intent` too:** the most common request would load a
  stateful loop, which breaks the no-controller driver.

## References

- [RFC-0107](../rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md)
- [Skill-routing survey](../product/findings/pe-skill-routing-survey.md)
