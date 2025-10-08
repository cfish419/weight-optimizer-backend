variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "weight-optimizer"
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC (/24 network)"
  type        = string
  default     = "10.0.0.0/24"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "enable_transit_gateway" {
  description = "Enable Transit Gateway for multi-VPC connectivity"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs for security monitoring"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}