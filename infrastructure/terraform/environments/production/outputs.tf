output "dns_info" {
  description = "DNS configuration information"
  value = {
    hosted_zone_id = module.dns.hosted_zone_id
    app_domain     = module.dns.app_domain
    api_domain     = module.dns.api_domain
    websocket_domain = module.dns.websocket_domain
  }
}

output "alb_info" {
  description = "Application Load Balancer information"
  value = {
    dns_name = module.alb.alb_dns_name
    zone_id  = module.alb.alb_zone_id
  }
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = module.ec2.instance_id
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.main.repository_url
}