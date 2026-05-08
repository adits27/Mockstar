import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class DBSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (Index("ix_session_user_id", "user_id"),)

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    job_role = Column(String)
    interview_type = Column(String)
    user_profile = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class DBTurn(Base):
    __tablename__ = "turns"
    __table_args__ = (
        UniqueConstraint("session_id", "turn_index", name="uk_session_turn_index"),
        Index("ix_turn_session_id", "session_id"),
    )

    turn_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id"), nullable=False)
    turn_index = Column(Integer, nullable=False)
    question_text = Column(Text)
    transcript = Column(Text)
    filler_count = Column(Integer)
    filler_words = Column(JSONB)
    pause_count = Column(Integer)
    wpm = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class DBFeedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("sessions.session_id"), nullable=False, unique=True
    )
    report = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
