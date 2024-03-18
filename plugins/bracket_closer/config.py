from pydantic import BaseModel


class Config(BaseModel):
    data_root: str
