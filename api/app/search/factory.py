from app.config import Settings
from app.search.base import SearchBackend
from app.search.elasticsearch.backend import ElasticsearchBackend


def create_search_backend(settings: Settings) -> SearchBackend:
    backend_name = settings.search_backend.lower()
    if backend_name == "elasticsearch":
        return ElasticsearchBackend(settings)
    raise ValueError(f"Unknown search backend: {settings.search_backend}")
