import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import DBFeedback, DBSession
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
            "company_name": body.company_name,
            "interview_type": body.interview_type,
            "job_description": body.job_description,
            "resume_text": body.resume_text,
            "num_questions": body.num_questions,
        },
    )
    return CreateSessionResponse(session_id=session_id)


@router.get("", response_model=list[SessionSummary])
async def list_sessions(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DBSession, DBFeedback.scores)
        .outerjoin(DBFeedback, DBFeedback.session_id == DBSession.session_id)
        .where(DBSession.user_id == user_id)
        .order_by(DBSession.created_at.desc())
    )
    rows = result.all()
    return [
        SessionSummary(
            session_id=str(session.session_id),
            job_role=session.job_role or "",
            interview_type=session.interview_type or "",
            created_at=str(session.created_at),
            completed_at=str(session.completed_at) if session.completed_at else None,
            overall_score=scores.get("overall") if scores else None,
        )
        for session, scores in rows
    ]


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(DBSession, uuid.UUID(session_id))
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")

    from app.models.db import DBTurn, DBCVAnalysis

    turns_result = await db.execute(
        select(DBTurn).where(DBTurn.session_id == uuid.UUID(session_id)).order_by(DBTurn.turn_index)
    )
    turns = turns_result.scalars().all()

    feedback_result = await db.execute(
        select(DBFeedback).where(DBFeedback.session_id == uuid.UUID(session_id))
    )
    feedback = feedback_result.scalar_one_or_none()

    cv_result = await db.execute(
        select(DBCVAnalysis).where(DBCVAnalysis.session_id == uuid.UUID(session_id))
    )
    cv = cv_result.scalar_one_or_none()

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
        "scores": feedback.scores if feedback else None,
        "confidence_score": cv.confidence_score if cv else None,
        "confidence_label": cv.confidence_label if cv else None,
        "observations": cv.observations if cv else None,
    }
