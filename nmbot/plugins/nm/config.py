from pydantic import BaseModel
from typing import Optional

class Config(BaseModel):
    nm_gemini_api_key: str | None = None
    nm_deepinfra_api_key: str | None = None
    nm_deepseek_api_key: str | None = None
    
