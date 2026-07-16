"""initial persistence schema

Revision ID: 202607160001
Revises:
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op

from app.persistence.models import Base


revision = "202607160001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
