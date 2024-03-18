from pydantic import BaseModel

class Config(BaseModel, extra='ignore'):
    data_root: str
