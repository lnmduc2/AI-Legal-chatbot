"""Entry point for the fake legal source NiceGUI application."""

import os

from nicegui import ui

import app.automation.source_ui  # noqa: F401
from app.automation.runtime import get_automation_services


if __name__ in {"__main__", "__mp_main__"}:
    services = get_automation_services()
    print("AI Legal fake source portal starting...")
    print(f"Source sender: {services.config.source_sender_email or 'not configured'}")
    print(f"Admin inbox: {services.config.admin_sender_email or 'not configured'}")
    ui.run(
        title="AI Legal Fake Source",
        port=int(os.getenv("SOURCE_APP_PORT", "8081")),
    )
