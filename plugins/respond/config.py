from pydantic import BaseSettings
from pathlib import Path

class Config(BaseSettings):
    IMAGES_PATH = Path('data/respond/images').absolute()

    class Config:
        extra = "ignore"