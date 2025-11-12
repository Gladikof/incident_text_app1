"""add_assignment_feedback

Revision ID: e039132bb1ac
Revises: b2557b6d9ca1
Create Date: 2025-11-12 18:13:50.228523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e039132bb1ac'
down_revision: Union[str, Sequence[str], None] = 'b2557b6d9ca1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Додаємо поля для підтвердження автоматичного призначення
    op.add_column('tickets', sa.Column('auto_assigned', sa.Boolean(), default=False, nullable=True))
    op.add_column('tickets', sa.Column('assignment_confirmed', sa.Boolean(), nullable=True))
    op.add_column('tickets', sa.Column('assignment_confirmed_at', sa.DateTime(), nullable=True))
    op.add_column('tickets', sa.Column('assignment_feedback', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tickets', 'assignment_feedback')
    op.drop_column('tickets', 'assignment_confirmed_at')
    op.drop_column('tickets', 'assignment_confirmed')
    op.drop_column('tickets', 'auto_assigned')
