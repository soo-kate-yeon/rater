"""add_feature_configs_and_subscriptions

Revision ID: c8b27d767a6e
Revises: 9eb28c0bcc1c
Create Date: 2026-01-28 01:03:26.240431

SPEC-TOEFL-FEATURE-001: Phase 1+2 Integration
- feature_configs: 피처 메타데이터 저장 (13개 피처)
- user_subscriptions: 사용자 구독 티어 관리
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8b27d767a6e'
down_revision: Union[str, Sequence[str], None] = '9eb28c0bcc1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create feature_configs table
    op.create_table(
        'feature_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feature_code', sa.String(50), nullable=False, comment='피처 코드 (예: silmean)'),
        sa.Column('feature_name_ko', sa.String(100), nullable=False, comment='한글 피처명'),
        sa.Column('category', sa.String(50), nullable=False, comment='카테고리 (delivery, grammar, vocabulary)'),
        sa.Column('weight', sa.Numeric(4, 2), nullable=False, comment='가중치 (0.00-1.00)'),
        sa.Column('requires_audio', sa.Boolean(), server_default='false', nullable=False, comment='오디오 파일 필요 여부'),
        sa.Column('description', sa.Text(), nullable=True, comment='피처 설명'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('feature_code')
    )
    op.create_index(op.f('ix_feature_configs_category'), 'feature_configs', ['category'], unique=False)
    op.create_index(op.f('ix_feature_configs_feature_code'), 'feature_configs', ['feature_code'], unique=True)

    # Create user_subscriptions table
    op.create_table(
        'user_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, comment='사용자 UUID'),
        sa.Column('tier', sa.String(20), nullable=False, comment='구독 티어 (basic, standard, premium)'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='만료일 (None = 무제한)'),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_user_subscriptions_user_id'), 'user_subscriptions', ['user_id'], unique=False)

    # Seed data: 13 features from Phase 1 (8 Delivery + 2 Grammar + 3 Vocabulary)
    op.execute("""
        INSERT INTO feature_configs (feature_code, feature_name_ko, category, weight, requires_audio, description) VALUES
        -- Delivery Features (8개, ~38% 가중치)
        ('silmean', '평균 침묵 길이', 'delivery', 0.05, false, '침묵(pause)의 평균 길이(초)'),
        ('wpsec', '발화 속도', 'delivery', 0.06, false, '초당 단어 수 (WPM/60)'),
        ('secpchk', '평균 청크 길이', 'delivery', 0.05, false, '침묵 사이 발화 구간 평균 길이'),
        ('numrep', '반복 횟수', 'delivery', 0.04, false, '단어/구문 반복 횟수'),
        ('numdff', '비유창성 횟수', 'delivery', 0.05, false, '필러(uh, um), 거짓 시작 등'),
        ('silpsecutt', '침묵 빈도', 'delivery', 0.05, false, '초당 침묵 발생 횟수'),
        ('IPC', '절 내 중단', 'delivery', 0.04, false, '절 내부 중단/재구성 횟수'),
        ('withinClauseSilMean', '절 내 침묵 평균', 'delivery', 0.04, false, '절 내부 침묵 평균 길이'),

        -- Grammar Features (2개, ~6% 가중치)
        ('poscvamax', 'POS 문법 유사도', 'grammar', 0.03, false, 'POS n-gram 기반 문법 프로파일 유사도'),
        ('dep_clauses_per_clause', '절당 종속절 수', 'grammar', 0.03, false, '평균 종속절 수'),

        -- Vocabulary Features (3개, ~20% 가중치)
        ('cvamax', '어휘 CVA 점수', 'vocabulary', 0.08, false, 'Content Vector Analysis 기반 어휘 유사도'),
        ('types', '고유 단어 수', 'vocabulary', 0.06, false, '응답 내 고유 단어 타입 수'),
        ('logFreq', '평균 단어 빈도', 'vocabulary', 0.06, false, '단어들의 평균 로그 빈도')
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop user_subscriptions table
    op.drop_index(op.f('ix_user_subscriptions_user_id'), table_name='user_subscriptions')
    op.drop_table('user_subscriptions')

    # Drop feature_configs table
    op.drop_index(op.f('ix_feature_configs_feature_code'), table_name='feature_configs')
    op.drop_index(op.f('ix_feature_configs_category'), table_name='feature_configs')
    op.drop_table('feature_configs')
