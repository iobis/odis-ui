from collections.abc import Callable
from urllib.parse import quote


def elasticsearch_document_url(base_url: str, index: str, record_id: str) -> str:
    # Document ids may be URLs (Gleaner); encode so the ES REST path is valid.
    return f"{base_url.rstrip('/')}/{index}/_doc/{quote(record_id, safe='')}"


DocumentUrlFor = Callable[[str], str]
