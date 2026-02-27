# AWS Deployment Guide

## Architecture

```
Internet
   │
   ▼
EC2 (t3.small)          ← Docker Compose: backend + worker + frontend
   │       │
   ▼       ▼
RDS         ElastiCache
(postgres)  (redis)
```

All resources live in a single VPC. RDS and ElastiCache are in private subnets
(no public internet access). EC2 is in a public subnet with an Elastic IP.

---

## Prerequisites

1. [AWS CLI](https://aws.amazon.com/cli/) configured (`aws configure`)
2. [Terraform](https://www.terraform.io/downloads) ≥ 1.6
3. An EC2 key pair created in your target AWS region
4. Your public IP address (for SSH allowlist)

---

## One-Time Setup

```bash
cd infra/terraform

# Copy example vars and fill in your values
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — set db_password, ssh_key_name, allowed_ssh_cidr

# Initialize Terraform
terraform init

# Preview what will be created
terraform plan

# Deploy (~5–10 minutes)
terraform apply
```

After apply completes, Terraform outputs:

```
app_public_ip   = "X.X.X.X"
rds_endpoint    = "lastmile-postgres.xxxx.us-west-2.rds.amazonaws.com"
redis_endpoint  = "lastmile-redis.xxxx.cfg.use1.cache.amazonaws.com"
```

---

## GitHub Actions CI/CD

Add these secrets to your GitHub repo (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `EC2_HOST` | Elastic IP from Terraform output |
| `EC2_SSH_KEY` | Contents of your `.pem` private key file |

Every push to `main`:
1. Runs all 25 unit tests
2. On pass → SSHes into EC2, pulls latest code, rebuilds containers
3. Runs `alembic upgrade head` automatically
4. Health-checks `/health` endpoint before marking deploy successful

The `production` environment in GitHub requires manual approval — add reviewers
under Settings → Environments → production → Required reviewers.

---

## Add API Keys After Deploy

Once the EC2 instance is running:

```bash
ssh -i your-key.pem ec2-user@<EC2_HOST>
cd /opt/lastmile
nano .env   # Set ORS_API_KEY and SECRET_KEY
docker compose restart backend worker
```

---

## Cost Estimate

| Resource | Type | Monthly Cost |
|----------|------|-------------|
| EC2 | t3.small | ~$15 |
| RDS | db.t3.micro | ~$13 (or free tier) |
| ElastiCache | cache.t3.micro | ~$12 (or free tier) |
| Elastic IP | — | Free while attached |
| Data transfer | — | ~$1 |
| **Total** | | **~$40/mo** |

Free tier covers RDS + ElastiCache for the first 12 months on a new account.

---

## Teardown

```bash
cd infra/terraform
terraform destroy
```
