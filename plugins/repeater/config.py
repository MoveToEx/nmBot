from pydantic import BaseModel


class Config(BaseModel):
    REPEAT_THRESHOLD: int = 3

    