#!/bin/sh
# Deploy hook: reload nginx after certbot renews a certificate.
# Installed by scripts/init-letsencrypt.sh at:
#   /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
set -eu

REPO_DIR="__REPO_DIR__"
cd "$REPO_DIR"
docker compose -f docker-compose.prod.yml exec -T nginx nginx -s reload
