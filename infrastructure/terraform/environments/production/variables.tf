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
  default     = "production"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "alert_emails" {
  description = "List of email addresses for CloudWatch alerts"
  type        = list(string)
  default     = []
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "key_pair_name" {
  description = "AWS key pair name for EC2 access"
  type        = string
  default     = "weight-optimizer-prod"
}

variable "root_volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 20
}

variable "data_volume_size" {
  description = "Data volume size in GB"
  type        = number
  default     = 50
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/24"
}

variable "enable_transit_gateway" {
  description = "Enable Transit Gateway"
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "owner" {
  description = "Owner tag for resources"
  type        = string
  default     = "DevOps Team"
}