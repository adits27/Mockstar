from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class UserProfile(BaseModel):
    communication_challenges: list[str] = []
    experience_level: str = "not specified"
    goals: str = "general improvement"


class CreateSessionRequest(BaseModel):
    user_id: str
    job_role: str = "not specified"
    interview_type: str = "general"
    user_profile: dict[str, Any] = {}


class CreateSessionResponse(BaseModel):
    session_id: str


class TurnResponse(BaseModel):
    turn_id: str
    transcript: str


class TurnSummary(BaseModel):
    turn_index: int
    question_text: str
    transcript: str
    filler_words: dict[str, int]
    pause_count: int
    wpm: float | None


class SessionSummary(BaseModel):
    session_id: str
    job_role: str
    interview_type: str
    created_at: str
    completed_at: str | None


class SessionDetail(BaseModel):
    session_id: str
    job_role: str
    interview_type: str
    user_profile: dict[str, Any]
    turns: list[TurnSummary]
    feedback: str | None


class FeedbackResponse(BaseModel):
    feedback: str
