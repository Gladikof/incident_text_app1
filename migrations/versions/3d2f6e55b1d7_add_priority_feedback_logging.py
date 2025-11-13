"""add priority feedback logging columns

Revision ID: 3d2f6e55b1d7
Revises: b2557b6d9ca1
Create Date: 2025-11-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d2f6e55b1d7'
down_revision: Union[str, Sequence[str], None] = 'b2557b6d9ca1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    priority_enum = sa.Enum('P1', 'P2', 'P3', name='priorityenum', create_type=False)

    op.add_column(
        'ml_prediction_logs',
        sa.Column('priority_feedback_previous', priority_enum, nullable=True),
    )
    op.add_column(
        'ml_prediction_logs',
        sa.Column('priority_feedback_reason', sa.Text(), nullable=True),
    )
    op.add_column(
        'ml_prediction_logs',
        sa.Column('priority_feedback_author_id', sa.Integer(), nullable=True),
    )
    op.add_column(
        'ml_prediction_logs',
        sa.Column('priority_feedback_recorded_at', sa.DateTime(), nullable=True),
    )

    op.create_foreign_key(
        'fk_ml_prediction_logs_feedback_author_id_users',
        'ml_prediction_logs',
        'users',
        ['priority_feedback_author_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_ml_prediction_logs_feedback_author_id_users',
        'ml_prediction_logs',
        type_='foreignkey',
    )
    op.drop_column('ml_prediction_logs', 'priority_feedback_recorded_at')
    op.drop_column('ml_prediction_logs', 'priority_feedback_author_id')
    op.drop_column('ml_prediction_logs', 'priority_feedback_reason')
    op.drop_column('ml_prediction_logs', 'priority_feedback_previous')
