"""Environment-backed settings and the batch window."""

from datetime import date
from functools import lru_cache

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DateWindow(BaseModel):
    """Inclusive loading-date window for an idempotent batch.

    The same predicate is used for delete and insert, so a rerun replaces the
    slice instead of appending to it.
    """

    start_date: date
    end_date: date

    @model_validator(mode="after")
    def start_not_after_end(self) -> "DateWindow":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        return self


class Settings(BaseSettings):
    """Process configuration.

    Defaults match ``docker-compose.yml`` so a local demo starts without a
    private secret store. Override them through the environment.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "deals_bigdata"
    postgres_user: str = "etl"
    postgres_password: str = "etl"

    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_db: str = "mart"
    clickhouse_user: str = "default"
    clickhouse_password: str = "clickhouse"

    as_of: date = Field(default=date(2026, 10, 26))
    ml_seed: int = 20261026
    ml_thread_count: int = 4
    window_start: date = date(2023, 1, 1)
    window_end: date = date(2027, 12, 31)

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def window(self) -> DateWindow:
        return DateWindow(start_date=self.window_start, end_date=self.window_end)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process settings, cached for the life of the process."""

    return Settings()
