variable "aws_region" {
  description = "AWS region used by the lab."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used as a prefix for bootstrap resources."
  type        = string
  default     = "ecs-ml-lab"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.project_name))
    error_message = "project_name must be 3-21 lowercase letters, digits, or hyphens."
  }
}

variable "github_repository" {
  description = "GitHub repository allowed to assume the deployment role (owner/name)."
  type        = string
}

variable "create_github_oidc_provider" {
  description = "Create the account-wide GitHub Actions OIDC provider. Set false if it already exists."
  type        = bool
  default     = true
}

variable "existing_github_oidc_provider_arn" {
  description = "Existing GitHub OIDC provider ARN when create_github_oidc_provider is false."
  type        = string
  default     = ""

  validation {
    condition = (
      var.create_github_oidc_provider ||
      can(regex("^arn:aws:iam::[0-9]{12}:oidc-provider/token.actions.githubusercontent.com$", var.existing_github_oidc_provider_arn))
    )
    error_message = "Provide a valid existing GitHub OIDC provider ARN."
  }
}
