from pydantic import BaseModel


class Config(BaseModel):
    wolframalpha_api_key: str