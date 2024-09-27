from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List
from nonebot_plugin_orm import Model

class Post(Model):
    id: Mapped[str] = mapped_column(primary_key=True)
    text: Mapped[str]
    rating: Mapped[str]
    tags: Mapped[str]
    image: Mapped[str]

    shortcuts: Mapped[List['Shortcut']] = relationship(back_populates='post')

class Shortcut(Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str]
    pattern: Mapped[str]
    group: Mapped[str]
    post_id: Mapped[str] = mapped_column(ForeignKey('long_post.id'))

    post: Mapped['Post'] = relationship(back_populates='shortcuts')

class Bind(Model):
    uid: Mapped[str] = mapped_column(primary_key=True)
    accessKey: Mapped[str]

class Template(Model):
    name: Mapped[str] = mapped_column(primary_key=True)
    x: Mapped[int]
    y: Mapped[int]
    width: Mapped[int]
    height: Mapped[int]
    image: Mapped[str]
