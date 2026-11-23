"""persist project-scoped S2 drug-condition results

Revision ID: 1a9c43d820ef
Revises: 4d2c7ea19a6b
Create Date: 2026-11-13
"""
from alembic import op
import sqlalchemy as sa


revision = "1a9c43d820ef"
down_revision = "4d2c7ea19a6b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "s2_condition_results",
        sa.Column("result_id", sa.String(length=100), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=100), nullable=False),
        sa.Column("pert_id", sa.String(length=100), nullable=False),
        sa.Column("condition_key", sa.String(length=500), nullable=False),
        sa.Column("rank_within_condition", sa.Float(), nullable=False),
        sa.Column("condition_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.analysis_run_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("result_id"),
        sa.UniqueConstraint("analysis_run_id", "condition_key", "pert_id", name="uq_s2_condition_run_condition_pert"),
    )
    op.create_index("ix_s2_condition_results_project_id", "s2_condition_results", ["project_id"], unique=False)
    op.create_index("ix_s2_condition_results_analysis_run_id", "s2_condition_results", ["analysis_run_id"], unique=False)
    op.create_index("ix_s2_condition_results_pert_id", "s2_condition_results", ["pert_id"], unique=False)
    op.create_index("ix_s2_condition_results_condition_key", "s2_condition_results", ["condition_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_s2_condition_results_condition_key", table_name="s2_condition_results")
    op.drop_index("ix_s2_condition_results_pert_id", table_name="s2_condition_results")
    op.drop_index("ix_s2_condition_results_analysis_run_id", table_name="s2_condition_results")
    op.drop_index("ix_s2_condition_results_project_id", table_name="s2_condition_results")
    op.drop_table("s2_condition_results")
