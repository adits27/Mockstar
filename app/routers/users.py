from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import DBUserResume
from app.schemas.schemas import ResumeResponse
from app.services.resume_parser import extract_text

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/{user_id}/resume")
async def upload_resume(
    user_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    resume_text = await extract_text(file)

    # Upsert: one resume per user
    await db.execute(
        text("""
            INSERT INTO user_resumes (resume_id, user_id, resume_text, filename, uploaded_at)
            VALUES (gen_random_uuid(), :user_id, :resume_text, :filename, :uploaded_at)
            ON CONFLICT (user_id) DO UPDATE
            SET resume_text = EXCLUDED.resume_text,
                filename    = EXCLUDED.filename,
                uploaded_at = EXCLUDED.uploaded_at
        """),
        {
            "user_id": user_id,
            "resume_text": resume_text,
            "filename": file.filename,
            "uploaded_at": datetime.utcnow(),
        },
    )
    await db.commit()

    return {"message": "ok", "char_count": len(resume_text)}


@router.get("/{user_id}/resume", response_model=ResumeResponse)
async def get_resume(user_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.execute(
        text("SELECT resume_text, filename, uploaded_at FROM user_resumes WHERE user_id = :uid"),
        {"uid": user_id},
    )
    record = row.mappings().first()
    if record is None:
        raise HTTPException(status_code=404, detail="No resume on file for this user.")

    return ResumeResponse(
        resume_text=record["resume_text"],
        filename=record["filename"],
        uploaded_at=str(record["uploaded_at"]),
    )


@router.post("/{user_id}/extract-text")
async def extract_document_text(
    user_id: str,  # kept for route consistency; not used for auth here
    file: UploadFile = File(...),
):
    """Extract plain text from a PDF or DOCX — used for job description uploads."""
    text = await extract_text(file)
    return {"text": text}
