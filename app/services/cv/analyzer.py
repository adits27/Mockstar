from __future__ import annotations

import os
import tempfile
from typing import List

import cv2
from fastapi import UploadFile

from app.schemas.schemas import CVAnalysisResult, CVMetrics, GazeEvent
from app.services.cv.confidence_scorer import score_session
from app.services.cv.gaze_tracker import GazeDirection, GazeTracker, FrameResult

_SAMPLE_INTERVAL_S = 0.1  # analyze one frame every 100 ms


async def analyze_video(video_file: UploadFile, session_id: str) -> CVAnalysisResult:
    ext = os.path.splitext(video_file.filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(await video_file.read())
        tmp_path = tmp.name

    try:
        frames = _process_video(tmp_path)
        metrics = _aggregate(frames)
        score, label, observations = score_session(metrics)
    finally:
        os.unlink(tmp_path)

    return CVAnalysisResult(
        session_id=session_id,
        confidence_score=score,
        confidence_label=label,
        metrics=metrics,
        observations=observations,
    )


def _process_video(path: str) -> List[FrameResult]:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_step = max(1, int(fps * _SAMPLE_INTERVAL_S))
    tracker = GazeTracker()
    results: List[FrameResult] = []
    idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % frame_step == 0:
                ts = idx / fps
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results.append(tracker.process_frame(rgb, ts))
            idx += 1
    finally:
        cap.release()
        tracker.close()

    return results


def _aggregate(frames: List[FrameResult]) -> CVMetrics:
    if not frames:
        return CVMetrics(
            total_duration=0.0,
            face_detected_pct=0.0,
            gaze_on_camera_pct=0.0,
            gaze_away_events=0,
            avg_gaze_away_duration=0.0,
            max_gaze_away_duration=0.0,
            blink_count=0,
            gaze_timeline=[],
        )

    n = len(frames)
    total_dur = frames[-1].timestamp if n > 1 else 0.0
    face_count = sum(1 for f in frames if f.face_detected)
    center_count = sum(1 for f in frames if f.gaze == GazeDirection.CENTER)
    blinks = sum(1 for f in frames if f.is_blink)

    # Build timeline of contiguous same-direction runs
    timeline: List[GazeEvent] = []
    cur_dir = frames[0].gaze
    cur_start = frames[0].timestamp

    for i in range(1, n):
        if frames[i].gaze != cur_dir:
            timeline.append(GazeEvent(
                timestamp=round(cur_start, 3),
                direction=cur_dir,
                duration=round(frames[i].timestamp - cur_start, 3),
            ))
            cur_dir = frames[i].gaze
            cur_start = frames[i].timestamp

    timeline.append(GazeEvent(
        timestamp=round(cur_start, 3),
        direction=cur_dir,
        duration=round(frames[-1].timestamp - cur_start, 3),
    ))

    away = [e for e in timeline if e.direction not in ("center", "no_face")]
    away_durs = [e.duration for e in away]

    return CVMetrics(
        total_duration=round(total_dur, 2),
        face_detected_pct=round(face_count / n, 3),
        gaze_on_camera_pct=round(center_count / n, 3),
        gaze_away_events=len(away),
        avg_gaze_away_duration=round(sum(away_durs) / len(away_durs), 3) if away_durs else 0.0,
        max_gaze_away_duration=round(max(away_durs), 3) if away_durs else 0.0,
        blink_count=blinks,
        gaze_timeline=timeline,
    )
