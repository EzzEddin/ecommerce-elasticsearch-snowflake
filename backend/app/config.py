import re

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


def _validate_sql_identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(
            f"Invalid SQL identifier: '{value}'. "
            "Only alphanumeric characters and underscores are allowed."
        )
    return value


class Settings(BaseSettings):
    # PostgreSQL
    database_url: str = Field(default="")
    database_url_sync: str = Field(default="")

    # Elasticsearch
    elasticsearch_url: str = Field(default="http://localhost:9200")
    elasticsearch_index_prefix: str = Field(default="ecom")

    # Snowflake
    snowflake_account: str = Field(default="")
    snowflake_user: str = Field(default="")
    snowflake_password: str = Field(default="")
    snowflake_database: str = Field(default="ECOM_ANALYTICS")
    snowflake_schema: str = Field(default="PUBLIC")
    snowflake_warehouse: str = Field(default="COMPUTE_WH")
    snowflake_role: str = Field(default="SYSADMIN")

    @field_validator("snowflake_database", "snowflake_schema", "snowflake_warehouse", "snowflake_role")
    @classmethod
    def validate_snowflake_identifiers(cls, v: str) -> str:
        if v:
            return _validate_sql_identifier(v)
        return v

    # App
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
