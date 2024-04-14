from nonebot import require
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

require('nonebot_plugin_datastore')

from nonebot_plugin_datastore import get_session, get_plugin_data

Model = get_plugin_data().Model

class Setting(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[str] = mapped_column(String(12))
    object_id: Mapped[int]
    mode: Mapped[str] = mapped_column(String(32))
