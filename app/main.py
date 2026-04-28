"""Entry point for the AI Legal MVP NiceGUI application."""

import logging

from nicegui import background_tasks, ui

import app.automation.event_ui  # noqa: F401
import app.automation.routes  # noqa: F401
import app.ui  # noqa: F401
from app.automation.runtime import get_automation_services
from app.config import AI_LEGAL_MODEL, OPENAI_BASE_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

def bootstrap_automation() -> None:
    services = get_automation_services()
    background_tasks.create_or_defer(
        services.poller.run_forever(),
        name="legal-mail-poller",
    )

if __name__ in {"__main__", "__mp_main__"}:
    bootstrap_automation()
    logger.info("AI Legal MVP starting...")
    logger.info("Model: %s", AI_LEGAL_MODEL)
    logger.info("Endpoint: %s", OPENAI_BASE_URL)
    ui.run(title="AI Legal Assistant", port=8080)
