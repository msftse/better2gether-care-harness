locals {
  suffix               = substr(sha1(azurerm_resource_group.bridge.id), 0, 6)
  storage_account_name = substr("st${var.name_prefix}${local.suffix}", 0, 24)
  function_app_name    = "func-${var.name_prefix}-teams-${local.suffix}"
  bot_name             = "bot-${var.name_prefix}-teams-${local.suffix}"
  plan_name            = "plan-${var.name_prefix}-teams"
  func_identity_name   = "id-${var.name_prefix}-teams-func"
  session_map_table    = "sessionmap"
  messaging_endpoint   = "https://${azurerm_function_app_flex_consumption.func.default_hostname}/api/messages"
}

resource "azurerm_resource_group" "bridge" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# Monitoring -----------------------------------------------------------------
resource "azurerm_log_analytics_workspace" "bridge" {
  name                = "log-${var.name_prefix}-teams"
  resource_group_name = azurerm_resource_group.bridge.name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_application_insights" "bridge" {
  name                = "appi-${var.name_prefix}-teams"
  resource_group_name = azurerm_resource_group.bridge.name
  location            = var.location
  workspace_id        = azurerm_log_analytics_workspace.bridge.id
  application_type    = "web"
  tags                = var.tags
}

# Bridge identity ------------------------------------------------------------
# One user-assigned managed identity serves BOTH as the Azure Bot Service
# identity (microsoft_app_type = UserAssignedMSI — no app registration or
# client secret) and as the credential the Function uses to call the Foundry
# hosted agent data plane.
resource "azurerm_user_assigned_identity" "func" {
  name                = local.func_identity_name
  resource_group_name = azurerm_resource_group.bridge.name
  location            = var.location
  tags                = var.tags
}

# Storage --------------------------------------------------------------------
resource "azurerm_storage_account" "func" {
  name                            = local.storage_account_name
  resource_group_name             = azurerm_resource_group.bridge.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = var.tags
}

resource "azurerm_storage_container" "deploy" {
  name                  = "deployment"
  storage_account_id    = azurerm_storage_account.func.id
  container_access_type = "private"
}

resource "azurerm_storage_table" "sessionmap" {
  name               = local.session_map_table
  storage_account_id = azurerm_storage_account.func.id
}

# Function App ---------------------------------------------------------------
resource "azurerm_service_plan" "func" {
  name                = local.plan_name
  resource_group_name = azurerm_resource_group.bridge.name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "FC1"
  tags                = var.tags
}

resource "azurerm_function_app_flex_consumption" "func" {
  name                = local.function_app_name
  resource_group_name = azurerm_resource_group.bridge.name
  location            = var.location
  service_plan_id     = azurerm_service_plan.func.id

  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.func.primary_blob_endpoint}${azurerm_storage_container.deploy.name}"
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.func.primary_access_key

  runtime_name           = "dotnet-isolated"
  runtime_version        = var.functions_runtime_version
  instance_memory_in_mb  = var.function_instance_memory_mb
  maximum_instance_count = var.function_max_instance_count

  identity {
    type         = "SystemAssigned, UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.func.id]
  }

  site_config {
    application_insights_connection_string = azurerm_application_insights.bridge.connection_string
  }

  app_settings = {
    AzureWebJobsStorage = azurerm_storage_account.func.primary_connection_string

    MicrosoftAppType     = "UserAssignedMSI"
    MicrosoftAppId       = azurerm_user_assigned_identity.func.client_id
    MicrosoftAppTenantId = var.tenant_id

    FOUNDRY_AGENT_RESPONSES_URL = var.foundry_agent_responses_url
    FOUNDRY_MI_CLIENT_ID        = azurerm_user_assigned_identity.func.client_id

    SESSION_MAP_TABLE = azurerm_storage_table.sessionmap.name
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      app_settings["AzureWebJobsStorage"],
      tags["hidden-link: /app-insights-resource-id"],
    ]
  }
}

# Bot Service + Teams channel ------------------------------------------------
resource "azurerm_bot_service_azure_bot" "bot" {
  name                    = local.bot_name
  display_name            = var.bot_display_name
  resource_group_name     = azurerm_resource_group.bridge.name
  location                = "global"
  microsoft_app_id        = azurerm_user_assigned_identity.func.client_id
  microsoft_app_type      = "UserAssignedMSI"
  microsoft_app_msi_id    = azurerm_user_assigned_identity.func.id
  microsoft_app_tenant_id = var.tenant_id
  sku                     = var.bot_sku
  endpoint                = local.messaging_endpoint
  tags                    = var.tags
}

resource "azurerm_bot_channel_ms_teams" "teams" {
  bot_name            = azurerm_bot_service_azure_bot.bot.name
  location            = azurerm_bot_service_azure_bot.bot.location
  resource_group_name = azurerm_resource_group.bridge.name
}

# RBAC -----------------------------------------------------------------------
# The bridge identity calls the Foundry hosted agent data plane. In this tenant
# the role definitions are stale: "Cognitive Services User" carries the
# Microsoft.CognitiveServices/* wildcard data action that covers the agents
# endpoints ("Azure AI User" does not exist here).
resource "azurerm_role_assignment" "func_foundry_user" {
  scope                = var.foundry_account_id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_user_assigned_identity.func.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "func_table" {
  scope                = azurerm_storage_account.func.id
  role_definition_name = "Storage Table Data Contributor"
  principal_id         = azurerm_user_assigned_identity.func.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "func_blob" {
  scope                = azurerm_storage_account.func.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.func.principal_id
  principal_type       = "ServicePrincipal"
}
