"""
File-based collaboration for accountability sessions.

Uses a shared folder and a short session code to coordinate two clients.
"""

from __future__ import annotations

import json
import random
import string
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional


class CollaborationSession:
    def __init__(self, logger, code_length: int = 6) -> None:
        self.logger = logger
        self.code_length = max(4, code_length)
        self.sender_id = uuid.uuid4().hex
        self.session_code: Optional[str] = None
        self.shared_dir: Optional[Path] = None
        self.session_file: Optional[Path] = None
        self.connected = False
        self.last_position = 0

    def generate_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(random.choice(alphabet) for _ in range(self.code_length))

    def _session_file_path(self, shared_dir: Path, code: str) -> Path:
        filename = f"focus_guard_{code}.jsonl"
        return shared_dir / filename

    def create_session(self, shared_dir: str, code: Optional[str] = None) -> str:
        shared_path = Path(shared_dir)
        shared_path.mkdir(parents=True, exist_ok=True)

        session_code = code or self.generate_code()
        session_file = self._session_file_path(shared_path, session_code)
        session_file.touch(exist_ok=True)

        self.session_code = session_code
        self.shared_dir = shared_path
        self.session_file = session_file
        self.connected = True
        self.last_position = 0

        self.publish_event("session_created", {"code": session_code})
        self.logger.info("Collaboration session created: %s", session_code)
        return session_code

    def join_session(self, shared_dir: str, code: str) -> bool:
        shared_path = Path(shared_dir)
        session_file = self._session_file_path(shared_path, code)
        if not session_file.exists():
            return False

        self.session_code = code
        self.shared_dir = shared_path
        self.session_file = session_file
        self.connected = True
        self.last_position = 0

        self.publish_event("session_joined", {"code": code})
        self.logger.info("Joined collaboration session: %s", code)
        return True

    def disconnect(self) -> None:
        if self.connected:
            self.publish_event("session_left", {})
        self.connected = False
        self.session_code = None
        self.shared_dir = None
        self.session_file = None
        self.last_position = 0

    def publish_event(self, event_type: str, payload: Dict) -> bool:
        if not self.connected or self.session_file is None:
            return False

        event = {
            "type": event_type,
            "timestamp": time.time(),
            "sender": self.sender_id,
            "payload": payload,
        }

        try:
            with self.session_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event) + "\n")
            return True
        except Exception as exc:
            self.logger.warning("Failed to write collaboration event: %s", exc)
            return False

    def poll_events(self) -> List[Dict]:
        if not self.connected or self.session_file is None:
            return []

        if not self.session_file.exists():
            return []

        events: List[Dict] = []
        try:
            file_size = self.session_file.stat().st_size
            if self.last_position > file_size:
                self.last_position = 0

            with self.session_file.open("r", encoding="utf-8") as handle:
                handle.seek(self.last_position)
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if event.get("sender") == self.sender_id:
                        continue
                    events.append(event)

                self.last_position = handle.tell()
        except Exception as exc:
            self.logger.warning("Failed to read collaboration events: %s", exc)

        return events
