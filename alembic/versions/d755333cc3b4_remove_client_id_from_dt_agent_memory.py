"""remove client_id from dt_agent_memory

Revision ID: d755333cc3b4
Revises: 7fa980de8146
Create Date: 2025-08-08 14:36:41.812925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd755333cc3b4'
down_revision: Union[str, Sequence[str], None] = '7fa980de8146'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table("dt_agent_memory", schema="ai") as batch_op:
        batch_op.drop_constraint("fk_agent_memory_client", type_="foreignkey")
        batch_op.drop_column("client_id")


def downgrade():
    with op.batch_alter_table("dt_agent_memory", schema="ai") as batch_op:
        batch_op.add_column(sa.Column("client_id", sa.dialects.postgresql.UUID(), nullable=False))
        batch_op.create_foreign_key(
            "fk_agent_memory_client",
            "ms_clients",
            ["client_id"],
            ["id"],
            ondelete="CASCADE",
            onupdate="NO ACTION"
        )