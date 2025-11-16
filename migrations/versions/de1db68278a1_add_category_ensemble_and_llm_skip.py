"""add_category_ensemble_and_llm_skip

Revision ID: de1db68278a1
Revises: 431101891901
Create Date: 2025-11-16 00:15:24.948779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de1db68278a1'
down_revision: Union[str, Sequence[str], None] = '431101891901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tickets",
        sa.Column("category_llm_suggested", sa.Enum("Hardware", "Software", "Network", "Access", "Other", name="categoryenum"), nullable=True),
    )
    op.add_column("tickets", sa.Column("category_llm_confidence", sa.Float(), nullable=True))
    op.add_column(
        "tickets",
        sa.Column("category_ensemble", sa.Enum("Hardware", "Software", "Network", "Access", "Other", name="categoryenum"), nullable=True),
    )
    op.add_column("tickets", sa.Column("category_ensemble_confidence", sa.Float(), nullable=True))
    op.add_column("tickets", sa.Column("category_ensemble_strategy", sa.String(length=50), nullable=True))
    op.add_column("tickets", sa.Column("category_ensemble_reasoning", sa.Text(), nullable=True))
    op.add_column(
        "tickets",
        sa.Column("llm_enrichment_required", sa.Boolean(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column("tickets", sa.Column("llm_enriched_at", sa.DateTime(), nullable=True))

    op.add_column(
        "ml_prediction_logs",
        sa.Column("category_llm_predicted", sa.Enum("Hardware", "Software", "Network", "Access", "Other", name="categoryenum"), nullable=True),
    )
    op.add_column("ml_prediction_logs", sa.Column("category_llm_confidence", sa.Float(), nullable=True))
    op.add_column(
        "ml_prediction_logs",
        sa.Column("ensemble_category", sa.Enum("Hardware", "Software", "Network", "Access", "Other", name="categoryenum"), nullable=True),
    )
    op.add_column("ml_prediction_logs", sa.Column("ensemble_category_confidence", sa.Float(), nullable=True))
    op.add_column("ml_prediction_logs", sa.Column("ensemble_category_strategy", sa.String(length=50), nullable=True))
    op.add_column("ml_prediction_logs", sa.Column("ensemble_category_reasoning", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ml_prediction_logs", "ensemble_category_reasoning")
    op.drop_column("ml_prediction_logs", "ensemble_category_strategy")
    op.drop_column("ml_prediction_logs", "ensemble_category_confidence")
    op.drop_column("ml_prediction_logs", "ensemble_category")
    op.drop_column("ml_prediction_logs", "category_llm_confidence")
    op.drop_column("ml_prediction_logs", "category_llm_predicted")

    op.drop_column("tickets", "llm_enriched_at")
    op.drop_column("tickets", "llm_enrichment_required")
    op.drop_column("tickets", "category_ensemble_reasoning")
    op.drop_column("tickets", "category_ensemble_strategy")
    op.drop_column("tickets", "category_ensemble_confidence")
    op.drop_column("tickets", "category_ensemble")
    op.drop_column("tickets", "category_llm_confidence")
    op.drop_column("tickets", "category_llm_suggested")
