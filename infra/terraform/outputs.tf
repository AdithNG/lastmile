output "app_public_ip" {
  description = "Elastic IP of the app server"
  value       = aws_eip.app.public_ip
}

output "app_public_dns" {
  description = "Public DNS of the app server"
  value       = aws_instance.app.public_dns
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (private)"
  value       = aws_db_instance.postgres.address
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint (private)"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "database_url" {
  description = "Full DATABASE_URL for the backend .env"
  value       = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}"
  sensitive   = true
}

output "redis_url" {
  description = "Full REDIS_URL for the backend .env"
  value       = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
}
