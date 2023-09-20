from pydantic import BaseSettings
from pathlib import Path


class Config(BaseSettings):
    WORKDIR = Path('data/long').absolute()
    MAX_REPEAT = 3
    LONG_HUB_URL = 'http://localhost:8081'

    class Config:
        extra = "ignore"