output "state_bucket_name" {
  description = "S3 bucket used by the application Terraform backend."
  value       = aws_s3_bucket.terraform_state.id
}

output "github_role_arn" {
  description = "Role ARN stored as the GitHub repository variable AWS_ROLE_ARN."
  value       = aws_iam_role.github_deploy.arn
}

output "aws_region" {
  value = var.aws_region
}
