from pydantic import BaseModel

class Config(BaseModel):
    saucenao_api_key: str
    
    