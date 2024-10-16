from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, mapped_column

class Entry(Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str]