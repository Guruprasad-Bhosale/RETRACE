# ==============================================================================
# RETRACE AWS ECS Fargate Cluster, Task Definitions & Services
# ==============================================================================

resource "aws_ecs_cluster" "main" {
  name = "retrace-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/ecs/retrace-${var.environment}-api"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "worker_logs" {
  name              = "/ecs/retrace-${var.environment}-worker"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "frontend_logs" {
  name              = "/ecs/retrace-${var.environment}-frontend"
  retention_in_days = 14
}

# ------------------------------------------------------------------------------
# 1. API Task Definition & Service
# ------------------------------------------------------------------------------
resource "aws_ecs_task_definition" "api" {
  family                   = "retrace-${var.environment}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_api_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.repos["retrace-api"].repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "DEBUG", value = "false" },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "STORAGE_BACKEND", value = "s3" },
        { name = "STORAGE_S3_BUCKET", value = aws_s3_bucket.artifacts.id },
        { name = "STORAGE_S3_REGION", value = var.aws_region }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = "retrace-${var.environment}-api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_groups  = [aws_security_group.ecs_api.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener_rule.api_routing]
}

# ------------------------------------------------------------------------------
# 2. Worker Task Definition & Service
# ------------------------------------------------------------------------------
resource "aws_ecs_task_definition" "worker" {
  family                   = "retrace-${var.environment}-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_worker_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = "${aws_ecr_repository.repos["retrace-worker"].repository_url}:latest"
      essential = true
      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "DEBUG", value = "false" },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "STORAGE_BACKEND", value = "s3" },
        { name = "STORAGE_S3_BUCKET", value = aws_s3_bucket.artifacts.id },
        { name = "STORAGE_S3_REGION", value = var.aws_region },
        { name = "WORKER_CONCURRENCY", value = "4" },
        { name = "WORKER_BROWSER_SANDBOX", value = "true" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.worker_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "worker" {
  name            = "retrace-${var.environment}-worker-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_groups  = [aws_security_group.ecs_worker.id]
    assign_public_ip = false
  }
}

# ------------------------------------------------------------------------------
# 3. Frontend Task Definition & Service
# ------------------------------------------------------------------------------
resource "aws_ecs_task_definition" "frontend" {
  family                   = "retrace-${var.environment}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${aws_ecr_repository.repos["retrace-frontend"].repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "frontend"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "frontend" {
  name            = "retrace-${var.environment}-frontend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_groups  = [aws_security_group.ecs_frontend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.http]
}
