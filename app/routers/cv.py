from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.schemas import CVAnalysisResult
from app.services.cv.analyzer import analyze_video
from app.store import session_store

router = APIRouter(prefix="/sessions", tags=["computer-vision"])


@router.post("/{session_id}/video", response_model=CVAnalysisResult)
async def analyze_session_video(
    session_id: str,
    video: UploadFile = File(...),
) -> CVAnalysisResult:
    if session_store.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    content_type = video.content_type or ""
    if not content_type.startswith("video/"):
        raise HTTPException(status_code=422, detail="Uploaded file must be a video")

    result = await analyze_video(video, session_id)
    session_store.set_cv_result(session_id, result.model_dump())
    return result
