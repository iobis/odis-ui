#!/usr/bin/env bash
# Bootstrap Let's Encrypt TLS on the VPS host (run once with sudo).
# Certbot runs on the host; nginx stays in Docker and reads certs via bind mounts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$REPO_DIR/docker-compose.prod.yml"
ENV_FILE="$REPO_DIR/.env"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo $0" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy .env.example and set DOMAIN / LETSENCRYPT_EMAIL." >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

DOMAIN="${DOMAIN:-}"
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-}"
CERTBOT_STAGING="${CERTBOT_STAGING:-0}"

if [[ -z "$DOMAIN" || -z "$LETSENCRYPT_EMAIL" ]]; then
  echo "Set DOMAIN and LETSENCRYPT_EMAIL in $ENV_FILE" >&2
  exit 1
fi

if ! command -v certbot >/dev/null 2>&1; then
  echo "Install certbot on the host first: apt update && apt install -y certbot" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required." >&2
  exit 1
fi

echo "==> Checking DNS for $DOMAIN"
if ! getent hosts "$DOMAIN" >/dev/null 2>&1; then
  echo "Warning: $DOMAIN does not resolve — fix DNS before continuing." >&2
fi

mkdir -p /var/www/certbot
chmod 755 /var/www/certbot

STAGING_ARGS=()
if [[ "$CERTBOT_STAGING" == "1" ]]; then
  echo "==> Using Let's Encrypt staging CA (CERTBOT_STAGING=1)"
  STAGING_ARGS=(--staging)
fi

echo "==> Starting stack (HTTP bootstrap — app on port 80, no HTTPS redirect yet)"
cd "$REPO_DIR"
docker compose -f "$COMPOSE_FILE" up -d --build

echo "==> Verifying ACME webroot is reachable via nginx"
TEST_FILE="preflight-$(date +%s)"
mkdir -p /var/www/certbot/.well-known/acme-challenge
echo ok > "/var/www/certbot/.well-known/acme-challenge/$TEST_FILE"
if ! curl -sf "http://127.0.0.1/.well-known/acme-challenge/$TEST_FILE" | grep -q ok; then
  echo "ACME webroot check failed — nginx is not serving /.well-known/acme-challenge/." >&2
  echo "Ensure the image removes /etc/nginx/conf.d/default.conf (see web/Dockerfile)." >&2
  rm -f "/var/www/certbot/.well-known/acme-challenge/$TEST_FILE"
  exit 1
fi
rm -f "/var/www/certbot/.well-known/acme-challenge/$TEST_FILE"

echo "==> Requesting certificate for $DOMAIN"
certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$LETSENCRYPT_EMAIL" \
  --agree-tos \
  --non-interactive \
  --keep-until-expiring \
  "${STAGING_ARGS[@]}"

echo "==> Enabling HTTPS nginx config"
sed "s/__DOMAIN__/$DOMAIN/g" "$REPO_DIR/nginx/nginx.prod.https.conf.template" \
  > "$REPO_DIR/nginx/nginx.prod.https.conf"

echo "==> Enabling HTTP → HTTPS redirect"
cp "$REPO_DIR/nginx/nginx.prod.http.redirect.conf" "$REPO_DIR/nginx/nginx.prod.http.conf"

echo "==> Reloading nginx"
docker compose -f "$COMPOSE_FILE" exec -T nginx nginx -s reload

HOOK_DIR="/etc/letsencrypt/renewal-hooks/deploy"
HOOK_PATH="$HOOK_DIR/reload-nginx.sh"
mkdir -p "$HOOK_DIR"
sed "s|__REPO_DIR__|$REPO_DIR|g" "$REPO_DIR/scripts/reload-nginx.sh" > "$HOOK_PATH"
chmod 755 "$HOOK_PATH"

echo "==> Deploy hook installed at $HOOK_PATH"
echo "==> Certificate status:"
certbot certificates

echo ""
echo "Done. Verify renewal with: sudo certbot renew --dry-run"
