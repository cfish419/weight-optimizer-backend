resource "aws_route53_zone" "public" {
  name = var.domain_name

  tags = {
    Name        = "${var.project_name}-public-zone"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_route53_record" "app" {
  zone_id = aws_route53_zone.public.zone_id
  name    = var.subdomain
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "api.${var.subdomain}"
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "ws" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "ws.${var.subdomain}"
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}