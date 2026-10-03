# ==============================================================================
# RETRACE Terraform Variables
# ==============================================================================

variable "environment" {
  description = "Target deployment environment (staging, production)"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "Target AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for multi-AZ topology"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# ECS Sizing
variable "api_cpu" {
  description = "Fargate CPU units for API container (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "api_memory" {
  description = "Fargate memory in MB for API container"
  type        = number
  default     = 2048
}

variable "api_desired_count" {
  description = "Desired count of API tasks"
  type        = number
  default     = 2
}

variable "worker_cpu" {
  description = "Fargate CPU units for Worker container (2048 = 2 vCPU for browser execution)"
  type        = number
  default     = 2048
}

variable "worker_memory" {
  description = "Fargate memory in MB for Worker container"
  type        = number
  default     = 4096
}

variable "worker_desired_count" {
  description = "Desired count of background worker tasks"
  type        = number
  default     = 2
}

variable "frontend_cpu" {
  description = "Fargate CPU units for Frontend container"
  type        = number
  default     = 512
}

variable "frontend_memory" {
  description = "Fargate memory in MB for Frontend container"
  type        = number
  default     = 1024
}

variable "frontend_desired_count" {
  description = "Desired count of frontend tasks"
  type        = number
  default     = 2
}

# RDS Configuration
variable "db_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.t4g.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB for PostgreSQL"
  type        = number
  default     = 50
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "retrace_prod"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "retrace_admin"
}

# ElastiCache Redis
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t4g.small"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes in Redis cluster"
  type        = number
  default     = 2
}
