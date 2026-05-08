import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import DBSession, DBTurn, DBFeedback


async def persist_completed_session(
    db: AsyncSession,
    session_id: str,
    session_data: dict,
    feedback_text: str,
) -> None:
    metadata = session_data["metadata"]
    sid = uuid.UUID(session_id)

    db_session = DBSession(
        session_id=sid,
        user_id=metadata.get("user_id", ""),
        job_role=metadata.get("job_role"),
        interview_type=metadata.get("interview_type"),
        user_profile=session_data.get("user_profile", {}),
        completed_at=datetime.utcnow(),
    )
    db.add(db_session)

    for turn in session_data.get("turns", []):
        filler_words = turn.get("filler_words", {})
        db_turn = DBTurn(
            session_id=sid,
            turn_index=turn["turn_index"],
            question_text=turn.get("question_text"),
            transcript=turn.get("transcript"),
            filler_count=sum(filler_words.values()),
            filler_words=filler_words,
            pause_count=turn.get("pause_count"),
            wpm=turn.get("wpm"),
        )
        db.add(db_turn)

    db_feedback = DBFeedback(session_id=sid, report=feedback_text)
    db.add(db_feedback)

    await db.commit()
