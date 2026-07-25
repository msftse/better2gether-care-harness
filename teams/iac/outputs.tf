output "function_app_name" {
  value = azurerm_function_app_flex_consumption.func.name
}

output "resource_group_name" {
  value = azurerm_resource_group.bridge.name
}

output "bot_app_id" {
  description = "The user-assigned identity client id — also the Teams manifest botId."
  value       = azurerm_user_assigned_identity.func.client_id
}

output "messaging_endpoint" {
  value = local.messaging_endpoint
}

output "bot_name" {
  value = azurerm_bot_service_azure_bot.bot.name
}
