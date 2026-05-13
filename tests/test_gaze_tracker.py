import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from app.services.cv.gaze_tracker import (
    GazeDirection,
    GazeTracker,
    _iris_center,
    _GAZE_THRESHOLD,
)


# ── _iris_center ──────────────────────────────────────────────────────────────

def test_iris_center_finds_darkest_pixel():
    img = np.full((30, 60), 200, dtype=np.uint8)
    img[15, 20] = 0  # single darkest pixel
    cx, cy = _iris_center(img)
    # GaussianBlur spreads the minimum slightly, allow small tolerance
    assert abs(cx - 20) <= 5
    assert abs(cy - 15) <= 5


def test_iris_center_uniform_image_returns_valid_coords():
    img = np.full((30, 60), 128, dtype=np.uint8)
    cx, cy = _iris_center(img)
    assert 0 <= cx < 60
    assert 0 <= cy < 30


# ── GazeTracker.process_frame ─────────────────────────────────────────────────

@pytest.fixture()
def mock_cascades():
    mock_face = MagicMock()
    mock_eye = MagicMock()
    mock_face.empty.return_value = False
    mock_eye.empty.return_value = False
    with (
        patch("app.services.cv.gaze_tracker._FACE_CASCADE", mock_face),
        patch("app.services.cv.gaze_tracker._EYE_CASCADE", mock_eye),
    ):
        yield mock_face, mock_eye


def _blank_frame() -> np.ndarray:
    return np.zeros((480, 640, 3), dtype=np.uint8)


def test_no_face_detected(mock_cascades):
    mock_face, _ = mock_cascades
    mock_face.detectMultiScale.return_value = ()

    result = GazeTracker().process_frame(_blank_frame(), timestamp=1.0)

    assert result.face_detected is False
    assert result.gaze == GazeDirection.NO_FACE
    assert result.ear == 0.0
    assert result.is_blink is False


def test_blink_when_no_eyes_in_face(mock_cascades):
    mock_face, mock_eye = mock_cascades
    mock_face.detectMultiScale.return_value = np.array([[0, 0, 200, 200]])
    mock_eye.detectMultiScale.return_value = ()

    result = GazeTracker().process_frame(_blank_frame(), timestamp=2.0)

    assert result.face_detected is True
    assert result.is_blink is True
    assert result.gaze == GazeDirection.CENTER  # default when blinking


def test_center_gaze(mock_cascades):
    mock_face, mock_eye = mock_cascades
    mock_face.detectMultiScale.return_value = np.array([[0, 0, 200, 200]])
    # Eye box: x=10,y=10,w=60,h=30 — iris at centre → both offsets = 0
    mock_eye.detectMultiScale.return_value = np.array([[10, 10, 60, 30]])

    with patch("app.services.cv.gaze_tracker._iris_center", return_value=(30.0, 15.0)):
        result = GazeTracker().process_frame(_blank_frame(), timestamp=3.0)

    assert result.face_detected is True
    assert result.gaze == GazeDirection.CENTER
    assert result.is_blink is False


def test_left_gaze(mock_cascades):
    mock_face, mock_eye = mock_cascades
    mock_face.detectMultiScale.return_value = np.array([[0, 0, 200, 200]])
    mock_eye.detectMultiScale.return_value = np.array([[10, 10, 60, 30]])

    # iris at x=5 → offset = 5/60 − 0.5 = −0.417, well past _GAZE_THRESHOLD
    with patch("app.services.cv.gaze_tracker._iris_center", return_value=(5.0, 15.0)):
        result = GazeTracker().process_frame(_blank_frame(), timestamp=4.0)

    assert result.gaze == GazeDirection.LEFT


def test_right_gaze(mock_cascades):
    mock_face, mock_eye = mock_cascades
    mock_face.detectMultiScale.return_value = np.array([[0, 0, 200, 200]])
    mock_eye.detectMultiScale.return_value = np.array([[10, 10, 60, 30]])

    # iris at x=55 → offset = 55/60 − 0.5 = +0.417
    with patch("app.services.cv.gaze_tracker._iris_center", return_value=(55.0, 15.0)):
        result = GazeTracker().process_frame(_blank_frame(), timestamp=5.0)

    assert result.gaze == GazeDirection.RIGHT


def test_up_gaze(mock_cascades):
    mock_face, mock_eye = mock_cascades
    mock_face.detectMultiScale.return_value = np.array([[0, 0, 200, 200]])
    mock_eye.detectMultiScale.return_value = np.array([[10, 10, 60, 30]])

    # iris at y=2 → v_offset = 2/30 − 0.5 = −0.433; h offset kept at 0
    with patch("app.services.cv.gaze_tracker._iris_center", return_value=(30.0, 2.0)):
        result = GazeTracker().process_frame(_blank_frame(), timestamp=6.0)

    assert result.gaze == GazeDirection.UP


def test_largest_face_used_when_multiple(mock_cascades):
    mock_face, mock_eye = mock_cascades
    # Two faces: small (50x50) and large (200x200)
    mock_face.detectMultiScale.return_value = np.array([[10, 10, 50, 50], [0, 0, 200, 200]])
    mock_eye.detectMultiScale.return_value = np.array([[10, 10, 60, 30]])

    with patch("app.services.cv.gaze_tracker._iris_center", return_value=(30.0, 15.0)):
        result = GazeTracker().process_frame(_blank_frame(), timestamp=7.0)

    # Should complete without error, processing the 200x200 face
    assert result.face_detected is True


def test_timestamp_preserved(mock_cascades):
    mock_face, _ = mock_cascades
    mock_face.detectMultiScale.return_value = ()

    result = GazeTracker().process_frame(_blank_frame(), timestamp=42.5)
    assert result.timestamp == 42.5
