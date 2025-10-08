# EC2 Module for Weight Optimizer
# Creates EC2 instance in private subnet with Docker and application deployment

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data source for latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# IAM Role for EC2 instance
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-ec2-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Policy for EC2 instance
resource "aws_iam_role_policy" "ec2_policy" {
  name = "${var.project_name}-ec2-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath",
          "ssm:PutParameter",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.ec2_role.name

  tags = {
    Name        = "${var.project_name}-ec2-profile"
    Environment = var.environment
    Project     = var.project_name
  }
}

# User Data Script for EC2 initialization
locals {
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    project_name = var.project_name
    environment  = var.environment
    ecr_region   = var.aws_region
  }))
}

# EC2 Instance in Private Subnet
resource "aws_instance" "main" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  vpc_security_group_ids = [var.security_group_id]
  subnet_id              = var.private_subnet_id
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = local.user_data

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size
    encrypted             = true
    delete_on_termination = true

    tags = {
      Name        = "${var.project_name}-root-volume"
      Environment = var.environment
      Project     = var.project_name
    }
  }

  # Additional EBS volume for application data
  ebs_block_device {
    device_name           = "/dev/sdf"
    volume_type           = "gp3"
    volume_size           = var.data_volume_size
    encrypted             = true
    delete_on_termination = false

    tags = {
      Name        = "${var.project_name}-data-volume"
      Environment = var.environment
      Project     = var.project_name
    }
  }

  tags = {
    Name        = "${var.project_name}-app-server"
    Environment = var.environment
    Project     = var.project_name
    Role        = "application-server"
    Backup      = "daily"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# CloudWatch Log Group for application logs
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ec2/${var.project_name}"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-app-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Agent configuration
resource "aws_ssm_parameter" "cloudwatch_config" {
  name  = "/aws/ec2/${var.project_name}/cloudwatch-config"
  type  = "String"
  value = jsonencode({
    agent = {
      metrics_collection_interval = 60
      run_as_user                 = "root"
    }
    logs = {
      logs_collected = {
        files = {
          collect_list = [
            {
              file_path      = "/var/log/weight-optimizer/app.log"
              log_group_name = aws_cloudwatch_log_group.app_logs.name
              log_stream_name = "{instance_id}/app"
              timezone       = "UTC"
            },
            {
              file_path      = "/var/log/docker.log"
              log_group_name = aws_cloudwatch_log_group.app_logs.name
              log_stream_name = "{instance_id}/docker"
              timezone       = "UTC"
            }
          ]
        }
      }
    }
    metrics = {
      namespace = "WeightOptimizer/EC2"
      metrics_collected = {
        cpu = {
          measurement = ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"]
          metrics_collection_interval = 60
        }
        disk = {
          measurement = ["used_percent"]
          metrics_collection_interval = 60
          resources = ["*"]
        }
        diskio = {
          measurement = ["io_time", "read_bytes", "write_bytes", "reads", "writes"]
          metrics_collection_interval = 60
          resources = ["*"]
        }
        mem = {
          measurement = ["mem_used_percent"]
          metrics_collection_interval = 60
        }
        netstat = {
          measurement = ["tcp_established", "tcp_time_wait"]
          metrics_collection_interval = 60
        }
      }
    }
  })

  tags = {
    Name        = "${var.project_name}-cloudwatch-config"
    Environment = var.environment
    Project     = var.project_name
  }
}