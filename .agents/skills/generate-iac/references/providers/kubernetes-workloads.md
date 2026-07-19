# Kubernetes workloads reference — experimental, not validated in v1

> **experimental — not validated in v1.**
>
> **Scope (D14):** This reference covers managing resources *inside* a Kubernetes
> cluster via the `kubernetes` and `helm` Terraform providers. It is
> cloud-agnostic — every major cloud has a Kubernetes variant. Provisioning the
> *cluster itself* (EKS/AKS/GKE) is in the respective cloud provider references
> (`providers/aws.md`, `providers/azure.md`, `providers/gcp.md`).
>
> **Out of scope:** using ArgoCD/Flux/Ansible as the runtime orchestrator. The
> `helm` provider can *install* ArgoCD/Flux; using them as the ongoing
> reconciliation engine is a multi-tool choice outside this reference.

## What is in scope

- Managing namespaces, RBAC, ConfigMaps, Secrets, and service accounts via the
  `kubernetes` provider
- Installing Helm charts (including operators, the OTEL Collector, ArgoCD itself)
  via the `helm` provider
- Managing in-cluster resources that the workload needs but that are not managed
  by the application itself

## Provider configuration

The `kubernetes` and `helm` providers are configured against an existing cluster.
They require cluster API endpoint and credentials — typically obtained from the
cloud provider's data source after the cluster is provisioned:

```hcl
terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

# For EKS — obtain credentials from the cluster data source
data "aws_eks_cluster" "main" {
  name = var.cluster_name
}

data "aws_eks_cluster_auth" "main" {
  name = var.cluster_name
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.main.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.main.token
}

provider "helm" {
  kubernetes {
    host                   = data.aws_eks_cluster.main.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.main.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.main.token
  }
}
```

For GKE and AKS, substitute the equivalent data sources from the respective
cloud provider.

## Common patterns

### Namespace and RBAC

```hcl
resource "kubernetes_namespace" "app" {
  metadata {
    name = "${var.system}-${var.environment}"
    labels = {
      environment = var.environment
      "managed-by" = "terraform"
    }
  }
}
```

### Helm chart (example: OTEL Collector)

```hcl
resource "helm_release" "otel_collector" {
  name       = "otel-collector"
  repository = "https://open-telemetry.github.io/opentelemetry-helm-charts"
  chart      = "opentelemetry-collector"
  version    = "0.90.0"  # pin to exact chart version
  namespace  = kubernetes_namespace.app.metadata[0].name

  values = [
    file("${path.module}/values/otel-collector.yaml")
  ]
}
```

Always pin Helm chart versions exactly — do not use floating ranges.

## Security notes

- Service account tokens should use projected volumes (short-lived) not static
  long-lived tokens.
- Namespace-scoped RBAC is preferred over cluster-wide roles where possible.
- Secrets created via `kubernetes_secret` land in etcd — ensure etcd encryption
  is enabled at the cluster level (configured via the cloud provider's cluster
  resource, not in this layer).
