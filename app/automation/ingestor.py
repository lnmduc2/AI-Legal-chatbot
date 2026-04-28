from pathlib import Path
from uuid import uuid4

from app import ui as chat_ui

from app.automation.config import AutomationConfig
from app.automation.event_store import EventStore
from app.automation.gmail_client import GmailClient
from app.automation.mail_filter import evaluate_legal_update, normalize_email_address
from app.automation.models import (
    EventAction,
    EventStatus,
    LegalDocumentEvent,
    MailAttachment,
    MailMessage,
    utc_now_iso,
)
from app.automation.subscriber_store import SubscriberStore
from app.doc_index import ensure_doc_indexes


class LegalUpdateIngestor:
    def __init__(
        self,
        *,
        config: AutomationConfig,
        event_store: EventStore,
        subscriber_store: SubscriberStore,
        gmail_client: GmailClient,
    ) -> None:
        self.config = config
        self.event_store = event_store
        self.subscriber_store = subscriber_store
        self.gmail_client = gmail_client
        self.config.docs_law_dir.mkdir(parents=True, exist_ok=True)
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

    def ingest_message(self, message: MailMessage) -> LegalDocumentEvent | None:
        sender_email = normalize_email_address(message.sender_email or message.sender)
        if self.config.source_sender_email and sender_email != self.config.source_sender_email:
            return None

        decision = evaluate_legal_update(
            message,
            allowed_sender=self.config.source_sender_email,
            subject_keywords=self.config.subject_keywords,
            body_keywords=self.config.body_keywords,
            attachment_suffixes=self.config.attachment_suffixes,
        )

        if not decision.accepted:
            if "No supported markdown attachment" in decision.reason:
                return None
            event = LegalDocumentEvent(
                event_id=str(uuid4()),
                created_at=utc_now_iso(),
                message_id=message.message_id,
                subject=message.subject,
                sender=message.sender,
                sender_email=message.sender_email,
                filename=decision.attachment_names[0] if decision.attachment_names else None,
                doc_path=None,
                action=EventAction.IGNORED.value,
                status=EventStatus.IGNORED.value,
                heuristic_reason=decision.reason,
                matched_keywords=decision.matched_keywords,
            )
            self.event_store.append_event(event)
            return event

        attachment = self._select_attachment(message.attachments)
        if attachment is None:
            event = LegalDocumentEvent(
                event_id=str(uuid4()),
                created_at=utc_now_iso(),
                message_id=message.message_id,
                subject=message.subject,
                sender=message.sender,
                sender_email=message.sender_email,
                filename=None,
                doc_path=None,
                action=EventAction.FAILED.value,
                status=EventStatus.FAILED.value,
                heuristic_reason="Attachment filter passed but no supported attachment could be selected.",
                matched_keywords=decision.matched_keywords,
                error="No markdown attachment selected",
            )
            self.event_store.append_event(event)
            return event

        target_path = self.config.docs_law_dir / Path(attachment.filename).name
        action = EventAction.UPDATED.value if target_path.exists() else EventAction.CREATED.value

        try:
            text = attachment.payload.decode("utf-8")
            target_path.write_text(text, encoding="utf-8")
            ensure_doc_indexes()
            chat_ui.trigger_sidebar_refresh()

            notification_recipients, notification_status = self._notify_legal_team(
                message, attachment, action
            )
            event = LegalDocumentEvent(
                event_id=str(uuid4()),
                created_at=utc_now_iso(),
                message_id=message.message_id,
                subject=message.subject,
                sender=message.sender,
                sender_email=message.sender_email,
                filename=attachment.filename,
                doc_path=str(target_path.relative_to(self.config.docs_law_dir.parent.parent)),
                action=action,
                status=EventStatus.PROCESSED.value,
                heuristic_reason=decision.reason,
                matched_keywords=decision.matched_keywords,
                notification_recipients=notification_recipients,
                notification_status=notification_status,
            )
            self.event_store.append_event(event)
            return event
        except Exception as exc:
            event = LegalDocumentEvent(
                event_id=str(uuid4()),
                created_at=utc_now_iso(),
                message_id=message.message_id,
                subject=message.subject,
                sender=message.sender,
                sender_email=message.sender_email,
                filename=attachment.filename,
                doc_path=str(target_path.relative_to(self.config.docs_law_dir.parent.parent)),
                action=EventAction.FAILED.value,
                status=EventStatus.FAILED.value,
                heuristic_reason=decision.reason,
                matched_keywords=decision.matched_keywords,
                error=str(exc),
            )
            self.event_store.append_event(event)
            return event

    def _select_attachment(self, attachments: list[MailAttachment]) -> MailAttachment | None:
        for attachment in attachments:
            if any(
                attachment.filename.lower().endswith(suffix.lower())
                for suffix in self.config.attachment_suffixes
            ):
                return attachment
        return None

    def _notify_legal_team(
        self, message: MailMessage, attachment: MailAttachment, action: str
    ) -> tuple[list[str], str]:
        subscribers = self.subscriber_store.list_subscribers()
        if not subscribers:
            return [], "skipped"
        if not self.config.admin_account.is_configured:
            return subscribers, "skipped"

        body = "\n".join(
            [
                "AI Legal vừa ingest một cập nhật văn bản pháp luật mới.",
                "",
                f"Trạng thái: {action}",
                f"Nguồn gửi: {message.sender_email or message.sender}",
                f"Tiêu đề email: {message.subject}",
                f"Tệp văn bản: {attachment.filename}",
                "",
                "Bạn nhận được email này vì đã subscribe kênh event cập nhật văn bản pháp luật.",
            ]
        )
        try:
            self.gmail_client.send_email(
                account=self.config.admin_account,
                recipients=subscribers,
                subject=f"[AI Legal] Văn bản pháp luật {action}: {attachment.filename}",
                body_text=body,
            )
            return subscribers, "sent"
        except Exception as exc:
            return subscribers, f"failed: {exc}"
