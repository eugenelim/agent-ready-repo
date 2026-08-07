# Cloud primitives — boundary vocabulary, service shorthand, gotchas

**Load this whenever a primitives / no-frills provider is named** — Hetzner is
the exemplar; the same vocabulary fits DigitalOcean, Linode/Akamai, Vultr, OVH.
These providers give you primitives, not managed services, so the diagram shows
*what you run yourself* — there is no managed-DB or serverless box to draw.

Common entry-point cues: Hetzner, hcloud, VPS, "bare VMs", Droplet, "cloud
servers", "self-managed Postgres", "we run our own", DigitalOcean, Vultr, Linode,
OVH — and any topology where the database and queue are processes *you* operate.

## Boundary hierarchy → subgraph nesting

```
Project / Account
└── Region / Location  (e.g. fsn1, nbg1)
    └── Private Network  (10.0.0.0/16)
        └── Subnet / zone  (app | data | edge)
```

Nest subgraphs in that order. The **private network is the trust boundary** —
anything reaching in from the public internet crosses it through a load balancer
or a firewall rule, and that crossing gets a dashed border and a labeled edge.

## Subgraph conventions

```
subgraph project["project: prod"]
    subgraph region["fsn1 (Falkenstein)"]
        subgraph pubnet["🌐 public edge"]
        end
        subgraph privnet["🔒 private network (10.0.0.0/16)"]
            subgraph apptier["app subnet"]
            end
            subgraph datatier["data subnet"]
            end
        end
    end
end
```

## Primitives that come up regularly

| Primitive | Shorthand label | Shape |
| --- | --- | --- |
| Cloud server (VM) | `<name> [cx22 / VM]` | rectangle |
| Load balancer (L4/L7, TLS term) | `LB [L7 + TLS]` | rectangle on the edge |
| Object storage (S3-compatible) | `<bucket> [/S3-compat/]` | trapezoid |
| Block volume | `<vol> [(volume)]` | cylinder attached to a server |
| Self-managed Postgres | `<db> [(Postgres — self-managed)]` | cylinder, **mark "self-managed"** |
| Self-managed queue/broker | `<q> [[Redis/RabbitMQ — self-run]]` | subroutine |
| Private network | the `privnet` subgraph border, not a node | — |
| Firewall | annotate on the boundary-crossing edge or as a note | — |
| Floating / primary IP | `vip [floating IP]` | small rectangle on the edge |
| Snapshot / backup | a note on the volume/DB, not a node | — |

## Cloud-specific gotchas

- **There is no managed-service box.** Don't draw a managed DB, a managed cache,
  or a serverless function — they don't exist here. A database is a Postgres
  *process on a server you patch*; render it that way and label it
  "self-managed" so the diagram doesn't imply a managed tier.
- **Mark what you own.** Replication, failover, and backups are *your*
  components on a primitives provider — if reliability is load-bearing, draw the
  replica server and the backup target, not an implied managed feature.
- **Private network is the trust boundary, not the region.** Cross-network and
  public-internet ingress are the boundaries that matter; make them visible with
  a dashed border and a labeled edge (LB, firewall rule).
- **TLS terminates at the load balancer** (or at your own reverse proxy) — show
  where, because nothing terminates it for you by default.
- **Object storage is S3-compatible but off-box.** Draw it outside the private
  network as an external-ish dependency reached over its API endpoint.
