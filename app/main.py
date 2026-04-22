"""Entry point for the AI Legal MVP NiceGUI application."""

from nicegui import ui

from app.config import AI_LEGAL_MODEL, OPENAI_BASE_URL

# Import ui module to register the upload endpoint and chat_page
import app.ui  # noqa: F401

if __name__ in {"__main__", "__mp_main__"}:
    print("AI Legal MVP starting...")
    print(f"Model: {AI_LEGAL_MODEL}")
    print(f"Endpoint: {OPENAI_BASE_URL}")
    ui.run(title="AI Legal Assistant", port=8080)
