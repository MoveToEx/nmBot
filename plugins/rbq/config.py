from pydantic import BaseSettings
from pathlib import Path


class Config(BaseSettings):
    WORKDIR = Path('data/rbq').absolute()

    class Config:
        extra = "ignore"
