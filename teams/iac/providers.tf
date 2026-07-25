terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
  # The needed providers (Web, Storage, ManagedIdentity, Insights,
  # OperationalInsights, BotService) are registered explicitly; skipping the
  # bulk auto-registration that can hang for 10+ minutes on fresh subscriptions.
  resource_provider_registrations = "none"
}
