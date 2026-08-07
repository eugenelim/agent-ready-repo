# Data platform providers reference

> **Status per provider:**
> - **Databricks — validated in v1** (passes `init -backend=false && fmt -check
>   && validate`; see `examples/databricks/`)
> - **Snowflake — experimental, not validated in v1**
> - **BigQuery, Redshift** — managed via the cloud provider (no separate
>   Terraform provider needed); see the respective cloud provider reference
> - **Others** — experimental; validate before use

## Databricks (validated in v1)

**Provider:** `databricks/databricks`

```hcl
terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
}

provider "databricks" {
  host = var.databricks_host
  # Authentication via env vars:
  # DATABRICKS_TOKEN (PAT)  — acceptable for ephemeral envs
  # Or use:
  # ARM_CLIENT_ID / ARM_CLIENT_SECRET — for Azure service principal
  # GOOGLE_CREDENTIALS — for GCP service account
  # AWS_PROFILE / instance profile — for AWS Credential passthrough
}
```

Common resources:
- `databricks_cluster` — interactive clusters (avoid for production; use SQL
  warehouse or job clusters)
- `databricks_job` — workflow jobs
- `databricks_sql_endpoint` — Databricks SQL warehouses
- `databricks_notebook` — managed notebooks (code stored in state — prefer
  `databricks_repo` for Git-backed notebooks)
- `databricks_group`, `databricks_user`, `databricks_service_principal` — IAM
- `databricks_secret_scope`, `databricks_secret` — secrets management (prefer
  secret scope backed by a cloud KV/Vault over Databricks-native storage)
- `databricks_unity_catalog_*` — Unity Catalog schemas, tables, volumes

**State backend:** Use the cloud backend appropriate for the Databricks
deployment cloud (S3 for AWS, GCS for GCP, AzureRM for Azure) — not
Databricks' DBFS or volumes.

**Credential tiering:** The CI service principal must be scoped to the
ephemeral workspace only. Never use a workspace admin PAT in CI for production.

## Snowflake (experimental)

**Provider:** `Snowflake-Labs/snowflake` — **DEPRECATED.** Use
`snowflakedb/snowflake` (the official Snowflake provider, maintained by
Snowflake Inc.) instead.

```hcl
terraform {
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 1.0"
    }
  }
}

provider "snowflake" {
  account  = var.snowflake_account   # <orgname>-<accountname>
  username = var.snowflake_user
  # Use key-pair authentication (SNOWFLAKE_PRIVATE_KEY_PATH env var), not
  # password auth. Never store the private key in state or as a variable default.
}
```

Common resources:
- `snowflake_database`, `snowflake_schema`, `snowflake_table`
- `snowflake_warehouse`
- `snowflake_role`, `snowflake_grant_privileges_to_role`
- `snowflake_storage_integration` — access to cloud object storage

## BigQuery (via `google` provider)

BigQuery datasets and tables are managed via `google_bigquery_dataset` and
`google_bigquery_table` — no separate provider. See `providers/gcp.md`.

## Redshift (via `aws` provider)

Redshift clusters, serverless namespaces, and IAM roles are managed via
`aws_redshift_cluster`, `aws_redshiftserverless_namespace` — no separate
provider. See `providers/aws.md`.

## Operational-safety notes

Data platform resources often contain or reference production data. Classify
table/schema deletion as `reversibility-class: one-way-door`. Run
`reconcile-iac` before any schema changes that could drop tables or columns.
