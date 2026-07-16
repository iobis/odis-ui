from app.config import Settings
from app.search.base import SearchBackend
from app.search.elasticsearch.backend import ElasticsearchBackend
from app.search.gleaner.backend import GleanerBackend

KNOWN_BACKENDS: tuple[str, ...] = ("elasticsearch", "gleaner")


def create_search_backend(settings: Settings, backend_name: str | None = None) -> SearchBackend:
    name = (backend_name or settings.search_backend).lower()
    if name == "elasticsearch":
        return ElasticsearchBackend(settings)
    if name == "gleaner":
        return GleanerBackend(settings)
    raise ValueError(
        f"Unknown search backend: {name}. Use 'elasticsearch' (ODIS metadata) or 'gleaner'."
    )


def create_all_backends(settings: Settings) -> dict[str, SearchBackend]:
    """Instantiate every known backend so the UI can switch without restarting."""
    return {name: create_search_backend(settings, name) for name in KNOWN_BACKENDS}
