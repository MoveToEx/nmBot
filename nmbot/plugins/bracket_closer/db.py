from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List
from nonebot_plugin_orm import Model

class Enabled(Model):
    group_id: Mapped[str] = mapped_column(primary_key=True)
    enabled: Mapped[bool]