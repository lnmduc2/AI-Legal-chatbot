from nicegui import ui

from app.automation.runtime import get_automation_services

PRIMARY = "#007A33"
PRIMARY_SOFT = "#EAF6EE"
SURFACE = "#FFFFFF"
TEXT = "#183022"
TEXT_MUTED = "#66756B"
BORDER = "#D9E6DD"
ERROR_BG = "#FFF3F1"
ERROR_TEXT = "#9A2B1F"


@ui.page("/events")
def event_log_page() -> None:
    services = get_automation_services()
    filter_state = {"value": "all"}
    refresh_timer: ui.timer | None = None

    ui.add_head_html(
        f"""
        <style>
            body {{
                background: linear-gradient(180deg, #eef7f1 0%, #e4efe8 100%);
                color: {TEXT};
            }}
            .events-shell {{
                width: min(1320px, calc(100vw - 24px));
                margin: 12px auto;
                padding: 18px;
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 22px;
                box-shadow: 0 12px 36px rgba(10, 74, 36, 0.08);
            }}
            .summary-card {{
                min-width: 170px;
                padding: 14px 16px;
                border: 1px solid {BORDER};
                border-radius: 14px;
                background: {PRIMARY_SOFT};
            }}
            .event-row {{
                border: 1px solid {BORDER};
                border-radius: 16px;
                padding: 16px;
                background: #fbfcfb;
                margin-top: 12px;
            }}
            .event-badge {{
                display: inline-flex;
                padding: 3px 10px;
                border-radius: 999px;
                font-size: 0.74rem;
                font-weight: 700;
                background: {PRIMARY_SOFT};
                color: {PRIMARY};
            }}
            .event-error {{
                padding: 10px 12px;
                border-radius: 10px;
                background: {ERROR_BG};
                color: {ERROR_TEXT};
                font-size: 0.84rem;
            }}
        </style>
        """
    )

    summary_labels: dict = {}

    with ui.column().classes("events-shell"):
        status_label = ui.label("")
        with ui.row().classes("w-full items-start"):
            with ui.column().classes("gap-1"):
                ui.label("Automation Event Log").classes("text-2xl font-bold")
                ui.label(
                    "Monitor newly ingested legal updates, ignored emails, and team notifications."
                ).classes("text-sm").style(f"color: {TEXT_MUTED};")
                status_label.classes("text-xs").style(f"color: {TEXT_MUTED};")
            ui.space()
            ui.link("Open advisory chat", "/").classes("text-sm")

        with ui.row().classes("w-full gap-3 items-center"):
            filter_select = ui.select(
                options={
                    "all": "All events",
                    "processed": "Processed",
                    "ignored": "Ignored",
                    "failed": "Failed",
                },
                value="all",
                label="Filter",
            ).props("outlined dense")

            def on_filter_change(_) -> None:
                filter_state["value"] = filter_select.value or "all"
                refresh_view()

            filter_select.on("update:model-value", on_filter_change)
            ui.button("Refresh", on_click=lambda: refresh_view()).props("outline")

        with ui.row().classes("w-full gap-3 wrap"):
            for key, label in [
                ("total", "Total"),
                ("processed", "Processed"),
                ("created", "Created"),
                ("updated", "Updated"),
                ("ignored", "Ignored"),
                ("failed", "Failed"),
            ]:
                with ui.column().classes("summary-card gap-1"):
                    ui.label(label).classes("text-xs font-medium").style(f"color: {TEXT_MUTED};")
                    summary_labels[key] = ui.label("0").classes("text-2xl font-bold")

        list_container = ui.column().classes("w-full")
        ui.label(
            f"UI auto-refresh: every 5s. "
            f"Server inbox poller: every {services.config.poll_interval_seconds}s "
            f"(independent of this page).",
        ).classes("text-xs").style(f"color: {TEXT_MUTED}; margin-top: 6px;")

        def refresh_view() -> None:
            nonlocal refresh_timer
            if list_container.is_deleted or status_label.is_deleted:
                if refresh_timer is not None:
                    refresh_timer.cancel()
                return
            summary = services.event_store.summary()
            for key, label in summary_labels.items():
                label.set_text(str(summary.get(key, 0)))

            readiness = []
            readiness.append("poller ready" if services.poller.is_ready() else "poller not configured")
            readiness.append("source sender ready" if services.config.source_ready else "source sender not configured")
            status_label.set_text(" | ".join(readiness))

            events = services.event_store.list_events()
            if filter_state["value"] != "all":
                events = [event for event in events if event.status == filter_state["value"]]

            list_container.clear()
            with list_container:
                if not events:
                    ui.label("No automation events yet. Send a legal update from the source app, then wait for the poller to process the message.").classes(
                        "text-sm"
                    ).style(f"color: {TEXT_MUTED};")
                    return

                for event in events:
                    with ui.column().classes("event-row w-full gap-2"):
                        with ui.row().classes("w-full items-center"):
                            with ui.column().classes("gap-0"):
                                ui.label(event.subject or "(no subject)").classes("text-md font-bold")
                                ui.label(event.created_at).classes("text-xs").style(f"color: {TEXT_MUTED};")
                            ui.space()
                            ui.label(event.status.upper()).classes("event-badge")
                        ui.label(f"Sender: {event.sender_email or event.sender}").classes("text-sm")
                        ui.label(f"Action: {event.action}").classes("text-sm")
                        ui.label(f"Filename: {event.filename or '-'}").classes("text-sm")
                        ui.label(f"Doc path: {event.doc_path or '-'}").classes("text-sm")
                        ui.label(f"Heuristic: {event.heuristic_reason}").classes("text-sm")
                        ui.label(
                            "Notifications: "
                            f"{event.notification_status}"
                            + (
                                f" -> {', '.join(event.notification_recipients)}"
                                if event.notification_recipients
                                else ""
                            )
                        ).classes("text-sm")
                        if event.error:
                            ui.label(event.error).classes("event-error")

        refresh_timer = ui.timer(5.0, refresh_view, once=False, immediate=True)
        refresh_view()
