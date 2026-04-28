from email.utils import parseaddr
from pathlib import Path

from app.automation.models import FilterDecision, MailMessage


def normalize_email_address(value: str) -> str:
    _, address = parseaddr(value or "")
    return address.strip().lower()


def _normalize_keywords(keywords: list[str]) -> list[str]:
    return [keyword.strip().lower() for keyword in keywords if keyword.strip()]


def evaluate_legal_update(
    message: MailMessage,
    *,
    allowed_sender: str,
    subject_keywords: list[str],
    body_keywords: list[str],
    attachment_suffixes: list[str],
) -> FilterDecision:
    attachment_names = [attachment.filename for attachment in message.attachments]
    sender_email = normalize_email_address(message.sender_email or message.sender)
    normalized_allowed_sender = normalize_email_address(allowed_sender)

    if normalized_allowed_sender and sender_email != normalized_allowed_sender:
        return FilterDecision(
            accepted=False,
            reason=f"Sender `{sender_email}` does not match configured source sender.",
            attachment_names=attachment_names,
        )

    suffixes = [suffix.lower() for suffix in attachment_suffixes if suffix.strip()]
    valid_attachments = [
        attachment.filename
        for attachment in message.attachments
        if any(attachment.filename.lower().endswith(suffix) for suffix in suffixes)
    ]
    if not valid_attachments:
        return FilterDecision(
            accepted=False,
            reason="No supported markdown attachment was found in the email.",
            attachment_names=attachment_names,
        )

    normalized_subject = (message.subject or "").lower()
    normalized_body = (message.body_text or "").lower()
    normalized_filenames = " ".join(Path(name).stem.lower() for name in valid_attachments)
    matched_keywords: list[str] = []

    for keyword in _normalize_keywords(subject_keywords):
        if keyword in normalized_subject:
            matched_keywords.append(keyword)

    for keyword in _normalize_keywords(body_keywords):
        if keyword in normalized_body:
            matched_keywords.append(keyword)

    for keyword in _normalize_keywords(subject_keywords + body_keywords):
        if keyword in normalized_filenames:
            matched_keywords.append(keyword)

    if not matched_keywords:
        return FilterDecision(
            accepted=False,
            reason="Email did not match any configured subject/body/filename legal-update keywords.",
            attachment_names=valid_attachments,
        )

    return FilterDecision(
        accepted=True,
        reason="Heuristics matched sender, keywords, and attachment requirements.",
        matched_keywords=sorted(set(matched_keywords)),
        attachment_names=valid_attachments,
    )
