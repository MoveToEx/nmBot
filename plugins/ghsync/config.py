from pydantic import BaseModel, Extra

from pathlib import Path

class Config(BaseModel, extra=Extra.ignore):
    WORKDIR: Path = Path('data/ghsync').absolute()
    DB_PATH: Path = WORKDIR / 'commits.json'
    REPO: list[dict] = [
        {
            "file": Path('data/icu/icu.json').absolute(),
            "name": 'ICU',
            "api": "https://api.github.com/repos/MoveToEx/ICU/contents/icu.json"
        },
        {
            "file": Path('data/animethesaurus/data.json').absolute(),
            "name": 'AnimeTheSaurus',
            "api": "https://api.github.com/repos/MoveToEx/AnimeThesaurus/contents/data.json"
        }
    ]
