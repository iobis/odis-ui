#!/usr/bin/env bash
# Exit non-zero if the production cert expires within DAYS (default 14).
# Usage: ./scripts/check-cert-expiry.sh [domain] [days]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

DOMAIN="${1:-}"
DAYS="${2:-14}"

if [[ -z "$DOMAIN" && -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "$ENV_FILE"
  set +a
  DOMAIN="${DOMAIN:-}"
fi

if [[ -z "$DOMAIN" ]]; then
  echo "Usage: $0 [domain] [days]" >&2
  echo "Or set DOMAIN in .env" >&2
  exit 2
fi

CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
if [[ ! -f "$CERT" ]]; then
  echo "Certificate not found: $CERT" >&2
  exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required." >&2
  exit 2
fi

echo "Domain: $DOMAIN"
echo "Checking expiry within $DAYS day(s)..."

if openssl x509 -checkend $((DAYS * 86400)) -noout -in "$CERT"; then
  echo "OK: certificate valid for at least $DAYS more day(s)"
  exit 0
fi

echo "WARNING: certificate expires in less than $DAYS days" >&2
exit 1
