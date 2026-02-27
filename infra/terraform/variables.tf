variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-west-2"
}

variable "project" {
  description = "Project name prefix for all resource names and tags"
  type        = string
  default     = "lastmile"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

variable "ec2_instance_type" {
  description = "EC2 instance type for the app server"
  type        = string
  default     = "t3.small"  # 2 vCPU, 2 GB — sufficient for the demo app
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"  # Free-tier eligible
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "lastmile"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "lastmile_user"
}

variable "db_password" {
  description = "PostgreSQL master password — supply via TF_VAR_db_password or tfvars"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"  # Free-tier eligible
}

variable "ssh_key_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH into the EC2 instance (your IP)"
  type        = string
  default     = "0.0.0.0/0"  # Restrict to your IP in production
}
