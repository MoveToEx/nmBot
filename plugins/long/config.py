from pydantic import BaseModel
from pathlib import Path


class Config(BaseModel):
    long_workdir: Path = Path('data/long').absolute()
    long_upstream: str = 'https://longhub.top/'