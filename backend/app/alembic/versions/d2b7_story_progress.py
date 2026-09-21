"""add durable per-story progress

Revision ID: d2b7f4a9c301
Revises: c1c8a1a8e1f2
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d2b7f4a9c301"
down_revision = "c1c8a1a8e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    columns = {column["name"] for column in sa.inspect(conn).get_columns("scenario_session")}
    if "story_progress" not in columns:
        op.add_column(
            "scenario_session",
            sa.Column(
                "story_progress",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default="{}",
            ),
        )


def downgrade() -> None:
    conn = op.get_bind()
    columns = {column["name"] for column in sa.inspect(conn).get_columns("scenario_session")}
    if "story_progress" in columns:
        op.drop_column("scenario_session", "story_progress")
