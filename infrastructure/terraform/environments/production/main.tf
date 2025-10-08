# Production Environment for Weight Optimizer
# Deploys complete infrastructure with VPC, EC2, ALB, and security

terraform {
  required_version = ">= 1.6"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Backend configuration provided via CLI or environment variables
    # bucket = "your-terraform-state-bucket"
    # key    = "weight-optimizer/production/terraform.tfstate"
    # region = "us-east-1"
    encrypt = true
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local variables
locals {
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)
  account_id         = data.aws_caller_identity.current.account_id
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = var.owner
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  project_name           = var.project_name
  environment           = var.environment
  vpc_cidr              = var.vpc_cidr
  availability_zones    = local.availability_zones
  enable_transit_gateway = var.enable_transit_gateway
  enable_flow_logs      = var.enable_flow_logs

  tags = local.common_tags
}

# Security Groups Module
module "security" {
  source = "../../modules/security"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id

  tags = local.common_tags
}

# Application Load Balancer Module
module "alb" {
  source = "../../modules/alb"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
}

# WAF Module
module "waf" {
  source = "../../modules/waf"

  project_name = var.project_name
  environment  = var.environment
  alb_arn      = module.alb.alb_arn
}

# DNS Module
module "dns" {
  source = "../../modules/dns"

  project_name  = var.project_name
  environment   = var.environment
  domain_name   = "balanceiq.com"
  subdomain     = "demo.dev.balanceiq.com"
  vpc_id        = module.vpc.vpc_id
  alb_dns_name  = module.alb.alb_dns_name
  alb_zone_id   = module.alb.alb_zone_id
}

# EC2 Module
module "ec2" {
  source = "../../modules/ec2"

  project_name        = var.project_name
  environment         = var.environment
  aws_region          = var.aws_region
  instance_type       = var.instance_type
  key_pair_name       = var.key_pair_name
  private_subnet_id   = module.vpc.private_subnet_ids[0]
  security_group_id   = module.security.ec2_security_group_id
  root_volume_size    = var.root_volume_size
  data_volume_size    = var.data_volume_size

  tags = local.common_tags
}

# ECR Repository for Docker images
resource "aws_ecr_repository" "main" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = local.common_tags
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 production images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["main-", "v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 5 development images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["develop-"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ALB Target Group Attachments
resource "aws_lb_target_group_attachment" "app" {
  target_group_arn = module.alb.app_target_group_arn
  target_id        = module.ec2.instance_id
  port             = 80
}

resource "aws_lb_target_group_attachment" "api" {
  target_group_arn = module.alb.api_target_group_arn
  target_id        = module.ec2.instance_id
  port             = 8000
}

# DNS records are managed by the DNS module

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", "InstanceId", module.ec2.instance_id],
            [".", "NetworkIn", ".", "."],
            [".", "NetworkOut", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "EC2 Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", module.alb.alb_arn],
            [".", "TargetResponseTime", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Application Load Balancer Metrics"
          period  = 300
        }
      }
    ]
  })
}

# SSM Parameters for application configuration
resource "aws_ssm_parameter" "database_url" {
  name  = "/${var.project_name}/${var.environment}/database-url"
  type  = "SecureString"
  value = "postgresql://weight_user:${random_password.db_password.result}@localhost:5432/weight_optimizer"

  tags = local.common_tags
}

resource "aws_ssm_parameter" "secret_key" {
  name  = "/${var.project_name}/${var.environment}/secret-key"
  type  = "SecureString"
  value = random_password.secret_key.result

  tags = local.common_tags
}

# Random passwords for security
resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "random_password" "secret_key" {
  length  = 64
  special = true
}