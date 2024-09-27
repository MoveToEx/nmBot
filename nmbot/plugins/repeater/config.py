from pydantic import BaseModel


class Config(BaseModel):
    repeater_threshold: int = 3

    