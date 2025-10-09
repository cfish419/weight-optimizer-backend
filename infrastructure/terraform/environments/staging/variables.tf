variable "aws_account_id" {
  description = "AWS Account ID for deployment validation"
  type        = string
  default     = ""
}

variable "deployment_role_arn" {
  description = "IAM role ARN for cross-account deployment"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "weight-optimizer"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}