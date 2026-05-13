import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.schemas import FeedbackResponse, NextQuestionResponse, ScoreBreakdown, TurnResponse
from app.services import analytics as analytics_svc
from app.services.feedback import generate_feedback
from app.services.interviewer import generate_next_question
from app.services.persistence import persist_completed_session
from app.services.whisper import transcribe
from app.store import session_store

router = APIRouter(prefix="/sessions", tags=["turns"])


def _run_analytics(session_id: str, turn_index: int, whisper_result: dict) -> None:
    words = whisper_result.get("words", [])
    duration = whisper_result.get("duration", 0)
    transcript = whisper_result.get("text", "")

    filler_words = analytics_svc.detect_fillers(transcript)
    pause_count = analytics_svc.detect_pauses(words)
    wpm = analytics_svc.calculate_wpm(len(words), duration)

    session_store.update_turn_metrics(session_id, turn_index, filler_words, pause_count, wpm)


@router.post("/{session_id}/turns", response_model=TurnResponse)
async def post_turn(
    session_id: str,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    question_text: str = Form(...),
):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    turn_index = len(session["turns"])
    whisper_result = await transcribe(audio)
    transcript = whisper_result["text"]
    turn_id = str(uuid.uuid4())

    session_store.add_turn(session_id, {
        "turn_id": turn_id,
        "turn_index": turn_index,
        "question_text": question_text,
        "transcript": transcript,
        "filler_words": {},
        "pause_count": 0,
        "wpm": None,
    })

    background_tasks.add_task(_run_analytics, session_id, turn_index, whisper_result)

    return TurnResponse(turn_id=turn_id, transcript=transcript)


@router.post("/{session_id}/next-question", response_model=NextQuestionResponse)
async def next_question(session_id: str):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    question = await generate_next_question(session)
    return NextQuestionResponse(question=question)


@router.post("/{session_id}/end", response_model=FeedbackResponse)
async def end_interview(session_id: str, db: AsyncSession = Depends(get_db)):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await generate_feedback(session)
    feedback_text = result["feedback"]
    scores = result["scores"]

    await persist_completed_session(db, session_id, session, feedback_text, scores)
    session_store.delete(session_id)

    return FeedbackResponse(feedback=feedback_text, scores=ScoreBreakdown(**scores))
