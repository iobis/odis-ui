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

```bash
docker compose -f docker-compose.prod.yml up --build
```

Open http://localhost (port 80).

## Project layout

```
odis-ui/
├── api/                    FastAPI backend
├── web/                    Vite + Svelte frontend
├── nginx/                  Reverse proxy configs
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
