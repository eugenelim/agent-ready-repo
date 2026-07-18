locals {
  standard_tags = {
    environment         = var.environment
    owner               = var.owner
    "cost-center"       = var.cost_center
    "managed-by"        = "terraform"
    system              = var.system
    "data-classification" = var.data_classification
  }
}

provider "google" {
  project        = var.project_id
  region         = var.region
  default_labels = local.standard_tags
}
