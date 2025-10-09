variable "table_prefix" {
  description = "Prefix for DynamoDB table names"
  type        = string
  default     = "weight-optimizer"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "weight-optimizer"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}