from pydantic import BaseModel


class Config(BaseModel):
    nm_gemini_api_key: str
    nm_deepinfra_api_key: str
    nm_deepseek_api_key: str
    nm_gemini_model: str = 'gemini-1.5-pro-latest'
