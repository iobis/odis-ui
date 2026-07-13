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


settings = Settings()
