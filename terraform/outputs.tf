output "api_gateway_url" {
  description = "Public HTTPS endpoint for the application."
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "alb_dns_name" {
  description = "Internal ALB DNS name."
  value       = aws_lb.main.dns_name
}

output "rds_endpoint" {
  description = "RDS Postgres connection endpoint."
  value       = aws_db_instance.postgres.endpoint
}

output "ecr_spa_repository_url" {
  description = "ECR repository URL for the SPA image."
  value       = aws_ecr_repository.spa.repository_url
}

output "ecr_api_repository_url" {
  description = "ECR repository URL for the API image."
  value       = aws_ecr_repository.api.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.main.name
}
