# Azure — boundary vocabulary, service shorthand, gotchas

**Load this whenever *any* Azure service is named** — even if it does
not appear in the service table below. The 15-ish services tabulated
are the high-frequency ones; the boundary vocabulary, subgraph
nesting, and gotchas in this file apply to every Azure diagram.

Common entry-point cues: App Service, Functions, Cosmos DB, AKS,
Service Bus, Front Door, AI Foundry, Container Apps, Container
Registry, Application Gateway, APIM, Logic Apps, Event Grid,
Storage Account — and anything else hosted under
`*.azure.com` / `*.windows.net`.

## Boundary hierarchy → subgraph nesting

```
Tenant
└── Management group(s)
    └── Subscription
        └── Resource group
            └── VNet
                └── Subnet
```

Nest subgraphs in that order. The **subscription boundary is the
trust boundary** — cross-subscription arrows get a dashed border and
a labeled edge (peering, Private Link, Lighthouse delegation).

## Subgraph conventions

```
subgraph sub_prod["subscription: prod"]
    subgraph rg["rg-orders-prod"]
        subgraph vnet["vnet-prod"]
            subgraph snet_app["🔒 snet-app"]
            end
            subgraph snet_data["🔒 snet-data"]
            end
        end
    end
end
```

## 15-ish services that come up regularly

| Service | Shorthand label | Shape |
| --- | --- | --- |
| Front Door | `AFD [Front Door]` | rectangle on the edge |
| Application Gateway | `App GW [WAF]` | rectangle |
| API Management | `APIM` | rectangle |
| App Service / Container Apps | `<name> [App Service]` / `[Container Apps]` | rectangle |
| Functions | `<name> ƒ [Functions, Node 20]` | rectangle |
| AKS | `<cluster> [AKS]` | rectangle |
| Storage Blob | `<account> [/Blob/]` | trapezoid |
| Cosmos DB | `<db> [(Cosmos DB)]` | cylinder |
| Azure SQL | `<db> [(Azure SQL)]` | cylinder |
| Service Bus | `<topic> [[Service Bus]]` | subroutine |
| Event Grid | `<topic> [[Event Grid]]` | subroutine |
| Event Hubs | `<hub> [[Event Hubs]]` | subroutine |
| Key Vault | `KV` | small rectangle |
| Entra ID | `Entra` | rectangle at the edge |
| Private DNS Zone | annotate on edge or note, not a node | — |
| AI Foundry | see `agentic-ai-foundry.md` for agent diagrams | — |

## Cloud-specific gotchas

- **Service Endpoint vs. Private Endpoint.** A service endpoint
  routes traffic over the Microsoft backbone but the destination
  still has a public IP. A private endpoint gives the destination
  an IP *inside your VNet*. The diagram is different — render the
  private endpoint as a node inside the subnet; render the service
  endpoint as a property of the subnet, not a node.
- **Subscription boundaries.** Different subscriptions = different
  trust zone, different billing, often different RBAC. Make it
  visible.
- **Resource groups are not security boundaries.** They are
  lifecycle / billing groupings. Don't render them as dashed-border
  subgraphs unless RBAC differs.
- **Managed identity vs. service principal.** When the diagram is
  about *who can call what*, annotate edges with the identity that
  authenticates the call. "App Service → Key Vault [Managed
  Identity]" beats "App Service → Key Vault".
- **Hub-and-spoke topology.** Common Azure pattern — render hub VNet
  as its own subgraph, spokes peer to it; label peerings explicitly.
