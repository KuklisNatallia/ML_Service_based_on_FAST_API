from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # POSTGRES_DB: str = "myapp_db"
    # POSTGRES_USER: str = "admin"
    # POSTGRES_PASSWORD: str = "secret123"
    # POSTGRES_HOST: str = "database"
    # POSTGRES_PORT: int = 5432

    # Настройки для MySQL
    MYSQL_DB: str = "myapp_db"
    MYSQL_USER: str = "admin"
    MYSQL_PASSWORD: str = "secret123"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306

    app_host: str = "0.0.0.0"
    app_port: str = "8080"

    SECRET_KEY: str = "SECRET_KEY"
    COOKIE_NAME: str = "auth_token"
    DEBUG: bool = True
    # @property
    # def DATABASE_URL_asyncpg(self):
    #     return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
    #
    # @property
    # def DATABASE_URL_psycopg(self):
    #     return f'postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'

    @property
    def DATABASE_URL_pymysql(self):
        return (
            f'mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}'
            f'@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}'
        )

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'  # Игнорировать лишние переменные
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()