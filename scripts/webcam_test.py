#!/usr/bin/env python3
"""
MockStar – Live Facial Analysis
Run from the project root:  python scripts/webcam_test.py
Q / ESC  – quit and print final confidence report
R        – reset the current session
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from app.services.cv.analyzer import _aggregate
from app.services.cv.confidence_scorer import score_session
from app.services.cv.gaze_tracker import GazeDirection, GazeTracker, FrameResult

# ── Layout constants ──────────────────────────────────────────────────────────
_HDR_H  = 72    # header panel height
_FTR_H  = 108   # footer panel height

# ── Colour palette (all tuples are BGR) ──────────────────────────────────────
_BG       = (22,  18,  16)    # near-black canvas
_PANEL    = (32,  28,  26)    # slightly lighter panel fill
_DIVIDER  = (58,  52,  48)    # subtle separator lines
_ACCENT   = (255, 195,  45)   # electric cyan-teal  (B high + G high)
_GREEN    = ( 85, 205,  60)   # success green
_ORANGE   = (  0, 155, 255)   # warning orange
_RED      = ( 55,  55, 220)   # alert red
_WHITE    = (248, 244, 240)   # warm white text
_SILVER   = (175, 168, 162)   # secondary text
_DIM      = ( 90,  82,  76)   # dimmed / hint text
_TRACK    = ( 60,  54,  50)   # progress-bar track
_LIVE_ON  = ( 45,  45, 235)   # pulsing REC dot (red)
_LIVE_OFF = ( 75,  68,  90)   # dim REC dot

_SF  = cv2.FONT_HERSHEY_SIMPLEX
_DF  = cv2.FONT_HERSHEY_DUPLEX
_AA  = cv2.LINE_AA

_GAZE_COLOR = {
    GazeDirection.CENTER:  _GREEN,
    GazeDirection.LEFT:    _ORANGE,
    GazeDirection.RIGHT:   _ORANGE,
    GazeDirection.UP:      _ORANGE,
    GazeDirection.DOWN:    _ORANGE,
    GazeDirection.NO_FACE: _RED,
}
_GAZE_LABEL = {
    GazeDirection.CENTER:  "CENTER",
    GazeDirection.LEFT:    "LEFT",
    GazeDirection.RIGHT:   "RIGHT",
    GazeDirection.UP:      "UP",
    GazeDirection.DOWN:    "DOWN",
    GazeDirection.NO_FACE: "NO FACE",
}


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _t(img, text, x, y, color=_WHITE, font=_SF, scale=0.52, thick=1):
    cv2.putText(img, text, (x, y), font, scale, color, thick, _AA)


def _panel(img, x1, y1, x2, y2, color=_BG, alpha=0.88):
    roi = img[y1:y2, x1:x2]
    fill = np.full_like(roi, color)
    cv2.addWeighted(fill, alpha, roi, 1 - alpha, 0, roi)
    img[y1:y2, x1:x2] = roi


def _hline(img, x1, x2, y, color=_DIVIDER, thick=1):
    cv2.line(img, (x1, y), (x2, y), color, thick, _AA)


def _vline(img, x, y1, y2, color=_DIVIDER, thick=1):
    cv2.line(img, (x, y1), (x, y2), color, thick, _AA)


def _bar(img, x, y, w, h, pct, fill_color=_GREEN):
    """Filled progress bar with track and a bright leading edge."""
    cv2.rectangle(img, (x, y), (x + w, y + h), _TRACK, -1)
    fill = int(w * max(0.0, min(1.0, pct)))
    if fill > 0:
        cv2.rectangle(img, (x, y), (x + fill, y + h), fill_color, -1)
        # Bright leading-edge accent
        cv2.rectangle(img, (x + fill - 2, y), (x + fill, y + h), _WHITE, -1)


def _corner_box(img, x, y, w, h, color, arm=22, thick=2):
    """Bracket-style corners — classic HUD / tech look."""
    pts = [
        ((x,     y),     (x+arm, y    )), ((x,     y),     (x,     y+arm)),
        ((x+w,   y),     (x+w-arm, y  )), ((x+w,   y),     (x+w,   y+arm)),
        ((x,     y+h),   (x+arm, y+h  )), ((x,     y+h),   (x,     y+h-arm)),
        ((x+w,   y+h),   (x+w-arm, y+h)), ((x+w,   y+h),   (x+w,   y+h-arm)),
    ]
    for p1, p2 in pts:
        cv2.line(img, p1, p2, color, thick, _AA)


def _gaze_eye(img, cx, cy, gaze: GazeDirection):
    """Tiny stylised eye widget showing iris position."""
    ew, eh = 32, 19
    col = _GAZE_COLOR.get(gaze, _SILVER)

    # Whites of the eye
    cv2.ellipse(img, (cx, cy), (ew, eh), 0, 0, 360, _DIVIDER, -1)
    cv2.ellipse(img, (cx, cy), (ew, eh), 0, 0, 360, _DIM,     1, _AA)

    iris_offsets = {
        GazeDirection.CENTER:  ( 0,  0),
        GazeDirection.LEFT:    (-14, 0),
        GazeDirection.RIGHT:   ( 14, 0),
        GazeDirection.UP:      ( 0, -8),
        GazeDirection.DOWN:    ( 0,  8),
        GazeDirection.NO_FACE: ( 0,  0),
    }
    ox, oy = iris_offsets.get(gaze, (0, 0))
    icx, icy = cx + ox, cy + oy

    cv2.circle(img, (icx, icy), 11, col,    -1, _AA)   # iris
    cv2.circle(img, (icx, icy),  5, _BG,    -1, _AA)   # pupil
    cv2.circle(img, (icx+3, icy-3), 2, _WHITE, -1, _AA)  # specular glint

    # Eyelid lines
    cv2.ellipse(img, (cx, cy), (ew, eh), 0, 190, 350, _SILVER, 1, _AA)


# ── Section renderers ─────────────────────────────────────────────────────────

def _draw_header(frame: np.ndarray, elapsed: float) -> None:
    fh, fw = frame.shape[:2]

    # Panel fill
    _panel(frame, 0, 0, fw, _HDR_H, _BG, alpha=0.94)

    # Left accent stripe
    cv2.rectangle(frame, (0, 0), (4, _HDR_H), _ACCENT, -1)

    # Logo mark: concentric rings
    lx, ly = 30, _HDR_H // 2
    cv2.circle(frame, (lx, ly), 14, _ACCENT, -1, _AA)
    cv2.circle(frame, (lx, ly),  8, _BG,     -1, _AA)
    cv2.circle(frame, (lx, ly),  3, _ACCENT, -1, _AA)

    # Brand name + subtitle
    _t(frame, "MOCKSTAR",              50, 31, _WHITE,  _DF,  0.78, 2)
    _t(frame, "Facial Analysis",       50, 55, _ACCENT, _SF,  0.44, 1)

    # Thin vertical rule
    _vline(frame, 248, 12, _HDR_H - 12, _DIVIDER)

    # Description
    _t(frame, "AI Interview Confidence Tracker", 264, 30, _SILVER, _SF, 0.44, 1)
    _t(frame, "Monitoring: gaze  /  eye contact  /  attention", 264, 52, _DIM, _SF, 0.36, 1)

    # Right side – timer
    mins, secs = int(elapsed // 60), int(elapsed % 60)
    _t(frame, f"{mins:02d}:{secs:02d}", fw - 190, 38, _WHITE, _DF, 0.78, 2)

    # Pulsing REC dot + label
    live_col = _LIVE_ON if int(time.time() * 2) % 2 == 0 else _LIVE_OFF
    cv2.circle(frame, (fw - 82, _HDR_H // 2 - 3), 6, live_col, -1, _AA)
    _t(frame, "REC", fw - 70, 37, live_col, _SF, 0.46, 1)

    # Bottom separator with accent flush at edges
    _hline(frame, 0, fw, _HDR_H,     _DIVIDER)
    cv2.rectangle(frame, (0, _HDR_H - 1), (fw, _HDR_H), _ACCENT, -1)


def _draw_video_overlay(frame: np.ndarray, result: FrameResult) -> None:
    fh, fw = frame.shape[:2]
    vy1 = _HDR_H
    vy2 = fh - _FTR_H

    # Outer HUD corner brackets
    _corner_box(frame, 18, vy1 + 18, fw - 36, vy2 - vy1 - 36, _ACCENT, arm=28, thick=2)

    # Face bounding-box (styled corners)
    if result.face_detected and result.face_rect:
        fx, fy, fw2, fh2 = result.face_rect
        box_color = _GREEN if not result.is_blink else _ORANGE
        _corner_box(frame, fx, fy, fw2, fh2, box_color, arm=18, thick=2)

        # Label above the box
        label = "BLINK" if result.is_blink else "TRACKING"
        lbl_w = cv2.getTextSize(label, _SF, 0.42, 1)[0][0]
        _t(frame, label, fx + (fw2 - lbl_w) // 2, fy - 10, box_color, _SF, 0.42, 1)

    # Floating status chip — top-right of video zone
    chip_w, chip_h = 208, 30
    cx = fw - chip_w - 22
    cy = vy1 + 14
    _panel(frame, cx, cy, cx + chip_w, cy + chip_h, _PANEL, alpha=0.75)
    cv2.rectangle(frame, (cx, cy), (cx + chip_w, cy + chip_h), _DIVIDER, 1, _AA)
    # Left-edge colour stripe on the chip
    gaze_col = _GAZE_COLOR.get(result.gaze, _SILVER)
    cv2.rectangle(frame, (cx, cy), (cx + 3, cy + chip_h), gaze_col, -1)
    _t(frame, "GAZE  " + _GAZE_LABEL.get(result.gaze, ""), cx + 14, cy + 20, gaze_col, _SF, 0.46, 1)

    # Small watermark in bottom-right of video zone
    _t(frame, "MockStar  v1.0", fw - 170, vy2 - 10, _DIM, _SF, 0.36, 1)


def _draw_footer(frame: np.ndarray, result: FrameResult, stats: dict) -> None:
    fh, fw = frame.shape[:2]
    fy0 = fh - _FTR_H

    _panel(frame, 0, fy0, fw, fh, _BG, alpha=0.94)
    # Top border: thin accent line then divider
    cv2.rectangle(frame, (0, fy0), (fw, fy0 + 2), _ACCENT, -1)
    _hline(frame, 0, fw, fy0 + 2, _DIVIDER)

    y0 = fy0 + 2   # usable top of footer
    col_w = fw // 4
    pad = 22

    # ── Col 1 · Face Status ───────────────────────────────────────────────────
    x = pad
    _t(frame, "FACE TRACKING", x, y0 + 22, _SILVER, _SF, 0.37, 1)

    face_col   = _GREEN if result.face_detected else _RED
    face_label = "DETECTED" if result.face_detected else "NOT FOUND"
    cv2.circle(frame, (x + 7, y0 + 44), 5, face_col, -1, _AA)
    _t(frame, face_label, x + 20, y0 + 49, face_col, _DF, 0.56, 1)
    _t(frame, f"Blinks: {stats['blinks']}", x, y0 + 74, _DIM, _SF, 0.38, 1)
    _t(frame, f"EAR: {result.ear:.3f}", x, y0 + 92, _DIM, _SF, 0.35, 1)

    _vline(frame, col_w, y0 + 12, fh - 10, _DIVIDER)

    # ── Col 2 · Gaze Direction ────────────────────────────────────────────────
    x = col_w + pad
    _t(frame, "GAZE DIRECTION", x, y0 + 22, _SILVER, _SF, 0.37, 1)

    gaze_col = _GAZE_COLOR.get(result.gaze, _SILVER)
    _gaze_eye(frame, x + 24, y0 + 56, result.gaze)
    _t(frame, _GAZE_LABEL.get(result.gaze, ""), x + 62, y0 + 62, gaze_col, _DF, 0.62, 1)
    blink_note = "eyes closed" if result.is_blink else ""
    if blink_note:
        _t(frame, blink_note, x + 62, y0 + 82, _ORANGE, _SF, 0.36, 1)

    _vline(frame, col_w * 2, y0 + 12, fh - 10, _DIVIDER)

    # ── Col 3 · Eye Contact % ─────────────────────────────────────────────────
    x = col_w * 2 + pad
    _t(frame, "EYE CONTACT", x, y0 + 22, _SILVER, _SF, 0.37, 1)

    n = stats["total_frames"]
    if n > 0:
        on_cam = stats["center_frames"] / n
        vis    = stats["face_frames"]   / n
        bar_col = _GREEN if on_cam >= 0.70 else (_ORANGE if on_cam >= 0.40 else _RED)

        _bar(frame, x, y0 + 32, col_w - pad * 2, 7, on_cam, bar_col)
        _t(frame, f"{on_cam*100:.0f}%", x, y0 + 60, bar_col, _DF, 0.68, 2)
        _t(frame, f"Face visible: {vis*100:.0f}%", x, y0 + 82, _DIM, _SF, 0.37, 1)
        _t(frame, f"Look-aways: {stats['away_events']}", x, y0 + 98, _DIM, _SF, 0.35, 1)
    else:
        _t(frame, "--", x, y0 + 60, _SILVER, _DF, 0.68, 1)

    _vline(frame, col_w * 3, y0 + 12, fh - 10, _DIVIDER)

    # ── Col 4 · Session Stats + Controls ─────────────────────────────────────
    x = col_w * 3 + pad
    _t(frame, "SESSION STATS", x, y0 + 22, _SILVER, _SF, 0.37, 1)

    elapsed = time.time() - stats["start_time"]
    _t(frame, f"Duration:   {int(elapsed)}s",           x, y0 + 46, _WHITE,  _SF, 0.48, 1)
    _t(frame, f"Look-aways: {stats['away_events']}",   x, y0 + 66, _WHITE,  _SF, 0.48, 1)
    _t(frame, f"Blinks:     {stats['blinks']}",         x, y0 + 86, _SILVER, _SF, 0.44, 1)

    # Keyboard hints
    hint_y = fh - 8
    _t(frame, "Q  quit + score    R  reset", x, hint_y, _DIM, _SF, 0.35, 1)


# ── Session state ─────────────────────────────────────────────────────────────

def _fresh_stats() -> dict:
    return {
        "total_frames": 0, "face_frames": 0,
        "center_frames": 0, "away_events": 0,
        "blinks": 0, "start_time": time.time(),
    }


def _print_results(frame_results: list) -> None:
    if not frame_results:
        print("No frames captured."); return

    metrics  = _aggregate(frame_results)
    score, label, obs = score_session(metrics)
    filled  = int(score // 5)
    bar_str = "#" * filled + "-" * (20 - filled)

    print()
    print("=" * 56)
    print("  MOCKSTAR  -  CONFIDENCE ANALYSIS REPORT")
    print("=" * 56)
    print(f"  Score      {score:5.1f} / 100   [ {label} ]")
    print(f"             [{bar_str}]")
    print("-" * 56)
    print(f"  Duration          {metrics.total_duration:.1f}s")
    print(f"  Face visible      {metrics.face_detected_pct*100:.0f}%")
    print(f"  On-camera gaze    {metrics.gaze_on_camera_pct*100:.0f}%")
    print(f"  Gaze-away events  {metrics.gaze_away_events}")
    print(f"  Avg away          {metrics.avg_gaze_away_duration:.1f}s")
    print(f"  Max away          {metrics.max_gaze_away_duration:.1f}s")
    print(f"  Blinks            {metrics.blink_count}")
    print("-" * 56)
    print("  Observations")
    for o in obs:
        print(f"    - {o}")
    print("=" * 56)
    print()


# ── Main loop ─────────────────────────────────────────────────────────────────

def run() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open webcam (index 0).")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    tracker = GazeTracker()
    frame_results = []
    stats = _fresh_stats()
    last_gaze = None

    print("MockStar Facial Analysis  -  Q to quit and score  -  R to reset")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ts    = time.time() - stats["start_time"]

            result = tracker.process_frame(rgb, ts)
            frame_results.append(result)

            stats["total_frames"] += 1
            if result.face_detected:
                stats["face_frames"] += 1
            if result.gaze == GazeDirection.CENTER:
                stats["center_frames"] += 1
            if result.is_blink:
                stats["blinks"] += 1

            if last_gaze is not None:
                was_ok = last_gaze in (GazeDirection.CENTER, GazeDirection.NO_FACE)
                is_off = result.gaze not in (GazeDirection.CENTER, GazeDirection.NO_FACE)
                if was_ok and is_off:
                    stats["away_events"] += 1
            last_gaze = result.gaze

            elapsed = time.time() - stats["start_time"]
            _draw_header(frame, elapsed)
            _draw_video_overlay(frame, result)
            _draw_footer(frame, result, stats)

            cv2.imshow("MockStar  |  Facial Analysis", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("r"):
                frame_results.clear()
                stats = _fresh_stats()
                last_gaze = None
                print("Session reset.")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        tracker.close()

    _print_results(frame_results)


if __name__ == "__main__":
    run()
