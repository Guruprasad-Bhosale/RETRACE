# ==============================================================================
# RETRACE Amazon ElastiCache Redis Replication Group
# ==============================================================================

resource "aws_elasticache_subnet_group" "redis" {
  name       = "retrace-${var.environment}-redis-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id          = "retrace-${var.environment}-redis"
  description                   = "Redis cluster for RETRACE stream queues"
  node_type                     = var.redis_node_type
  num_cache_clusters            = var.redis_num_cache_nodes
  parameter_group_name          = "default.redis7"
  port                          = 6379
  subnet_group_name             = aws_elasticache_subnet_group.redis.name
  security_group_ids            = [aws_security_group.redis.id]
  automatic_failover_enabled    = var.redis_num_cache_nodes > 1 ? true : false
  multi_az_enabled              = var.redis_num_cache_nodes > 1 ? true : false
  transit_encryption_enabled    = false
  at_rest_encryption_enabled   = true

  tags = {
    Name = "retrace-${var.environment}-redis"
  }
}
