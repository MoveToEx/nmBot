from pydantic import BaseModel, Extra

from pathlib import Path


class Config(BaseModel, extra=Extra.ignore):
    WORKDIR = Path('data/animethesaurus').absolute()
    DB_PATH = WORKDIR / 'data.json'

