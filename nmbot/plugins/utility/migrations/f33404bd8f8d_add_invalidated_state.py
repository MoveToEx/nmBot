"""add invalidated state

迁移 ID: f33404bd8f8d
父迁移: e356940c4418
创建时间: 2024-09-28 11:18:48.976320

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'f33404bd8f8d'
down_revision: str | Sequence[str] | None = 'e356940c4418'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('utility_groupinvitation', schema=None) as batch_op:
        batch_op.alter_column('state',
               existing_type=sa.VARCHAR(length=8),
               type_=sa.Enum('valid', 'accepted', 'denied', 'invalidated', name='invitationstate'),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade(name: str = "") -> None:
    if name:
        return
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('utility_groupinvitation', schema=None) as batch_op:
        batch_op.alter_column('state',
               existing_type=sa.Enum('valid', 'accepted', 'denied', 'invalidated', name='invitationstate'),
               type_=sa.VARCHAR(length=8),
               existing_nullable=False)

    # ### end Alembic commands ###
