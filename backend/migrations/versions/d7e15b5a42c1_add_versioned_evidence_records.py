"""persist source assertions by graph build

Revision ID: d7e15b5a42c1
Revises: b6d3e9a24f10
Create Date: 2026-11-14
"""
from alembic import op
import sqlalchemy as sa


revision = "d7e15b5a42c1"
down_revision = "b6d3e9a24f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_records",
        sa.Column("record_id", sa.String(length=64), nullable=False),
        sa.Column("graph_build_id", sa.String(length=100), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("source_release", sa.String(length=250), nullable=False),
        sa.Column("source_record_id", sa.Text(), nullable=False),
        sa.Column("subject_id", sa.Text(), nullable=False),
        sa.Column("predicate", sa.String(length=120), nullable=False),
        sa.Column("object_id", sa.Text(), nullable=False),
        sa.Column("source_assertion", sa.JSON(), nullable=False),
        sa.Column("source_url", sa.JSON(), nullable=True),
        sa.Column("assertion_sha256", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["graph_build_id"], ["graph_builds.graph_build_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("record_id"),
        sa.UniqueConstraint("graph_build_id", "evidence_id", name="uq_evidence_graph_build_id"),
    )
    op.create_index("ix_evidence_records_graph_build_id", "evidence_records", ["graph_build_id"])
    op.create_index("ix_evidence_records_project_id", "evidence_records", ["project_id"])
    op.create_index("ix_evidence_records_evidence_id", "evidence_records", ["evidence_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_records_evidence_id", table_name="evidence_records")
    op.drop_index("ix_evidence_records_project_id", table_name="evidence_records")
    op.drop_index("ix_evidence_records_graph_build_id", table_name="evidence_records")
    op.drop_table("evidence_records")
