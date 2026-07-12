"""Field mappings for the odis_metadata index."""

TITLE_FIELDS = ("name^3", "schema:name^3")
TEXT_FIELDS = (
    *TITLE_FIELDS,
    "description",
    "schema:description",
    "keywords^2",
    "schema:keywords^2",
)
TYPE_FIELD = "@type"
DATASOURCE_FIELD = "datasource_id"
