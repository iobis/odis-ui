# ODIS UI

Faceted search UI for ODIS metadata records. Read-only FastAPI backend + Svelte frontend.

Search is backed by the `odis_metadata` Elasticsearch index. See [`docs/faceted-search-plan.md`](docs/faceted-search-plan.md) and [`docs/data-sources-analysis.md`](docs/data-sources-analysis.md) for background.

## Prerequisites

- Docker and Docker Compose
- Elasticsearch with the `odis_metadata` index (runs on the host, not in this stack)

## Quick start (development)

```bash
cp .env.example .env
# Edit .env with your Elasticsearch credentials

docker compose up --build
```

Open http://localhost:8080

- Frontend: http://localhost:8080/
- API health: http://localhost:8080/api/v1/health
- API docs (Swagger): http://localhost:8080/api/docs
- API docs (ReDoc): http://localhost:8080/api/redoc

## Production

Production runs nginx (static UI + reverse proxy) and the API in Docker. TLS uses **host-installed Certbot** with certificates on the VPS filesystem, bind-mounted into the nginx container.

### Prerequisites

- A domain pointing at the VPS (DNS A/AAAA record)
- Ports **80** and **443** open in the firewall
- Docker and Docker Compose on the VPS
- Certbot on the host (not in Docker):

```bash
sudo apt update && sudo apt install -y certbot
sudo mkdir -p /var/www/certbot
```

Verify automatic renewal is scheduled (installed with the `certbot` package):

```bash
systemctl status certbot.timer
```

### First deploy with TLS

```bash
cp .env.example .env
# Set ELASTICSEARCH_* and production TLS variables:
#   DOMAIN=search.example.org
#   LETSENCRYPT_EMAIL=you@example.org
# Optional while testing: CERTBOT_STAGING=1

sudo ./scripts/init-letsencrypt.sh
```

The bootstrap script:

1. Starts the stack with HTTP only (serves the app and ACME challenges on port 80)
2. Runs `certbot certonly --webroot` on the host
3. Generates `nginx/nginx.prod.https.conf` from the template and enables HTTP → HTTPS redirect
4. Reloads nginx and installs a deploy hook at `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh`

Open `https://your-domain` after bootstrap completes.

### Manual stack control

Without TLS bootstrap (local HTTP-only on port 80):

```bash
docker compose -f docker-compose.prod.yml up --build
```

### Renewal

Renewal is automatic via the OS `certbot.timer` (typically twice daily). When a certificate is renewed, the deploy hook reloads nginx inside Docker so it picks up the new files from `/etc/letsencrypt/live/$DOMAIN/`.

Verify renewal (run on the VPS after setup):

```bash
sudo certbot renew --dry-run
sudo certbot certificates
```

Optional monitoring — exit non-zero if the cert expires within 14 days:

```bash
./scripts/check-cert-expiry.sh
```

### Troubleshooting TLS

| Symptom | Check |
|---------|--------|
| ACME challenge fails | DNS points to this host; port 80 reachable; `/.well-known/acme-challenge/` served from `/var/www/certbot` |
| HTTPS shows old cert after renew | Deploy hook exists and is executable: `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh` |
| nginx won't start | `docker compose -f docker-compose.prod.yml exec nginx nginx -t` |
| Bootstrap used staging CA | Set `CERTBOT_STAGING=1` in `.env`, or re-issue with production: `sudo certbot certonly --webroot --force-renewal ...` |

Host paths bind-mounted into nginx:

- `/etc/letsencrypt` — certificates (read-only)
- `/var/www/certbot` — ACME webroot (read-only)


## Project layout

```
odis-ui/
├── api/                    FastAPI backend
├── web/                    Vite + Svelte frontend
├── nginx/                  Reverse proxy configs
├── scripts/                Production TLS bootstrap and ops helpers
├── docker-compose.yml      Development stack
├── docker-compose.prod.yml Production stack
├── .env                    Local configuration (not committed)
└── docs/                   Design and data analysis
```

## Running tests

```bash
cd api && pip install -e ".[dev]" && pytest
```

Or via Docker:

```bash
docker compose run --rm api pytest
```

## Configuration

All settings live in the root `.env` file:

| Variable | Description |
|----------|-------------|
| `SEARCH_BACKEND` | Search adapter (`elasticsearch`) |
| `ELASTICSEARCH_URL` | ES cluster URL (`http://host.docker.internal:9200` in Docker) |
| `ES_INDEX` | Index name (default: `odis_metadata`) |
| `VITE_API_URL` | Frontend API base path (default: `/api/v1`) |
| `DOMAIN` | Production hostname for TLS (e.g. `search.example.org`) |
| `LETSENCRYPT_EMAIL` | Email for Let's Encrypt expiry notices |
| `CERTBOT_STAGING` | Set to `1` to use the Let's Encrypt staging CA during bootstrap |
