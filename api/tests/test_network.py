from app.domain.network import classify_odiscat_hits, truncate_errors


def test_truncate_errors_under_limit() -> None:
    assert truncate_errors(["a", "b"]) == ["a", "b"]


def test_truncate_errors_over_limit() -> None:
    messages = [f"err-{i}" for i in range(7)]
    assert truncate_errors(messages) == [
        "err-0",
        "err-1",
        "err-2",
        "err-3",
        "err-4",
        "… and 2 more",
    ]


def test_classify_healthy_unresponsive_parsing_and_missing_source() -> None:
    hits = [
        {
            "_id": "healthy",
            "_source": {
                "name": "Healthy Node",
                "url": "https://healthy.example/sitemap.xml",
                "last_indexed": "2026-09-01T12:00:00Z",
                "summoner_stored": 1200,
                "summoner_errors": 0,
                "summoner_pages_seen": 10,
                "summoner_messages": [],
            },
        },
        {
            "_id": "down",
            "_source": {
                "name": "Down Node",
                "url": "https://down.example/sitemap.xml",
                "summoner_stored": 0,
                "summoner_errors": 2,
                "summoner_pages_seen": 0,
                "summoner_messages": ["timed out", "no page URLs from sitemap"],
            },
        },
        {
            "_id": "parse",
            "_source": {
                "name": "Parse Node",
                "url": "https://parse.example/sitemap.xml",
                "dateModified": "2026-08-15T08:00:00Z",
                "summoner_stored": 40,
                "summoner_errors": 3,
                "summoner_pages_seen": 5,
                "summoner_messages": ["no application/ld+json script tags found"],
            },
        },
        {"_id": "broken"},
    ]

    status = classify_odiscat_hits(hits)

    assert status.total_nodes == 4
    assert status.unresponsive_count == 1
    assert status.parsing_error_count == 1
    assert status.summoner_error_count == 1
    assert status.total_error_nodes == 3
    assert status.unresponsive[0].name == "Down Node"
    assert status.unresponsive[0].errors == ["timed out", "no page URLs from sitemap"]
    assert status.parsing_errors[0].name == "Parse Node"
    assert [n.name for n in status.all_nodes] == [
        "broken",
        "Down Node",
        "Healthy Node",
        "Parse Node",
    ]
    healthy = next(n for n in status.all_nodes if n.id == "healthy")
    assert healthy.last_indexed == "2026-09-01T12:00:00Z"
    assert healthy.summoner_stored == 1200
    assert healthy.responsive is True
    parse = next(n for n in status.all_nodes if n.id == "parse")
    assert parse.last_indexed == "2026-08-15T08:00:00Z"
    assert parse.summoner_stored == 40
    assert parse.responsive is True
    down = next(n for n in status.all_nodes if n.id == "down")
    assert down.responsive is False
    broken = next(n for n in status.all_nodes if n.id == "broken")
    assert broken.responsive is False
    assert status.updated_at


def test_classify_truncates_long_error_lists() -> None:
    hits = [
        {
            "_id": "many",
            "_source": {
                "name": "Many Errors",
                "url": "https://many.example/sitemap.xml",
                "summoner_errors": 8,
                "summoner_pages_seen": 0,
                "summoner_messages": [f"error {i}" for i in range(8)],
            },
        }
    ]
    status = classify_odiscat_hits(hits)
    assert status.unresponsive[0].errors[-1] == "… and 3 more"
    assert len(status.unresponsive[0].errors) == 6


def test_classify_sorts_error_lists_by_name() -> None:
    def failing(node_id: str, name: str, pages_seen: int) -> dict:
        return {
            "_id": node_id,
            "_source": {
                "name": name,
                "summoner_errors": 1,
                "summoner_pages_seen": pages_seen,
                "summoner_messages": ["error"],
            },
        }

    hits = [
        failing("d2", "zeta down", 0),
        failing("p2", "Zeta Parse", 3),
        failing("d1", "Alpha Down", 0),
        failing("p1", "alpha parse", 3),
    ]
    status = classify_odiscat_hits(hits)
    assert [n.name for n in status.unresponsive] == ["Alpha Down", "zeta down"]
    assert [n.name for n in status.parsing_errors] == ["alpha parse", "Zeta Parse"]
