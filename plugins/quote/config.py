from pydantic import BaseModel

class Config(BaseModel):
    data_root: str
    quote_avatar_size: int = 96
    quote_avatar_padding: int = 16
    quote_max_width: int = 512
    quote_border_radius: int = 32
    quote_background_color: str = '#1f1f1f'
    quote_foreground_color: str = '#ffffff'
    quote_padding: int = 48
