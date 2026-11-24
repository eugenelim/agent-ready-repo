variable "databricks_host" {
  description = "Databricks workspace URL (e.g. https://adb-1234567890.azuredatabricks.net)"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "system" {
  description = "System or service name — used in resource naming"
  type        = string
}
