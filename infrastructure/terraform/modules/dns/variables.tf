variable "domain_name" {
  description = "The domain name for the hosted zone"
  type        = string
  default     = "balanceiq.com"
}

variable "subdomain" {
  description = "The subdomain for the application"
  type        = string
  default     = "demo.dev.balanceiq.com"
}

variable "vpc_id" {
  description = "VPC ID for the private hosted zone"
  type        = string
}

variable "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  type        = string
}

variable "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  type        = string
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