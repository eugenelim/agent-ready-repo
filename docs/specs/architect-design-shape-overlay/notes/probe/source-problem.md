# Source problem — billing webhook ingestion subsystem

One brief, used verbatim for both arms. Frozen before either is authored.

## Situation

An existing SaaS product bills through a third-party payment provider. Today a
single endpoint in the monolith receives the provider's webhooks and updates
subscription records inline, in the request. That endpoint has grown to nine
event types, and three incidents in the last quarter traced back to it:

- A customer was double-charged after a retry the provider sent when our
  response timed out.
- A subscription showed as active for eleven days after the provider had
  cancelled it; nobody noticed until the customer called.
- A deploy during a provider outage lost roughly forty minutes of events, and
  reconstructing them took two engineers a day and a half against the
  provider's dashboard.

The team wants to carve webhook ingestion out of the monolith into its own
subsystem, owned by the billing team, with the monolith consuming whatever the
new subsystem produces.

## What the subsystem must do

- Receive webhooks from the payment provider and make their effects visible to
  the billing domain in the product.
- Keep working when the provider is slow or unavailable, and when the product's
  own database is briefly unavailable.
- Let an engineer answer, for any customer and any point in the last 90 days,
  what the provider told us and what we did about it.

## Constraints

- The provider is external. Its retry behaviour, payload schema, and ordering
  guarantees are its own, documented but not negotiable, and it has changed a
  payload shape once before without a major version bump.
- The team runs on AWS and has Postgres, SQS, and Lambda already in production
  use. Adding a new managed service is possible but needs a case.
- Two engineers, one quarter. The monolith stays in place.
- Billing data is in scope for the company's SOC 2 audit.

## Decided already

- The subsystem is separate and billing-team owned.
- The monolith is a consumer, not a co-owner of the ingestion path.

## Open

- How the subsystem is internally structured, and what its boundary with the
  monolith looks like.
- What it stores, and for how long.
- How the team operates it, and what they watch.
- Everything else.
