# CI/CD Guide - Boeing 737 Weight & Balance Optimizer

## Overview

Dual-pipeline CI/CD strategy with separate workflows for application and infrastructure deployment. This approach ensures clean separation of concerns, enhanced security, and optimized deployment processes.

## Pipeline Architecture

### Separation Strategy
```
┌─────────────────────────────────────────────────────────────────┐
│                    MONOREPO STRUCTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Application Code          Infrastructure Code                  │
│  ┌─────────────────┐      ┌─────────────────────────────────┐   │
│  │ src/            │      │ infrastructure/terraform/       │   │
│  │ api/            │      │ ├── modules/                    │   │
│  │ services/       │      │ │   ├── vpc/                    │   │
│  │ frontend/       │      │ │   ├── ec2/                    │   │
│  │ docker/         │      │ │   └── alb/                    │   │
│  └─────────────────┘      │ └── environments/               │   │
│          │                │     ├── production/             │   │
│          │                │     └── staging/                │   │
│          │                └─────────────────────────────────┘   │
│          │                          │                           │
│          ▼                          ▼                           │
│  ┌─────────────────┐      ┌─────────────────────────────────┐   │
│  │ App CI/CD       │      │ Infrastructure CI/CD            │   │
│  │ Pipeline        │      │ Pipeline                        │   │
│  └─────────────────┘      └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Application CI/CD Pipeline

### File: `.github/workflows/app-ci-cd.yml`

### Trigger Conditions
```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'api/**'
      - 'services/**'
      - 'data/**'
      - 'frontend/**'
      - 'docker/**'
      - 'requirements.txt'
      - 'package.json'
```

### Pipeline Stages

#### 1. Testing & Quality Assurance
```yaml
backend-test:
  - Python unit tests (pytest)
  - Integration tests
  - Code coverage reporting (Codecov)
  - Performance benchmarks

frontend-test:
  - React component tests (Jest)
  - End-to-end tests (Cypress)
  - Build verification
  - Bundle size analysis
```

#### 2. Security Scanning
```yaml
security-scan:
  - Trivy vulnerability scanning
  - SAST analysis
  - Dependency checking
  - License compliance
```

#### 3. Build & Registry
```yaml
docker-build:
  - Multi-architecture builds (AMD64, ARM64)
  - ECR repository push
  - Image tagging strategy
  - SBOM generation
  - Image signing
```

#### 4. Deployment
```yaml
deploy-production:
  - EC2 deployment via SSM
  - Health checks and verification
  - Rollback capabilities
  - Performance monitoring
```

### Environment Variables
```bash
# Required GitHub Secrets
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
ECR_REPOSITORY=weight-optimizer
CODECOV_TOKEN=<codecov-token>
```

## Infrastructure CI/CD Pipeline

### File: `.github/workflows/infrastructure-ci-cd.yml`

### Trigger Conditions
```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'infrastructure/**'
  pull_request:
    branches: [main]
    paths:
      - 'infrastructure/**'
```

### Pipeline Stages

#### 1. Validation & Planning
```yaml
terraform-plan:
  - Terraform format checking
  - Configuration validation
  - Plan generation
  - PR comment with plan details
```

#### 2. Security & Compliance
```yaml
terraform-security:
  - Checkov security scanning
  - TFSec policy validation
  - CIS benchmark compliance
  - SARIF report generation

terraform-cost:
  - Infracost estimation
  - Cost impact analysis
  - Budget threshold alerts
  - PR cost comments
```

#### 3. Infrastructure Deployment
```yaml
terraform-apply:
  - State locking and encryption
  - Terraform apply execution
  - Output parameter storage
  - Infrastructure verification
```

### Environment Variables
```bash
# Required GitHub Secrets
TF_STATE_BUCKET=<terraform-state-bucket>
INFRACOST_API_KEY=<infracost-api-key>
CHECKOV_API_KEY=<checkov-api-key>
```

## Deployment Environments

### Production Environment
- **Branch**: `main`
- **Approval**: Required for infrastructure changes
- **Monitoring**: Full CloudWatch integration
- **Backup**: Automated EBS snapshots

### Staging Environment
- **Branch**: `develop`
- **Approval**: Automatic deployment
- **Resources**: Smaller instance sizes
- **Data**: Anonymized production data

## Security Implementation

### Pipeline Security
```yaml
# GitHub Environment Protection
production:
  required_reviewers: 2
  wait_timer: 5  # minutes
  deployment_branches:
    - main

production-infrastructure:
  required_reviewers: 3
  wait_timer: 10  # minutes
  deployment_branches:
    - main
```

### Secret Management
- **GitHub Secrets**: Encrypted at rest
- **AWS IAM**: Least privilege access
- **Terraform State**: S3 encryption + DynamoDB locking
- **Container Images**: Signed and scanned

### Access Control
```yaml
# IAM Policy for CI/CD
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "ecr:*",
        "ssm:*",
        "cloudwatch:*",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    }
  ]
}
```

## Monitoring & Observability

### Pipeline Monitoring
- **GitHub Actions**: Workflow success/failure rates
- **Deployment Metrics**: Frequency, duration, success rate
- **Security Alerts**: Vulnerability detection notifications
- **Cost Alerts**: Budget threshold notifications

### Application Monitoring
- **Health Checks**: Multi-level verification
- **Performance**: Response time tracking
- **Errors**: Exception monitoring and alerting
- **Business Metrics**: Weight optimization success rates

## Rollback Procedures

### Application Rollback
```bash
# Automatic rollback on health check failure
if ! curl -f https://api.weight-optimizer.com/health; then
  echo "Health check failed, rolling back..."
  docker pull $ECR_REGISTRY/weight-optimizer:previous
  docker stop weight-optimizer
  docker run -d --name weight-optimizer $ECR_REGISTRY/weight-optimizer:previous
fi
```

### Infrastructure Rollback
```bash
# Manual rollback procedure
cd infrastructure/terraform/environments/production
terraform plan -destroy -target=aws_instance.main
terraform apply -target=aws_instance.main
```

## Performance Optimization

### Build Optimization
- **Docker Layer Caching**: GitHub Actions cache
- **Parallel Jobs**: Concurrent testing and building
- **Artifact Reuse**: Shared build artifacts
- **Conditional Execution**: Path-based triggering

### Deployment Optimization
- **Blue-Green Deployment**: Zero-downtime updates
- **Health Check Optimization**: Fast failure detection
- **Resource Preallocation**: Faster startup times
- **CDN Integration**: Static asset optimization

## Troubleshooting Guide

### Common Pipeline Issues

#### 1. Test Failures
```bash
# Debug test failures
pytest tests/ -v --tb=short
npm test -- --verbose

# Check test coverage
pytest --cov=src tests/
```

#### 2. Build Failures
```bash
# Docker build debugging
docker build --no-cache -t debug-image .
docker run -it debug-image /bin/bash

# ECR push issues
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
```

#### 3. Deployment Failures
```bash
# Check EC2 instance status
aws ec2 describe-instances --instance-ids $INSTANCE_ID

# Review deployment logs
aws ssm get-command-invocation --command-id $COMMAND_ID --instance-id $INSTANCE_ID
```

#### 4. Infrastructure Issues
```bash
# Terraform debugging
terraform plan -detailed-exitcode
terraform apply -auto-approve -lock-timeout=10m

# State file issues
terraform force-unlock $LOCK_ID
```

### Emergency Procedures

#### 1. Pipeline Failure
- Check GitHub Actions logs
- Verify AWS service status
- Review recent commits
- Contact on-call engineer

#### 2. Security Alert
- Stop all deployments
- Review security scan results
- Patch vulnerabilities
- Re-run security validation

#### 3. Infrastructure Outage
- Check AWS service health
- Review CloudWatch alarms
- Execute disaster recovery plan
- Communicate with stakeholders

## Best Practices

### Code Quality
- **Pre-commit Hooks**: Automated formatting and linting
- **Branch Protection**: Required reviews and status checks
- **Semantic Versioning**: Consistent release tagging
- **Changelog**: Automated release notes

### Security
- **Dependency Updates**: Automated security patches
- **Secret Rotation**: Regular credential updates
- **Access Reviews**: Quarterly permission audits
- **Compliance Scanning**: Continuous policy validation

### Performance
- **Resource Monitoring**: Track pipeline resource usage
- **Optimization Reviews**: Monthly performance analysis
- **Capacity Planning**: Proactive scaling decisions
- **Cost Management**: Regular cost optimization reviews

## Metrics & KPIs

### Pipeline Metrics
- **Deployment Frequency**: Daily deployments target
- **Lead Time**: Code to production < 2 hours
- **MTTR**: Mean time to recovery < 15 minutes
- **Change Failure Rate**: < 5% deployment failures

### Quality Metrics
- **Test Coverage**: > 80% code coverage
- **Security Scan**: Zero high/critical vulnerabilities
- **Performance**: < 2 second response times
- **Availability**: 99.9% uptime target

This CI/CD implementation provides enterprise-grade automation with security, reliability, and performance optimization built-in from the ground up.