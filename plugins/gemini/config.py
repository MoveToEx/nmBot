from pydantic import BaseModel


class Config(BaseModel):
    gemini_api_key: str
