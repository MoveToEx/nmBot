from pydantic import BaseModel

class Config(BaseModel, extra='ignore'):
    pass
