from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Odoo connection settings
    ODOO_URL: str = Field(init=False)
    ODOO_DB: str = Field(init=False)
    ODOO_USER: str = Field(init=False)
    ODOO_PASSWORD: str = Field(init=False)

    # Google connection settings
    GOOGLE_CREDENTIAL_SERVICE_FILE: str = Field(init=False)
    GOOGLE_PROJECT_ID: str = Field(init=False)
    GOOGLE_LOCATION: str = Field(init=False)

    # Big Query settings
    BQ_DATASET_RAW: str = Field(init=False)
    BQ_DATASET_CONTROL: str = Field(init=False)

    # Pipeline tuning (env-overridable)
    BATCH_SIZE: int = 1000
    LOG_BACKEND: str = "gcp"

    model_config = SettingsConfigDict(env_file=".env")
