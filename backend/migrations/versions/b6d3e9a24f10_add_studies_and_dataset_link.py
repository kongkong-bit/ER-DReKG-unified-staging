"""add project-scoped studies and optional dataset linkage

Revision ID: b6d3e9a24f10
Revises: 1a9c43d820ef
Create Date: 2026-11-14
"""
from alembic import op
import sqlalchemy as sa


revision = "b6d3e9a24f10"
down_revision = "1a9c43d820ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "studies",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("accession", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("organism", sa.String(length=120), nullable=False),
        sa.Column("design_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id"),
        sa.UniqueConstraint("project_id", "accession", name="uq_studies_project_accession"),
    )
    op.create_index("ix_studies_project_id", "studies", ["project_id"], unique=False)
    with op.batch_alter_table("datasets") as batch:
        batch.add_column(sa.Column("study_id", sa.String(length=36), nullable=True))
        batch.create_foreign_key("fk_datasets_study_id_studies", "studies", ["study_id"], ["study_id"], ondelete="SET NULL")
        batch.create_index("ix_datasets_study_id", ["study_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("datasets") as batch:
        batch.drop_index("ix_datasets_study_id")
        batch.drop_constraint("fk_datasets_study_id_studies", type_="foreignkey")
        batch.drop_column("study_id")
    op.drop_index("ix_studies_project_id", table_name="studies")
    op.drop_table("studies")
