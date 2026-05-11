from __future__ import annotations

from typing import Any, Optional
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
    wpm: Optional[float]


class SessionSummary(BaseModel):
    session_id: str
    job_role: str
    interview_type: str
    created_at: str
    completed_at: Optional[str]


class SessionDetail(BaseModel):
    session_id: str
    job_role: str
    interview_type: str
    user_profile: dict[str, Any]
    turns: list[TurnSummary]
    feedback: Optional[str]


class FeedbackResponse(BaseModel):
    feedback: str


class GazeEvent(BaseModel):
    timestamp: float
    direction: str
    duration: float


class CVMetrics(BaseModel):
    total_duration: float
    face_detected_pct: float
    gaze_on_camera_pct: float
    gaze_away_events: int
    avg_gaze_away_duration: float
    max_gaze_away_duration: float
    blink_count: int
    gaze_timeline: list[GazeEvent]


class CVAnalysisResult(BaseModel):
    session_id: str
    confidence_score: float
    confidence_label: str
    metrics: CVMetrics
    observations: list[str]
