from pydantic import BaseModel, Extra

from pathlib import Path


class Config(BaseModel, extra=Extra.ignore):
    WORKDIR: Path = Path('data/animethesaurus').absolute()
    DB_PATH: Path = WORKDIR / 'data.json'

