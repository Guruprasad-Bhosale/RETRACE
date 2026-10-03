# ==============================================================================
# RETRACE Amazon RDS PostgreSQL 16
# ==============================================================================

resource "aws_db_subnet_group" "rds" {
  name       = "retrace-${var.environment}-rds-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "retrace-${var.environment}-rds-subnet-group"
  }
}

resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "retrace/${var.environment}/database"
  description = "RDS PostgreSQL Master Credentials"
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    engine   = "postgres"
    host     = aws_db_instance.postgres.address
    port     = 5432
    username = var.db_username
    password = random_password.db_password.result
    database = var.db_name
  })
}

resource "aws_db_instance" "postgres" {
  identifier                  = "retrace-${var.environment}-postgres"
  engine                      = "postgres"
  engine_version              = "16.1"
  instance_class              = var.db_instance_class
  allocated_storage           = var.db_allocated_storage
  max_allocated_storage       = 200
  storage_type                = "gp3"
  storage_encrypted           = true
  db_name                     = var.db_name
  username                    = var.db_username
  password                    = random_password.db_password.result
  db_subnet_group_name        = aws_db_subnet_group.rds.name
  vpc_security_group_ids      = [aws_security_group.rds.id]
  publicly_accessible         = false
  multi_az                    = var.environment == "production" ? true : false
  backup_retention_period     = 7
  auto_minor_version_upgrade  = true
  deletion_protection         = var.environment == "production" ? true : false
  skip_final_snapshot         = var.environment == "production" ? false : true
  final_snapshot_identifier   = "retrace-${var.environment}-postgres-final"

  tags = {
    Name = "retrace-${var.environment}-postgres"
  }
}
