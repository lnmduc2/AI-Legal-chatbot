"""Entry point for the AI Legal MVP NiceGUI application."""

from nicegui import background_tasks, ui

import app.automation.event_ui  # noqa: F401
import app.automation.routes  # noqa: F401
import app.ui  # noqa: F401
from app.automation.runtime import get_automation_services
from app.config import AI_LEGAL_MODEL, OPENAI_BASE_URL

def bootstrap_automation() -> None:
    services = get_automation_services()
    background_tasks.create_or_defer(
        services.poller.run_forever(),
        name="legal-mail-poller",
    )

if __name__ in {"__main__", "__mp_main__"}:
    bootstrap_automation()
    print("AI Legal MVP starting...")
    print(f"Model: {AI_LEGAL_MODEL}")
    print(f"Endpoint: {OPENAI_BASE_URL}")
    ui.run(title="AI Legal Assistant", port=8080)
