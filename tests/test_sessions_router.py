# tests/test_sessions_router.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select


async def test_create_session_returns_session_id(client):
    with patch("app.routers.sessions.get_db"):
        resp = await client.post("/sessions", json={
            "user_id": "user-1",
            "job_role": "Software Engineer",
            "interview_type": "technical",
            "user_profile": {"communication_challenges": [], "experience_level": "junior"},
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert len(data["session_id"]) == 36  # UUID format


async def test_create_session_stores_in_memory(client):
    from app.store import session_store
    with patch("app.routers.sessions.get_db"):
        resp = await client.post("/sessions", json={
            "user_id": "user-1",
            "job_role": "SWE",
            "interview_type": "behavioral",
            "user_profile": {},
        })
    session_id = resp.json()["session_id"]
    assert session_store.get(session_id) is not None


async def test_get_sessions_returns_list(client):
    import uuid

    mock_db_sessions = [
        MagicMock(
            session_id=uuid.uuid4(),
            job_role="SWE",
            interview_type="technical",
            created_at=MagicMock(__str__=lambda s: "2026-05-07T10:00:00"),
            completed_at=None,
        )
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_db_sessions
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    async def override_db():
        yield mock_db

    from app.main import app
    from app.database import get_db
    app.dependency_overrides[get_db] = override_db

    resp = await client.get("/sessions?user_id=user-1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    app.dependency_overrides.clear()
