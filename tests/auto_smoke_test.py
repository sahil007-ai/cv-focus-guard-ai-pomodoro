"""Basic automated smoke tests for core modules.

These tests avoid GUI and hardware dependencies.
"""

import tempfile
import time
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from collaboration import CollaborationSession
from focus_detector import FocusDetector
from logger import logger as app_logger
import config


class DummyLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def build_landmarks(default_x=0.5, default_y=0.5):
    landmarks = [DummyLandmark(default_x, default_y) for _ in range(468)]
    return landmarks


def set_open_eyes(landmarks, left_center=(0.6, 0.5), right_center=(0.4, 0.5)):
    # Left eye indices: [362, 385, 387, 263, 373, 380]
    landmarks[362] = DummyLandmark(left_center[0] - 0.05, left_center[1])
    landmarks[263] = DummyLandmark(left_center[0] + 0.05, left_center[1])
    landmarks[385] = DummyLandmark(left_center[0], left_center[1] - 0.04)
    landmarks[380] = DummyLandmark(left_center[0], left_center[1] + 0.04)
    landmarks[387] = DummyLandmark(left_center[0] + 0.02, left_center[1] - 0.04)
    landmarks[373] = DummyLandmark(left_center[0] + 0.02, left_center[1] + 0.04)

    # Right eye indices: [33, 160, 158, 133, 153, 144]
    landmarks[33] = DummyLandmark(right_center[0] - 0.05, right_center[1])
    landmarks[133] = DummyLandmark(right_center[0] + 0.05, right_center[1])
    landmarks[160] = DummyLandmark(right_center[0], right_center[1] - 0.04)
    landmarks[144] = DummyLandmark(right_center[0], right_center[1] + 0.04)
    landmarks[158] = DummyLandmark(right_center[0] + 0.02, right_center[1] - 0.04)
    landmarks[153] = DummyLandmark(right_center[0] + 0.02, right_center[1] + 0.04)


def set_closed_eyes(landmarks, left_center=(0.6, 0.5), right_center=(0.4, 0.5)):
    # Use a tiny vertical eye opening to trigger drowsy detection.
    landmarks[362] = DummyLandmark(left_center[0] - 0.05, left_center[1])
    landmarks[263] = DummyLandmark(left_center[0] + 0.05, left_center[1])
    landmarks[385] = DummyLandmark(left_center[0], left_center[1] - 0.005)
    landmarks[380] = DummyLandmark(left_center[0], left_center[1] + 0.005)
    landmarks[387] = DummyLandmark(left_center[0] + 0.02, left_center[1] - 0.005)
    landmarks[373] = DummyLandmark(left_center[0] + 0.02, left_center[1] + 0.005)

    landmarks[33] = DummyLandmark(right_center[0] - 0.05, right_center[1])
    landmarks[133] = DummyLandmark(right_center[0] + 0.05, right_center[1])
    landmarks[160] = DummyLandmark(right_center[0], right_center[1] - 0.005)
    landmarks[144] = DummyLandmark(right_center[0], right_center[1] + 0.005)
    landmarks[158] = DummyLandmark(right_center[0] + 0.02, right_center[1] - 0.005)
    landmarks[153] = DummyLandmark(right_center[0] + 0.02, right_center[1] + 0.005)


class CollaborationTests(unittest.TestCase):
    def test_create_join_and_events(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)
            self.assertTrue(code)

            guest = CollaborationSession(app_logger)
            joined = guest.join_session(tmp_dir, code)
            self.assertTrue(joined)

            payload = {"goals": ["Goal A", "Goal B"]}
            self.assertTrue(host.publish_event("goals_update", payload))
            time.sleep(0.05)

            events = guest.poll_events()
            self.assertTrue(events)
            self.assertEqual(events[-1]["type"], "goals_update")
            self.assertEqual(events[-1]["payload"], payload)

    def test_poll_ignores_own_events(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            session = CollaborationSession(app_logger)
            code = session.create_session(tmp_dir)
            self.assertTrue(code)
            self.assertTrue(session.publish_event("ping", {"ok": True}))
            time.sleep(0.05)
            self.assertEqual(session.poll_events(), [])

    def test_join_missing_session_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            guest = CollaborationSession(app_logger)
            self.assertFalse(guest.join_session(tmp_dir, "NOPE"))

    def test_publish_without_connection_returns_false(self):
        session = CollaborationSession(app_logger)
        self.assertFalse(session.publish_event("ping", {"ok": True}))

    def test_poll_after_session_file_deleted(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)
            session_file = Path(tmp_dir) / f"focus_guard_{code}.jsonl"
            self.assertTrue(session_file.exists())
            session_file.unlink()
            self.assertEqual(host.poll_events(), [])


class FocusDetectorTests(unittest.TestCase):
    def test_unfocused_none_when_center(self):
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.5, 0.5)  # nose
        set_open_eyes(landmarks, left_center=(0.6, 0.5), right_center=(0.4, 0.5))
        detector = FocusDetector(landmarks)
        self.assertIsNone(detector.is_unfocused())

    def test_unfocused_left_when_nose_shifts(self):
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.35, 0.5)
        set_open_eyes(landmarks, left_center=(0.8, 0.5), right_center=(0.4, 0.5))
        detector = FocusDetector(landmarks)
        self.assertEqual(detector.is_unfocused(), "Looking Left")

    def test_unfocused_drowsy_when_eyes_closed(self):
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.5, 0.5)
        set_closed_eyes(landmarks)
        detector = FocusDetector(landmarks)
        self.assertEqual(detector.is_unfocused(), "Drowsy")


class ConfigTests(unittest.TestCase):
    def test_paths_exist(self):
        self.assertTrue(Path(config.DATA_DIR).exists())
        self.assertTrue(Path(config.LOG_DIR).exists())
        self.assertTrue(Path(config.COLLAB_DIR).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
