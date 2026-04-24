import json
import threading
from pathlib import Path

from app.automation.models import EventStatus, LegalDocumentEvent


class EventStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({"events": []}, indent=2), encoding="utf-8")

    def _read_payload(self) -> dict:
        if not self.path.exists():
            return {"events": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"events": []}

    def _write_payload(self, payload: dict) -> None:
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_events(self) -> list[LegalDocumentEvent]:
        payload = self._read_payload()
        events = payload.get("events", [])
        return [LegalDocumentEvent.from_dict(item) for item in reversed(events)]

    def append_event(self, event: LegalDocumentEvent) -> None:
        with self._lock:
            payload = self._read_payload()
            payload.setdefault("events", []).append(event.to_dict())
            self._write_payload(payload)

    def has_message_id(self, message_id: str) -> bool:
        if not message_id:
            return False
        payload = self._read_payload()
        return any(item.get("message_id") == message_id for item in payload.get("events", []))

    def summary(self) -> dict[str, int]:
        counts = {
            "total": 0,
            EventStatus.PROCESSED.value: 0,
            EventStatus.IGNORED.value: 0,
            EventStatus.FAILED.value: 0,
            "created": 0,
            "updated": 0,
        }
        for event in self.list_events():
            counts["total"] += 1
            counts[event.status] = counts.get(event.status, 0) + 1
            if event.action in {"created", "updated"}:
                counts[event.action] = counts.get(event.action, 0) + 1
        return counts


class MailStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(
                json.dumps({"processed_message_ids": [], "last_seen_uid": 0}, indent=2),
                encoding="utf-8",
            )

    def _read_payload(self) -> dict:
        if not self.path.exists():
            return {"processed_message_ids": [], "last_seen_uid": 0}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"processed_message_ids": [], "last_seen_uid": 0}

    def _write_payload(self, payload: dict) -> None:
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_last_seen_uid(self) -> int:
        payload = self._read_payload()
        return int(payload.get("last_seen_uid", 0) or 0)

    def has_processed(self, message_id: str) -> bool:
        if not message_id:
            return False
        payload = self._read_payload()
        return message_id in payload.get("processed_message_ids", [])

    def mark_processed(self, message_id: str, uid: int | None) -> None:
        with self._lock:
            payload = self._read_payload()
            processed = payload.setdefault("processed_message_ids", [])
            if message_id and message_id not in processed:
                processed.append(message_id)
                if len(processed) > 1000:
                    payload["processed_message_ids"] = processed[-1000:]
            if uid is not None:
                payload["last_seen_uid"] = max(int(payload.get("last_seen_uid", 0) or 0), uid)
            self._write_payload(payload)

    def update_last_seen_uid(self, uid: int) -> None:
        with self._lock:
            payload = self._read_payload()
            payload["last_seen_uid"] = max(int(payload.get("last_seen_uid", 0) or 0), uid)
            self._write_payload(payload)
