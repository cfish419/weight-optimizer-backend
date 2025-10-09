# Terraform Deployment Guide

## Required Variables

### Variables That MUST Be Set

**1. AWS Key Pair (Required)**
```bash
# Create key pair in AWS Console or CLI first
aws ec2 create-key-pair --key-name weight-optimizer-prod --query 'KeyMaterial' --output text > weight-optimizer-prod.pem
chmod 400 weight-optimizer-prod.pem
```

**2. Alert Emails (Recommended)**
Edit `terraform.tfvars`:
```hcl
alert_emails = [
  "your-email@company.com",
  "ops-team@company.com"
]
```

### Variables With Defaults (Optional to Override)

All other variables have sensible defaults but can be customized:

```hcl
# Infrastructure sizing
instance_type      = "t3.medium"    # Can upgrade to t3.large, etc.
root_volume_size   = 20             # GB
data_volume_size   = 50             # GB

# Network configuration
vpc_cidr = "10.0.0.0/24"           # Adjust if conflicts with existing VPCs

# Feature toggles
enable_transit_gateway = true       # Set false if not needed
enable_flow_logs      = true        # Set false to reduce costs
```

## Deployment Steps

### 1. Prerequisites
```bash
# Install Terraform
brew install terraform  # macOS
# or download from https://terraform.io

# Configure AWS credentials
aws configure
# or set environment variables:
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

### 2. Initialize Terraform
```bash
cd infrastructure/terraform/environments/production
terraform init
```

### 3. Configure Variables
```bash
# Edit terraform.tfvars with your values
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

### 4. Plan Deployment
```bash
terraform plan
```

### 5. Deploy Infrastructure
```bash
terraform apply
```

## Variable Configuration Options

### Minimal Configuration (Uses Defaults)
```hcl
# terraform.tfvars - Minimal setup
key_pair_name = "your-existing-key-pair"
alert_emails = ["your-email@company.com"]
```

### Full Configuration (All Options)
```hcl
# terraform.tfvars - Full customization
project_name = "weight-optimizer"
environment  = "production"
aws_region   = "us-east-1"

# Infrastructure
instance_type      = "t3.large"
root_volume_size   = 30
data_volume_size   = 100
key_pair_name      = "my-production-key"

# Network
vpc_cidr = "10.1.0.0/24"

# Features
enable_transit_gateway = false
enable_flow_logs      = true

# Monitoring
alert_emails = [
  "ops@company.com",
  "devops@company.com",
  "alerts@company.com"
]

# Tags
owner = "Platform Team"
```

## Environment Variables (Alternative)

Instead of terraform.tfvars, you can use environment variables:

```bash
export TF_VAR_key_pair_name="weight-optimizer-prod"
export TF_VAR_alert_emails='["ops@company.com"]'
export TF_VAR_instance_type="t3.large"
export TF_VAR_owner="DevOps Team"
```

## Backend Configuration

For production, configure S3 backend:

```bash
# Create S3 bucket for state
aws s3 mb s3://your-terraform-state-bucket

# Initialize with backend
terraform init \
  -backend-config="bucket=your-terraform-state-bucket" \
  -backend-config="key=weight-optimizer/production/terraform.tfstate" \
  -backend-config="region=us-east-1"
```

## Cost Estimation

### Default Configuration (~$146/month)
- t3.medium EC2: ~$30/month
- ALB: ~$22/month  
- NAT Gateway: ~$45/month
- EBS volumes: ~$10/month
- Data transfer: ~$20/month
- CloudWatch: ~$10/month
- Other services: ~$9/month

### Optimized Configuration (~$85/month)
```hcl
instance_type = "t3.small"
enable_transit_gateway = false
# Use single AZ deployment for dev/test
```

## Troubleshooting

### Common Issues

**1. Key Pair Not Found**
```
Error: InvalidKeyPair.NotFound
```
Solution: Create the key pair first or update `key_pair_name` variable.

**2. VPC CIDR Conflicts**
```
Error: InvalidVpc.Range
```
Solution: Change `vpc_cidr` to non-conflicting range.

**3. Missing Permissions**
```
Error: UnauthorizedOperation
```
Solution: Ensure AWS credentials have required permissions.

### Required AWS Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "elasticloadbalancing:*",
        "route53:*",
        "cloudwatch:*",
        "logs:*",
        "sns:*",
        "ssm:*",
        "ecr:*",
        "wafv2:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Summary

**Required Actions:**
1. ✅ Create AWS key pair
2. ✅ Set alert emails in terraform.tfvars
3. ✅ Run `terraform init && terraform apply`

**All other variables have defaults and will work out of the box!**