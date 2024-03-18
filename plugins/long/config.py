from pydantic import BaseModel
from pathlib import Path


class Config(BaseModel):
    data_root: str
    long_upstream: str = 'https://longhub.top/'