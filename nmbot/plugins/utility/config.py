from pydantic import BaseModel


class Config(BaseModel):
    controller: int | None = None
    
