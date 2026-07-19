# Observability standard

> **Binding — scoped by workload class.** A long-lived compute/service/data-plane
> stack must emit OpenTelemetry-compatible telemetry and provision the carrying
> pieces described here. A leaf resource (a lone S3 bucket, a DNS record, a
> firewall rule) is NOT required to stand up a collector + backend + dashboards.
> Apply judgment: if the resource receives requests or processes data, apply this
> standard. If it is purely a configuration or permission resource, skip.

## What to provision (long-lived compute/service/data-plane)

### (a) The OTEL Collector — as compute, not a Terraform provider

There is **no first-party "OTEL Collector" Terraform provider**. The collector
deploys as a **compute workload**:
- ECS/Fargate task or EKS DaemonSet/Deployment (AWS)
- Azure Container Instances or AKS DaemonSet (Azure)
- GKE DaemonSet or Cloud Run container (GCP)
- Or via the `helm` provider as a Helm chart (`open-telemetry/opentelemetry-collector`)

The collector is provisioned using the existing cloud or `helm` provider —
not a new provider dependency.

### (b) The telemetry backend — via the vendor's own Terraform provider

Pick one and provision via its provider:
- **Hyperscaler-native:**
  - AWS: CloudWatch + ADOT (AWS Distro for OpenTelemetry) — `aws_cloudwatch_*`
  - Azure: Azure Monitor + Azure Managed Grafana — `azurerm_monitor_*`
  - GCP: Cloud Monitoring + Cloud Trace — `google_monitoring_*`
- **Third-party (each has an official Terraform provider):**
  - Datadog (`datadog/datadog`)
  - Grafana Cloud (`grafana/grafana`)
  - Honeycomb (`honeycombio/honeycomb`)
  - New Relic (`newrelic/newrelic`)

### (c) Dashboards, alerts, and SLOs as code

Provision the observability control plane as Terraform resources alongside the
workload — not as manual configuration:
- Alert rules / alarm policies
- SLO definitions and error budgets
- Dashboard templates (Grafana dashboards via the `grafana` provider; CloudWatch
  dashboards via `aws_cloudwatch_dashboard`; etc.)

## Verification side (do NOT re-specify — refer to `release-loop`)

The verification of telemetry correctness (the data-plane probe that reads
metrics/traces back after a deploy) is `release-loop`'s `observability-and-smoke`
module. This standard covers the **provisioning** side only — what Terraform
emits. The smoke probe is built by `release-loop` against the deployed stack.

## Checklist

- [ ] Collector provisioned as a compute workload alongside the service (not a
  standalone manual installation).
- [ ] Telemetry backend provisioned via its official Terraform provider.
- [ ] Dashboard and alert resources managed as code, not manual configuration.
- [ ] Collector endpoint and backend credentials supplied via the secret manager.
- [ ] For workload-identity-enabled backends (e.g. AWS CloudWatch via IAM role),
  the IRSA/workload-identity binding is part of the Terraform config.
- [ ] If using a third-party backend, its API key is in the secrets manager and
  referenced via a data source — never hardcoded.
