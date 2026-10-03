# ==============================================================================
# RETRACE Security Groups (Least-Privilege Network Isolation)
# ==============================================================================

# ALB Security Group (Public Entrypoint)
resource "aws_security_group" "alb" {
  name        = "retrace-${var.environment}-alb-sg"
  description = "Controls ingress from internet to Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Egress to ECS tasks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "retrace-${var.environment}-alb-sg"
  }
}

# ECS API Security Group
resource "aws_security_group" "ecs_api" {
  name        = "retrace-${var.environment}-ecs-api-sg"
  description = "Allows ingress only from ALB to API container"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Inbound from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "retrace-${var.environment}-ecs-api-sg"
  }
}

# ECS Frontend Security Group
resource "aws_security_group" "ecs_frontend" {
  name        = "retrace-${var.environment}-ecs-frontend-sg"
  description = "Allows ingress from ALB to Frontend Nginx"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Inbound from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "retrace-${var.environment}-ecs-frontend-sg"
  }
}

# ECS Worker Security Group (No Inbound Required)
resource "aws_security_group" "ecs_worker" {
  name        = "retrace-${var.environment}-ecs-worker-sg"
  description = "Strict outbound-only security group for background worker tasks"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "retrace-${var.environment}-ecs-worker-sg"
  }
}

# RDS PostgreSQL Security Group
resource "aws_security_group" "rds" {
  name        = "retrace-${var.environment}-rds-sg"
  description = "Allows PostgreSQL traffic strictly from API and Worker tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from ECS API"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_api.id]
  }

  ingress {
    description     = "PostgreSQL from ECS Worker"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_worker.id]
  }

  tags = {
    Name = "retrace-${var.environment}-rds-sg"
  }
}

# ElastiCache Redis Security Group
resource "aws_security_group" "redis" {
  name        = "retrace-${var.environment}-redis-sg"
  description = "Allows Redis traffic strictly from API and Worker tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from ECS API"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_api.id]
  }

  ingress {
    description     = "Redis from ECS Worker"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_worker.id]
  }

  tags = {
    Name = "retrace-${var.environment}-redis-sg"
  }
}
