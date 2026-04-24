import email
import imaplib
import smtplib
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

from app.automation.config import AutomationConfig, MailAccount
from app.automation.models import MailAttachment, MailMessage


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    return str(make_header(decode_header(value)))


class GmailClient:
    def __init__(self, config: AutomationConfig) -> None:
        self.config = config

    def send_email(
        self,
        *,
        account: MailAccount,
        recipients: list[str],
        subject: str,
        body_text: str,
        attachments: list[MailAttachment] | None = None,
    ) -> None:
        if not account.is_configured:
            raise RuntimeError("Mail account is not configured for SMTP sending.")
        if not recipients:
            raise ValueError("At least one recipient is required to send an email.")

        message = EmailMessage()
        message["From"] = account.email
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid()
        message.set_content(body_text)

        for attachment in attachments or []:
            maintype, _, subtype = (attachment.content_type or "text/markdown").partition("/")
            message.add_attachment(
                attachment.payload,
                maintype=maintype or "text",
                subtype=subtype or "plain",
                filename=attachment.filename,
            )

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(account.email, account.password)
            smtp.send_message(message)

    def fetch_messages_since_uid(
        self,
        *,
        account: MailAccount,
        last_seen_uid: int,
        limit: int,
    ) -> list[MailMessage]:
        if not account.is_configured:
            return []

        with imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port) as mail:
            mail.login(account.email, account.password)
            mail.select("INBOX")
            status, data = mail.uid("search", None, "ALL")
            if status != "OK":
                raise RuntimeError("Failed to search IMAP inbox.")

            all_uids = [int(item) for item in data[0].split() if item]
            candidate_uids = [uid for uid in all_uids if uid > last_seen_uid][:limit]
            messages: list[MailMessage] = []

            for uid in candidate_uids:
                status, payload = mail.uid("fetch", str(uid), "(RFC822)")
                if status != "OK" or not payload:
                    continue
                raw_message = self._extract_rfc822_bytes(payload)
                if not raw_message:
                    continue
                messages.append(self._parse_message(raw_message, uid))

            return messages

    def mark_as_seen(self, *, account: MailAccount, uid: int) -> None:
        if not account.is_configured:
            return
        with imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port) as mail:
            mail.login(account.email, account.password)
            mail.select("INBOX")
            mail.uid("store", str(uid), "+FLAGS", "(\\Seen)")

    def _extract_rfc822_bytes(self, payload: list[tuple | bytes]) -> bytes:
        for item in payload:
            if isinstance(item, tuple) and len(item) > 1 and isinstance(item[1], bytes):
                return item[1]
        return b""

    def _parse_message(self, raw_message: bytes, uid: int) -> MailMessage:
        message = email.message_from_bytes(raw_message)
        subject = _decode_header_value(message.get("Subject"))
        sender = message.get("From", "")
        _, sender_email = parseaddr(sender)
        message_id = (message.get("Message-ID") or "").strip() or f"imap-uid-{uid}"
        received_at = message.get("Date", "")

        attachments: list[MailAttachment] = []
        body_parts: list[str] = []

        if message.is_multipart():
            for part in message.walk():
                disposition = (part.get_content_disposition() or "").lower()
                filename = part.get_filename()
                content_type = part.get_content_type()
                payload = part.get_payload(decode=True) or b""

                if disposition == "attachment" and filename:
                    attachments.append(
                        MailAttachment(
                            filename=_decode_header_value(filename),
                            content_type=content_type,
                            payload=payload,
                        )
                    )
                    continue

                if content_type == "text/plain" and payload:
                    charset = part.get_content_charset() or "utf-8"
                    body_parts.append(payload.decode(charset, errors="replace"))
        else:
            payload = message.get_payload(decode=True) or b""
            charset = message.get_content_charset() or "utf-8"
            if payload:
                body_parts.append(payload.decode(charset, errors="replace"))

        return MailMessage(
            message_id=message_id,
            subject=subject,
            sender=sender,
            sender_email=sender_email,
            body_text="\n".join(part.strip() for part in body_parts if part.strip()),
            received_at=received_at,
            attachments=attachments,
            imap_uid=uid,
        )
