from app.automation.mail_filter import evaluate_legal_update
from app.automation.models import MailAttachment, MailMessage


def build_message(**overrides) -> MailMessage:
    payload = {
        "message_id": "<test-1>",
        "subject": "Legal update - Data privacy law",
        "sender": "Source <source@example.com>",
        "sender_email": "source@example.com",
        "body_text": "This update covers personal data protection obligations.",
        "received_at": "Fri, 24 Apr 2026 10:00:00 +0000",
        "attachments": [
            MailAttachment(
                filename="privacy-law.md",
                content_type="text/markdown",
                payload=b"# Privacy Law",
            )
        ],
        "imap_uid": 123,
    }
    payload.update(overrides)
    return MailMessage(**payload)


def test_mail_filter_accepts_expected_legal_update() -> None:
    decision = evaluate_legal_update(
        build_message(),
        allowed_sender="source@example.com",
        subject_keywords=["legal update", "privacy"],
        body_keywords=["personal data"],
        attachment_suffixes=[".md"],
    )

    assert decision.accepted is True
    assert "privacy" in decision.matched_keywords
    assert decision.attachment_names == ["privacy-law.md"]


def test_mail_filter_rejects_wrong_sender() -> None:
    decision = evaluate_legal_update(
        build_message(sender_email="other@example.com"),
        allowed_sender="source@example.com",
        subject_keywords=["legal update"],
        body_keywords=["personal data"],
        attachment_suffixes=[".md"],
    )

    assert decision.accepted is False
    assert "does not match configured source sender" in decision.reason


def test_mail_filter_rejects_missing_markdown_attachment() -> None:
    decision = evaluate_legal_update(
        build_message(
            attachments=[
                MailAttachment(
                    filename="privacy-law.pdf",
                    content_type="application/pdf",
                    payload=b"%PDF",
                )
            ]
        ),
        allowed_sender="source@example.com",
        subject_keywords=["legal update"],
        body_keywords=["personal data"],
        attachment_suffixes=[".md"],
    )

    assert decision.accepted is False
    assert "No supported markdown attachment" in decision.reason
