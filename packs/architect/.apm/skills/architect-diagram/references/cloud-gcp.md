# GCP — boundary vocabulary, service shorthand, gotchas

**Load this whenever *any* GCP / Google Cloud service is named** —
even if it does not appear in the service table below. The 15-ish
services tabulated are the high-frequency ones; the boundary
vocabulary, subgraph nesting, and gotchas in this file apply to
every GCP diagram.

Common entry-point cues: Cloud Run, GKE, BigQuery, Pub/Sub, Vertex,
Spanner, Cloud Functions, Cloud Storage, Firestore, Dataflow,
Composer, IAP, Apigee, Cloud SQL — and anything else with
`gcp-` / `google-cloud-` in the name.

## Boundary hierarchy → subgraph nesting

```
Organization
└── Folder(s)
    └── Project
        └── VPC (shared or own)
            └── Subnet (regional)
```

Nest subgraphs in that order. The **project boundary is the trust
boundary** — cross-project arrows get a dashed border and a labeled
edge (Shared VPC, VPC Peering, IAM grant).

Note: GCP VPCs are *global*, not regional. Subnets are regional. If
the diagram cares about regions, render the region as a subgraph
*inside* the VPC, containing the regional subnet(s).

## Subgraph conventions

```
subgraph proj_prod["project: orders-prod"]
    subgraph vpc["vpc-prod (global)"]
        subgraph region_us["region: us-central1"]
            subgraph snet["🔒 snet-app"]
            end
        end
    end
end
```

## 15-ish services that come up regularly

| Service | Shorthand label | Shape |
| --- | --- | --- |
| Cloud Load Balancing | `GLB [External HTTPS LB]` | rectangle on the edge |
| Cloud Armor | annotate on the LB or as a note | — |
| Cloud Run | `<svc> [Cloud Run]` | rectangle |
| Cloud Functions | `<name> ƒ [Functions Gen2]` | rectangle |
| GKE | `<cluster> [GKE Autopilot]` / `[GKE Standard]` | rectangle |
| App Engine | `<svc> [App Engine]` | rectangle |
| Cloud Storage | `<bucket> [/GCS/]` | trapezoid |
| Firestore | `<db> [(Firestore)]` | cylinder |
| Cloud SQL | `<db> [(Cloud SQL Postgres)]` | cylinder |
| Spanner | `<db> [(Spanner)]` | cylinder |
| BigQuery | `<dataset> [(BigQuery)]` | cylinder |
| Pub/Sub | `<topic> [[Pub/Sub]]` | subroutine |
| Cloud Tasks | `<queue> [[Cloud Tasks]]` | subroutine |
| Secret Manager | `SM` | small rectangle |
| Identity-Aware Proxy | `IAP` | rectangle on the edge |
| Apigee | `Apigee` | rectangle |
| Vertex AI | see `agentic-vertex-agent-engine.md` for agent diagrams | — |

## Cloud-specific gotchas

- **VPC is global, subnets are regional.** Don't render VPC inside a
  region — render the region inside the VPC.
- **Project boundaries.** Different projects = different IAM,
  different billing, different default network. The trust boundary.
- **Shared VPC.** Host project's VPC is shared with service
  projects. When this is the topology, render the host project's
  VPC as the parent subgraph with service-project containers
  attached to its subnets. Otherwise the diagram is misleading.
- **Service accounts are first-class.** When the diagram is about
  *who calls what*, label edges with the service account (or "SA
  of <service>"). "Cloud Run → Cloud Storage [SA: orders-runtime]"
  beats unlabeled.
- **Cloud Run + VPC connector vs. Direct VPC egress.** If the
  service reaches a VPC resource, name the egress method on the
  edge — they have different latency and IP semantics.
- **BigQuery is not in a VPC.** Render it outside the VPC
  subgraph, even when accessed from inside the VPC. Use a labeled
  edge through Private Google Access if that's how it's reached.
