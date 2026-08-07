# Cloud primitives — the provider class with no managed services

A primitives provider gives you compute, storage, and network *primitives* and
little else: no managed database, no serverless, no managed identity, no managed
multi-region failover, no well-architected framework of its own. Hetzner is the
named exemplar; the class is the same shape as DigitalOcean, Linode/Akamai,
Vultr, OVH. The reusable substance is the **class**, not Hetzner specifics.

> Note: this reference is intentionally duplicated into `architect-review`'s
> `references/cloud-primitives.md`. Skill autonomy beats DRY at this scale —
> each skill stands alone. See the pack README.

## Why this class earns its own reference

On a hyperscaler you largely *achieve a pillar by selecting a managed service*.
On a primitives provider the same pillar is met by **building it yourself**. A
by-construction pillar pass therefore reads completely differently: Reliability
shifts from "pick multi-AZ managed DB" to "you must design replication,
backup/restore, and failover, because nothing does it for you." Naming that
contrast is the teaching — it stops the "cheap VPS = done" trap by making the
founder see what they now *own*.

What the class typically *does* supply: cloud servers, L4/L7 load balancers
(with TLS termination), S3-compatible object storage, block volumes, private
networks, firewalls, snapshots/backups.

## Capability gaps you must fill

When the design targets a primitives provider, enumerate the **gap categories
the provider does not supply** and name, for the ones that apply, *what the
design builds itself*. The categories below are the spine; at least one concrete
gap must be named for the workload (the examples are illustrative, not a pinned
contract).

| Gap category | What's missing | What the design now owns (concrete example) |
|---|---|---|
| **Managed data tier** | managed Postgres/MySQL, HA, automated backups, PITR | run Postgres yourself: streaming replication, a tested restore path, failover orchestration |
| **Edge / CDN** | global CDN, edge caching, DDoS scrubbing at the edge | front static + cacheable content with your own caching tier / a third-party CDN; plan origin-shield |
| **Managed identity** | managed user pools, OIDC/SAML IdP, managed secrets store | run your own IdP or wire a third-party one; stand up a secrets store and rotation |
| **Serverless / event glue** | functions-as-a-service, managed queues, managed event bus | run a queue/broker and worker pool yourself; own scaling and dead-letter handling |
| **Managed K8s / orchestration** | managed control plane, managed node lifecycle | run your own orchestrator or stay VM-native; own upgrades and node health |
| **Managed multi-region failover** | cross-region replication + automated failover | design region placement, data replication, and a manual or scripted failover runbook |
| **Observability** | managed metrics/logs/traces, managed alerting | stand up your own metrics/logs/traces stack and on-call alerting |

## The lock-in credit

A primitives provider also *lowers lock-in*: portable primitives, an
S3-compatible API, plain VMs. The build-vs-buy / lock-in question
(`cross-cutting-questions.md`) should credit that — the founder trades managed
convenience for portability and a flatter, more predictable bill.

## Use, don't recite

Name the gaps this workload actually hits and what it builds for each. A design
that lists all seven categories generically, without saying what *this* system
owns, has missed the point of the class.
