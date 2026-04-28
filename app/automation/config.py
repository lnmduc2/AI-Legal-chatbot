import os
from dataclasses import dataclass
from pathlib import Path

from app.config import DOCS_DIR, PROJECT_ROOT


def _parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _parse_bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class MailAccount:
    email: str
    password: str

    @property
    def is_configured(self) -> bool:
        return bool(self.email and self.password)


@dataclass(frozen=True)
class AutomationConfig:
    enabled: bool
    source_account: MailAccount
    admin_account: MailAccount
    team_recipients: list[str]
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int
    poll_interval_seconds: int
    max_messages_per_poll: int
    docs_law_dir: Path
    data_dir: Path
    event_log_path: Path
    mail_state_path: Path
    subscriber_path: Path
    subject_keywords: list[str]
    body_keywords: list[str]
    attachment_suffixes: list[str]
    source_label: str

    @property
    def source_sender_email(self) -> str:
        return self.source_account.email.strip().lower()

    @property
    def admin_sender_email(self) -> str:
        return self.admin_account.email.strip().lower()

    @property
    def poller_ready(self) -> bool:
        return self.enabled and self.admin_account.is_configured

    @property
    def source_ready(self) -> bool:
        return self.enabled and self.source_account.is_configured


def load_automation_config() -> AutomationConfig:
    data_dir = PROJECT_ROOT / os.getenv("LEGAL_DATA_DIR", "data")
    docs_law_dir = DOCS_DIR / "law"

    source_email = os.getenv("LEGAL_MAIL_SOURCE_EMAIL", "").strip()
    source_password = os.getenv("LEGAL_MAIL_SOURCE_APP_PASSWORD", "").strip()
    admin_email = os.getenv("LEGAL_MAIL_ADMIN_EMAIL", "").strip()
    admin_password = os.getenv("LEGAL_MAIL_ADMIN_APP_PASSWORD", "").strip()

    return AutomationConfig(
        enabled=_parse_bool(os.getenv("LEGAL_AUTOMATION_ENABLED"), True),
        source_account=MailAccount(source_email, source_password),
        admin_account=MailAccount(admin_email, admin_password),
        team_recipients=_parse_csv(os.getenv("LEGAL_MAIL_TEAM_RECIPIENTS", "")),
        smtp_host=os.getenv("LEGAL_MAIL_SMTP_HOST", "smtp.gmail.com").strip(),
        smtp_port=int(os.getenv("LEGAL_MAIL_SMTP_PORT", "587")),
        imap_host=os.getenv("LEGAL_MAIL_IMAP_HOST", "imap.gmail.com").strip(),
        imap_port=int(os.getenv("LEGAL_MAIL_IMAP_PORT", "993")),
        poll_interval_seconds=max(5, int(os.getenv("LEGAL_MAIL_POLL_INTERVAL_SECONDS", "15"))),
        max_messages_per_poll=max(1, int(os.getenv("LEGAL_MAIL_MAX_MESSAGES_PER_POLL", "20"))),
        docs_law_dir=docs_law_dir,
        data_dir=data_dir,
        event_log_path=data_dir / "event_log.json",
        mail_state_path=data_dir / "mail_state.json",
        subscriber_path=data_dir / "legal_team_subscribers.json",
        subject_keywords=_parse_csv(
            os.getenv(
                "LEGAL_MAIL_SUBJECT_KEYWORDS",
                "legal update,law,data privacy,privacy,data protection,luat,van ban phap luat",
            )
        ),
        body_keywords=_parse_csv(
            os.getenv(
                "LEGAL_MAIL_BODY_KEYWORDS",
                "privacy,data protection,personal data,du lieu ca nhan,bao ve du lieu",
            )
        ),
        attachment_suffixes=_parse_csv(os.getenv("LEGAL_MAIL_ATTACHMENT_SUFFIXES", ".md")),
        source_label=os.getenv("LEGAL_SOURCE_LABEL", "thuvienphapluat.vn").strip() or "thuvienphapluat.vn",
    )
