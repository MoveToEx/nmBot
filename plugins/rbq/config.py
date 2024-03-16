from pydantic import BaseModel
from pathlib import Path


class Config(BaseModel):
    WORKDIR: Path = Path('data/rbq').absolute()

    
