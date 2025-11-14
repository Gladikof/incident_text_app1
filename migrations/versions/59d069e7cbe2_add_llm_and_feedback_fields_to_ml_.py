"""add llm and feedback fields to ml_prediction_logs

Revision ID: 59d069e7cbe2
Revises: 2f4256ef35bf
Create Date: 2025-11-13 23:45:59.586352

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59d069e7cbe2'
down_revision: Union[str, Sequence[str], None] = '2f4256ef35bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Direct column additions work in SQLite without batch mode
    op.add_column('ml_prediction_logs', sa.Column('priority_llm_predicted', sa.Enum('P1', 'P2', 'P3', name='priorityenum', create_type=False), nullable=True))
    op.add_column('ml_prediction_logs', sa.Column('priority_llm_confidence', sa.Float(), nullable=True))
    op.add_column('ml_prediction_logs', sa.Column('priority_feedback_previous', sa.Enum('P1', 'P2', 'P3', name='priorityenum', create_type=False), nullable=True))
    op.add_column('ml_prediction_logs', sa.Column('priority_feedback_reason', sa.Text(), nullable=True))
    op.add_column('ml_prediction_logs', sa.Column('priority_feedback_author_id', sa.Integer(), nullable=True))
    op.add_column('ml_prediction_logs', sa.Column('priority_feedback_recorded_at', sa.DateTime(), nullable=True))
    op.add_column('ml_prediction_logs', sa.Column('triage_reason', sa.Enum('LOW_PRIORITY_CONF', 'LOW_CATEGORY_CONF', 'ML_DISABLED', 'MANUAL_FLAG', 'LLM_PRIORITY_MISMATCH', name='triagereasonenum', create_type=False), nullable=True))

    # Note: SQLite doesn't support adding foreign key constraints after table creation
    # The relationship will work through SQLAlchemy ORM layer


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ml_prediction_logs', 'triage_reason')
    op.drop_column('ml_prediction_logs', 'priority_feedback_recorded_at')
    op.drop_column('ml_prediction_logs', 'priority_feedback_author_id')
    op.drop_column('ml_prediction_logs', 'priority_feedback_reason')
    op.drop_column('ml_prediction_logs', 'priority_feedback_previous')
    op.drop_column('ml_prediction_logs', 'priority_llm_confidence')
    op.drop_column('ml_prediction_logs', 'priority_llm_predicted')
