"""
Initial schema: users, competencies, review_cycles, reviews, review_entries,
conflicts, summaries, audit_logs, templates
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    role_enum = sa.Enum("admin", "user", name="user_role")
    review_type_enum = sa.Enum("self", "peer", name="review_type")
    review_status_enum = sa.Enum("draft", "submitted", name="review_status")
    conflict_kind_enum = sa.Enum("dup", "contradiction", name="conflict_kind")

    role_enum.create(op.get_bind(), checkfirst=True)
    review_type_enum.create(op.get_bind(), checkfirst=True)
    review_status_enum.create(op.get_bind(), checkfirst=True)
    conflict_kind_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ext_platform", sa.Text(), nullable=True),
        sa.Column("handle", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True, index=True),
        sa.Column("role", role_enum, nullable=False, server_default="user"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "competencies",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "review_cycles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("starts_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ends_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("cycle_id", sa.BigInteger(), sa.ForeignKey("review_cycles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", review_type_enum, nullable=False),
        sa.Column("status", review_status_enum, nullable=False, server_default="draft"),
        sa.Column("lang", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_reviews_cycle", "reviews", ["cycle_id"])
    op.create_index("idx_reviews_author", "reviews", ["author_id"])
    op.create_index("idx_reviews_subject", "reviews", ["subject_id"])

    op.create_table(
        "review_entries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("review_id", sa.BigInteger(), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("competency_id", sa.BigInteger(), sa.ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("refined_text", sa.Text(), nullable=True),
        sa.Column("llm_score", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("hints", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("idx_review_entries_review", "review_entries", ["review_id"])

    op.create_table(
        "conflicts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("review_id", sa.BigInteger(), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("competency_id", sa.BigInteger(), sa.ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", conflict_kind_enum, nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "summaries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("subject_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cycle_id", sa.BigInteger(), sa.ForeignKey("review_cycles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_summaries_subject_cycle", "summaries", ["subject_id", "cycle_id"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_audit_logs_user", "audit_logs", ["user_id"])

    op.create_table(
        "templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("competency_id", sa.BigInteger(), sa.ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("idx_templates_competency_language", "templates", ["competency_id", "language"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_templates_competency_language", table_name="templates")
    op.drop_table("templates")

    op.drop_index("idx_audit_logs_user", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("idx_summaries_subject_cycle", table_name="summaries")
    op.drop_table("summaries")

    op.drop_table("conflicts")

    op.drop_index("idx_review_entries_review", table_name="review_entries")
    op.drop_table("review_entries")

    op.drop_index("idx_reviews_subject", table_name="reviews")
    op.drop_index("idx_reviews_author", table_name="reviews")
    op.drop_index("idx_reviews_cycle", table_name="reviews")
    op.drop_table("reviews")

    op.drop_table("review_cycles")

    op.drop_table("competencies")

    op.drop_table("users")

    sa.Enum(name="conflict_kind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="review_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="review_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)




