"""add immutable graph build records

Revision ID: 4d2c7ea19a6b
Revises: ea96f975270f
Create Date: 2026-11-13
"""
from alembic import op
import sqlalchemy as sa


revision = "4d2c7ea19a6b"
down_revision = "ea96f975270f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "graph_builds",
        sa.Column("graph_build_id", sa.String(length=100), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=100), nullable=False),
        sa.Column("build_key", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("graph_source", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("input_hashes", sa.JSON(), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.analysis_run_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("graph_build_id"),
        sa.UniqueConstraint("project_id", "build_key"),
    )
    op.create_index(op.f("ix_graph_builds_project_id"), "graph_builds", ["project_id"], unique=False)
    op.create_index(op.f("ix_graph_builds_analysis_run_id"), "graph_builds", ["analysis_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_graph_builds_analysis_run_id"), table_name="graph_builds")
    op.drop_index(op.f("ix_graph_builds_project_id"), table_name="graph_builds")
    op.drop_table("graph_builds")
