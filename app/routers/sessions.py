import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import DBSession
from app.schemas.schemas import CreateSessionRequest, CreateSessionResponse, SessionSummary
from app.store import session_store

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=CreateSessionResponse)
async def create_session(body: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    session_id = str(uuid.uuid4())
    profile = body.user_profile if isinstance(body.user_profile, dict) else body.user_profile.model_dump()
    session_store.create(
        session_id,
        user_profile=profile,
        metadata={
            "user_id": body.user_id,
            "job_role": body.job_role,
            "interview_type": body.interview_type,
        },
    )
    return CreateSessionResponse(session_id=session_id)


@router.get("", response_model=list[SessionSummary])
async def list_sessions(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBSession).where(DBSession.user_id == user_id))
    rows = result.scalars().all()
    return [
        SessionSummary(
            session_id=str(row.session_id),
            job_role=row.job_role or "",
            interview_type=row.interview_type or "",
            created_at=str(row.created_at),
            completed_at=str(row.completed_at) if row.completed_at else None,
        )
        for row in rows
    ]


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(DBSession, uuid.UUID(session_id))
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")

    from sqlalchemy import select as sa_select
    from app.models.db import DBTurn, DBFeedback

    turns_result = await db.execute(
        sa_select(DBTurn).where(DBTurn.session_id == uuid.UUID(session_id)).order_by(DBTurn.turn_index)
    )
    turns = turns_result.scalars().all()

    feedback_result = await db.execute(
        sa_select(DBFeedback).where(DBFeedback.session_id == uuid.UUID(session_id))
    )
    feedback = feedback_result.scalar_one_or_none()

    return {
        "session_id": session_id,
        "job_role": row.job_role,
        "interview_type": row.interview_type,
        "user_profile": row.user_profile or {},
        "turns": [
            {
                "turn_index": t.turn_index,
                "question_text": t.question_text,
                "transcript": t.transcript,
                "filler_words": t.filler_words or {},
                "pause_count": t.pause_count,
                "wpm": t.wpm,
            }
            for t in turns
        ],
        "feedback": feedback.report if feedback else None,
    }
