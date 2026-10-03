# ==============================================================================
# RETRACE Terraform Outputs
# ==============================================================================

output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "artifact_bucket_name" {
  description = "Name of the S3 bucket for artifact persistence"
  value       = aws_s3_bucket.artifacts.id
}

output "ecr_repository_urls" {
  description = "Map of ECR repository URLs for API, Worker, and Frontend"
  value = {
    for k, v in aws_ecr_repository.repos : k => v.repository_url
  }
}

output "rds_endpoint" {
  description = "PostgreSQL RDS connection endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}
