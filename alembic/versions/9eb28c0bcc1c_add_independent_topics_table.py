"""Add independent_topics table

Revision ID: 9eb28c0bcc1c
Revises: 20260127_schema
Create Date: 2026-01-27 16:20:42.962648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9eb28c0bcc1c'
down_revision: Union[str, Sequence[str], None] = '20260127_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create independent_topics table only
    op.create_table('independent_topics',
    sa.Column('number', sa.Integer(), nullable=False, comment='토픽 번호'),
    sa.Column('prompt', sa.Text(), nullable=False, comment='토픽 프롬프트 (질문)'),
    sa.Column('source', sa.String(length=100), nullable=False, comment='출처 (예: Independent_Topics.pdf)'),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_independent_topics_id'), 'independent_topics', ['id'], unique=False)
    op.create_index(op.f('ix_independent_topics_number'), 'independent_topics', ['number'], unique=True)
    op.create_index(op.f('ix_independent_topics_source'), 'independent_topics', ['source'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_independent_topics_source'), table_name='independent_topics')
    op.drop_index(op.f('ix_independent_topics_number'), table_name='independent_topics')
    op.drop_index(op.f('ix_independent_topics_id'), table_name='independent_topics')
    op.drop_table('independent_topics')
