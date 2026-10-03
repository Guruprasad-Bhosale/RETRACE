# ==============================================================================
# RETRACE S3 Artifact Storage Bucket
# ==============================================================================

resource "aws_s3_bucket" "artifacts" {
  bucket        = "retrace-${var.environment}-artifacts-${var.aws_region}"
  force_destroy = false

  tags = {
    Name = "retrace-${var.environment}-artifacts"
  }
}

# Block all public access (Strict Private Bucket)
resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Server-side encryption by default
resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Versioning for disaster recovery & rollback safety
resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle rule to transition old non-current objects
resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}
