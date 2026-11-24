# Networking standard

> **Binding.** Every generated networking configuration must comply with these
> principles. Cite in the plan's standards-mapping table.

## Five principles

1. **Private by default.** Workloads run in private subnets. No public ingress
   unless the spec explicitly requires it and an ADR or plan note justifies it.
2. **Network-as-input.** Consume a central-team-owned network as an input via
   variables (`network_id`, `private_subnet_ids`). Do not create address space
   unless the spec owns the network — and if it does, document the CIDR blocks
   in the plan.
3. **Egress-only least-open.** Security groups / NSGs default to no ingress,
   egress restricted to 443 + named destinations. Prefer prefix-lists /
   service-tags over `0.0.0.0/0`. **Never emit `0.0.0.0/0` ingress** — blocked
   by the OPA gate.
4. **Private service access.** Reach storage, secrets, KMS, and container
   registries via private/service endpoints, not the public internet.
5. **Governed front door only.** LB+WAF or API Gateway as the entry point for
   any public-facing workload. Never a raw public IP.

## Per-cloud mapping table

| Concept | AWS | Azure | GCP |
| --- | --- | --- | --- |
| Network | VPC | Virtual Network (VNet) | VPC network (global) |
| Segment | Subnet | Subnet | Subnetwork (regional) |
| Firewall | Security Group / NACL | NSG | Firewall rule |
| Private service access | VPC Endpoint (Gateway + Interface) | Private Endpoint | Private Service Connect + Private Google Access |
| Front door | ALB + WAF · API Gateway | App Gateway + WAF · APIM | Global Load Balancer + Cloud Armor · API Gateway |
| Egress control | Security Group outbound rules + prefix lists | NSG outbound rules + service tags | Firewall rules + service accounts |

## GCP network scoping note

GCP VPC networks are **global** (not regional) — a single VPC spans all regions.
Subnetworks are regional. This differs from AWS and Azure where VPCs/VNets are
regional. The networking template must reflect this when creating GCP resources.

## Checklist (review before merge)

- [ ] Workloads in private subnets; no public subnet assignment without justification.
- [ ] No `0.0.0.0/0` ingress in security groups, NSGs, or firewall rules.
- [ ] Storage and secrets reached via private/service endpoints (not public URLs).
- [ ] Front door is LB+WAF or API GW; no raw public IP attached to a compute resource.
- [ ] Egress restricted to 443 + named destinations; wildcard egress documented as exception.
- [ ] If the config owns the network: CIDR blocks recorded in the plan and non-overlapping.
- [ ] If consuming a network: `network_id` and `private_subnet_ids` are input variables.
