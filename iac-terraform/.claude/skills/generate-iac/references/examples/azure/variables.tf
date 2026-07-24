variable "subscription_id" {
  description = "Azure subscription ID"
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

variable "owner" {
  description = "Team or individual owning this resource"
  type        = string
}

variable "cost_center" {
  description = "Cost center code for billing attribution"
  type        = string
}

variable "data_classification" {
  description = "Data classification level (public, internal, confidential, restricted)"
  type        = string
  default     = "internal"
}
