from pydantic import BaseSettings

from pathlib import Path

class Config(BaseSettings):
    CACHE_DIR = Path('data/sauce/cache').absolute()
    
    class Config:
        extra = "ignore"