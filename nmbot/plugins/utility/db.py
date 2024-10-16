from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from sqlalchemy import Enum as SqlEnum
from nonebot_plugin_orm import Model
from typing import Optional

class InvitationState(Enum):
    valid = 1
    accepted = 2
    denied = 3
    invalidated = 4

class GroupInvitation(Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inviter_id: Mapped[str]
    message_id: Mapped[str]
    flag: Mapped[str]
    state: Mapped[InvitationState] = mapped_column(SqlEnum(InvitationState))

class FriendRequest(Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id = Mapped[str]
    message_id = Mapped[str]
    flag: Mapped[str]
    state: Mapped[InvitationState] = mapped_column(SqlEnum(InvitationState))
    reason: Mapped[Optional[str]]