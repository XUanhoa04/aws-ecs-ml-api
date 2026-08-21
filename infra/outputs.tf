output "api_url" {
  description = "Public base URL of the deployed API."
  value       = "http://${aws_lb.api.dns_name}"
}

output "ecr_repository_url" {
  description = "Repository URL used by the build step."
  value       = aws_ecr_repository.api.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "ecs_service_name" {
  value = aws_ecs_service.api.name
}

output "cloudwatch_dashboard_url" {
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards/dashboard/${aws_cloudwatch_dashboard.api.dashboard_name}"
}
