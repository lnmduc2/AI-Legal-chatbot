import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from nicegui import ui

from app.automation.runtime import get_automation_services

PRIMARY = "#0B7A3B"
PRIMARY_DARK = "#064B2A"
PRIMARY_SOFT = "#EAF7EF"
ACCENT = "#F58220"
ACCENT_SOFT = "#FFF3E8"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F8FBF9"
TEXT = "#18251D"
TEXT_MUTED = "#66756B"
BORDER = "#DDEAE2"
ERROR_BG = "#FFF3F1"
ERROR_TEXT = "#9A2B1F"
WARNING = "#B95C00"


def _status_label(status: str) -> str:
    labels = {
        "processed": "Đã xử lý",
        "ignored": "Bỏ qua",
        "failed": "Lỗi",
    }
    return labels.get(status, status.title())


def _action_label(action: str) -> str:
    labels = {
        "created": "Tạo mới",
        "updated": "Cập nhật",
        "ignored": "Bỏ qua",
        "failed": "Thất bại",
    }
    return labels.get(action, action.title())


def _format_vietnam_time(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        local_time = parsed.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
        return local_time.strftime("%H:%M, %d/%m/%Y")
    except ValueError:
        return value


def _source_events(events: list, source_email: str) -> list:
    normalized_source = source_email.strip().lower()
    if not normalized_source:
        return events
    return [event for event in events if (event.sender_email or "").strip().lower() == normalized_source]


def _event_summary(events: list) -> dict[str, int]:
    counts = {
        "total": len(events),
        "processed": 0,
        "ignored": 0,
        "failed": 0,
        "created": 0,
        "updated": 0,
    }
    for event in events:
        counts[event.status] = counts.get(event.status, 0) + 1
        if event.action in {"created", "updated"}:
            counts[event.action] = counts.get(event.action, 0) + 1
    return counts


@ui.page("/events")
def event_log_page() -> None:
    services = get_automation_services()
    filter_state = {"value": "all"}
    refresh_timer: ui.timer | None = None
    last_refresh_label: ui.label | None = None

    ui.add_head_html(
        f"""
        <style>
            body {{
                background:
                    radial-gradient(circle at 12% 8%, rgba(11,122,59,0.10), transparent 28%),
                    radial-gradient(circle at 88% 0%, rgba(245,130,32,0.16), transparent 24%),
                    linear-gradient(180deg, #f3faf5 0%, #edf5f0 100%);
                color: {TEXT};
                font-size: 15px;
            }}
            .events-page {{
                width: 100%;
                min-height: 100vh;
                padding: 16px;
            }}
            .events-shell {{
                width: min(1320px, 100%);
                margin: 0 auto;
                gap: 14px;
            }}
            .hero-card {{
                padding: 22px;
                border-radius: 22px;
                background: linear-gradient(135deg, {PRIMARY_DARK}, {PRIMARY});
                color: white;
                box-shadow: 0 18px 40px rgba(6, 75, 42, 0.18);
                overflow: hidden;
                position: relative;
            }}
            .hero-card::after {{
                content: "";
                position: absolute;
                width: 260px;
                height: 260px;
                right: -90px;
                top: -120px;
                border-radius: 999px;
                background: rgba(255,255,255,0.12);
            }}
            .hero-icon {{
                width: 64px;
                height: 64px;
                border-radius: 20px;
                background: rgba(255,255,255,0.16);
                border: 1px solid rgba(255,255,255,0.18);
            }}
            .hero-icon .q-icon {{
                font-size: 2.2rem;
            }}
            .hero-kicker {{
                font-size: 0.78rem;
                font-weight: 900;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: rgba(255,255,255,0.76);
            }}
            .hero-title {{
                font-size: clamp(1.7rem, 3vw, 2.55rem);
                font-weight: 900;
                line-height: 1.08;
                letter-spacing: -0.04em;
            }}
            .hero-subtitle {{
                max-width: 760px;
                color: rgba(255,255,255,0.84);
                line-height: 1.55;
                font-size: 1rem;
            }}
            .hero-status {{
                min-width: 260px;
                padding: 14px;
                border-radius: 18px;
                background: rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.18);
                z-index: 1;
            }}
            .status-dot {{
                width: 9px;
                height: 9px;
                border-radius: 999px;
                background: #7CFFB2;
                box-shadow: 0 0 0 4px rgba(124,255,178,0.14);
            }}
            .main-grid {{
                display: grid;
                grid-template-columns: minmax(0, 1fr) 360px;
                gap: 14px;
                align-items: start;
            }}
            .panel {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 20px;
                box-shadow: 0 14px 34px rgba(6, 75, 42, 0.08);
            }}
            .panel-pad {{
                padding: 18px;
            }}
            .panel-title {{
                color: {TEXT};
                font-size: 1.14rem;
                font-weight: 900;
                line-height: 1.25;
            }}
            .panel-subtitle {{
                color: {TEXT_MUTED};
                font-size: 0.92rem;
                line-height: 1.45;
            }}
            .summary-card {{
                flex: 1 1 135px;
                min-width: 130px;
                padding: 14px;
                border-radius: 16px;
                background: {SURFACE_ALT};
                border: 1px solid {BORDER};
            }}
            .summary-label {{
                color: {TEXT_MUTED};
                font-size: 0.76rem;
                font-weight: 900;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }}
            .summary-value {{
                color: {PRIMARY_DARK};
                font-size: 1.75rem;
                font-weight: 900;
                line-height: 1;
            }}
            .toolbar {{
                gap: 10px;
                align-items: center;
                flex-wrap: wrap;
            }}
            .event-list {{
                gap: 8px;
            }}
            .event-row {{
                padding: 12px 14px;
                border-radius: 14px;
                border: 1px solid {BORDER};
                background: #ffffff;
                box-shadow: 0 6px 16px rgba(6, 75, 42, 0.05);
            }}
            .mail-header {{
                gap: 10px;
                align-items: flex-start;
            }}
            .mail-body {{
                margin-left: 42px;
                padding-top: 6px;
            }}
            .event-icon {{
                width: 32px;
                height: 32px;
                border-radius: 999px;
                background: {PRIMARY_SOFT};
                color: {PRIMARY};
                flex: 0 0 32px;
            }}
            .event-icon.failed {{
                background: {ERROR_BG};
                color: {ERROR_TEXT};
            }}
            .event-icon.ignored {{
                background: #F3F5F4;
                color: {TEXT_MUTED};
            }}
            .event-title {{
                color: {TEXT};
                font-size: 1rem;
                font-weight: 900;
                line-height: 1.28;
            }}
            .event-sender {{
                color: {TEXT_MUTED};
                font-size: 0.9rem;
                font-weight: 500;
                overflow-wrap: anywhere;
            }}
            .event-time {{
                color: {TEXT_MUTED};
                font-size: 0.84rem;
                white-space: nowrap;
            }}
            .event-meta {{
                color: {TEXT_MUTED};
                font-size: 0.9rem;
                line-height: 1.45;
            }}
            .mail-details {{
                display: flex;
                align-items: center;
                gap: 12px;
                flex-wrap: wrap;
                color: {TEXT_MUTED};
                font-size: 0.9rem;
                line-height: 1.45;
            }}
            .detail-label {{
                color: {TEXT_MUTED};
                font-weight: 700;
            }}
            .detail-value {{
                color: {TEXT};
                font-weight: 700;
                overflow-wrap: anywhere;
            }}
            .detail-separator {{
                color: #c2d2c9;
            }}
            .event-badge {{
                display: inline-flex;
                width: fit-content;
                padding: 4px 8px;
                border-radius: 999px;
                font-size: 0.7rem;
                font-weight: 900;
                background: {PRIMARY_SOFT};
                color: {PRIMARY};
            }}
            .event-badge.failed {{
                background: {ERROR_BG};
                color: {ERROR_TEXT};
            }}
            .event-badge.ignored {{
                background: #F3F5F4;
                color: {TEXT_MUTED};
            }}
            .event-error {{
                padding: 10px 12px;
                border-radius: 12px;
                background: {ERROR_BG};
                color: {ERROR_TEXT};
                font-size: 0.95rem;
                line-height: 1.5;
            }}
            .subscriber-card {{
                padding: 0;
                overflow: hidden;
                gap: 0;
            }}
            .subscriber-hero {{
                padding: 16px;
                background:
                    radial-gradient(circle at 86% 20%, rgba(255,255,255,0.18), transparent 30%),
                    linear-gradient(135deg, {PRIMARY_DARK}, {PRIMARY});
                color: white;
            }}
            .subscriber-hero-icon {{
                width: 42px;
                height: 42px;
                border-radius: 14px;
                background: rgba(255,255,255,0.14);
                border: 1px solid rgba(255,255,255,0.18);
                flex: 0 0 42px;
            }}
            .subscriber-hero-title {{
                font-size: 1.08rem;
                font-weight: 900;
                line-height: 1.2;
            }}
            .subscriber-hero-subtitle {{
                color: rgba(255,255,255,0.78);
                font-size: 0.9rem;
                line-height: 1.45;
            }}
            .subscriber-body {{
                padding: 14px 16px 16px;
                gap: 12px;
            }}
            .subscriber-count-card {{
                padding: 11px 12px;
                border-radius: 14px;
                background: {PRIMARY_SOFT};
                border: 1px solid #cfe8d8;
                align-items: center;
            }}
            .subscriber-count-label {{
                color: {PRIMARY_DARK};
                font-size: 0.74rem;
                font-weight: 900;
                letter-spacing: 0.07em;
                text-transform: uppercase;
            }}
            .subscriber-count-number {{
                color: {PRIMARY_DARK};
                font-size: 1.65rem;
                font-weight: 900;
                line-height: 1;
            }}
            .subscribe-form {{
                padding: 5px;
                border: 1px solid {BORDER};
                border-radius: 14px;
                background: #fff;
                gap: 6px;
            }}
            .subscribe-form .q-field__control {{
                border: 0;
                min-height: 42px;
                box-shadow: none;
            }}
            .subscriber-list {{
                gap: 8px;
                max-height: 250px;
                overflow-y: auto;
                padding-right: 2px;
            }}
            .subscriber-row {{
                padding: 10px 12px;
                border: 1px solid {BORDER};
                border-radius: 14px;
                background: linear-gradient(180deg, #ffffff, {SURFACE_ALT});
                gap: 9px;
                align-items: center;
            }}
            .subscriber-avatar {{
                width: 32px;
                height: 32px;
                border-radius: 999px;
                background: {PRIMARY_SOFT};
                color: {PRIMARY};
                flex: 0 0 32px;
            }}
            .subscriber-email {{
                color: {TEXT};
                font-size: 0.92rem;
                font-weight: 800;
                overflow-wrap: anywhere;
            }}
            .subscriber-role {{
                color: {TEXT_MUTED};
                font-size: 0.74rem;
                font-weight: 700;
            }}
            .unsubscribe-button {{
                color: {TEXT_MUTED};
                font-size: 0.74rem;
                font-weight: 900;
                letter-spacing: 0.02em;
            }}
            .subscriber-empty {{
                padding: 13px;
                border-radius: 14px;
                background: {ACCENT_SOFT};
                color: {WARNING};
                font-size: 0.9rem;
                line-height: 1.45;
            }}
            .subscribe-button {{
                min-height: 40px;
                background: linear-gradient(180deg, {PRIMARY}, {PRIMARY_DARK});
                color: white;
                border-radius: 11px;
                font-weight: 900;
                box-shadow: 0 8px 16px rgba(6,75,42,0.16);
            }}
            .link-button {{
                color: white;
                border: 1px solid rgba(255,255,255,0.28);
                border-radius: 999px;
                padding: 8px 12px;
                text-decoration: none;
                font-weight: 800;
            }}
            @media (max-width: 980px) {{
                .main-grid {{
                    grid-template-columns: 1fr;
                }}
                .hero-status {{
                    min-width: 100%;
                }}
                .event-time {{
                    white-space: normal;
                }}
            }}
        </style>
        """
    )

    summary_labels: dict[str, ui.label] = {}

    def refresh_subscribers() -> None:
        subscribers = services.subscriber_store.list_subscribers()
        subscriber_count_label.set_text(str(len(subscribers)))
        subscriber_list.clear()
        with subscriber_list:
            if not subscribers:
                ui.label(
                    "Chưa có email nào subscribe. Khi có văn bản mới, hệ thống sẽ ingest nhưng không gửi thông báo cho legal team."
                ).classes("subscriber-empty")
                return

            for email in subscribers:
                with ui.row().classes("subscriber-row w-full"):
                    with ui.element("div").classes(
                        "subscriber-avatar flex items-center justify-center"
                    ):
                        ui.icon("person", size="xs")
                    with ui.column().classes("gap-0 grow"):
                        ui.label(email).classes("subscriber-email")
                        ui.label("Legal event listener").classes("subscriber-role")
                    ui.button(
                        "Unsubscribe",
                        on_click=lambda _, item=email: unsubscribe_email(item),
                    ).classes("unsubscribe-button").props("flat dense")

    def subscribe_email() -> None:
        email = (email_input.value or "").strip()
        ok, message = services.subscriber_store.subscribe(email)
        ui.notify(message, color="positive" if ok else "warning", position="top")
        if ok:
            email_input.value = ""
        refresh_subscribers()

    def unsubscribe_email(email: str) -> None:
        ok, message = services.subscriber_store.unsubscribe(email)
        ui.notify(message, color="positive" if ok else "warning", position="top")
        refresh_subscribers()

    with ui.column().classes("events-page"):
        with ui.column().classes("events-shell"):
            status_label = ui.label("")
            with ui.row().classes("hero-card w-full items-center justify-between gap-5 wrap"):
                with ui.row().classes("items-center gap-4"):
                    with ui.element("div").classes("hero-icon flex items-center justify-center"):
                        ui.icon("hub")
                    with ui.column().classes("gap-2"):
                        ui.label("Legal automation event channel").classes("hero-kicker")
                        ui.label("Legal Event Log").classes("hero-title")
                        ui.label(
                            "Theo dõi văn bản pháp luật được cập nhật tự động, quản lý danh sách legal team subscribe để nhận thông báo khi có cập nhật mới."
                        ).classes("hero-subtitle")
                with ui.column().classes("hero-status gap-2"):
                    with ui.row().classes("items-center gap-2"):
                        ui.element("span").classes("status-dot")
                        ui.label("Realtime monitor").classes("font-bold")
                    status_label.classes("text-sm")
                    ui.link("Mở chatbot", "/").classes("link-button")

            with ui.element("div").classes("main-grid"):
                with ui.column().classes("gap-3"):
                    with ui.column().classes("panel panel-pad gap-4"):
                        with ui.row().classes("w-full items-center justify-between gap-3 wrap"):
                            with ui.column().classes("gap-1"):
                                ui.label("Tổng quan sự kiện").classes("panel-title")
                            with ui.row().classes("toolbar"):
                                filter_select = ui.select(
                                    options={
                                        "all": "Tất cả",
                                        "processed": "Đã xử lý",
                                        "ignored": "Bỏ qua",
                                        "failed": "Lỗi",
                                    },
                                    value="all",
                                    label="Lọc sự kiện",
                                ).props("outlined dense")

                                def on_filter_change(_) -> None:
                                    filter_state["value"] = filter_select.value or "all"
                                    refresh_view()

                                filter_select.on("update:model-value", on_filter_change)

                                async def refresh_now() -> None:
                                    refresh_button.disable()
                                    refresh_button.set_text("Refreshing...")
                                    try:
                                        await asyncio.to_thread(services.poller.poll_once)
                                        refresh_view()
                                    finally:
                                        refresh_button.set_text("Refresh")
                                        refresh_button.enable()

                                refresh_button = ui.button(
                                    "Refresh", on_click=refresh_now
                                ).props("outline")

                        last_refresh_label = ui.label("").classes("panel-subtitle")

                        with ui.row().classes("w-full gap-3 wrap"):
                            for key, label in [
                                ("total", "Tổng"),
                                ("processed", "Đã xử lý"),
                                ("created", "Tạo mới"),
                                ("updated", "Cập nhật"),
                                ("ignored", "Bỏ qua"),
                                ("failed", "Lỗi"),
                            ]:
                                with ui.column().classes("summary-card gap-2"):
                                    ui.label(label).classes("summary-label")
                                    summary_labels[key] = ui.label("0").classes(
                                        "summary-value"
                                    )

                    list_container = ui.column().classes("event-list w-full")

                with ui.column().classes("panel subscriber-card"):
                    with ui.column().classes("subscriber-hero gap-3"):
                        with ui.row().classes("items-center gap-3"):
                            with ui.element("div").classes(
                                "subscriber-hero-icon flex items-center justify-center"
                            ):
                                ui.icon("groups", size="sm")
                            with ui.column().classes("gap-1"):
                                ui.label("Legal team subscribers").classes(
                                    "subscriber-hero-title"
                                )
                                ui.label(
                                    "Subscribe để nhận thông báo khi có văn bản pháp luật mới."
                                ).classes("subscriber-hero-subtitle")
                    with ui.column().classes("subscriber-body"):
                        with ui.row().classes("subscriber-count-card w-full justify-between"):
                            with ui.column().classes("gap-1"):
                                ui.label("Đang subscribe").classes("subscriber-count-label")
                                ui.label("Kênh event pháp luật").classes("subscriber-role")
                            subscriber_count_label = ui.label("0").classes(
                                "subscriber-count-number"
                            )
                        with ui.row().classes("subscribe-form w-full items-center"):
                            email_input = ui.input("Email legal team").props(
                                "borderless dense type=email"
                            ).classes("grow")
                            ui.button("Subscribe", on_click=subscribe_email).classes(
                                "subscribe-button"
                            ).props("unelevated")
                        subscriber_list = ui.column().classes("subscriber-list w-full")

        def refresh_view() -> None:
            nonlocal refresh_timer, last_refresh_label
            if list_container.is_deleted or status_label.is_deleted:
                if refresh_timer is not None:
                    refresh_timer.cancel()
                return

            events = _source_events(
                services.event_store.list_events(),
                services.config.source_sender_email,
            )
            summary = _event_summary(events)
            for key, label in summary_labels.items():
                label.set_text(str(summary.get(key, 0)))

            readiness = []
            readiness.append("Poller sẵn sàng" if services.poller.is_ready() else "Poller chưa cấu hình")
            readiness.append("Nguồn gửi sẵn sàng" if services.config.source_ready else "Nguồn gửi chưa cấu hình")
            readiness.append(f"{len(services.subscriber_store.list_subscribers())} subscriber")
            status_label.set_text(" • ".join(readiness))
            if last_refresh_label is not None and not last_refresh_label.is_deleted:
                last_refresh_label.set_text(
                    f"Cập nhật lần cuối: {_format_vietnam_time(datetime.now().astimezone().isoformat())}"
                )

            if filter_state["value"] != "all":
                events = [event for event in events if event.status == filter_state["value"]]

            list_container.clear()
            with list_container:
                if not events:
                    with ui.column().classes("panel panel-pad w-full gap-2"):
                        ui.label("Chưa có sự kiện automation").classes("panel-title")
                        ui.label(
                            "Gửi một văn bản từ source portal, sau đó chờ poller xử lý để thấy event xuất hiện tại đây."
                        ).classes("panel-subtitle")
                    return

                for event in events:
                    icon_class = event.status if event.status in {"failed", "ignored"} else ""
                    badge_class = event.status if event.status in {"failed", "ignored"} else ""
                    icon_name = {
                        "processed": "check_circle",
                        "ignored": "visibility_off",
                        "failed": "error",
                    }.get(event.status, "article")
                    notification_text = event.notification_status
                    if event.notification_recipients:
                        notification_text += f" → {', '.join(event.notification_recipients)}"

                    with ui.column().classes("event-row w-full"):
                        with ui.row().classes("mail-header w-full"):
                            with ui.element("div").classes(
                                f"event-icon {icon_class} flex items-center justify-center"
                            ):
                                ui.icon(icon_name)
                            with ui.column().classes("gap-1 grow"):
                                with ui.row().classes("w-full items-start gap-3"):
                                    ui.label(event.subject or "(không có tiêu đề)").classes(
                                        "event-title grow"
                                    )
                                    ui.label(_status_label(event.status)).classes(
                                        f"event-badge {badge_class}"
                                    )
                                ui.label(f"<{event.sender_email or event.sender}>").classes("event-sender")
                            ui.label(_format_vietnam_time(event.created_at)).classes("event-time")

                        with ui.column().classes("mail-body"):
                            with ui.row().classes("mail-details"):
                                ui.label("Hành động:").classes("detail-label")
                                ui.label(_action_label(event.action)).classes("detail-value")
                                ui.label("•").classes("detail-separator")
                                ui.label("Tệp văn bản:").classes("detail-label")
                                ui.label(event.filename or "-").classes("detail-value")
                                ui.label("•").classes("detail-separator")
                                ui.label("Legal team:").classes("detail-label")
                                ui.label(notification_text).classes("detail-value")
                            if event.error:
                                ui.label(event.error).classes("event-error")

            refresh_subscribers()

        refresh_timer = ui.timer(5.0, refresh_view, once=False, immediate=True)
        refresh_view()
