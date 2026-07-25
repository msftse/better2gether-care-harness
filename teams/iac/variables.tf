variable "subscription_id" {
  description = "Subscription hosting the bridge and the Foundry agent."
  type        = string
}

variable "tenant_id" {
  description = "Entra tenant id for Bot Framework authentication."
  type        = string
}

variable "location" {
  description = "Region for the bridge resources."
  type        = string
  default     = "northcentralus"
}

variable "resource_group_name" {
  description = "Resource group to create for the Teams bridge."
  type        = string
  default     = "rg-care-teams-bridge"
}

variable "name_prefix" {
  description = "Short prefix for bridge resource names (lowercase alphanumeric)."
  type        = string
  default     = "care"
}

variable "bot_display_name" {
  description = "Display name of the Teams bot."
  type        = string
  default     = "Better2gether Care Copilot"
}

variable "bot_sku" {
  description = "Azure Bot Service SKU."
  type        = string
  default     = "F0"
}

variable "foundry_account_id" {
  description = "ARM resource id of the Foundry (Cognitive Services) account hosting the agent."
  type        = string
}

variable "foundry_agent_responses_url" {
  description = "Full Responses-protocol URL of the hosted agent endpoint."
  type        = string
}

variable "functions_runtime_version" {
  type    = string
  default = "8.0"
}

variable "function_instance_memory_mb" {
  type    = number
  default = 2048
}

variable "function_max_instance_count" {
  type    = number
  default = 40
}

variable "tags" {
  type = map(string)
  default = {
    project         = "better2gether-care-harness"
    SecurityControl = "Ignore"
  }
}
