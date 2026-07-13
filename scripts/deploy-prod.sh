#!/usr/bin/env bash
# Pull latest code, rebuild, and restore TLS nginx configs on a bootstrapped server.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$REPO_DIR/docker-compose.prod.yml"
ENV_FILE="$REPO_DIR/.env"

cd "$REPO_DIR"

if [[ "${1:-}" == "--pull" ]]; then
  shift
  echo "==> Pulling latest changes"
  git pull "$@"
fi

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "$ENV_FILE"
  set +a
fi

if [[ -n "${DOMAIN:-}" && -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
  echo "==> Restoring TLS nginx configs for $DOMAIN"
  sed "s/__DOMAIN__/$DOMAIN/g" "$REPO_DIR/nginx/nginx.prod.https.conf.template" \
    > "$REPO_DIR/nginx/nginx.prod.https.conf"
  cp "$REPO_DIR/nginx/nginx.prod.http.redirect.conf" "$REPO_DIR/nginx/nginx.prod.http.conf"
fi

echo "==> Building and starting stack"
docker compose -f "$COMPOSE_FILE" up -d --build

if docker compose -f "$COMPOSE_FILE" ps --status running nginx >/dev/null 2>&1; then
  echo "==> Reloading nginx"
  docker compose -f "$COMPOSE_FILE" exec -T nginx nginx -s reload
fi

echo "Done."
