# ─────────────────────────────────────────────
# RDS — PostgreSQL 15
# ─────────────────────────────────────────────

resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = { Name = "${var.project}-db-subnet-group", Project = var.project }
}

resource "aws_db_instance" "postgres" {
  identifier        = "${var.project}-postgres"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = var.db_instance_class
  allocated_storage = 20
  storage_type      = "gp2"

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # No public internet access — EC2 connects via private VPC
  publicly_accessible = false

  # Backups: 7-day retention
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  # Skip final snapshot for dev/demo — set to false in real prod
  skip_final_snapshot = true

  tags = { Name = "${var.project}-postgres", Project = var.project, Environment = var.environment }
}
