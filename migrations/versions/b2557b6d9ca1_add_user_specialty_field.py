"""add_user_specialty_field

Revision ID: b2557b6d9ca1
Revises: 174a2a24f639
Create Date: 2025-11-12 14:38:34.687330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2557b6d9ca1'
down_revision: Union[str, Sequence[str], None] = '174a2a24f639'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('specialty', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'specialty')
