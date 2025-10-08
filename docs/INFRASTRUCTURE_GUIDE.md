# Infrastructure Guide - Boeing 737 Weight & Balance Optimizer

## Overview

Enterprise-grade AWS infrastructure with separate CI/CD pipelines for application and infrastructure deployment. Features a secure /24 VPC with private subnet EC2 deployment, automated scaling, and comprehensive monitoring.

## Architecture Components

### Network Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        VPC (10.0.0.0/24)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐                    ┌─────────────────┐     │
│  │ Public Subnet   │                    │ Public Subnet   │     │
│  │ 10.0.0.0/28     │                    │ 10.0.0.16/28    │     │
│  │ ┌─────────────┐ │                    │ ┌─────────────┐ │     │
│  │ │     ALB     │ │                    │ │ NAT Gateway │ │     │
│  │ └─────────────┘ │                    │ └─────────────┘ │     │
│  └─────────────────┘                    └─────────────────┘     │
│           │                                       │             │
│  ┌─────────────────┐                    ┌─────────────────┐     │
│  │ Private Subnet  │                    │ Private Subnet  │     │
│  │ 10.0.0.32/28    │                    │ 10.0.0.48/28    │     │
│  │ ┌─────────────┐ │                    │                 │     │
│  │ │ EC2 Instance│ │                    │   (Reserved)    │     │
│  │ │   Docker    │ │                    │                 │     │
│  │ └─────────────┘ │                    │                 │     │
│  └─────────────────┘                    └─────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Internet Gateway  │
                    └───────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Transit Gateway   │
                    │   (Optional)      │
                    └───────────────────┘
```

### Infrastructure Components

#### VPC Module (`infrastructure/terraform/modules/vpc/`)
- **CIDR Block**: 10.0.0.0/24 (256 IP addresses)
- **Subnets**: 2 public, 2 private across 2 AZs
- **Gateways**: Internet Gateway, NAT Gateways (HA), Transit Gateway (optional)
- **Security**: VPC Flow Logs, encrypted traffic

#### EC2 Module (`infrastructure/terraform/modules/ec2/`)
- **Instance**: t3.medium in private subnet
- **Storage**: Encrypted EBS volumes (root + data)
- **Runtime**: Docker with application containers
- **Monitoring**: CloudWatch Agent with custom metrics
- **Security**: IAM roles, security groups, hardened OS

#### ALB Module (`infrastructure/terraform/modules/alb/`)
- **Load Balancer**: Application Load Balancer in public subnets
- **SSL/TLS**: Certificate integration with Route 53
- **Health Checks**: Application health monitoring
- **Routing**: Path-based routing for API and frontend

#### Security Module (`infrastructure/terraform/modules/security/`)
- **Security Groups**: Least privilege access controls
- **Network ACLs**: Additional network-level security
- **IAM Policies**: Fine-grained permissions
- **Encryption**: At-rest and in-transit encryption

## CI/CD Pipelines

### Application Pipeline (`.github/workflows/app-ci-cd.yml`)

**Triggers**: Changes to application code (`src/`, `api/`, `services/`, `frontend/`, `docker/`)

**Stages**:
1. **Testing**
   - Backend unit and integration tests
   - Frontend React testing
   - Code coverage reporting

2. **Security Scanning**
   - Trivy vulnerability scanning
   - SAST analysis
   - Dependency checking

3. **Build & Push**
   - Multi-architecture Docker builds
   - ECR repository push
   - SBOM generation

4. **Deployment**
   - Production deployment via SSM
   - Health checks and verification
   - Rollback capabilities

### Infrastructure Pipeline (`.github/workflows/infrastructure-ci-cd.yml`)

**Triggers**: Changes to infrastructure code (`infrastructure/`)

**Stages**:
1. **Validation**
   - Terraform format checking
   - Configuration validation
   - Plan generation

2. **Security & Compliance**
   - Checkov security scanning
   - TFSec policy validation
   - Cost estimation (Infracost)

3. **Deployment**
   - Terraform apply with state locking
   - Output parameter storage
   - Infrastructure verification

## Deployment Environments

### Production Environment
- **Location**: `infrastructure/terraform/environments/production/`
- **State**: S3 backend with encryption and locking
- **Monitoring**: CloudWatch dashboards and alarms
- **Backup**: Automated EBS snapshots

### Staging Environment
- **Location**: `infrastructure/terraform/environments/staging/`
- **Purpose**: Pre-production testing and validation
- **Resources**: Smaller instance sizes for cost optimization
- **Data**: Anonymized production data

## Security Implementation

### Network Security
- **Private Subnets**: Application servers isolated from internet
- **NAT Gateways**: Controlled outbound internet access
- **Security Groups**: Port-specific access controls
- **VPC Flow Logs**: Network traffic monitoring

### Application Security
- **Container Scanning**: Automated vulnerability detection
- **Secrets Management**: AWS SSM Parameter Store
- **IAM Roles**: Least privilege access
- **Encryption**: All data encrypted at rest and in transit

### Infrastructure Security
- **State Encryption**: Terraform state encrypted in S3
- **Access Control**: IAM policies for infrastructure access
- **Audit Logging**: CloudTrail for all API calls
- **Compliance**: Automated policy validation

## Monitoring & Observability

### CloudWatch Integration
- **Metrics**: EC2, ALB, and custom application metrics
- **Logs**: Centralized logging with retention policies
- **Dashboards**: Real-time operational visibility
- **Alarms**: Proactive alerting for issues

### Application Monitoring
- **Health Checks**: Multi-level health verification
- **Performance**: Response time and throughput tracking
- **Errors**: Error rate and exception monitoring
- **Business Metrics**: Weight optimization success rates

## Cost Management

### Resource Optimization
- **Right-sizing**: Appropriate instance types for workload
- **Reserved Instances**: Cost savings for predictable workloads
- **Spot Instances**: Development and testing cost reduction
- **Auto Scaling**: Dynamic resource allocation

### Cost Controls
- **Budgets**: AWS Budget alerts for cost overruns
- **Tagging**: Resource cost allocation and tracking
- **Lifecycle Policies**: Automated cleanup of unused resources
- **Infracost**: PR-level cost impact analysis

### Estimated Monthly Costs
```
Production Environment:
├── EC2 t3.medium (24/7)        $30
├── NAT Gateway (2 AZs)         $32
├── Application Load Balancer   $18
├── EBS Storage (50GB)          $5
├── Data Transfer               $5
├── CloudWatch Logs/Metrics     $3
└── Route 53 (if used)          $1
Total: ~$94/month

Staging Environment: ~$47/month (50% of production)
```

## Disaster Recovery

### Backup Strategy
- **EBS Snapshots**: Daily automated backups
- **Database Backups**: Point-in-time recovery
- **Configuration Backup**: Infrastructure as Code
- **Cross-Region**: Optional multi-region deployment

### Recovery Procedures
- **RTO**: 15 minutes (Recovery Time Objective)
- **RPO**: 1 hour (Recovery Point Objective)
- **Automation**: Terraform-based infrastructure recreation
- **Testing**: Monthly disaster recovery drills

## Scaling Strategy

### Horizontal Scaling
- **Auto Scaling Groups**: Dynamic EC2 scaling
- **Load Balancer**: Traffic distribution
- **Database**: Read replicas for performance
- **Caching**: Redis for session and data caching

### Vertical Scaling
- **Instance Types**: Easy upgrade path (t3.medium → t3.large → t3.xlarge)
- **Storage**: EBS volume expansion without downtime
- **Memory**: Application container resource limits
- **CPU**: Burstable performance instances

## Maintenance Procedures

### Regular Maintenance
- **Security Updates**: Automated OS patching
- **Application Updates**: CI/CD automated deployments
- **Certificate Renewal**: Automated SSL/TLS renewal
- **Log Rotation**: Automated log cleanup

### Monitoring Tasks
- **Cost Review**: Monthly cost analysis
- **Security Audit**: Quarterly security reviews
- **Performance Review**: Monthly performance optimization
- **Capacity Planning**: Quarterly growth planning

## Troubleshooting Guide

### Common Issues
1. **Application Deployment Failures**
   - Check ECR image availability
   - Verify IAM permissions
   - Review CloudWatch logs

2. **Network Connectivity Issues**
   - Verify security group rules
   - Check NAT Gateway status
   - Review route table configurations

3. **Performance Issues**
   - Monitor CloudWatch metrics
   - Check application logs
   - Review resource utilization

### Emergency Procedures
1. **Service Outage**
   - Check ALB health checks
   - Verify EC2 instance status
   - Review application logs

2. **Security Incident**
   - Isolate affected resources
   - Review VPC Flow Logs
   - Contact security team

3. **Data Loss**
   - Restore from EBS snapshots
   - Recover from database backups
   - Verify data integrity

## Getting Started

### Prerequisites
- AWS CLI configured
- Terraform >= 1.6 installed
- GitHub repository access
- Domain name (optional)

### Initial Setup
1. **Configure Backend**
   ```bash
   # Create S3 bucket for Terraform state
   aws s3 mb s3://your-terraform-state-bucket
   ```

2. **Set Environment Variables**
   ```bash
   export TF_VAR_project_name="weight-optimizer"
   export TF_VAR_environment="production"
   export TF_VAR_owner="your-team"
   ```

3. **Deploy Infrastructure**
   ```bash
   cd infrastructure/terraform/environments/production
   terraform init
   terraform plan
   terraform apply
   ```

4. **Deploy Application**
   - Push code to main branch
   - CI/CD pipeline automatically deploys
   - Verify deployment via health checks

This infrastructure provides enterprise-grade security, scalability, and reliability for the Weight & Balance Optimizer application.