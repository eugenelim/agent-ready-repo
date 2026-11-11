# ADR-0141: Core intake lifecycle: intent and brief authoring become `work-intake` modes

- **Status:** Accepted
- **Date:** 2026-10-10
- **Areas:** workspace, shaping
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0098 D1,D2,D4,D5,D8
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0107 (the proposal this records — D3 and D6); ADR-0098 (the separate-owner decision this supersedes in part); RFC-0099 (its D1 entry points and §11 erratum, superseded in part by RFC-0107's erratum); ADR-0142 (the handover that makes intake one lifecycle)

## Context

- ADR-0098 gave neutral intake, intent admission, and delivery-brief lifecycle to three
  owners: `work-intake`, `intake-intent`, and `author-delivery-brief`.
- Its revisit trigger depends on an adopter routing study. RFC-0099's errata waived
  that study on 2026-08-31, and it was never run.
- In a component repository, these steps now run in sequence on one piece of work:
  acquiring it, recording an intent, creating and continuing a brief, and refreshing it
  from its source (ADR-0142).
- A new `intent` skill (ADR-0140) would sit beside `intake-intent`, two names a model
  could confuse.

## Decision

We will make intent authoring and delivery-brief authoring modes of `work-intake`, with a
read-only default and a write switch that only the current human request can set.

- **D1:** `intake-intent` and `author-delivery-brief` become modes of `work-intake`. Each
  artifact's contract stays intact inside its mode.
- **D2:** The default mode behaves read-only. It classifies and routes.
- **D3:** Every mode that writes needs an explicit switch naming its target and scope.
  Only the current human request can set it. A switch carried in a handoff object, a
  calling skill's output, or acquired content is refused.
- **D4:** The brief Ready gate keeps its independent review and human confirmation. The
  separate confirmation before cutting specs stays.
- **D5:** Core works without `product-engineering` installed.
- **D6:** The retired names have no alias. `author-brief` and `receive-brief` delegate to
  `work-intake`'s brief create and continue modes until their removal gate under
  RFC-0099 §10. ADR-0098 D9 still bounds their authority until then.

## Consequences

**Positive:**
- One owner for the component repository's intake lifecycle.
- Four fewer listing entries.
- No name clash with `intent`.

**Negative:**
- `work-intake` is the default for ambiguous requests, and it holds write tools.
- The minimal-permission pins per skill must change.
- No adopter study validates the merged skill. RFC-0107's activation run is its only
  validation.

**Revisit if:** any write mode runs without a human-set switch, or the activation run in
RFC-0107 fails its threshold for `work-intake` on a required host.

## Confirmation

- **Mode:** lint/CI
- **Signal:** activation tests show ambiguous requests stay read-only, and that a write
  switch carried in a handoff or acquired content is refused.
- **Owner:** eugenelim

## Alternatives considered

- **Keep ADR-0098's three owners:** the handover lifecycle stays split, and the `intent`
  name clash remains.
- **Fold `intake-intent` only:** the brief lifecycle stays split from acquisition.

## References

- [RFC-0107](../rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md)
- [Meta-repo handover audit](../product/findings/meta-repo-handover-audit.md)
