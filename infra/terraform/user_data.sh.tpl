#!/bin/bash
set -euo pipefail

# ─── System packages ──────────────────────────────────────────────────────────
yum update -y
yum install -y docker git

# Start Docker and enable on boot
systemctl enable --now docker
usermod -aG docker ec2-user

# Docker Compose v2 plugin
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# ─── Application ──────────────────────────────────────────────────────────────
APP_DIR=/opt/lastmile

# Clone repo (replace with your actual GitHub repo URL)
git clone https://github.com/AdithNG/lastmile.git "$APP_DIR"
cd "$APP_DIR"

# Write production .env — values injected by Terraform templatefile()
cat > .env <<EOF
ENVIRONMENT=production
DATABASE_URL=${db_url}
REDIS_URL=${redis_url}
CELERY_BROKER_URL=${redis_url}/0
CELERY_RESULT_BACKEND=${redis_url}/1
# Add your secrets below after initial deploy:
SECRET_KEY=REPLACE_WITH_RANDOM_32_CHAR_STRING
ORS_API_KEY=
VITE_API_BASE_URL=http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000
VITE_WS_BASE_URL=ws://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000
EOF

# Bring up all services (no frontend build args needed — Vite env baked at build time)
docker compose up --build -d

# ─── Systemd service — restart on reboot ──────────────────────────────────────
cat > /etc/systemd/system/lastmile.service <<UNIT
[Unit]
Description=LastMile Docker Compose
After=docker.service
Requires=docker.service

[Service]
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/lib/docker/cli-plugins/docker-compose up
ExecStop=/usr/local/lib/docker/cli-plugins/docker-compose down
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT

systemctl enable lastmile
