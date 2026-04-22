"""Entry point for the AI Legal MVP NiceGUI application."""

from nicegui import ui

from app.config import AI_LEGAL_MODEL, OPENAI_BASE_URL
from app.ui import chat_page
from app.workspace import get_workspace_summary

if __name__ in {"__main__", "__mp_main__"}:
    print("AI Legal MVP starting...")
    print(f"Model: {AI_LEGAL_MODEL}")
    print(f"Endpoint: {OPENAI_BASE_URL}")
    print(get_workspace_summary())
    chat_page()
    ui.run(title="AI Legal Assistant", port=8080)
