from pydantic import BaseModel


class Config(BaseModel):
    gemini_api_key: str
    gemini_model: str = 'gemini-1.5-pro-latest'
