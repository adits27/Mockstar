import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, String, JSON, event
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.db import Base, DBSession, DBTurn, DBFeedback
from app.services.persistence import persist_completed_session

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


def _sqlite_compat_create_all(conn):
    """Create all tables with SQLite-compatible type substitutions for JSONB and UUID."""
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
    from sqlalchemy import Table, Column, String, JSON, MetaData, Integer, Float, DateTime, Text, ForeignKey, Index, UniqueConstraint

    # Build a SQLite-compatible mirror of Base.metadata
    sqlite_meta = MetaData()
    col_type_map = {
        PG_UUID: String,
        PG_JSONB: JSON,
    }

    for table in Base.metadata.sorted_tables:
        new_cols = []
        for col in table.columns:
            col_type = col.type
            mapped_type = None
            for pg_type, sq_type in col_type_map.items():
                if isinstance(col_type, pg_type):
                    mapped_type = sq_type()
                    break
            if mapped_type is None:
                mapped_type = col_type
            new_col = Column(
                col.name,
                mapped_type,
                primary_key=col.primary_key,
                nullable=col.nullable,
                default=col.default,
            )
            new_cols.append(new_col)

        # Rebuild table args (skip constraints that reference other tables for simplicity)
        new_table_args = []
        for arg in (table.__table_args__ if hasattr(table, '__table_args__') else ()):
            if isinstance(arg, Index):
                new_table_args.append(arg)

        Table(table.name, sqlite_meta, *new_cols)

    sqlite_meta.create_all(conn)


@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(_sqlite_compat_create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def test_persist_completed_session_writes_all_tables(db_session):
    session_id = str(uuid.uuid4())
    session_data = {
        "user_profile": {"communication_challenges": ["stammer"], "experience_level": "junior"},
        "metadata": {"user_id": "user-1", "job_role": "SWE", "interview_type": "technical"},
        "turns": [
            {
                "turn_index": 0,
                "question_text": "Tell me about yourself.",
                "transcript": "Um I worked at Google.",
                "filler_words": {"um": 1},
                "filler_count": 1,
                "pause_count": 2,
                "wpm": 130.0,
            }
        ],
    }
    feedback_text = "Great communication overall."

    scores = {"answer_relevance": 8, "experience_articulation": 7, "industry_fit": 7, "clarity_and_structure": 8, "filler_word_usage": 9, "overall": 7.8}
    await persist_completed_session(db_session, session_id, session_data, feedback_text, scores)

    db_sess = await db_session.get(DBSession, uuid.UUID(session_id))
    assert db_sess is not None
    assert db_sess.job_role == "SWE"
    assert db_sess.completed_at is not None

    result = await db_session.execute(
        select(DBTurn).where(DBTurn.session_id == uuid.UUID(session_id))
    )
    turns = result.scalars().all()
    assert len(turns) == 1
    assert turns[0].transcript == "Um I worked at Google."
    assert turns[0].wpm == 130.0

    result = await db_session.execute(
        select(DBFeedback).where(DBFeedback.session_id == uuid.UUID(session_id))
    )
    feedback = result.scalar_one()
    assert feedback.report == "Great communication overall."
