import json
import threading
from email.utils import parseaddr
from pathlib import Path


class SubscriberStore:
    def __init__(self, path: Path, initial_subscribers: list[str] | None = None) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_payload({"subscribers": self._normalize_many(initial_subscribers or [])})

    def _read_payload(self) -> dict:
        if not self.path.exists():
            return {"subscribers": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"subscribers": []}

    def _write_payload(self, payload: dict) -> None:
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _normalize_email(self, value: str) -> str:
        _, address = parseaddr(value or "")
        return address.strip().lower()

    def _normalize_many(self, values: list[str]) -> list[str]:
        unique: list[str] = []
        for value in values:
            email = self._normalize_email(value)
            if email and "@" in email and email not in unique:
                unique.append(email)
        return unique

    def list_subscribers(self) -> list[str]:
        payload = self._read_payload()
        return self._normalize_many(payload.get("subscribers", []))

    def subscribe(self, email: str) -> tuple[bool, str]:
        normalized = self._normalize_email(email)
        if not normalized or "@" not in normalized:
            return False, "Email không hợp lệ."

        with self._lock:
            payload = self._read_payload()
            subscribers = self._normalize_many(payload.get("subscribers", []))
            if normalized in subscribers:
                return False, "Email này đã subscribe kênh event."
            subscribers.append(normalized)
            payload["subscribers"] = subscribers
            self._write_payload(payload)
        return True, "Đã subscribe kênh event pháp luật."

    def unsubscribe(self, email: str) -> tuple[bool, str]:
        normalized = self._normalize_email(email)
        if not normalized:
            return False, "Email không hợp lệ."

        with self._lock:
            payload = self._read_payload()
            subscribers = self._normalize_many(payload.get("subscribers", []))
            if normalized not in subscribers:
                return False, "Email này chưa nằm trong danh sách subscribe."
            payload["subscribers"] = [item for item in subscribers if item != normalized]
            self._write_payload(payload)
        return True, "Đã unsubscribe khỏi kênh event pháp luật."
