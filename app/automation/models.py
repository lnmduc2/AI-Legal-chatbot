from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventStatus(StrEnum):
    PROCESSED = "processed"
    IGNORED = "ignored"
    FAILED = "failed"


class EventAction(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    IGNORED = "ignored"
    FAILED = "failed"


@dataclass
class MailAttachment:
    filename: str
    content_type: str
    payload: bytes


@dataclass
class MailMessage:
    message_id: str
    subject: str
    sender: str
    sender_email: str
    body_text: str
    received_at: str
    attachments: list[MailAttachment] = field(default_factory=list)
    imap_uid: int | None = None


@dataclass
class FilterDecision:
    accepted: bool
    reason: str
    matched_keywords: list[str] = field(default_factory=list)
    attachment_names: list[str] = field(default_factory=list)


@dataclass
class LegalDocumentEvent:
    event_id: str
    created_at: str
    message_id: str
    subject: str
    sender: str
    sender_email: str
    filename: str | None
    doc_path: str | None
    action: str
    status: str
    heuristic_reason: str
    matched_keywords: list[str] = field(default_factory=list)
    notification_recipients: list[str] = field(default_factory=list)
    notification_status: str = "skipped"
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LegalDocumentEvent":
        return cls(**data)
