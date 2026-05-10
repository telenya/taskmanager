"""initial schema

Revision ID: 202605100001
Revises:
Create Date: 2026-05-10 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202605100001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    task_status = postgresql.ENUM(
        "pending",
        "in_progress",
        "done",
        name="task_status",
        create_type=False,
    )
    task_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tg_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("tg_id", name=op.f("uq_users_tg_id")),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", task_status, server_default="pending", nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["users.id"],
            name=op.f("fk_tasks_creator_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    op.create_index(op.f("ix_tasks_creator_id"), "tasks", ["creator_id"], unique=False)
    op.create_index(op.f("ix_tasks_deadline"), "tasks", ["deadline"], unique=False)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_deadline"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_creator_id"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_table("users")

    task_status = postgresql.ENUM(
        "pending",
        "in_progress",
        "done",
        name="task_status",
        create_type=False,
    )
    task_status.drop(op.get_bind(), checkfirst=True)
