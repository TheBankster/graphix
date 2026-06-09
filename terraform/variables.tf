variable "project_name" {
  description = "Short name used to prefix resource names."
  type        = string
  default     = "webapp"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)."
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "AZs to spread subnets across."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "spa_image" {
  description = "Container image for the SPA frontend."
  type        = string
  default     = "webapp/spa:latest"
}

variable "api_image" {
  description = "Container image for the API backend."
  type        = string
  default     = "webapp/api:latest"
}

variable "db_name" {
  description = "Initial Postgres database name."
  type        = string
  default     = "webapp"
}

variable "db_username" {
  description = "Master username for the RDS Postgres instance."
  type        = string
  default     = "webapp_admin"
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t3.medium"
}

variable "sendgrid_api_key" {
  description = "SendGrid API key for transactional email. Provide via TF_VAR or a secrets backend; do not commit real values."
  type        = string
  default     = "SG.PLACEHOLDER_TEST_KEY"
  sensitive   = true
}

variable "payment_processor_api_key" {
  description = "API key for the external payment processor. Provide via TF_VAR or a secrets backend; do not commit real values."
  type        = string
  default     = "pk_test_PLACEHOLDER"
  sensitive   = true
}

variable "payment_processor_url" {
  description = "Base URL for the external payment processor API."
  type        = string
  default     = "https://api.payments.example.com"
}
