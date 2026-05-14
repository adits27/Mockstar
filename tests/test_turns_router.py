import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.store import session_store


@pytest.fixture
def session_id():
    sid = str(uuid.uuid4())
    session_store.create(sid, user_profile={}, metadata={"job_role": "SWE", "interview_type": "technical"})
    return sid


async def test_post_turn_returns_empty_transcript_immediately(client, session_id):
    with patch("app.routers.turns._run_transcription_and_analytics", AsyncMock()):
        resp = await client.post(
            f"/sessions/{session_id}/turns",
            data={"question_text": "Tell me about yourself."},
            files={"audio": ("audio.webm", b"fake-bytes", "audio/webm")},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["transcript"] == ""
    assert "turn_id" in data


async def test_post_turn_returns_404_for_unknown_session(client):
    resp = await client.post(
        "/sessions/nonexistent-id/turns",
        data={"question_text": "Q?"},
        files={"audio": ("audio.webm", b"bytes", "audio/webm")},
    )
    assert resp.status_code == 404


async def test_post_turn_stores_turn_with_pending_transcript(client, session_id):
    with patch("app.routers.turns._run_transcription_and_analytics", AsyncMock()):
        await client.post(
            f"/sessions/{session_id}/turns",
            data={"question_text": "Background?"},
            files={"audio": ("audio.webm", b"bytes", "audio/webm")},
        )

    session = session_store.get(session_id)
    assert len(session["turns"]) == 1
    # transcript starts as None; background task fills it in asynchronously
    assert session["turns"][0]["transcript"] is None


async def test_post_end_returns_feedback(client, session_id):
    session_store.add_turn(session_id, {
        "turn_id": "t1",
        "turn_index": 0,
        "question_text": "Tell me about yourself.",
        "transcript": "I worked at Google for three years.",
        "filler_words": {"um": 1},
        "pause_count": 1,
        "wpm": 140.0,
    })

    mock_scores = {"answer_relevance": 8, "experience_articulation": 7, "industry_fit": 7, "clarity_and_structure": 8, "filler_word_usage": 9, "overall": 7.8}
    mock_result = {"feedback": "Strong answers overall. Work on reducing filler words.", "scores": mock_scores}

    with patch("app.routers.turns.generate_feedback", AsyncMock(return_value=mock_result)), \
         patch("app.routers.turns.persist_completed_session", AsyncMock()), \
         patch("app.routers.turns.get_db"):
        resp = await client.post(f"/sessions/{session_id}/end")

    assert resp.status_code == 200
    assert resp.json()["feedback"] == mock_result["feedback"]
    assert resp.json()["scores"]["answer_relevance"] == 8


async def test_post_end_returns_404_for_unknown_session(client):
    with patch("app.routers.turns.get_db"):
        resp = await client.post("/sessions/does-not-exist/end")
    assert resp.status_code == 404


async def test_post_end_clears_session_from_memory(client, session_id):
    session_store.add_turn(session_id, {
        "turn_id": "t1", "turn_index": 0, "question_text": "Q?",
        "transcript": "A.", "filler_words": {}, "pause_count": 0, "wpm": 100.0,
    })

    mock_result = {"feedback": "Feedback.", "scores": {"answer_relevance": 8, "experience_articulation": 7, "industry_fit": 7, "clarity_and_structure": 8, "filler_word_usage": 9, "overall": 7.8}}

    with patch("app.routers.turns.generate_feedback", AsyncMock(return_value=mock_result)), \
         patch("app.routers.turns.persist_completed_session", AsyncMock()), \
         patch("app.routers.turns.get_db"):
        await client.post(f"/sessions/{session_id}/end")

    assert session_store.get(session_id) is None
