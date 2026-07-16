BACKEND_LABELS: dict[str, str] = {
    "elasticsearch": "ODIS",
    "gleaner": "Gleaner",
}


def backend_label(backend_id: str) -> str:
    return BACKEND_LABELS.get(backend_id, backend_id)
