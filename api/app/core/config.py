from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="REGISTRY_", extra="ignore")

    database_url: str = "postgresql+psycopg://registry:registry@localhost:5432/registry"


settings = Settings()
