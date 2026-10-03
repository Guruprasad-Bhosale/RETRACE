# RETRACE Least-Privilege IAM Architecture

## 1. Role Separation

RETRACE enforces strict role separation so that no single component has blanket administrative privileges.

```text
┌────────────────────────────────┐       ┌────────────────────────────────┐
│      ECS Task Execution Role   │       │       ECS API Task Role        │
├────────────────────────────────┤       ├────────────────────────────────┤
│ • ecr:GetAuthorizationToken    │       │ • s3:GetObject                 │
│ • ecr:BatchGetImage            │       │ • s3:PutObject                 │
│ • logs:CreateLogStream         │       │ • s3:ListBucket                │
│ • logs:PutLogEvents            │       │ • logs:PutLogEvents            │
│ • secretsmanager:GetSecretValue│       │ • Zero AWS Admin Permissions   │
└────────────────────────────────┘       └────────────────────────────────┘

┌────────────────────────────────┐       ┌────────────────────────────────┐
│     ECS Worker Task Role       │       │    CI/CD Deployment Role       │
├────────────────────────────────┤       ├────────────────────────────────┤
│ • s3:GetObject                 │       │ • ecr:GetDownloadUrlForLayer   │
│ • s3:PutObject                 │       │ • ecr:PutImage                 │
│ • s3:DeleteObject              │       │ • ecs:UpdateService            │
│ • s3:ListBucket                │       │ • ecs:DescribeServices         │
│ • logs:PutLogEvents            │       │ • Zero DB/S3 Data Access       │
└────────────────────────────────┘       └────────────────────────────────┘
```

## 2. Resource Scoping

All S3 policies are strictly scoped to `arn:aws:s3:::retrace-${var.environment}-artifacts-*` with no wildcards outside the dedicated artifact bucket.
