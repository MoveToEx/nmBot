from pydantic import BaseModel
from pathlib import Path

class Config(BaseModel, extra='ignore'):
    WORKDIR: Path = Path('data/icu').absolute()
    DB_PATH: Path = WORKDIR / 'icu.json'
