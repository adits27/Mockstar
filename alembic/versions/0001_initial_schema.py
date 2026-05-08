"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sessions',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('job_role', sa.String(), nullable=True),
        sa.Column('interview_type', sa.String(), nullable=True),
        sa.Column('user_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index('ix_session_user_id', 'sessions', ['user_id'])

    op.create_table(
        'turns',
        sa.Column('turn_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('turn_index', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('filler_count', sa.Integer(), nullable=True),
        sa.Column('filler_words', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('pause_count', sa.Integer(), nullable=True),
        sa.Column('wpm', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id']),
        sa.PrimaryKeyConstraint('turn_id'),
        sa.UniqueConstraint('session_id', 'turn_index', name='uk_session_turn_index')
    )
    op.create_index('ix_turn_session_id', 'turns', ['session_id'])

    op.create_table(
        'feedback',
        sa.Column('feedback_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id']),
        sa.PrimaryKeyConstraint('feedback_id'),
        sa.UniqueConstraint('session_id')
    )


def downgrade() -> None:
    op.drop_table('feedback')
    op.drop_index('ix_turn_session_id', 'turns')
    op.drop_table('turns')
    op.drop_index('ix_session_user_id', 'sessions')
    op.drop_table('sessions')
