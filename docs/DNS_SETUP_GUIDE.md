# DNS Setup Guide - Boeing 737 Weight & Balance Optimizer

## Quick DNS Deployment Strategy

### Overview
This guide provides rapid DNS setup using Route 53 private hosted zones with `demo.dev.balanceiq.com` for immediate demo deployment without external DNS verification delays.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DNS ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 ROUTE 53 PRIVATE ZONE                      │ │
│  │                   balanceiq.com                             │ │
│  │                                                             │ │
│  │  ┌─────────────────┐    ┌─────────────────┐                │ │
│  │  │ demo.dev        │    │ api.demo.dev    │                │ │
│  │  │ .balanceiq.com  │    │ .balanceiq.com  │                │ │
│  │  │                 │    │                 │                │ │
│  │  │ Frontend App    │    │ API Endpoints   │                │ │
│  │  └─────────────────┘    └─────────────────┘                │ │
│  │           │                       │                        │ │
│  │           └───────────┬───────────┘                        │ │
│  │                       │                                    │ │
│  │  ┌─────────────────────▼─────────────────┐                 │ │
│  │  │         ws.demo.dev.balanceiq.com     │                 │ │
│  │  │         WebSocket Connections         │                 │ │
│  │  └───────────────────────────────────────┘                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                │                                │
│  ┌─────────────────────────────▼───────────────────────────────┐ │
│  │              APPLICATION LOAD BALANCER                      │ │
│  │                                                             │ │
│  │  ┌─────────────────┐    ┌─────────────────┐                │ │
│  │  │ Target Group    │    │ Target Group    │                │ │
│  │  │ Frontend:80     │    │ API:8000        │                │ │
│  │  └─────────────────┘    └─────────────────┘                │ │
│  │           │                       │                        │ │
│  │           └───────────┬───────────┘                        │ │
│  │                       │                                    │ │
│  │  ┌─────────────────────▼─────────────────┐                 │ │
│  │  │            EC2 Instance               │                 │ │
│  │  │         Private Subnet                │                 │ │
│  │  └───────────────────────────────────────┘                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Steps

### 1. Infrastructure Deployment
```bash
cd infrastructure/terraform/environments/production
terraform init
terraform plan
terraform apply
```

### 2. DNS Configuration
The Terraform deployment automatically creates:
- **Private Hosted Zone**: `balanceiq.com`
- **A Records**: 
  - `demo.dev.balanceiq.com` → ALB
  - `api.demo.dev.balanceiq.com` → ALB  
  - `ws.demo.dev.balanceiq.com` → ALB

### 3. ALB Listener Rules
- **Default**: Routes to frontend (port 80)
- **api.*** : Routes to API backend (port 8000)
- **ws.*** : Routes to WebSocket server (port 8000)

### 4. Quick Access URLs
After deployment:
- **Frontend**: `http://demo.dev.balanceiq.com`
- **API**: `http://api.demo.dev.balanceiq.com`
- **WebSocket**: `ws://ws.demo.dev.balanceiq.com`

## Configuration Details

### Route 53 Private Zone
```hcl
resource "aws_route53_zone" "private" {
  name = "balanceiq.com"
  
  vpc {
    vpc_id = var.vpc_id
  }
}
```

### DNS Records
```hcl
# Main application
resource "aws_route53_record" "app" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "demo.dev.balanceiq.com"
  type    = "A"
  
  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# API endpoint
resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "api.demo.dev.balanceiq.com"
  type    = "A"
  
  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# WebSocket endpoint
resource "aws_route53_record" "ws" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "ws.demo.dev.balanceiq.com"
  type    = "A"
  
  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}
```

### ALB Configuration
```hcl
# Default listener (frontend)
resource "aws_lb_listener" "web" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# API routing rule
resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.web.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
  
  condition {
    host_header {
      values = ["api.*"]
    }
  }
}

# WebSocket routing rule
resource "aws_lb_listener_rule" "websocket" {
  listener_arn = aws_lb_listener.web.arn
  priority     = 200
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
  
  condition {
    host_header {
      values = ["ws.*"]
    }
  }
}
```

## Advantages of This Approach

### 1. **Rapid Deployment** (< 10 minutes)
- No external DNS verification required
- Private hosted zone setup is immediate
- ALB provides instant load balancing

### 2. **Professional Demo URLs**
- Clean, branded domain names
- Separate endpoints for different services
- Easy to remember and share

### 3. **Production-Ready Architecture**
- Scalable ALB with health checks
- Private subnet security
- Route 53 DNS resolution

### 4. **Cost Effective**
- Private hosted zone: $0.50/month
- ALB: ~$16/month
- No additional DNS service costs

## Testing & Validation

### 1. DNS Resolution Test
```bash
# From within VPC (EC2 instance)
nslookup demo.dev.balanceiq.com
nslookup api.demo.dev.balanceiq.com
nslookup ws.demo.dev.balanceiq.com
```

### 2. Health Check Validation
```bash
# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>
```

### 3. Application Access Test
```bash
# Frontend
curl -I http://demo.dev.balanceiq.com

# API health check
curl http://api.demo.dev.balanceiq.com/health

# WebSocket connection test
wscat -c ws://ws.demo.dev.balanceiq.com/ws
```

## Troubleshooting

### Common Issues

#### 1. DNS Resolution Fails
```bash
# Check hosted zone configuration
aws route53 list-hosted-zones
aws route53 list-resource-record-sets --hosted-zone-id <zone-id>
```

#### 2. ALB Health Check Failures
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn <arn>

# Check security group rules
aws ec2 describe-security-groups --group-ids <sg-id>
```

#### 3. Application Not Accessible
```bash
# Check ALB listener rules
aws elbv2 describe-listeners --load-balancer-arn <alb-arn>
aws elbv2 describe-rules --listener-arn <listener-arn>
```

### Quick Fixes

#### Update DNS Records
```bash
cd infrastructure/terraform/environments/production
terraform apply -target=module.dns
```

#### Restart ALB Target Registration
```bash
terraform apply -target=aws_lb_target_group_attachment.app
terraform apply -target=aws_lb_target_group_attachment.api
```

## Production Considerations

### 1. **SSL/TLS Certificates**
For production deployment, add SSL certificates:
```hcl
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn
}
```

### 2. **Public Hosted Zone Migration**
When ready for production:
1. Create public hosted zone for `balanceiq.com`
2. Update DNS records to point to public zone
3. Configure domain registrar nameservers

### 3. **CDN Integration**
Add CloudFront for global performance:
```hcl
resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name = module.alb.alb_dns_name
    origin_id   = "ALB-${var.project_name}"
  }
}
```

## Deployment Timeline

| Step | Duration | Description |
|------|----------|-------------|
| 1. Terraform Init | 1 min | Initialize Terraform state |
| 2. Infrastructure Deploy | 5-7 min | VPC, ALB, EC2, DNS creation |
| 3. Application Deploy | 2-3 min | Docker container deployment |
| 4. Health Check Validation | 1-2 min | ALB target health verification |
| **Total** | **9-13 min** | **Complete system ready** |

This DNS setup provides immediate access to a professionally configured demo environment with `demo.dev.balanceiq.com` while maintaining production-ready architecture and scalability.