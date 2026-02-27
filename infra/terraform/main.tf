terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment after creating the S3 bucket + DynamoDB table for remote state:
  # backend "s3" {
  #   bucket         = "lastmile-tf-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-west-2"
  #   dynamodb_table = "lastmile-tf-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
}

# ─────────────────────────────────────────────
# Data sources
# ─────────────────────────────────────────────

data "aws_availability_zones" "available" {
  state = "available"
}

# Latest Amazon Linux 2023 AMI
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}
