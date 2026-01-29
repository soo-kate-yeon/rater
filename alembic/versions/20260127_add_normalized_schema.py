"""Add normalized schema: sets, items, stimuli, answer_keys

Revision ID: 20260127_schema
Revises: 5ac6e5d77682
Create Date: 2026-01-27 12:00:00.000000

SPEC: SPEC-TOEFL-SCHEMA-001
Description: 정규화된 데이터 스키마 추가
- Set: 문제 세트
- Item: 개별 문항
- Stimulus: 자극자료
- AnswerKey: 모범답안
- Task.item_id: Item 연결 FK
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260127_schema"
down_revision: str | Sequence[str] | None = "5ac6e5d77682"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add normalized tables."""

    # 1. Create Enum types
    topic_type_enum = postgresql.ENUM(
        "preference",
        "agree_disagree",
        "description",
        "opinion",
        "hypothetical",
        name="topic_type_enum",
        create_type=False,
    )
    topic_category_enum = postgresql.ENUM(
        "education",
        "technology",
        "lifestyle",
        "work",
        "relationships",
        "society",
        name="topic_category_enum",
        create_type=False,
    )
    difficulty_enum = postgresql.ENUM(
        "easy",
        "medium",
        "hard",
        name="difficulty_enum",
        create_type=False,
    )
    stimulus_kind_enum = postgresql.ENUM(
        "reading",
        "audio",
        "image",
        "direction",
        name="stimulus_kind_enum",
        create_type=False,
    )
    answer_key_type_enum = postgresql.ENUM(
        "sample_response",
        "transcript",
        "outline",
        "points",
        "blueprint",
        name="answer_key_type_enum",
        create_type=False,
    )
    answer_key_level_enum = postgresql.ENUM(
        "high",
        "mid",
        "low",
        name="answer_key_level_enum",
        create_type=False,
    )

    # Create enum types
    op.execute(
        "CREATE TYPE topic_type_enum AS ENUM ('preference', 'agree_disagree', 'description', 'opinion', 'hypothetical')"
    )
    op.execute(
        "CREATE TYPE topic_category_enum AS ENUM ('education', 'technology', 'lifestyle', 'work', 'relationships', 'society')"
    )
    op.execute("CREATE TYPE difficulty_enum AS ENUM ('easy', 'medium', 'hard')")
    op.execute("CREATE TYPE stimulus_kind_enum AS ENUM ('reading', 'audio', 'image', 'direction')")
    op.execute(
        "CREATE TYPE answer_key_type_enum AS ENUM ('sample_response', 'transcript', 'outline', 'points', 'blueprint')"
    )
    op.execute("CREATE TYPE answer_key_level_enum AS ENUM ('high', 'mid', 'low')")

    # 2. Create 'sets' table
    op.create_table(
        "sets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False, comment="세트 제목"),
        sa.Column(
            "source",
            sa.String(length=100),
            nullable=False,
            comment="출처 (예: ETS Official, Kaplan)",
        ),
        sa.Column("version", sa.String(length=20), nullable=False, comment="버전 (예: v1.0)"),
        sa.Column("description", sa.Text(), nullable=True, comment="세트 설명"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sets_id", "sets", ["id"], unique=False)
    op.create_index("ix_sets_source", "sets", ["source"], unique=False)
    op.create_index("ix_sets_version", "sets", ["version"], unique=False)
    op.create_index("ix_sets_source_version", "sets", ["source", "version"], unique=True)

    # 3. Create 'items' table
    op.create_table(
        "items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("set_id", sa.UUID(), nullable=False, comment="소속 Set UUID"),
        sa.Column("task_no", sa.Integer(), nullable=False, comment="Set 내 문항 번호 (1-4)"),
        sa.Column(
            "task_type",
            sa.Enum("INDEPENDENT", "INTEGRATED", name="task_type_enum", create_type=False),
            nullable=False,
            comment="문항 유형 (INDEPENDENT/INTEGRATED)",
        ),
        sa.Column("prompt", sa.Text(), nullable=False, comment="문제 지시문"),
        sa.Column(
            "prep_seconds",
            sa.Integer(),
            nullable=False,
            server_default="15",
            comment="준비 시간 (초)",
        ),
        sa.Column(
            "response_seconds",
            sa.Integer(),
            nullable=False,
            server_default="45",
            comment="응답 시간 (초)",
        ),
        sa.Column(
            "topic_type", topic_type_enum, nullable=True, comment="주제 유형 (Independent 전용)"
        ),
        sa.Column(
            "topic_category",
            topic_category_enum,
            nullable=True,
            comment="주제 카테고리 (Independent 전용)",
        ),
        sa.Column(
            "question_pattern",
            sa.String(length=200),
            nullable=True,
            comment="질문 패턴 (예: Do you agree or disagree...)",
        ),
        sa.Column(
            "tags", postgresql.JSONB(), nullable=False, server_default="[]", comment="태그 목록"
        ),
        sa.Column(
            "difficulty", difficulty_enum, nullable=True, comment="난이도 (easy/medium/hard)"
        ),
        sa.Column(
            "scoring_focus",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
            comment="채점 가중치",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["set_id"], ["sets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("set_id", "task_no", name="uq_items_set_task_no"),
    )
    op.create_index("ix_items_id", "items", ["id"], unique=False)
    op.create_index("ix_items_set_id", "items", ["set_id"], unique=False)
    op.create_index("ix_items_task_type", "items", ["task_type"], unique=False)
    op.create_index("ix_items_topic_type", "items", ["topic_type"], unique=False)
    op.create_index("ix_items_topic_category", "items", ["topic_category"], unique=False)
    op.create_index("ix_items_difficulty", "items", ["difficulty"], unique=False)

    # 4. Create 'stimuli' table
    op.create_table(
        "stimuli",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("item_id", sa.UUID(), nullable=False, comment="소속 Item UUID"),
        sa.Column(
            "kind",
            stimulus_kind_enum,
            nullable=False,
            comment="자료 유형 (reading/audio/image/direction)",
        ),
        sa.Column("title", sa.String(length=200), nullable=True, comment="자료 제목"),
        sa.Column(
            "content_text", sa.Text(), nullable=True, comment="텍스트 내용 (reading, direction 용)"
        ),
        sa.Column(
            "asset_url",
            sa.String(length=500),
            nullable=True,
            comment="미디어 URL (audio, image 용)",
        ),
        sa.Column(
            "duration_seconds", sa.Integer(), nullable=True, comment="음성 길이 (초, audio 전용)"
        ),
        sa.Column(
            "display_order", sa.Integer(), nullable=False, server_default="0", comment="표시 순서"
        ),
        sa.Column(
            "notes_allowed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="노트 필기 허용 여부",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stimuli_id", "stimuli", ["id"], unique=False)
    op.create_index("ix_stimuli_item_id", "stimuli", ["item_id"], unique=False)
    op.create_index("ix_stimuli_kind", "stimuli", ["kind"], unique=False)
    op.create_index(
        "ix_stimuli_display_order", "stimuli", ["item_id", "display_order"], unique=False
    )

    # 5. Create 'answer_keys' table
    op.create_table(
        "answer_keys",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("item_id", sa.UUID(), nullable=False, comment="소속 Item UUID"),
        sa.Column("answer_type", answer_key_type_enum, nullable=False, comment="모범답안 유형"),
        sa.Column(
            "level", answer_key_level_enum, nullable=True, comment="품질 수준 (high/mid/low)"
        ),
        sa.Column(
            "content",
            postgresql.JSONB(),
            nullable=False,
            comment="모범답안 내용 또는 Blueprint JSON",
        ),
        sa.Column(
            "source", sa.String(length=100), nullable=True, comment="출처 (예: ETS Official)"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_answer_keys_id", "answer_keys", ["id"], unique=False)
    op.create_index("ix_answer_keys_item_id", "answer_keys", ["item_id"], unique=False)
    op.create_index("ix_answer_keys_type", "answer_keys", ["answer_type"], unique=False)
    op.create_index("ix_answer_keys_level", "answer_keys", ["level"], unique=False)

    # 6. Add item_id column to tasks table (for migration)
    op.add_column(
        "tasks",
        sa.Column("item_id", sa.UUID(), nullable=True, comment="연결된 Item UUID (마이그레이션용)"),
    )
    op.create_index("ix_tasks_item_id", "tasks", ["item_id"], unique=False)
    op.create_foreign_key(
        "fk_tasks_item_id",
        "tasks",
        "items",
        ["item_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema - Remove normalized tables."""

    # 1. Remove item_id from tasks
    op.drop_constraint("fk_tasks_item_id", "tasks", type_="foreignkey")
    op.drop_index("ix_tasks_item_id", table_name="tasks")
    op.drop_column("tasks", "item_id")

    # 2. Drop answer_keys table
    op.drop_index("ix_answer_keys_level", table_name="answer_keys")
    op.drop_index("ix_answer_keys_type", table_name="answer_keys")
    op.drop_index("ix_answer_keys_item_id", table_name="answer_keys")
    op.drop_index("ix_answer_keys_id", table_name="answer_keys")
    op.drop_table("answer_keys")

    # 3. Drop stimuli table
    op.drop_index("ix_stimuli_display_order", table_name="stimuli")
    op.drop_index("ix_stimuli_kind", table_name="stimuli")
    op.drop_index("ix_stimuli_item_id", table_name="stimuli")
    op.drop_index("ix_stimuli_id", table_name="stimuli")
    op.drop_table("stimuli")

    # 4. Drop items table
    op.drop_index("ix_items_difficulty", table_name="items")
    op.drop_index("ix_items_topic_category", table_name="items")
    op.drop_index("ix_items_topic_type", table_name="items")
    op.drop_index("ix_items_task_type", table_name="items")
    op.drop_index("ix_items_set_id", table_name="items")
    op.drop_index("ix_items_id", table_name="items")
    op.drop_table("items")

    # 5. Drop sets table
    op.drop_index("ix_sets_source_version", table_name="sets")
    op.drop_index("ix_sets_version", table_name="sets")
    op.drop_index("ix_sets_source", table_name="sets")
    op.drop_index("ix_sets_id", table_name="sets")
    op.drop_table("sets")

    # 6. Drop enum types
    op.execute("DROP TYPE IF EXISTS answer_key_level_enum")
    op.execute("DROP TYPE IF EXISTS answer_key_type_enum")
    op.execute("DROP TYPE IF EXISTS stimulus_kind_enum")
    op.execute("DROP TYPE IF EXISTS difficulty_enum")
    op.execute("DROP TYPE IF EXISTS topic_category_enum")
    op.execute("DROP TYPE IF EXISTS topic_type_enum")
