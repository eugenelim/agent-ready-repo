# Observability vendor providers reference — experimental, not validated in v1

> **experimental — not validated in v1.** All providers here are contract-aware
> but no worked examples have been validated. Use as a starting point; verify
> before relying on these configurations.
>
> **Scope note:** This reference covers *provisioning* observability vendor
> resources via Terraform — dashboards as code, monitors, alert policies, data
> sources. It is distinct from `observability-standard.md`, which covers the
> *design* principles for workload observability (what to emit and how).

## Datadog

**Provider:** `DataDog/datadog`

```hcl
terraform {
  required_providers {
    datadog = {
      source  = "DataDog/datadog"
      version = "~> 3.0"
    }
  }
}

provider "datadog" {
  api_key = var.datadog_api_key  # via DD_API_KEY env var preferred
  app_key = var.datadog_app_key  # via DD_APP_KEY env var preferred
  api_url = "https://api.datadoghq.com/"  # adjust for EU: datadoghq.eu
}
```

Common resources:
- `datadog_monitor` — alert monitors (metric, log, APM)
- `datadog_dashboard`, `datadog_dashboard_json` — dashboards as code
- `datadog_service_level_objective` — SLOs
- `datadog_logs_index`, `datadog_logs_pipeline` — log processing pipelines
- `datadog_synthetics_test` — synthetic monitoring

Never store API keys as variable defaults or in state — use environment
variables (`DD_API_KEY`, `DD_APP_KEY`) or a secrets manager.

## Grafana

**Provider:** `grafana/grafana`

```hcl
terraform {
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 3.0"
    }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_service_account_token  # via GRAFANA_AUTH env var
}
```

Common resources:
- `grafana_dashboard` — JSON dashboard definitions
- `grafana_folder` — dashboard organization
- `grafana_alert_rule`, `grafana_notification_policy` — Grafana Alerting
- `grafana_data_source` — connect Prometheus, Loki, Tempo, etc.
- `grafana_slo` — SLO definitions (Grafana Cloud)

## Honeycomb

**Provider:** `honeycombio/honeycomb`

```hcl
terraform {
  required_providers {
    honeycomb = {
      source  = "honeycombio/honeycomb"
      version = "~> 0.20"
    }
  }
}

provider "honeycomb" {
  api_key = var.honeycomb_api_key  # via HONEYCOMB_API_KEY env var
}
```

Common resources:
- `honeycomb_dataset` — dataset configuration
- `honeycomb_board` — query boards
- `honeycomb_trigger` — alert triggers
- `honeycomb_derived_column` — computed columns

## New Relic

**Provider:** `newrelic/newrelic`

```hcl
terraform {
  required_providers {
    newrelic = {
      source  = "newrelic/newrelic"
      version = "~> 3.0"
    }
  }
}

provider "newrelic" {
  account_id = var.newrelic_account_id
  api_key    = var.newrelic_api_key   # via NEW_RELIC_API_KEY env var
  region     = "US"                  # or "EU"
}
```

Common resources:
- `newrelic_alert_policy`, `newrelic_alert_condition` — alert policies
- `newrelic_one_dashboard` — dashboards
- `newrelic_service_level` — SLOs

## Security notes

All observability vendor API keys carry production-scoped read/write access —
treat them as secrets, not config. Store via secrets manager; never include in
variables with `default = "key_..."`. Dashboard state files may contain metric
query logic that is sensitive context for attackers; use a state backend with
encryption-at-rest.
