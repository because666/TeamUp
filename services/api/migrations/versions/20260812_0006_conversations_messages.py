"""Add two-party conversations and text messages.

Revision ID: 20260812_0006
Revises: 20260812_0005
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260812_0006"
down_revision: Union[str, None] = "20260812_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("conversation_key", sa.String(128), nullable=False),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("conversation_key", name="uq_conversations_conversation_key"),
    )
    op.create_index(
        "ix_conversations_project_created", "conversations", ["project_id", "created_at", "id"]
    )
    op.create_table(
        "conversation_participants",
        sa.Column(
            "conversation_id",
            sa.String(40),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE')", name="ck_conversation_participants_status"),
    )
    op.create_index(
        "ix_conversation_participants_user_status",
        "conversation_participants",
        ["user_id", "status", "conversation_id"],
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("conversation_id", sa.String(40), nullable=False),
        sa.Column("sender_id", sa.String(36), nullable=False),
        sa.Column("client_message_id", sa.String(64), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("content", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id", "sender_id"],
            ["conversation_participants.conversation_id", "conversation_participants.user_id"],
            ondelete="RESTRICT",
            name="fk_messages_sender_participant",
        ),
        sa.UniqueConstraint("sender_id", "client_message_id", name="uq_messages_sender_client_id"),
        sa.CheckConstraint("type IN ('TEXT')", name="ck_messages_type"),
        sa.CheckConstraint("status IN ('SENT')", name="ck_messages_status"),
    )
    op.create_index(
        "ix_messages_conversation_created", "messages", ["conversation_id", "created_at", "id"]
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("conversation_participants")
    op.drop_table("conversations")
