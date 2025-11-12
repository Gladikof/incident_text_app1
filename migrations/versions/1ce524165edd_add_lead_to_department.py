"""add_lead_to_department

Revision ID: 1ce524165edd
Revises: e039132bb1ac
Create Date: 2025-11-12 23:46:11.423336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ce524165edd'
down_revision: Union[str, Sequence[str], None] = 'e039132bb1ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add lead_user_id column to departments table (SQLite batch mode)
    with op.batch_alter_table('departments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lead_user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_departments_lead_user_id', 'users', ['lead_user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove lead_user_id column from departments table
    with op.batch_alter_table('departments', schema=None) as batch_op:
        batch_op.drop_constraint('fk_departments_lead_user_id', type_='foreignkey')
        batch_op.drop_column('lead_user_id')
