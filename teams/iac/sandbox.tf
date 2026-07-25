# Azure Container Apps Sandboxes (preview) — data-plane RBAC.
# This tenant's built-in "Azure ContainerApps Session Executor" role predates
# the Sandboxes preview (sessionPools/* only), so define a custom role carrying
# the Microsoft.App/sandboxGroups/* data actions and assign it to the callers.

variable "sandbox_group_id" {
  description = "ARM id of the Microsoft.App/sandboxGroups resource."
  type        = string
  default     = "/subscriptions/04197a4f-e8b8-449d-8774-b0a9484fab46/resourceGroups/rg-care-agent-dev/providers/Microsoft.App/sandboxGroups/sbg-care-agent"
}

variable "sandbox_callers" {
  description = "Principal ids allowed to execute in the sandbox group (user + hosted-agent identity)."
  type = map(object({ principal_id = string, principal_type = string }))
  default = {
    roey        = { principal_id = "9e61bcec-0592-494f-98d2-981f6464bbbf", principal_type = "User" }
    care_agent  = { principal_id = "9be4ded5-7a5b-497f-a7b0-1d63c9569667", principal_type = "ServicePrincipal" }
  }
}

resource "azurerm_role_definition" "sandbox_executor" {
  name        = "Sandbox Group Executor (custom)"
  scope       = "/subscriptions/${var.subscription_id}"
  description = "Execute commands and manage sandboxes inside Microsoft.App sandboxGroups (preview data plane)."

  permissions {
    actions      = ["Microsoft.App/sandboxGroups/*/read", "Microsoft.Authorization/*/read"]
    data_actions = ["Microsoft.App/sandboxGroups/*"]
  }

  assignable_scopes = ["/subscriptions/${var.subscription_id}"]
}

resource "azurerm_role_assignment" "sandbox_callers" {
  for_each           = var.sandbox_callers
  scope              = var.sandbox_group_id
  role_definition_id = azurerm_role_definition.sandbox_executor.role_definition_resource_id
  principal_id       = each.value.principal_id
  principal_type     = each.value.principal_type
}
