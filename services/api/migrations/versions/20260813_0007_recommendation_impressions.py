"""Persist recommendation requests, candidates and impression events.

Revision ID: 20260813_0007
Revises: 20260812_0006
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260813_0007"
down_revision: Union[str, None] = "20260812_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_requests",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("viewer_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("context", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_recommendation_requests_viewer_created",
        "recommendation_requests",
        ["viewer_user_id", "created_at"],
    )
    op.create_table(
        "recommendation_candidates",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column(
            "request_id",
            sa.String(128),
            sa.ForeignKey("recommendation_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(64), nullable=False),
        sa.UniqueConstraint("request_id", "rank", name="uq_recommendation_candidates_request_rank"),
        sa.UniqueConstraint(
            "request_id", "target_type", "target_id", name="uq_recommendation_candidates_request_target"
        ),
    )
    op.create_index(
        "ix_recommendation_candidates_request_rank",
        "recommendation_candidates",
        ["request_id", "rank"],
    )
    op.create_table(
        "recommendation_impressions",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "request_id",
            sa.String(128),
            sa.ForeignKey("recommendation_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("viewer_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("client_occurred_at", sa.DateTime(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "request_id",
            "viewer_user_id",
            "target_type",
            "target_id",
            name="uq_recommendation_impressions_request_viewer_target",
        ),
    )
    op.create_index(
        "ix_recommendation_impressions_viewer_received",
        "recommendation_impressions",
        ["viewer_user_id", "received_at"],
    )


def downgrade() -> None:
    op.drop_table("recommendation_impressions")
    op.drop_table("recommendation_candidates")
    op.drop_table("recommendation_requests")
