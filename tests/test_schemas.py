import uuid
from app.schemas.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    TurnResponse,
    SessionSummary,
    SessionDetail,
    FeedbackResponse,
)


def test_create_session_request_requires_user_id():
    req = CreateSessionRequest(
        user_id="user-1",
        job_role="Software Engineer",
        interview_type="technical",
        user_profile={"communication_challenges": ["stammer"], "experience_level": "junior"},
    )
    assert req.user_id == "user-1"
    assert req.user_profile["experience_level"] == "junior"


def test_turn_response_has_transcript():
    resp = TurnResponse(turn_id=str(uuid.uuid4()), transcript="I worked at Google.")
    assert resp.transcript == "I worked at Google."
