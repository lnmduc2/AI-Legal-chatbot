from app.automation.config import AutomationConfig, MailAccount
from app.automation.event_store import EventStore
from app.automation.ingestor import LegalUpdateIngestor
from app.automation.models import MailAttachment, MailMessage


class FakeGmailClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict] = []

    def send_email(self, **kwargs) -> None:
        self.sent_messages.append(kwargs)


def build_config(tmp_path) -> AutomationConfig:
    data_dir = tmp_path / "data"
    docs_law_dir = tmp_path / "docs" / "law"
    return AutomationConfig(
        enabled=True,
        source_account=MailAccount("source@example.com", "source-pass"),
        admin_account=MailAccount("admin@example.com", "admin-pass"),
        team_recipients=["legal@example.com"],
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        imap_host="imap.gmail.com",
        imap_port=993,
        poll_interval_seconds=15,
        max_messages_per_poll=20,
        docs_law_dir=docs_law_dir,
        data_dir=data_dir,
        event_log_path=data_dir / "event_log.json",
        mail_state_path=data_dir / "mail_state.json",
        subject_keywords=["legal update", "privacy"],
        body_keywords=["personal data"],
        attachment_suffixes=[".md"],
        source_label="thuvienphapluat.vn",
    )


def build_message() -> MailMessage:
    return MailMessage(
        message_id="<msg-1>",
        subject="Legal update - Data privacy law",
        sender="Source <source@example.com>",
        sender_email="source@example.com",
        body_text="Personal data obligations changed.",
        received_at="Fri, 24 Apr 2026 10:00:00 +0000",
        attachments=[
            MailAttachment(
                filename="privacy-law.md",
                content_type="text/markdown",
                payload="# Privacy Law\n\nUpdated content.".encode("utf-8"),
            )
        ],
        imap_uid=10,
    )


def test_ingestor_writes_document_and_event(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.automation.ingestor.ensure_doc_indexes", lambda: None)

    config = build_config(tmp_path)
    fake_gmail_client = FakeGmailClient()
    store = EventStore(config.event_log_path)
    ingestor = LegalUpdateIngestor(
        config=config,
        event_store=store,
        gmail_client=fake_gmail_client,
    )

    event = ingestor.ingest_message(build_message())

    saved_file = config.docs_law_dir / "privacy-law.md"
    assert saved_file.exists()
    assert "Updated content." in saved_file.read_text(encoding="utf-8")
    assert event.status == "processed"
    assert event.action == "created"
    assert event.doc_path == "docs/law/privacy-law.md"
    assert fake_gmail_client.sent_messages[0]["recipients"] == ["legal@example.com"]


def test_ingestor_ignores_non_matching_mail(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.automation.ingestor.ensure_doc_indexes", lambda: None)

    config = build_config(tmp_path)
    fake_gmail_client = FakeGmailClient()
    store = EventStore(config.event_log_path)
    ingestor = LegalUpdateIngestor(
        config=config,
        event_store=store,
        gmail_client=fake_gmail_client,
    )

    message = build_message()
    message.sender_email = "other@example.com"
    event = ingestor.ingest_message(message)

    assert event.status == "ignored"
    assert fake_gmail_client.sent_messages == []
    assert store.summary()["ignored"] == 1
