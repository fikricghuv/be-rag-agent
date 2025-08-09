"""remove client_id from dt_agent_sessions

Revision ID: 7fa980de8146
Revises: 
Create Date: 2025-08-08 14:23:59.873360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fa980de8146'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_constraint('fk_agent_sessions_client', 'dt_agent_sessions', schema='ai', type_='foreignkey')
    op.drop_column('dt_agent_sessions', 'client_id', schema='ai')

def downgrade():
    op.add_column('dt_agent_sessions',
        sa.Column('client_id', sa.UUID(), nullable=False)
    )
    op.create_foreign_key(
        'fk_agent_sessions_client',
        'dt_agent_sessions', 'ms_clients',
        ['client_id'], ['id'],
        source_schema='ai',
        referent_schema='ai',
        ondelete='CASCADE'
    )
