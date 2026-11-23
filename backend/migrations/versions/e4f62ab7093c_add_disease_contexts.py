"""persist disease contexts by graph build

Revision ID: e4f62ab7093c
Revises: d7e15b5a42c1
Create Date: 2026-11-14
"""
from alembic import op
import sqlalchemy as sa

revision = "e4f62ab7093c"
down_revision = "d7e15b5a42c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "disease_contexts",
        sa.Column("record_id", sa.String(64), nullable=False),
        sa.Column("graph_build_id", sa.String(100), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("context_id", sa.Text(), nullable=False),
        sa.Column("disease_id", sa.Text(), nullable=False),
        sa.Column("context_label", sa.Text(), nullable=False),
        sa.Column("context_json", sa.JSON(), nullable=False),
        sa.Column("context_sha256", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["graph_build_id"], ["graph_builds.graph_build_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("record_id"),
        sa.UniqueConstraint("graph_build_id", "context_id", name="uq_disease_context_graph_build_id"),
    )
    op.create_index("ix_disease_contexts_graph_build_id", "disease_contexts", ["graph_build_id"])
    op.create_index("ix_disease_contexts_project_id", "disease_contexts", ["project_id"])
    op.create_index("ix_disease_contexts_context_id", "disease_contexts", ["context_id"])


def downgrade() -> None:
    op.drop_index("ix_disease_contexts_context_id", table_name="disease_contexts")
    op.drop_index("ix_disease_contexts_project_id", table_name="disease_contexts")
    op.drop_index("ix_disease_contexts_graph_build_id", table_name="disease_contexts")
    op.drop_table("disease_contexts")
