import asyncio
from typing import Any

from nicegui import events, ui

from app.automation.models import MailAttachment
from app.automation.runtime import get_automation_services

ORANGE = "#F58220"
ORANGE_DARK = "#D85A00"
ORANGE_DEEP = "#9F2F00"
ORANGE_SOFT = "#FFF3E8"
AMBER = "#FFB547"
RED = "#C0392B"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#FFF8F1"
BORDER = "#F1C7A4"
TEXT = "#2D1B12"
TEXT_MUTED = "#745B4D"
SUCCESS = "#1D7A46"
SUCCESS_SOFT = "#EAF8EF"
SUCCESS_BORDER = "#B8E1C7"
ERROR_SOFT = "#FFF0EC"
ERROR_BORDER = "#F2B9AC"
INFO_SOFT = "#FFF7ED"
INFO_BORDER = "#F7C28B"


def _notify(message: str, color: str) -> None:
    ui.notify(message, color=color, position="top", close_button=True)


@ui.page("/")
def source_portal_page() -> None:
    services = get_automation_services()
    uploaded: dict[str, str | bytes | None] = {"name": None, "content": None}

    status_card: Any = None
    status_badge: Any = None
    status_title: Any = None
    status_detail: Any = None

    ui.add_head_html(
        f"""
        <style>
            body {{
                background:
                    radial-gradient(circle at top right, rgba(245, 130, 32, 0.16), transparent 24%),
                    linear-gradient(180deg, #fff8f1 0%, #f6ede4 100%);
                color: {TEXT};
                font-size: 15px;
            }}
            .portal-page {{
                width: 100%;
                min-height: 100vh;
                padding: 14px 16px;
            }}
            .portal-shell {{
                width: min(1160px, 100%);
                margin: 0 auto;
                gap: 12px;
            }}
            .portal-header {{
                overflow: hidden;
                border-radius: 16px;
                border: 1px solid rgba(159, 47, 0, 0.18);
                background: {SURFACE};
                box-shadow: 0 14px 34px rgba(111, 54, 13, 0.10);
            }}
            .top-strip {{
                width: 100%;
                min-height: 34px;
                padding: 6px 16px;
                background: linear-gradient(90deg, {ORANGE_DEEP} 0%, {ORANGE_DARK} 52%, {ORANGE} 100%);
                color: white;
                font-size: 0.9rem;
                font-weight: 800;
            }}
            .brand-area {{
                width: 100%;
                padding: 14px 18px;
                background:
                    linear-gradient(90deg, rgba(255,255,255,0.98), rgba(255,248,241,0.94)),
                    radial-gradient(circle at 92% 20%, rgba(245,130,32,0.18), transparent 30%);
            }}
            .brand-mark {{
                width: 52px;
                height: 52px;
                border-radius: 14px;
                background: linear-gradient(145deg, {ORANGE} 0%, {ORANGE_DARK} 100%);
                color: white;
                box-shadow: 0 10px 20px rgba(216, 90, 0, 0.24);
            }}
            .brand-mark .q-icon {{
                font-size: 1.8rem;
            }}
            .brand-eyebrow {{
                color: {ORANGE_DEEP};
                font-size: 0.86rem;
                font-weight: 900;
                letter-spacing: 0.07em;
                text-transform: uppercase;
            }}
            .brand-title {{
                color: {ORANGE_DEEP};
                font-size: clamp(1.45rem, 2.7vw, 2.2rem);
                font-weight: 900;
                line-height: 1.05;
                letter-spacing: -0.03em;
            }}
            .brand-subtitle {{
                max-width: 700px;
                color: {TEXT_MUTED};
                font-size: 0.96rem;
                line-height: 1.45;
            }}
            .contact-panel {{
                min-width: 300px;
                max-width: 370px;
                padding: 12px 14px;
                border-radius: 14px;
                border: 1px solid rgba(245, 130, 32, 0.24);
                background: rgba(255, 255, 255, 0.88);
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.9);
            }}
            .contact-title {{
                color: {ORANGE_DEEP};
                font-size: 0.98rem;
                font-weight: 900;
            }}
            .contact-label {{
                color: {TEXT_MUTED};
                font-size: 0.78rem;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }}
            .contact-value {{
                color: {TEXT};
                font-size: 0.94rem;
                font-weight: 800;
                overflow-wrap: anywhere;
            }}
            .content-grid {{
                gap: 12px;
                align-items: stretch;
            }}
            .surface-card {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 16px;
                box-shadow: 0 14px 30px rgba(111, 54, 13, 0.08);
            }}
            .form-card {{
                flex: 1 1 740px;
                padding: 18px;
                gap: 12px;
            }}
            .side-card {{
                flex: 0 1 330px;
                min-width: 280px;
            }}
            .panel-header {{
                gap: 4px;
            }}
            .section-title {{
                color: {ORANGE_DEEP};
                font-size: 1.18rem;
                font-weight: 900;
                line-height: 1.2;
            }}
            .section-subtitle {{
                color: {TEXT_MUTED};
                line-height: 1.45;
                font-size: 0.94rem;
            }}
            .input-grid {{
                gap: 12px;
            }}
            .date-input {{
                flex: 1 1 220px;
            }}
            .date-input .q-field__append {{
                color: {ORANGE_DARK};
            }}
            .form-card .q-field__control {{
                min-height: 48px;
                border-radius: 10px;
                background: #fffdfb;
            }}
            .form-card .q-field__label {{
                font-size: 0.94rem;
                color: {TEXT_MUTED};
            }}
            .form-card .q-field__native, .form-card textarea {{
                color: {TEXT};
                font-size: 0.96rem;
            }}
            .form-card .q-textarea .q-field__control {{
                min-height: 72px;
            }}
            .upload-frame {{
                padding: 14px;
                border-radius: 14px;
                border: 1px dashed {ORANGE};
                background:
                    linear-gradient(180deg, rgba(245,130,32,0.08), rgba(255,248,241,0.86)),
                    {SURFACE_ALT};
                gap: 10px;
            }}
            .upload-title-row {{
                align-items: center;
                gap: 10px;
            }}
            .upload-icon {{
                width: 34px;
                height: 34px;
                border-radius: 10px;
                background: {ORANGE};
                color: white;
            }}
            .helper-note {{
                color: {TEXT_MUTED};
                font-size: 0.9rem;
                line-height: 1.45;
            }}
            .upload-action-row {{
                gap: 10px;
                align-items: center;
                flex-wrap: wrap;
            }}
            .upload-control {{
                width: min(360px, 100%);
            }}
            .upload-control .q-uploader {{
                width: 100%;
                max-height: 82px;
                border-radius: 12px;
                border: 1px solid rgba(159,47,0,0.20);
                box-shadow: none;
                overflow: hidden;
                background: white;
            }}
            .upload-control .q-uploader__header {{
                background: linear-gradient(90deg, {ORANGE_DARK}, {ORANGE});
                color: white;
                min-height: 42px;
            }}
            .upload-control .q-uploader__list {{
                min-height: 0;
                max-height: 36px;
                padding: 0;
            }}
            .upload-control .q-uploader__title {{
                font-size: 0.94rem;
                font-weight: 900;
            }}
            .file-pill {{
                display: inline-flex;
                align-items: center;
                width: fit-content;
                max-width: 100%;
                padding: 9px 12px;
                border-radius: 10px;
                background: white;
                border: 1px solid rgba(245, 130, 32, 0.32);
                color: {ORANGE_DEEP};
                font-size: 0.9rem;
                font-weight: 800;
                overflow-wrap: anywhere;
            }}
            .meta-row {{
                gap: 8px;
                flex-wrap: wrap;
            }}
            .meta-chip {{
                padding: 9px 12px;
                border-radius: 10px;
                background: #fffaf5;
                border: 1px solid rgba(245, 130, 32, 0.24);
                min-width: min(245px, 100%);
            }}
            .meta-label {{
                color: {TEXT_MUTED};
                font-size: 0.78rem;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }}
            .meta-value {{
                color: {TEXT};
                font-size: 0.92rem;
                font-weight: 800;
                overflow-wrap: anywhere;
            }}
            .action-row {{
                gap: 10px;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
            }}
            .primary-button {{
                min-height: 42px;
                padding: 0 16px;
                background: linear-gradient(180deg, {ORANGE} 0%, {ORANGE_DARK} 100%);
                color: white;
                border-radius: 10px;
                font-size: 0.94rem;
                font-weight: 900;
                letter-spacing: 0.01em;
                box-shadow: 0 10px 18px rgba(216, 90, 0, 0.20);
            }}
            .primary-button:hover {{
                filter: brightness(1.03);
            }}
            .status-card {{
                width: 100%;
                height: 100%;
                padding: 16px;
                border-radius: 16px;
                border: 1px solid {INFO_BORDER};
                background: {INFO_SOFT};
                gap: 10px;
            }}
            .status-badge {{
                width: fit-content;
                padding: 6px 10px;
                border-radius: 999px;
                background: rgba(245,130,32,0.14);
                color: {ORANGE_DEEP};
                font-size: 0.76rem;
                font-weight: 900;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }}
            .status-title {{
                color: {ORANGE_DEEP};
                font-size: 1.05rem;
                font-weight: 900;
                line-height: 1.3;
            }}
            .status-detail {{
                color: {TEXT_MUTED};
                line-height: 1.5;
                font-size: 0.94rem;
                white-space: pre-wrap;
            }}
            .portal-footer-note {{
                color: {TEXT_MUTED};
                font-size: 0.88rem;
                line-height: 1.45;
            }}
            .divider-soft {{
                background: rgba(245,130,32,0.22);
            }}
            @media (max-width: 760px) {{
                .portal-page {{
                    padding: 10px;
                }}
                .brand-area, .form-card {{
                    padding: 14px;
                }}
                .brand-mark {{
                    width: 46px;
                    height: 46px;
                }}
                .contact-panel {{
                    min-width: 100%;
                }}
            }}
        </style>
        """
    )

    def show_status(kind: str, title: str, detail: str) -> None:
        palettes = {
            "info": {
                "background": INFO_SOFT,
                "border": INFO_BORDER,
                "accent": ORANGE_DEEP,
                "badge_bg": "rgba(245, 130, 32, 0.14)",
                "badge_text": ORANGE_DEEP,
                "badge_label": "Đang chờ",
            },
            "success": {
                "background": SUCCESS_SOFT,
                "border": SUCCESS_BORDER,
                "accent": SUCCESS,
                "badge_bg": "rgba(29, 122, 70, 0.12)",
                "badge_text": SUCCESS,
                "badge_label": "Thành công",
            },
            "error": {
                "background": ERROR_SOFT,
                "border": ERROR_BORDER,
                "accent": RED,
                "badge_bg": "rgba(192, 57, 43, 0.10)",
                "badge_text": RED,
                "badge_label": "Cần xử lý",
            },
        }
        palette = palettes[kind]
        status_card.style(
            f"background: {palette['background']}; border-color: {palette['border']};"
        )
        status_badge.set_text(palette["badge_label"])
        status_badge.style(
            f"background: {palette['badge_bg']}; color: {palette['badge_text']};"
        )
        status_title.set_text(title)
        status_title.style(f"color: {palette['accent']};")
        status_detail.set_text(detail)

    async def handle_upload(event: events.UploadEventArguments) -> None:
        uploaded["name"] = event.file.name
        uploaded["content"] = await event.file.read()
        selected_file_label.set_text(f"Đã chọn: {event.file.name}")
        show_status(
            "info",
            "Hồ sơ đính kèm đã sẵn sàng",
            "Bạn có thể rà soát tiêu đề, ngày hiệu lực và ghi chú trước khi gửi bản cập nhật.",
        )
        _notify("Đã tải tệp Markdown lên thành công.", "positive")

    async def send_update() -> None:
        filename = str(uploaded["name"] or "").strip()
        content = uploaded["content"]
        if not filename or not isinstance(content, bytes):
            show_status(
                "error",
                "Chưa có tệp Markdown",
                "Vui lòng tải lên một tệp .md để mô phỏng văn bản pháp luật mới trước khi gửi.",
            )
            _notify("Vui lòng tải lên tệp Markdown trước khi gửi.", "negative")
            return
        if not filename.lower().endswith(".md"):
            show_status(
                "error",
                "Định dạng tệp chưa hợp lệ",
                "Cổng này chỉ tiếp nhận tệp Markdown (.md) để mô phỏng quy trình ingest của AI Legal.",
            )
            _notify("Chỉ chấp nhận tệp .md.", "negative")
            return
        if not services.config.source_ready:
            show_status(
                "error",
                "Nguồn gửi chưa được cấu hình",
                "Tài khoản Gmail của nguồn pháp lý chưa sẵn sàng. Hãy kiểm tra lại cấu hình LEGAL_MAIL_SOURCE_* trong môi trường.",
            )
            _notify("Tài khoản Gmail nguồn chưa được cấu hình.", "negative")
            return
        if not services.config.admin_sender_email:
            show_status(
                "error",
                "Thiếu địa chỉ hộp thư quản trị",
                "Chưa có email đích để nhận bản cập nhật pháp luật từ cổng này.",
            )
            _notify("Admin inbox chưa được cấu hình.", "negative")
            return

        title = title_input.value.strip() or filename
        effective_date = effective_date_input.value.strip() or "Chưa xác định"
        note = note_input.value.strip() or "Không có ghi chú bổ sung."
        subject = f"[{services.config.source_label}] Cập nhật pháp luật - {title}"
        body = "\n".join(
            [
                f"Nguồn: {services.config.source_label}",
                f"Tên văn bản pháp luật: {title}",
                f"Ngày hiệu lực: {effective_date}",
                "",
                "Ghi chú cập nhật pháp luật:",
                note,
                "",
                "Tệp đính kèm: văn bản pháp luật dạng Markdown để AI Legal ingest.",
            ]
        )

        send_button.disable()
        sending_spinner.visible = True
        show_status(
            "info",
            "Đang gửi bản cập nhật",
            "Hệ thống đang tạo email mô phỏng và chuyển đến hộp thư quản trị. Vui lòng chờ trong giây lát...",
        )

        try:
            await asyncio.to_thread(
                services.gmail_client.send_email,
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
            show_status(
                "success",
                "Đã gửi bản cập nhật pháp luật",
                f"Email mô phỏng đã được gửi đến {services.config.admin_sender_email}. Hệ thống AI Legal có thể bắt đầu poll và ingest tệp {filename}.",
            )
            _notify("Đã gửi legal update thành công.", "positive")
        except Exception as exc:
            show_status(
                "error",
                "Gửi bản cập nhật thất bại",
                f"Không thể gửi email mô phỏng tới hộp thư quản trị. Chi tiết lỗi: {exc}",
            )
            _notify(f"Gửi thất bại: {exc}", "negative")
        finally:
            send_button.enable()
            sending_spinner.visible = False

    def info_chip(label: str, value: str) -> None:
        with ui.column().classes("meta-chip gap-1"):
            ui.label(label).classes("meta-label")
            ui.label(value).classes("meta-value")

    with ui.column().classes("portal-page"):
        with ui.column().classes("portal-shell"):
            with ui.column().classes("portal-header"):
                with ui.row().classes("top-strip items-center justify-between gap-3 wrap"):
                    ui.label("THƯ VIỆN PHÁP LUẬT • Cổng thông tin văn bản")
                    ui.label("Cập nhật văn bản mới cho hệ thống AI Legal")

                with ui.row().classes("brand-area items-start justify-between gap-6 wrap"):
                    with ui.row().classes("items-start gap-4"):
                        with ui.element("div").classes("brand-mark flex items-center justify-center"):
                            ui.icon("gavel")
                        with ui.column().classes("gap-1"):
                            ui.label("Nguồn dữ liệu pháp luật mô phỏng").classes(
                                "brand-eyebrow"
                            )
                            ui.label("Trung tâm tiếp nhận văn bản pháp luật").classes(
                                "brand-title"
                            )
                            ui.label(
                                "Gửi hồ sơ Markdown với metadata rõ ràng, sẵn sàng cho bước kiểm duyệt tự động của AI Legal."
                            ).classes("brand-subtitle")

                    with ui.column().classes("contact-panel gap-2"):
                        ui.label("Thông tin chuyển tiếp").classes("contact-title")
                        ui.separator().classes("divider-soft")
                        ui.label("Kênh công bố").classes("contact-label")
                        ui.label(
                            services.config.source_label or "thuvienphapluat.vn"
                        ).classes("contact-value")
                        ui.label("Hộp thư nguồn").classes("contact-label")
                        ui.label(
                            services.config.source_sender_email or "Chưa cấu hình"
                        ).classes("contact-value")

            with ui.row().classes("content-grid w-full wrap"):
                with ui.column().classes("surface-card form-card"):
                    with ui.column().classes("panel-header"):
                        ui.label("Soạn hồ sơ cập nhật").classes("section-title")
                        ui.label(
                            "Nhập thông tin văn bản và đính kèm tệp Markdown để gửi vào luồng xử lý."
                        ).classes("section-subtitle")

                    with ui.row().classes("w-full input-grid wrap"):
                        title_input = ui.input("Tên văn bản hoặc tiêu đề cập nhật").props(
                            "outlined"
                        )
                        title_input.style("flex: 1 1 430px;")

                        with ui.input("Ngày hiệu lực").props(
                            "outlined readonly mask=####-##-##"
                        ).classes("date-input") as effective_date_input:
                            with ui.menu().props("no-parent-event") as date_menu:
                                ui.date().bind_value(effective_date_input).props(
                                    "today-btn minimal"
                                )
                            with effective_date_input.add_slot("append"):
                                ui.icon("event").classes("cursor-pointer").on(
                                    "click", date_menu.open
                                )

                    note_input = ui.textarea("Tóm tắt nội dung thay đổi").props(
                        "outlined autogrow"
                    )
                    note_input.classes("w-full")

                    with ui.column().classes("upload-frame w-full"):
                        with ui.row().classes("upload-title-row"):
                            with ui.element("div").classes(
                                "upload-icon flex items-center justify-center"
                            ):
                                ui.icon("upload_file")
                            with ui.column().classes("gap-1"):
                                ui.label("Đính kèm tệp Markdown").classes("section-title")
                                ui.label("Chỉ nhận tệp .md đã chuẩn hóa.").classes(
                                    "helper-note"
                                )
                        with ui.row().classes("upload-action-row"):
                            ui.upload(
                                label="Chọn tệp .md",
                                auto_upload=True,
                                on_upload=handle_upload,
                                max_files=1,
                            ).props("accept=.md bordered flat").classes("upload-control")
                            selected_file_label = ui.label(
                                "Chưa có tệp Markdown nào được chọn."
                            ).classes("file-pill")

                    with ui.row().classes("action-row w-full"):
                        with ui.row().classes("meta-row"):
                            info_chip(
                                "Nguồn gửi",
                                services.config.source_sender_email or "Chưa cấu hình",
                            )
                            info_chip(
                                "Hộp thư nhận",
                                services.config.admin_sender_email or "Chưa cấu hình",
                            )
                        with ui.row().classes("items-center gap-3"):
                            sending_spinner = ui.spinner(size="sm", color=ORANGE_DARK)
                            sending_spinner.visible = False
                            send_button = ui.button(
                                "Gửi cập nhật pháp luật",
                                on_click=send_update,
                            ).props("unelevated")
                            send_button.classes("primary-button")

                    ui.label(
                        "Sau khi gửi, poller của AI Legal sẽ kiểm tra inbox quản trị, đánh giá email và đưa tài liệu phù hợp vào quy trình ingest."
                    ).classes("portal-footer-note")

                with ui.column().classes("side-card"):
                    status_card = ui.column().classes("status-card")
                    with status_card:
                        status_badge = ui.label("Đang chờ").classes("status-badge")
                        status_title = ui.label("Sẵn sàng tiếp nhận hồ sơ").classes(
                            "status-title"
                        )
                        status_detail = ui.label(
                            "Tải lên tệp Markdown và bấm gửi để mô phỏng một nguồn pháp luật phát hành nội dung mới tới AI Legal."
                        ).classes("status-detail")
