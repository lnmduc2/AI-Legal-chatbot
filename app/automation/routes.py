import asyncio

from fastapi.responses import JSONResponse
from nicegui import app

from app.automation.runtime import get_automation_services


@app.get("/api/events")
def api_events() -> dict:
    services = get_automation_services()
    return {
        "summary": services.event_store.summary(),
        "events": [event.to_dict() for event in services.event_store.list_events()],
        "poller_ready": services.poller.is_ready(),
        "source_ready": services.config.source_ready,
    }


@app.post("/api/automation/poll")
async def api_poll_now() -> JSONResponse:
    services = get_automation_services()
    try:
        processed = await asyncio.to_thread(services.poller.poll_once)
        return JSONResponse({"processed": processed})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
