locals {
  standard_tags = {
    environment           = var.environment
    owner                 = var.owner
    "cost-center"         = var.cost_center
    "managed-by"          = "terraform"
    system                = var.system
    "data-classification" = var.data_classification
  }
}

provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
}
