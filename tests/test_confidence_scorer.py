import pytest

from app.schemas.schemas import CVMetrics
from app.services.cv.confidence_scorer import score_session


def _metrics(**kwargs) -> CVMetrics:
    defaults = dict(
        total_duration=60.0,
        face_detected_pct=1.0,
        gaze_on_camera_pct=1.0,
        gaze_away_events=0,
        avg_gaze_away_duration=0.0,
        max_gaze_away_duration=0.0,
        blink_count=10,
        gaze_timeline=[],
    )
    defaults.update(kwargs)
    return CVMetrics(**defaults)


# ── Score ranges ──────────────────────────────────────────────────────────────

def test_perfect_session_scores_100():
    score, label, _ = score_session(_metrics())
    assert score == pytest.approx(100.0)
    assert label == "High"


def test_high_label_threshold():
    # gaze=75%, 2 events/min, avg 0.5s away, full face → should be High
    score, label, _ = score_session(_metrics(
        gaze_on_camera_pct=0.75,
        gaze_away_events=2,
        avg_gaze_away_duration=0.5,
    ))
    assert label == "High"
    assert score >= 75.0


def test_medium_label_threshold():
    score, label, _ = score_session(_metrics(
        gaze_on_camera_pct=0.50,
        gaze_away_events=6,
        avg_gaze_away_duration=1.5,
        face_detected_pct=0.90,
    ))
    assert label == "Medium"
    assert 50.0 <= score < 75.0


def test_low_label_threshold():
    score, label, _ = score_session(_metrics(
        gaze_on_camera_pct=0.20,
        gaze_away_events=20,
        avg_gaze_away_duration=6.0,
        max_gaze_away_duration=10.0,
        face_detected_pct=0.50,
    ))
    assert label == "Low"
    assert score < 50.0


# ── Gaze score component ──────────────────────────────────────────────────────

def test_gaze_score_proportional():
    s1, _, _ = score_session(_metrics(gaze_on_camera_pct=1.0))
    s2, _, _ = score_session(_metrics(gaze_on_camera_pct=0.5))
    assert s1 > s2


def test_zero_gaze_on_camera():
    score, label, obs = score_session(_metrics(gaze_on_camera_pct=0.0))
    assert label == "Low"
    assert any("low" in o.lower() or "frequent" in o.lower() for o in obs)


# ── Event frequency component ─────────────────────────────────────────────────

def test_high_event_frequency_deducts_points():
    hi_events, _, _ = score_session(_metrics(gaze_away_events=30))  # 30/min
    lo_events, _, _ = score_session(_metrics(gaze_away_events=2))   # 2/min
    assert lo_events > hi_events


def test_event_observation_triggered_above_threshold():
    _, _, obs = score_session(_metrics(gaze_away_events=20))
    assert any("looked away" in o.lower() for o in obs)


def test_no_event_observation_when_infrequent():
    _, _, obs = score_session(_metrics(gaze_away_events=3))
    assert not any("looked away" in o.lower() for o in obs)


# ── Duration component ────────────────────────────────────────────────────────

def test_long_avg_duration_deducts_points():
    short, _, _ = score_session(_metrics(avg_gaze_away_duration=0.5))
    long_, _, _ = score_session(_metrics(avg_gaze_away_duration=4.0))
    assert short > long_


def test_max_gaze_away_observation():
    _, _, obs = score_session(_metrics(max_gaze_away_duration=8.0))
    assert any("longest" in o.lower() for o in obs)


# ── Face visibility component ─────────────────────────────────────────────────

def test_low_face_visibility_deducts_and_observes():
    score_full, _, _ = score_session(_metrics(face_detected_pct=1.0))
    score_low, _, obs = score_session(_metrics(face_detected_pct=0.5))
    assert score_full > score_low
    assert any("visible" in o.lower() or "frame" in o.lower() for o in obs)


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_zero_duration_does_not_raise():
    score, label, obs = score_session(_metrics(total_duration=0.0, gaze_away_events=5))
    assert isinstance(score, float)
    assert label in ("High", "Medium", "Low")


def test_fallback_observation_when_all_perfect():
    _, _, obs = score_session(_metrics())
    assert len(obs) == 1
    assert "confident" in obs[0].lower() or "excellent" in obs[0].lower()
