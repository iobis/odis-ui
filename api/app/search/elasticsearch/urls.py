from collections.abc import Callable


def elasticsearch_document_url(base_url: str, index: str, record_id: str) -> str:
    return f"{base_url.rstrip('/')}/{index}/_doc/{record_id}"


DocumentUrlFor = Callable[[str], str]
