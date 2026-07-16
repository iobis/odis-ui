from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    search_backend: str = "elasticsearch"
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_user: str = ""
    elasticsearch_password: str = ""
    es_index: str = "odis_metadata"
    es_catalogue_index: str = "catalogue"

    # Used when SEARCH_BACKEND=gleaner (multi-index cluster, one index per source)
    gleaner_elasticsearch_url: str = "http://odis.org:9400"
    gleaner_elasticsearch_user: str = ""
    gleaner_elasticsearch_password: str = ""
    # Comma-separated; empty = default gleaner-obps,gleaner-medin,gleaner-obis,gleaner-oe
    gleaner_indices: str = ""


settings = Settings()
