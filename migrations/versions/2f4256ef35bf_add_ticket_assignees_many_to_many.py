"""add_ticket_assignees_many_to_many

Revision ID: 2f4256ef35bf
Revises: 1ce524165edd
Create Date: 2025-11-13 14:22:10.226155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f4256ef35bf'
down_revision: Union[str, Sequence[str], None] = '1ce524165edd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ticket_assignees',
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('ticket_id', 'user_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ticket_assignees')
