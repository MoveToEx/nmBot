from pydantic import BaseSettings
from pathlib import Path


class Config(BaseSettings):
    WORKDIR = Path('data/long').absolute()
    MAX_REPEAT = 3

    class Config:
        extra = "ignore"