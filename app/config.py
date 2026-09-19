from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    db_schema: str = "mediashelf"
    tmdb_api_key: str | None = None

    # extra="ignore": .env may carry deployment-only settings (e.g. PORT, read
    # by the Docker CMD's shell substitution, never by this app's Python code)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
