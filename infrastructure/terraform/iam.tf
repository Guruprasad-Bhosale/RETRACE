# ==============================================================================
# RETRACE Least-Privilege IAM Roles
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. ECS Task Execution Role (for pulling images & fetching secrets)
# ------------------------------------------------------------------------------
resource "aws_iam_role" "ecs_execution_role" {
  name = "retrace-${var.environment}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "ecs-tasks.amazonaws.com" }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_standard" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ------------------------------------------------------------------------------
# 2. ECS API Task Role (Runtime permissions for API container)
# ------------------------------------------------------------------------------
resource "aws_iam_role" "ecs_api_task_role" {
  name = "retrace-${var.environment}-api-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "ecs-tasks.amazonaws.com" }
      }
    ]
  })
}

resource "aws_iam_policy" "s3_artifact_policy" {
  name        = "retrace-${var.environment}-s3-artifact-policy"
  description = "Scoped S3 access for RETRACE artifacts"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:HeadBucket"
        ]
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_s3" {
  role       = aws_iam_role.ecs_api_task_role.name
  policy_arn = aws_iam_policy.s3_artifact_policy.arn
}

# ------------------------------------------------------------------------------
# 3. ECS Worker Task Role (Runtime permissions for analysis worker)
# ------------------------------------------------------------------------------
resource "aws_iam_role" "ecs_worker_task_role" {
  name = "retrace-${var.environment}-worker-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "ecs-tasks.amazonaws.com" }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "worker_s3" {
  role       = aws_iam_role.ecs_worker_task_role.name
  policy_arn = aws_iam_policy.s3_artifact_policy.arn
}
