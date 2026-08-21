variable "aws_region" {
  description = "AWS region used by the lab."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short resource-name prefix."
  type        = string
  default     = "ecs-ml-lab"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.project_name))
    error_message = "project_name must be 3-21 lowercase letters, digits, or hyphens."
  }
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,8}$", var.environment))
    error_message = "environment must be 2-9 lowercase letters, digits, or hyphens."
  }
}

variable "image_tag" {
  description = "Immutable application image tag, normally the Git commit SHA."
  type        = string

  validation {
    condition     = length(var.image_tag) >= 7 && length(var.image_tag) <= 128
    error_message = "image_tag must contain 7-128 characters."
  }
}

variable "desired_count" {
  description = "Number of tasks normally kept running."
  type        = number
  default     = 1

  validation {
    condition     = var.desired_count >= 1 && var.desired_count <= 3
    error_message = "desired_count must be between 1 and 3 for this lab."
  }
}
