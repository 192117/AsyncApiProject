import os
from logging import config as logging_config

from pydantic import BaseSettings

from src.core.logger import LOGGING


class Settings(BaseSettings):
    """The settings class that the pydantic uses to work with environment variables."""

    ELASTIC_HOST: str = '127.0.0.1'
    ELASTIC_PORT: int = 9200
    ELASTIC_SCHEME_MOVIES: str = 'movies'
    ELASTIC_SCHEME_GENRES: str = 'genres'
    ELASTIC_SCHEME_PERSONS: str = 'persons'
    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379

    class Config:
        env_file = './src/core/.env'


settings = Settings()

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Настройки Redis
REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT

# Настройки Elasticsearch
ELASTIC_HOST = settings.ELASTIC_HOST
ELASTIC_PORT = settings.ELASTIC_PORT
ELASTIC_SCHEME_MOVIES = settings.ELASTIC_SCHEME_MOVIES
ELASTIC_SCHEME_GENRES = settings.ELASTIC_SCHEME_GENRES
ELASTIC_SCHEME_PERSONS = settings.ELASTIC_SCHEME_PERSONS

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
