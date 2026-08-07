# Well-architected pillars — the spine + cloud-agnostic distillation

The provider-independent quality spine an architect carries across clouds.
AWS ships six pillars, Azure five, Google six — they differ in count, not in
substance. Distil them to six dimensions and reason against those; map to a
provider's own framework only when the user is committed to that provider.

> Note: this reference is intentionally duplicated from `architect-design`'s
> `references/well-architected-pillars.md`. Skill autonomy beats DRY at this
> scale — each skill stands alone. See the pack README.

## The six dimensions

1. **Reliability / Resilience** — availability, fault tolerance, blast radius,
   recovery (RTO/RPO), single-point-of-failure analysis, graceful degradation.
2. **Security** (Google folds in *Privacy & Compliance*) — trust boundaries,
   identity, least privilege, data classification, encryption, attack surface.
3. **Cost Optimization** (FinOps) — unit economics, right-sizing, linear-vs-
   sublinear scaling, commitment/spot, cost visibility.
4. **Performance Efficiency** — workload-to-resource fit, scaling model,
   latency budget (p50/p99), elasticity.
5. **Operational Excellence** — observability (metrics/logs/traces), deployment
   & rollback, runbooks, incident response, "debuggable at 3am."
6. **Sustainability** — energy/carbon efficiency, resource utilization,
   region/carbon-aware placement (top-level on AWS + Google; folded in on Azure).

## By construction — name *how* each pillar is achieved on the provider

The spine is provider-agnostic; *how each pillar is met* is provider-specific.
When a provider is named or inferred, the design must say — per relevant pillar
— **how it is achieved on that provider**, not merely that it matters. This is
where the design is made well-architected *by construction* rather than caught
in review.

Two provider classes read very differently:

- **Hyperscalers (AWS / Azure / GCP)** — you largely *achieve a pillar by
  selecting the right managed service*: multi-AZ managed DB → reliability;
  IAM + KMS → security; autoscaling → performance. Name the service that
  carries each pillar.
- **Primitives providers (Hetzner and its class)** — the *same* pillars are met
  by **building them yourself**. The managed service does not exist, so the
  design owns it. Load `cloud-primitives.md` for the capability-gap framing —
  on a primitives provider the by-construction pass is mostly *naming what you
  must build*.

A per-pillar provider sketch (illustrative — confirm current specifics with the
provider, never pin them here):

| Pillar | Hyperscaler shape | Primitives shape (self-managed) |
|---|---|---|
| Reliability | multi-AZ managed DB, autoscaling, managed failover | multiple servers + LB + **your** replication / backups / failover |
| Security | managed identity + KMS + managed firewall/threat-detection | firewall + private network; **you** run identity, secrets, patching |
| Performance | autoscaling + managed cache | vertical / manual horizontal scaling, **your** cache tier |
| Cost | commitments / spot / tagging | flat predictable price; few levers, low lock-in |
| Operational excellence | managed metrics/logs/traces + managed IaC | **your** Prometheus/Grafana + IaC |
| Sustainability | region carbon data, efficient instance families | green-energy DC region choice; fewer levers |

## Security pillar — stay at design altitude

The Security dimension here reasons about **trust boundaries, identity and IAM
design, data egress, encryption-in-transit/at-rest decisions, OAuth scope
minimization, and assessability** — design-altitude concerns. It does **not**
reproduce a control checklist. Where a workload touches restricted-scope user
data (e.g. Google-user data under OAuth) or needs third-party security
attestation, name **CASA / ASVS as a downstream verification gate** and route
control-level verification to the repo's `security-reviewer` /
`security-checklists`. See `cross-cutting-questions.md` for the assessability
question. Naming the gate is the design's job; running it is not.

## Prioritize before grinding every pillar

Don't walk all six flat. Rank the dimensions by **business-importance ×
architectural-risk** and spend where it matters — a one-pass ranking (the
"utility-tree-lite" move), not a workshop. The top two or three become the
prioritized quality attributes the concept stage commits to. Load
`quality-attribute-scenarios.md` to turn each into a testable claim and
`tradeoffs-and-sensitivity.md` to name where pillars pull against each other.

## Use, don't recite

This is a prompt for honest per-pillar reasoning, not a section template. A
design that names *how* reliability is achieved on the chosen provider — and
what it must build when the provider supplies nothing — beats one that lists
six headings and a sentence each.
