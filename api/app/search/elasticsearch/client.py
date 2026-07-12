from elasticsearch import AsyncElasticsearch

from app.config import Settings


def create_client(settings: Settings) -> AsyncElasticsearch:
    kwargs: dict = {"hosts": [settings.elasticsearch_url]}
    if settings.elasticsearch_user:
        kwargs["basic_auth"] = (settings.elasticsearch_user, settings.elasticsearch_password)
    return AsyncElasticsearch(**kwargs)
