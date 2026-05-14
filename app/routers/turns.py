import asyncio
import os
import tempfile
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.schemas import FeedbackResponse, NextQuestionResponse, ScoreBreakdown, TurnResponse
from app.services import analytics as analytics_svc
from app.services.cv.analyzer import _aggregate, _process_video
from app.services.cv.confidence_scorer import score_session
from app.services.feedback import generate_feedback
from app.services.interviewer import generate_next_question
from app.services.persistence import persist_completed_session
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


async def _run_transcription_and_analytics(
    session_id: str,
    turn_index: int,
    audio_bytes: bytes,
    audio_filename: str,
    audio_content_type: str,
) -> None:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=(audio_filename, audio_bytes, audio_content_type),
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )
        whisper_result = {
            "text": response.text,
            "words": [{"word": w.word, "start": w.start, "end": w.end} for w in (response.words or [])],
            "duration": response.duration,
        }
        session_store.update_turn_transcript(session_id, turn_index, whisper_result["text"])
        _run_analytics(session_id, turn_index, whisper_result)
    finally:
        session_store.decrement_pending(session_id)


def _run_cv(session_id: str, turn_index: int, video_bytes: bytes, filename: str) -> None:
    ext = os.path.splitext(filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    try:
        frames = _process_video(tmp_path)
        metrics = _aggregate(frames)
        score, label, observations = score_session(metrics)
        session_store.update_turn_cv(session_id, turn_index, {
            "confidence_score": score,
            "confidence_label": label,
            "metrics": metrics.model_dump(),
            "observations": observations,
        })
    finally:
        os.unlink(tmp_path)


def _aggregate_cv_results(turns: list[dict]) -> Optional[dict]:
    results = [t["cv_result"] for t in turns if t.get("cv_result")]
    if not results:
        return None
    avg_score = sum(r["confidence_score"] for r in results) / len(results)
    label = "High" if avg_score >= 75 else "Medium" if avg_score >= 50 else "Low"
    observations = [obs for r in results for obs in r["observations"]]
    return {
        "confidence_score": round(avg_score, 1),
        "confidence_label": label,
        "observations": observations,
    }


@router.post("/{session_id}/turns", response_model=TurnResponse)
async def post_turn(
    session_id: str,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    question_text: str = Form(...),
    video: Optional[UploadFile] = File(None),
):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Read bytes now — UploadFile is only readable while the request is open
    audio_bytes = await audio.read()
    audio_filename = audio.filename or "audio.webm"
    audio_content_type = audio.content_type or "audio/webm"

    turn_index = len(session["turns"])
    turn_id = str(uuid.uuid4())

    session_store.add_turn(session_id, {
        "turn_id": turn_id,
        "turn_index": turn_index,
        "question_text": question_text,
        "transcript": None,
        "filler_words": {},
        "pause_count": 0,
        "wpm": None,
        "cv_result": None,
    })

    session_store.increment_pending(session_id)
    background_tasks.add_task(
        _run_transcription_and_analytics,
        session_id, turn_index, audio_bytes, audio_filename, audio_content_type,
    )

    if video is not None:
        video_bytes = await video.read()
        background_tasks.add_task(_run_cv, session_id, turn_index, video_bytes, video.filename or "turn.webm")

    return TurnResponse(turn_id=turn_id, transcript="")


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

    elapsed = 0.0
    while session_store.pending_count(session_id) > 0:
        if elapsed >= 30.0:
            break
        await asyncio.sleep(0.25)
        elapsed += 0.25

    session = session_store.get(session_id)
    session_cv = _aggregate_cv_results(session["turns"])
    result = await generate_feedback(session, session_cv)
    feedback_text = result["feedback"]
    scores = result["scores"]

    await persist_completed_session(db, session_id, session, feedback_text, scores)
    session_store.delete(session_id)

    return FeedbackResponse(
        feedback=feedback_text,
        scores=ScoreBreakdown(**scores),
        confidence_score=session_cv["confidence_score"] if session_cv else None,
        confidence_label=session_cv["confidence_label"] if session_cv else None,
        observations=session_cv["observations"] if session_cv else None,
    )
