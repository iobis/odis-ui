from elasticsearch import AsyncElasticsearch

from app.config import Settings

# Fail fast when a cluster is unreachable (health probes + search).
_REQUEST_TIMEOUT_SECONDS = 3


def create_client(settings: Settings) -> AsyncElasticsearch:
    kwargs: dict = {
        "hosts": [settings.elasticsearch_url],
        "request_timeout": _REQUEST_TIMEOUT_SECONDS,
        "max_retries": 0,
        "retry_on_timeout": False,
    }
    if settings.elasticsearch_user:
        kwargs["basic_auth"] = (settings.elasticsearch_user, settings.elasticsearch_password)
    return AsyncElasticsearch(**kwargs)
