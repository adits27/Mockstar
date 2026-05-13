from __future__ import annotations

from typing import List, Tuple

from app.schemas.schemas import CVMetrics


def score_session(metrics: CVMetrics) -> Tuple[float, str, List[str]]:
    """
    Returns (score 0-100, label "High"/"Medium"/"Low", observations).

    Point breakdown:
      40 — gaze-on-camera percentage
      30 — gaze-away event frequency (per minute)
      20 — average gaze-away duration
      10 — face-visible percentage
    """
    observations: List[str] = []

    # ── 40 pts: gaze on camera ──────────────────────────────────────────────
    gaze_score = metrics.gaze_on_camera_pct * 40.0

    if metrics.gaze_on_camera_pct >= 0.80:
        observations.append("Excellent eye contact — you maintained camera focus throughout.")
    elif metrics.gaze_on_camera_pct >= 0.60:
        observations.append("Good eye contact overall with some brief moments of looking away.")
    elif metrics.gaze_on_camera_pct >= 0.40:
        observations.append(
            "Eye contact was inconsistent — aim to keep your gaze toward the camera more steadily."
        )
    else:
        observations.append(
            "Eye contact was low — frequent gaze breaks can signal low confidence to an interviewer."
        )

    # ── 30 pts: gaze-away frequency ─────────────────────────────────────────
    duration_min = metrics.total_duration / 60.0 if metrics.total_duration > 0 else 1.0
    events_per_min = metrics.gaze_away_events / duration_min

    if events_per_min <= 4:
        events_score = 30.0
    elif events_per_min <= 8:
        events_score = 20.0
    elif events_per_min <= 14:
        events_score = 10.0
    else:
        events_score = 0.0

    if events_per_min > 8:
        observations.append(
            f"You looked away {metrics.gaze_away_events} time(s) "
            f"({events_per_min:.1f}/min) — try to reduce frequent gaze breaks."
        )

    # ── 20 pts: average gaze-away duration ──────────────────────────────────
    avg = metrics.avg_gaze_away_duration

    if avg <= 1.0:
        duration_score = 20.0
    elif avg <= 2.5:
        duration_score = 12.0
    elif avg <= 5.0:
        duration_score = 5.0
    else:
        duration_score = 0.0

    if avg > 2.5:
        observations.append(
            f"Average gaze-away lasted {avg:.1f}s — prolonged breaks from the camera are noticeable."
        )

    if metrics.max_gaze_away_duration > 5.0:
        observations.append(
            f"Longest single gaze-away was {metrics.max_gaze_away_duration:.1f}s — "
            "avoid extended periods of looking away."
        )

    # ── 10 pts: face visibility ──────────────────────────────────────────────
    face_score = metrics.face_detected_pct * 10.0

    if metrics.face_detected_pct < 0.80:
        observations.append(
            "Your face was not always clearly visible — "
            "ensure you are well-lit and centered in the frame."
        )

    total = round(gaze_score + events_score + duration_score + face_score, 1)

    if total >= 75:
        label = "High"
    elif total >= 50:
        label = "Medium"
    else:
        label = "Low"

    if not observations:
        observations.append("Strong confident presence throughout — excellent focus and composure.")

    return total, label, observations
