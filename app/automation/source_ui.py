from nicegui import events, ui

from app.automation.models import MailAttachment
from app.automation.runtime import get_automation_services

PRIMARY = "#007A33"
PRIMARY_DARK = "#0A4A24"
PRIMARY_SOFT = "#EAF6EE"
BORDER = "#D9E6DD"
TEXT = "#183022"
TEXT_MUTED = "#66756B"


@ui.page("/")
def source_portal_page() -> None:
    services = get_automation_services()
    uploaded: dict[str, str | bytes | None] = {"name": None, "content": None}

    ui.add_head_html(
        f"""
        <style>
            body {{
                background: linear-gradient(180deg, #eef7f1 0%, #e4efe8 100%);
                color: {TEXT};
            }}
            .source-shell {{
                width: min(920px, calc(100vw - 24px));
                margin: 24px auto;
                padding: 22px;
                background: white;
                border: 1px solid {BORDER};
                border-radius: 22px;
                box-shadow: 0 12px 36px rgba(10, 74, 36, 0.08);
            }}
        </style>
        """
    )

    async def handle_upload(event: events.UploadEventArguments) -> None:
        uploaded["name"] = event.file.name
        uploaded["content"] = await event.file.read()
        selected_file_label.set_text(f"Selected file: {event.file.name}")

    async def send_update() -> None:
        filename = str(uploaded["name"] or "").strip()
        content = uploaded["content"]
        if not filename or not isinstance(content, bytes):
            ui.notify("Upload a markdown file before sending.", color="negative")
            return
        if not filename.lower().endswith(".md"):
            ui.notify("The demo source only accepts .md attachments.", color="negative")
            return
        if not services.config.source_ready:
            ui.notify("Source Gmail account is not configured.", color="negative")
            return
        if not services.config.admin_sender_email:
            ui.notify("Admin inbox email is not configured.", color="negative")
            return

        title = title_input.value.strip() or filename
        effective_date = effective_date_input.value.strip() or "Not specified"
        note = note_input.value.strip() or "No extra note provided."
        subject = f"[{services.config.source_label}] Legal update - {title}"
        body = "\n".join(
            [
                f"Source: {services.config.source_label}",
                f"Document title: {title}",
                f"Effective date: {effective_date}",
                "",
                "Summary note:",
                note,
                "",
                "Attachment: markdown legal document for ingestion by AI Legal.",
            ]
        )

        try:
            services.gmail_client.send_email(
                account=services.config.source_account,
                recipients=[services.config.admin_sender_email],
                subject=subject,
                body_text=body,
                attachments=[
                    MailAttachment(
                        filename=filename,
                        content_type="text/markdown",
                        payload=content,
                    )
                ],
            )
            ui.notify("Legal update email sent to the admin inbox.", color="positive")
        except Exception as exc:
            ui.notify(f"Failed to send email: {exc}", color="negative")

    with ui.column().classes("source-shell"):
        ui.label("Fake Legal Source Portal").classes("text-2xl font-bold")
        ui.label(
            "Use this page to simulate a legal source publishing a new markdown document into the AI Legal automation flow."
        ).classes("text-sm").style(f"color: {TEXT_MUTED};")

        title_input = ui.input("Document title").props("outlined")
        effective_date_input = ui.input("Effective date").props("outlined")
        note_input = ui.textarea("Change note").props("outlined autogrow")
        selected_file_label = ui.label("No markdown file selected yet.").classes("text-sm").style(
            f"color: {TEXT_MUTED};"
        )

        with ui.row().classes("w-full gap-4 wrap"):
            title_input.classes("col")
            effective_date_input.classes("col")

        note_input.classes("w-full")
        ui.upload(
            label="Upload markdown file",
            auto_upload=True,
            on_upload=handle_upload,
            max_files=1,
        ).props("accept=.md bordered")

        with ui.row().classes("w-full items-center"):
            ui.label(
                f"Source sender: {services.config.source_sender_email or 'not configured'}"
            ).classes("text-sm").style(f"color: {TEXT_MUTED};")
            ui.space()
            ui.button("Send legal update", on_click=send_update).props("unelevated").style(
                f"background: {PRIMARY_DARK}; color: white;"
            )
