# Non-functional requirements — cross-cutting concerns checklist

A design doc that names the function but not the cross-cutting
properties is incomplete. Walk this list when *Cross-cutting* in the
rubric fails; surface the dimensions that matter for this proposal,
skip the ones that don't.

Naming a concern as *not material* is fine — *silently* skipping it is
not.

## Performance and scale

- What's the expected request shape? RPS at p50 and at peak; payload
  size; tail-latency tolerance.
- What's the failure-budget shape? (SLO if one exists; otherwise
  what counts as "down" to a user.)
- What changes at 10× volume? At 100×?
- Is there a performance budget committed up front — a latency,
  throughput, or resource target the design must meet? "Fast enough"
  left undefined can be neither met nor missed. State it as a testable
  claim (`quality-attribute-scenarios.md`).

### Optimizing — earn each optimization against the budget

When the proposal trades simplicity for speed, the reasoning is owed,
not just the mechanism:

- **Measure before optimizing.** Name the evidence the bottleneck is
  real and where it sits — not a guess. Optimizing an unmeasured hotspot
  ships complexity for no proven gain.
- **Spend on the hotspot.** Most of the cost usually sits in a small
  fraction of the system. Optimize that fraction; leave the rest simple.
  Effort off the bottleneck buys nothing.
- **Weigh complexity against gain.** Every optimization carries an
  ongoing cost — harder to read, change, and operate. Name the gain, and
  whether it clears that cost against the budget. One that doesn't move
  the budget isn't worth its complexity.

## Availability and reliability

- What's the blast radius if this component fails — single user,
  tenant, region, fleet?
- What's the recovery shape — graceful degradation, retry, manual
  intervention, full outage?
- What dependencies become single points of failure?

## Security and trust

- Where do trust boundaries cross? (User → service, service →
  service, tenant → tenant, region → region.)
- What credentials, tokens, or secrets does this surface introduce
  or move?
- What new attack surface? Authn? Authz? Injection? Deserialization?
- Data classification — does this change what categories of data the
  surface handles?

## Privacy and data handling

- Personal data: collected, stored, processed, exported?
- Retention: how long, with what deletion guarantees?
- Residency: any obligations on where data lives?
- Consent: any flows that need explicit user opt-in?

## Observability and operability

- What signals (metrics, logs, traces) does this emit? Are they
  enough to debug at 3am?
- What dashboards or alerts change? Who owns them?
- How does an on-call engineer recognize this is the failing
  component?

## Cost

- One-time vs. recurring cost shape.
- What scales linearly with usage? What scales sub-linearly?
- Is there a free/cheap tier the design accidentally exits?

## Compatibility and migration

- Backwards compatibility surface — APIs, data shapes, file formats,
  configuration.
- Forward compatibility — what is this proposal locking us into?
- Migration shape — big-bang, phased, dual-write, shadow.

## Team and operational fit

- Who runs this in production? Do they have the skills?
- What new on-call surface does this create?
- What does *deprecation* look like in two years?

## Use, don't recite

This is a prompt for honest thinking, not a section template. Don't
paste the headings into the design doc unless they earn their place.
Surface the ones that matter; the rest go unmentioned.
