import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.store import session_store


@pytest.fixture
def session_id():
    sid = str(uuid.uuid4())
    session_store.create(sid, user_profile={}, metadata={"job_role": "SWE", "interview_type": "technical"})
    return sid


async def test_post_turn_returns_transcript(client, session_id):
    mock_whisper = {"text": "I worked at Google.", "words": [], "duration": 3.0}

    with patch("app.routers.turns.transcribe", AsyncMock(return_value=mock_whisper)):
        resp = await client.post(
            f"/sessions/{session_id}/turns",
            data={"question_text": "Tell me about yourself.", "turn_index": "0"},
            files={"audio": ("audio.webm", b"fake-bytes", "audio/webm")},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["transcript"] == "I worked at Google."
    assert "turn_id" in data


async def test_post_turn_returns_404_for_unknown_session(client):
    with patch("app.routers.turns.transcribe", AsyncMock(return_value={"text": "x", "words": [], "duration": 1.0})):
        resp = await client.post(
            "/sessions/nonexistent-id/turns",
            data={"question_text": "Q?", "turn_index": "0"},
            files={"audio": ("audio.webm", b"bytes", "audio/webm")},
        )
    assert resp.status_code == 404


async def test_post_turn_stores_transcript_in_session_store(client, session_id):
    mock_whisper = {"text": "My background is in ML.", "words": [], "duration": 4.0}

    with patch("app.routers.turns.transcribe", AsyncMock(return_value=mock_whisper)):
        await client.post(
            f"/sessions/{session_id}/turns",
            data={"question_text": "Background?", "turn_index": "0"},
            files={"audio": ("audio.webm", b"bytes", "audio/webm")},
        )

    session = session_store.get(session_id)
    assert len(session["turns"]) == 1
    assert session["turns"][0]["transcript"] == "My background is in ML."


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

    mock_feedback = "Strong answers overall. Work on reducing filler words."

    with patch("app.routers.turns.generate_feedback", AsyncMock(return_value=mock_feedback)), \
         patch("app.routers.turns.persist_completed_session", AsyncMock()), \
         patch("app.routers.turns.get_db"):
        resp = await client.post(f"/sessions/{session_id}/end")

    assert resp.status_code == 200
    assert resp.json()["feedback"] == mock_feedback


async def test_post_end_returns_404_for_unknown_session(client):
    with patch("app.routers.turns.get_db"):
        resp = await client.post("/sessions/does-not-exist/end")
    assert resp.status_code == 404


async def test_post_end_clears_session_from_memory(client, session_id):
    session_store.add_turn(session_id, {
        "turn_id": "t1", "turn_index": 0, "question_text": "Q?",
        "transcript": "A.", "filler_words": {}, "pause_count": 0, "wpm": 100.0,
    })

    with patch("app.routers.turns.generate_feedback", AsyncMock(return_value="Feedback.")), \
         patch("app.routers.turns.persist_completed_session", AsyncMock()), \
         patch("app.routers.turns.get_db"):
        await client.post(f"/sessions/{session_id}/end")

    assert session_store.get(session_id) is None
