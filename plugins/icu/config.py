from pydantic import BaseModel, Extra
from pathlib import Path

class Config(BaseModel, extra=Extra.ignore):
    WORKDIR = Path('data/icu').absolute()
    DB_PATH = WORKDIR / 'icu.json'
