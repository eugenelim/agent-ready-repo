locals {
  standard_tags = {
    environment         = var.environment
    owner               = var.owner
    cost-center         = var.cost_center
    managed-by          = "terraform"
    system              = var.system
    data-classification = var.data_classification
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.standard_tags
  }
}
