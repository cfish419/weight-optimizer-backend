output "hosted_zone_id" {
  description = "ID of the Route 53 hosted zone"
  value       = aws_route53_zone.public.zone_id
}

output "hosted_zone_name_servers" {
  description = "Name servers for the hosted zone"
  value       = aws_route53_zone.public.name_servers
}

output "app_domain" {
  description = "Full domain name for the application"
  value       = var.subdomain
}

output "api_domain" {
  description = "Full domain name for the API"
  value       = "api.${var.subdomain}"
}

output "websocket_domain" {
  description = "Full domain name for WebSocket connections"
  value       = "ws.${var.subdomain}"
}