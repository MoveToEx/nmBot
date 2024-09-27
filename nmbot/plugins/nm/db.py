from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean
from datetime import datetime
from nonebot_plugin_orm import Model

class Setting(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[str] = mapped_column(String(12))
    object_id: Mapped[int]
    model: Mapped[str] = mapped_column(String(128))
    mode: Mapped[str] = mapped_column(String(32))

class History(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[str] = mapped_column(String(32))
    object_id: Mapped[int] = mapped_column(Integer())
    content: Mapped[str] = mapped_column(String(4096))
    role: Mapped[str] = mapped_column(String(12))
    date: Mapped[datetime] = mapped_column(DateTime(False))
    visible: Mapped[bool] = mapped_column(Boolean())
    tokens: Mapped[int] = mapped_column(Integer())

