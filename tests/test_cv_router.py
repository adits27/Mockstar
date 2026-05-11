import io
import pytest
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.schemas.schemas import CVAnalysisResult, CVMetrics


_FAKE_METRICS = CVMetrics(
    total_duration=60.0,
    face_detected_pct=0.95,
    gaze_on_camera_pct=0.85,
    gaze_away_events=3,
    avg_gaze_away_duration=0.8,
    max_gaze_away_duration=1.2,
    blink_count=12,
    gaze_timeline=[],
)

_FAKE_RESULT = CVAnalysisResult(
    session_id="test-session-id",
    confidence_score=88.5,
    confidence_label="High",
    metrics=_FAKE_METRICS,
    observations=["Excellent eye contact."],
)


@pytest.fixture()
def client():
    import asyncio

    async def _client():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            return c

    return asyncio.get_event_loop().run_until_complete(_client())


@pytest.fixture()
def async_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_analyze_video_success(async_client):
    with (
        patch("app.routers.cv.session_store.get", return_value={"turns": []}),
        patch("app.routers.cv.analyze_video", new_callable=AsyncMock, return_value=_FAKE_RESULT),
        patch("app.routers.cv.session_store.set_cv_result"),
    ):
        async with async_client as c:
            video_bytes = io.BytesIO(b"fake-video-data")
            resp = await c.post(
                "/sessions/test-session-id/video",
                files={"video": ("interview.webm", video_bytes, "video/webm")},
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == "test-session-id"
    assert body["confidence_label"] == "High"
    assert body["confidence_score"] == pytest.approx(88.5)
    assert body["metrics"]["gaze_on_camera_pct"] == pytest.approx(0.85)
    assert body["observations"] == ["Excellent eye contact."]


@pytest.mark.asyncio
async def test_analyze_video_session_not_found(async_client):
    with patch("app.routers.cv.session_store.get", return_value=None):
        async with async_client as c:
            video_bytes = io.BytesIO(b"fake-video-data")
            resp = await c.post(
                "/sessions/nonexistent-id/video",
                files={"video": ("interview.webm", video_bytes, "video/webm")},
            )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Session not found"


@pytest.mark.asyncio
async def test_analyze_video_non_video_content_type(async_client):
    with patch("app.routers.cv.session_store.get", return_value={"turns": []}):
        async with async_client as c:
            resp = await c.post(
                "/sessions/test-session-id/video",
                files={"video": ("transcript.txt", io.BytesIO(b"hello"), "text/plain")},
            )

    assert resp.status_code == 422
    assert "video" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cv_result_stored_in_session(async_client):
    stored = {}

    def fake_set_cv_result(sid, result):
        stored[sid] = result

    with (
        patch("app.routers.cv.session_store.get", return_value={"turns": []}),
        patch("app.routers.cv.analyze_video", new_callable=AsyncMock, return_value=_FAKE_RESULT),
        patch("app.routers.cv.session_store.set_cv_result", side_effect=fake_set_cv_result),
    ):
        async with async_client as c:
            await c.post(
                "/sessions/test-session-id/video",
                files={"video": ("interview.webm", io.BytesIO(b"data"), "video/webm")},
            )

    assert "test-session-id" in stored
    assert stored["test-session-id"]["confidence_label"] == "High"
