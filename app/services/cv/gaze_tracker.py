from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

import cv2
import numpy as np


class GazeDirection(str, Enum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    NO_FACE = "no_face"


@dataclass
class FrameResult:
    timestamp: float
    face_detected: bool
    gaze: GazeDirection
    ear: float                                    # eye h/w ratio proxy for openness
    is_blink: bool                                # face visible but no eyes detected
    face_rect: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h) in frame coords


# OpenCV ships these XML files alongside the library — no separate download needed
_FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
_EYE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye.xml"
)

_GAZE_THRESHOLD = 0.15   # normalised offset from centre to call a direction


def _iris_center(eye_gray: np.ndarray) -> tuple[float, float]:
    """Return (x, y) of the darkest pixel — a reliable pupil/iris proxy."""
    blurred = cv2.GaussianBlur(eye_gray, (7, 7), 0)
    _, _, min_loc, _ = cv2.minMaxLoc(blurred)
    return float(min_loc[0]), float(min_loc[1])


class GazeTracker:
    def __init__(self) -> None:
        if _FACE_CASCADE.empty() or _EYE_CASCADE.empty():
            raise RuntimeError(
                "OpenCV Haar cascade XML files not found. "
                "Ensure opencv-python is properly installed."
            )

    def process_frame(self, frame_rgb: np.ndarray, timestamp: float) -> FrameResult:
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)

        faces = _FACE_CASCADE.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        if not len(faces):
            return FrameResult(
                timestamp=timestamp,
                face_detected=False,
                gaze=GazeDirection.NO_FACE,
                ear=0.0,
                is_blink=False,
            )

        # Use the largest detected face
        fx, fy, fw, fh = max(faces, key=lambda r: r[2] * r[3])
        face_gray = gray[fy : fy + fh, fx : fx + fw]

        # Eyes sit in the upper half of the face bounding box
        upper = face_gray[: fh // 2, :]
        eyes = _EYE_CASCADE.detectMultiScale(
            upper, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20)
        )

        face_rect = (int(fx), int(fy), int(fw), int(fh))

        # Face present but eyes not detected → blink / eyes closed
        if not len(eyes):
            return FrameResult(
                timestamp=timestamp,
                face_detected=True,
                gaze=GazeDirection.CENTER,
                ear=0.0,
                is_blink=True,
                face_rect=face_rect,
            )

        h_offsets: list[float] = []
        v_offsets: list[float] = []
        ear_vals: list[float] = []

        for ex, ey, ew, eh in eyes[:2]:
            eye_gray = upper[ey : ey + eh, ex : ex + ew]
            ix, iy = _iris_center(eye_gray)

            # Offset of iris from eye-box centre, normalised to [-0.5, 0.5]
            h_offsets.append((ix / ew) - 0.5 if ew > 0 else 0.0)
            v_offsets.append((iy / eh) - 0.5 if eh > 0 else 0.0)
            ear_vals.append(eh / ew if ew > 0 else 0.0)

        avg_h = sum(h_offsets) / len(h_offsets)
        avg_v = sum(v_offsets) / len(v_offsets)
        avg_ear = sum(ear_vals) / len(ear_vals)

        if abs(avg_h) < _GAZE_THRESHOLD and abs(avg_v) < _GAZE_THRESHOLD:
            gaze = GazeDirection.CENTER
        elif abs(avg_h) >= abs(avg_v):
            gaze = GazeDirection.LEFT if avg_h < 0 else GazeDirection.RIGHT
        else:
            gaze = GazeDirection.UP if avg_v < 0 else GazeDirection.DOWN

        return FrameResult(
            timestamp=timestamp,
            face_detected=True,
            gaze=gaze,
            ear=round(avg_ear, 4),
            is_blink=False,
            face_rect=face_rect,
        )

    def close(self) -> None:
        pass  # cascade classifiers have no resources to release
