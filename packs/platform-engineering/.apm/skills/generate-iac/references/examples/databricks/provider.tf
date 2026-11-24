provider "databricks" {
  host = var.databricks_host
  # Authentication via DATABRICKS_TOKEN env var (PAT — acceptable for
  # ephemeral and CI environments).
  # For Azure: ARM_CLIENT_ID / ARM_CLIENT_SECRET (service principal)
  # For GCP: GOOGLE_CREDENTIALS (service account key)
  # Never hardcode credentials in provider configuration.
}
