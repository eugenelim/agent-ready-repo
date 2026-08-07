# AWS — boundary vocabulary, service shorthand, gotchas

**Load this whenever *any* AWS service is named** — even if it does
not appear in the service table below. The 15-ish services tabulated
are the high-frequency ones; the boundary vocabulary, subgraph
nesting, and gotchas in this file apply to every AWS diagram.

Common entry-point cues: Lambda, S3, Bedrock, DynamoDB, EKS, ECS,
CloudFront, Route 53, IAM, SNS, SQS, Kinesis, RDS, Aurora, App
Runner, API Gateway — and anything else with `aws-` in the name.

## Boundary hierarchy → subgraph nesting

```
Organization
└── Account
    └── Region
        └── VPC
            └── Subnet  (public | private | isolated)
```

Nest subgraphs in that order. The **account boundary is the trust
boundary** — cross-account arrows get a dashed border and a labeled
edge naming what crosses (RAM share, cross-account IAM role, peering).

## Subgraph conventions

```
subgraph account_prod["acct: prod (111122223333)"]
    subgraph region["us-east-1"]
        subgraph vpc["vpc-prod"]
            subgraph public["🌐 public subnet"]
            end
            subgraph private["🔒 private subnet"]
            end
        end
    end
end
```

## 15-ish services that come up regularly

| Service | Shorthand label | Shape |
| --- | --- | --- |
| API Gateway | `APIGW` or `API GW [REST/HTTP/WS]` | rectangle |
| Application LB / Network LB | `ALB` / `NLB` | rectangle |
| Lambda | `<name> λ [Node 20]` | rectangle (or `((λ))` for inline) |
| ECS (Fargate) | `<name> [ECS Fargate]` | rectangle |
| EKS | `<name> [EKS]` | rectangle, with pods as nested rectangles when relevant |
| S3 | `<bucket> [/S3/]` | trapezoid |
| DynamoDB | `<table> [(DynamoDB)]` | cylinder |
| RDS / Aurora | `<db> [(RDS Postgres)]` | cylinder |
| SQS | `<queue> [[SQS]]` | subroutine |
| SNS | `<topic> [[SNS]]` | subroutine |
| EventBridge | `<bus> [[EventBridge]]` | subroutine |
| Kinesis / MSK | `<stream> [[Kinesis]]` / `[[MSK]]` | subroutine |
| CloudFront | `CF [CloudFront]` | rectangle on the edge |
| Route 53 | `R53 [DNS]` | rectangle on the edge |
| Secrets Manager / SSM | `SM` / `SSM` | small rectangle |
| IAM role | annotate on the edge or as a note, not a node | — |
| Cognito | `Cognito [User pool]` | rectangle |
| Bedrock | see `agentic-bedrock-agentcore.md` for full agent diagrams | — |

## Cloud-specific gotchas

- **Public vs. private subnet semantics.** Public subnet = has an
  IGW route. Private subnet = NAT or VPC endpoint only. Always
  render them as separate subgraphs with distinct labels.
- **Cross-AZ vs. cross-Region.** AZ-level boundaries usually don't
  appear in architecture diagrams (too fine-grained); Region-level
  do. Mention multi-AZ in prose, not in the picture, unless it's
  load-bearing.
- **VPC endpoints (Interface / Gateway).** When a service inside
  the VPC reaches an AWS service over VPC endpoints (not the
  internet), draw the endpoint as a node inside the subnet and
  route through it — otherwise the diagram is misleading about the
  data path.
- **Lambda inside vs. outside VPC.** A Lambda *inside a VPC* sits
  in private subnets; *outside a VPC* it doesn't appear inside any
  subnet. Get this right — security review reads diagrams for this.
- **Account boundaries.** When two AWS accounts appear in the same
  diagram, the *account* is the trust boundary, not the VPC. Make
  the boundary visible.
