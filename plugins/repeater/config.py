from pydantic import BaseSettings


class Config(BaseSettings):
    REPEAT_THRESHOLD = 3

    class Config:
        extra = "ignore"