import asyncio
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from fastapi.responses import JSONResponse
from nicegui import app, ui

from app.agent import ask_question

PRIMARY = "#007A33"
PRIMARY_DARK = "#0A4A24"
PRIMARY_SOFT = "#EAF6EE"
SURFACE = "#FFFFFF"
SURFACE_MUTED = "#F6F8F7"
TEXT = "#183022"
TEXT_MUTED = "#66756B"
BORDER = "#D9E6DD"
ERROR_BG = "#FFF3F1"
ERROR_BORDER = "#F3C8C1"
ERROR_TEXT = "#9A2B1F"

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

FOLDER_CONFIG = {
    "faq": {"label": "FAQ", "hint": "Câu hỏi thường gặp"},
    "policy": {"label": "Policy", "hint": "Chính sách nội bộ"},
    "law": {"label": "Văn bản luật", "hint": "Quy định, nghị định pháp luật"},
}


def get_session_id() -> str:
    session_id = app.storage.client.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
        app.storage.client["session_id"] = session_id
    return session_id


def list_docs_files() -> dict[str, list[str]]:
    """Return {folder_key: [file_names]} from the docs directory."""
    result: dict[str, list[str]] = {}
    for key in FOLDER_CONFIG:
        folder = DOCS_DIR / key
        if folder.is_dir():
            result[key] = sorted(
                f.name for f in folder.iterdir() if f.is_file() and f.name != ".gitkeep"
            )
        else:
            result[key] = []
    return result


def delete_doc_file(folder_key: str, filename: str) -> None:
    filepath = DOCS_DIR / folder_key / filename
    if filepath.exists():
        filepath.unlink()


@app.post("/api/upload")
async def api_upload(folder: str, files: list[UploadFile]):
    global _sidebar_refresh_counter
    target = DOCS_DIR / folder
    if not target.is_relative_to(DOCS_DIR):
        return JSONResponse({"error": "Invalid folder"}, status_code=400)
    target.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files:
        if f.filename:
            dest = target / f.filename
            with open(dest, "wb") as fh:
                shutil.copyfileobj(f.file, fh)
            saved.append(f.filename)
    # Increment counter so active sessions pick up the change without a full
    # page reload (which would wipe chat history).
    _sidebar_refresh_counter += 1
    return {"saved": saved}


# Store a global counter; incrementing it signals all page instances to refresh
# the sidebar without losing their own message history.
_sidebar_refresh_counter = 0


def trigger_sidebar_refresh() -> None:
    """Signal all active sessions to refresh their sidebar view."""
    global _sidebar_refresh_counter
    _sidebar_refresh_counter += 1


@ui.page("/")
def chat_page() -> None:
    session_id = get_session_id()
    # Capture the current sidebar refresh counter so we can detect when a
    # refresh signal is sent from upload/delete handlers.
    refresh_slot = {"count": _sidebar_refresh_counter}

    # We'll populate folders here
    folder_containers: dict = {}

    def refresh_folder_view():
        """Re-render all folder cards from the current docs directory state."""
        docs = list_docs_files()
        for key, containers in folder_containers.items():
            files = docs.get(key, [])
            count = len(files)
            containers["badge"].text = f"{count} file{'s' if count != 1 else ''}"
            containers["empty_msg"].visible = count == 0

            # Clear file list
            containers["file_list"].clear()

            for fname in files:
                with containers["file_list"]:
                    with ui.element("div").classes("file-row"):
                        ui.label(fname).classes("file-name")

                        def make_delete_handler(fk: str, fn: str):
                            def handler():
                                delete_doc_file(fk, fn)
                                trigger_sidebar_refresh()
                                refresh_folder_view()
                            return handler

                        delete_btn = ui.element("button").props("flat dense").classes("file-delete-btn")
                        with delete_btn:
                            ui.icon("close", size="xs")
                        delete_btn.on("click", make_delete_handler(key, fname))

    ui.add_head_html(
        f"""
        <style>
            body {{
                background:
                    radial-gradient(ellipse at top left, rgba(0,122,51,0.06) 0%, transparent 60%),
                    linear-gradient(180deg, #eef7f1 0%, #e4efe8 100%);
                color: {TEXT};
            }}
            .app-shell {{
                width: min(1480px, calc(100vw - 24px));
                height: calc(100vh - 24px);
                margin: 12px auto;
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 22px;
                box-shadow: 0 12px 36px rgba(10, 74, 36, 0.08);
                overflow: hidden;
            }}
            .topbar {{
                padding: 18px 22px 16px;
                background: linear-gradient(135deg, {PRIMARY_DARK}, {PRIMARY});
                color: white;
            }}
            .topbar-kicker {{
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                opacity: 0.78;
            }}
            .topbar-title {{
                margin-top: 4px;
                font-size: 1.2rem;
                font-weight: 800;
                line-height: 1.2;
            }}
            .topbar-subtitle {{
                margin-top: 6px;
                max-width: 700px;
                font-size: 0.9rem;
                line-height: 1.5;
                color: rgba(255, 255, 255, 0.86);
            }}
            .session-chip {{
                padding: 7px 11px;
                border-radius: 999px;
                border: 1px solid rgba(255, 255, 255, 0.16);
                background: rgba(255, 255, 255, 0.12);
                color: white;
                font-size: 0.78rem;
                font-weight: 700;
                white-space: nowrap;
            }}
            .body-split {{
                display: flex;
                flex: 1;
                overflow: hidden;
                width: 100%;
            }}
            .sidebar {{
                width: 360px;
                min-width: 360px;
                background: {PRIMARY_SOFT};
                border-right: 1px solid {BORDER};
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }}
            .sidebar-header {{
                padding: 16px 18px 12px;
                border-bottom: 1px solid {BORDER};
            }}
            .sidebar-title {{
                font-size: 1rem;
                font-weight: 800;
                color: {PRIMARY_DARK};
            }}
            .sidebar-subtitle {{
                margin-top: 3px;
                font-size: 0.82rem;
                color: {TEXT_MUTED};
                line-height: 1.45;
            }}
            .sidebar-scroll {{
                flex: 1;
                overflow-y: auto;
                padding: 14px 16px 20px;
            }}
            .folder-card {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 14px;
                padding: 14px 15px 14px;
                margin-bottom: 12px;
                box-shadow: 0 2px 8px rgba(10,74,36,0.04);
            }}
            .folder-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                width: 100%;
            }}
            .folder-name {{
                font-size: 0.95rem;
                font-weight: 700;
                color: {TEXT};
            }}
            .folder-upload-btn {{
                padding: 5px 12px;
                border-radius: 8px;
                border: 1px solid {BORDER};
                background: {SURFACE};
                color: {PRIMARY};
                font-size: 0.8rem;
                font-weight: 700;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }}
            .folder-upload-btn:hover {{
                background: {PRIMARY_SOFT};
            }}
            .folder-meta {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-top: 6px;
            }}
            .folder-hint {{
                font-size: 0.78rem;
                color: {TEXT_MUTED};
            }}
            .folder-badge {{
                font-size: 0.72rem;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 999px;
                background: {PRIMARY_SOFT};
                color: {PRIMARY};
            }}
            .file-list {{
                margin-top: 10px;
            }}
            .file-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 6px 8px;
                border-radius: 8px;
                margin-top: 4px;
                background: {SURFACE_MUTED};
                font-size: 0.83rem;
                color: {TEXT};
            }}
            .file-row:hover {{
                background: {PRIMARY_SOFT};
            }}
            .file-name {{
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                flex: 1;
                margin-right: 8px;
            }}
            .file-delete-btn {{
                width: 22px;
                height: 22px;
                border-radius: 50%;
                border: none;
                background: {ERROR_BG};
                color: {ERROR_TEXT};
                font-size: 0.85rem;
                font-weight: 700;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }}
            .file-delete-btn:hover {{
                background: {ERROR_BORDER};
            }}
            .empty-folder-msg {{
                margin-top: 10px;
                font-size: 0.8rem;
                color: {TEXT_MUTED};
                font-style: italic;
            }}
            .chat-area {{
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                background: linear-gradient(180deg, #f7faf8 0%, #f2f5f3 100%);
            }}
            .messages-pane {{
                background: transparent;
            }}
            .messages-column {{
                width: 100%;
                gap: 14px;
                padding: 18px 4px 10px;
            }}
            .row-user,
            .row-assistant,
            .row-status,
            .row-error {{
                display: flex;
                width: 100%;
            }}
            .row-user {{
                justify-content: flex-end;
            }}
            .row-assistant,
            .row-status,
            .row-error {{
                justify-content: flex-start;
            }}
            .bubble {{
                max-width: min(760px, 86%);
                padding: 14px 16px;
                border-radius: 18px;
                border: 1px solid {BORDER};
                box-shadow: 0 4px 14px rgba(10, 74, 36, 0.04);
            }}
            .bubble-user {{
                background: linear-gradient(135deg, {PRIMARY}, #138545);
                color: white;
                border-color: transparent;
                border-bottom-right-radius: 6px;
            }}
            .bubble-assistant {{
                background: {SURFACE};
                color: {TEXT};
                border-bottom-left-radius: 6px;
            }}
            .bubble-status {{
                background: {PRIMARY_SOFT};
                color: {TEXT_MUTED};
                border-color: #d6eadc;
                border-bottom-left-radius: 6px;
            }}
            .bubble-error {{
                background: {ERROR_BG};
                color: {ERROR_TEXT};
                border-color: {ERROR_BORDER};
                border-bottom-left-radius: 6px;
            }}
            .message-label {{
                margin-bottom: 8px;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                opacity: 0.72;
            }}
            .bubble-user .message-label {{
                color: rgba(255, 255, 255, 0.8);
            }}
            .bubble-assistant .message-label,
            .bubble-status .message-label {{
                color: {PRIMARY};
            }}
            .bubble-error .message-label {{
                color: {ERROR_TEXT};
            }}
            .message-text {{
                white-space: pre-wrap;
                line-height: 1.6;
                font-size: 0.97rem;
            }}
            .message-markdown {{
                font-size: 0.97rem;
                line-height: 1.7;
            }}
            .message-markdown p:first-child {{
                margin-top: 0;
            }}
            .message-markdown p:last-child {{
                margin-bottom: 0;
            }}
            .message-markdown h1,
            .message-markdown h2,
            .message-markdown h3 {{
                margin: 0.95rem 0 0.45rem;
                color: {PRIMARY_DARK};
                font-weight: 800;
                line-height: 1.3;
            }}
            .message-markdown h1 {{ font-size: 1.16rem; }}
            .message-markdown h2 {{ font-size: 1.05rem; }}
            .message-markdown h3 {{ font-size: 0.98rem; }}
            .message-markdown ul,
            .message-markdown ol {{
                margin: 0.4rem 0 0.8rem;
                padding-left: 1.15rem;
            }}
            .message-markdown li {{
                margin: 0.18rem 0;
            }}
            .message-markdown strong {{
                color: {PRIMARY_DARK};
            }}
            .message-markdown code {{
                padding: 0.1rem 0.32rem;
                border-radius: 6px;
                background: rgba(0, 122, 51, 0.08);
                color: {PRIMARY_DARK};
                font-size: 0.92em;
            }}
            .message-markdown hr {{
                border: 0;
                border-top: 1px solid {BORDER};
                margin: 1rem 0;
            }}
            .composer {{
                padding: 14px 16px 16px;
                background: {SURFACE};
                border-top: 1px solid {BORDER};
            }}
            .composer-note {{
                margin-top: 8px;
                color: {TEXT_MUTED};
                font-size: 0.81rem;
            }}
            .thinking-dots {{
                display: inline-flex;
                gap: 6px;
                margin-right: 10px;
            }}
            .dot {{
                width: 8px;
                height: 8px;
                border-radius: 999px;
                background: {PRIMARY};
                animation: pulse 1.25s infinite ease-in-out both;
            }}
            .dot:nth-child(1) {{ animation-delay: -0.24s; }}
            .dot:nth-child(2) {{ animation-delay: -0.12s; }}
            @keyframes pulse {{
                0%, 80%, 100% {{ transform: scale(0.55); opacity: 0.35; }}
                40% {{ transform: scale(1); opacity: 1; }}
            }}
            @media (max-width: 768px) {{
                .app-shell {{
                    width: calc(100vw - 10px);
                    height: calc(100vh - 10px);
                    margin: 5px auto;
                    border-radius: 16px;
                }}
                .topbar {{
                    padding: 16px 16px 14px;
                }}
                .topbar-title {{
                    font-size: 1.08rem;
                }}
                .topbar-subtitle {{
                    font-size: 0.84rem;
                }}
                .bubble {{
                    max-width: 100%;
                }}
                .composer {{
                    padding: 12px;
                }}
                .sidebar {{
                    width: 100%;
                    min-width: unset;
                    border-right: none;
                    border-bottom: 1px solid {BORDER};
                }}
                .body-split {{
                    flex-direction: column;
                }}
            }}
        </style>
        """
    )

    with ui.column().classes("app-shell"):
        # ===== TOPBAR =====
        with ui.row().classes("topbar w-full items-start no-wrap"):
            with ui.column().classes("gap-0"):
                ui.label("AI LEGAL DEMO").classes("topbar-kicker")
                ui.label("Tra cứu chính sách và văn bản pháp luật").classes("topbar-title")
                ui.label(
                    "Trả lời dựa trên tài liệu đã nạp, có trích dẫn nguồn để kiểm chứng khi demo."
                ).classes("topbar-subtitle")
            ui.space()
            ui.label(f"Session {session_id}").classes("session-chip")

        # ===== BODY: split sidebar + chat =====
        with ui.element("div").classes("body-split"):
            # --- SIDEBAR ---
            with ui.element("div").classes("sidebar"):
                with ui.element("div").classes("sidebar-header"):
                    ui.label("Tài liệu").classes("sidebar-title")
                    ui.label("Quản lý file tài liệu tham chiếu để tra cứu.").classes("sidebar-subtitle")

                sidebar_scroll = ui.element("div").classes("sidebar-scroll")

                with sidebar_scroll:
                    for key, cfg in FOLDER_CONFIG.items():
                        with ui.element("div").classes("folder-card") as folder_card:
                            with ui.row().classes("folder-header w-full no-wrap items-center"):
                                ui.label(cfg["label"]).classes("folder-name")

                                target_dir = DOCS_DIR / key
                                target_dir.mkdir(parents=True, exist_ok=True)

                                # Simple compact upload button using native file input
                                upload_wrapper = ui.element("div").style(
                                    "position:relative;display:inline-block;"
                                )
                                upload_btn = ui.element("button").props("flat dense")
                                upload_btn.style(f"""
                                    padding: 4px 10px;
                                    border-radius: 6px;
                                    border: 1px solid {BORDER};
                                    background: {SURFACE};
                                    color: {PRIMARY};
                                    font-size: 0.75rem;
                                    font-weight: 600;
                                    cursor: pointer;
                                    display: inline-flex;
                                    align-items: center;
                                    gap: 3px;
                                """)
                                with upload_btn:
                                    with ui.row().classes("no-wrap items-center gap-1"):
                                        ui.icon("arrow_upward", size="xs").style("font-size:13px;")
                                        ui.label("Upload").style("font-size:0.72rem;")

                                def make_upload_trigger(fk: str):
                                    def trigger(_):
                                        ui.run_javascript(f"""
                                            (async () => {{
                                                const input = document.createElement('input');
                                                input.type = 'file';
                                                input.multiple = true;
                                                input.accept = '.md,.txt,.pdf,.docx,.doc,.xlsx,.csv';
                                                input.onchange = async (e) => {{
                                                    const files = e.target.files;
                                                    if (!files || files.length === 0) return;
                                                    const formData = new FormData();
                                                    for (const f of files) {{
                                                        formData.append('files', f, f.name);
                                                    }}
                                                    try {{
                                                        await fetch('/api/upload?folder={fk}', {{
                                                            method: 'POST',
                                                            body: formData,
                                                        }});
                                                    }} catch (err) {{
                                                        console.error('Upload failed:', err);
                                                    }}
                                                }};
                                                input.click();
                                            }})();
                                        """)
                                    return trigger
                                upload_btn.on("click", make_upload_trigger(key))

                            with ui.row().classes("folder-meta"):
                                ui.label(cfg["hint"]).classes("folder-hint")
                                badge = ui.label("").classes("folder-badge")

                            empty_msg = ui.label("Chưa có file nào. Nhấn Upload để thêm.").classes("empty-folder-msg")

                            file_list_el = ui.element("div").classes("file-list")

                            folder_containers[key] = {
                                "card": folder_card,
                                "badge": badge,
                                "empty_msg": empty_msg,
                                "file_list": file_list_el,
                            }

            # --- CHAT AREA ---
            with ui.element("div").classes("chat-area"):
                chat_container = ui.scroll_area().classes("messages-pane").style(
                    "flex-grow: 1; width: 100%; padding: 0 14px;"
                )
                with chat_container:
                    messages_column = ui.column().classes("messages-column")

                with ui.column().classes("composer w-full"):
                    with ui.row().classes("w-full no-wrap items-end gap-3"):
                        input_field = (
                            ui.textarea(placeholder="Nhập câu hỏi để tra cứu từ tài liệu...")
                            .props("outlined autogrow")
                            .style("flex-grow: 1;")
                        )
                        send_btn = ui.button("Gửi").props("unelevated size=lg")
                        send_btn.style(
                            f"background: {PRIMARY}; color: white; border-radius: 14px; padding: 0 22px;"
                        )
                    ui.label(
                        "Mẹo: có thể hỏi về điều luật, mức phân loại bảo mật, trách nhiệm doanh nghiệp, hoặc xử lý sự cố an ninh thông tin."
                    ).classes("composer-note")

    # ===== HELPER FUNCTIONS =====

    # Poll for sidebar refresh signals from upload/delete handlers.
    # Each page instance tracks its own slot count; when the global counter
    # advances, we refresh the sidebar without touching chat messages.
    async def poll_sidebar_refresh() -> None:
        if _sidebar_refresh_counter > refresh_slot["count"]:
            refresh_slot["count"] = _sidebar_refresh_counter
            refresh_folder_view()

    ui.timer(0.5, poll_sidebar_refresh, once=False)

    # Initial render
    refresh_folder_view()

    def scroll_to_latest() -> None:
        ui.run_javascript(
            "setTimeout(() => { "
            "const el = document.querySelector('.nicegui-scroll-area__content'); "
            "if (el) el.scrollTop = el.scrollHeight; }, 80);"
        )

    def add_user_message(text: str) -> None:
        with messages_column:
            with ui.element("div").classes("row-user"):
                with ui.element("div").classes("bubble bubble-user"):
                    ui.label("Người dùng").classes("message-label")
                    ui.label(text).classes("message-text")
        scroll_to_latest()

    def add_assistant_message(text: str) -> None:
        with messages_column:
            with ui.element("div").classes("row-assistant"):
                with ui.element("div").classes("bubble bubble-assistant"):
                    ui.label("Trợ lý").classes("message-label")
                    ui.markdown(text).classes("message-markdown")
        scroll_to_latest()

    def add_status_message(text: str):
        with messages_column:
            with ui.element("div").classes("row-status"):
                with ui.element("div").classes("bubble bubble-status") as wrapper:
                    ui.label("Đang xử lý").classes("message-label")
                    with ui.row().classes("items-center no-wrap"):
                        with ui.element("div").classes("thinking-dots"):
                            ui.element("div").classes("dot")
                            ui.element("div").classes("dot")
                            ui.element("div").classes("dot")
                        ui.label(text).style(
                            f"color: {TEXT_MUTED}; font-size: 0.95rem;"
                        )
        scroll_to_latest()
        return wrapper

    def add_error_message(text: str) -> None:
        with messages_column:
            with ui.element("div").classes("row-error"):
                with ui.element("div").classes("bubble bubble-error"):
                    ui.label("Lỗi").classes("message-label")
                    ui.markdown(text).classes("message-markdown")
        scroll_to_latest()

    async def handle_send() -> None:
        question = input_field.value.strip()
        if not question:
            return

        input_field.value = ""
        input_field.enabled = False
        send_btn.enabled = False

        add_user_message(question)
        thinking = add_status_message("Đang đọc tài liệu và tổng hợp câu trả lời có trích dẫn...")

        try:
            answer = await asyncio.wait_for(
                ask_question(question, session_id),
                timeout=60,
            )
            thinking.delete()
            add_assistant_message(answer or "Không nhận được nội dung trả lời từ mô hình.")
        except asyncio.TimeoutError:
            thinking.delete()
            add_error_message(
                "Câu trả lời vượt quá thời gian chờ **60 giây**. Hãy thử rút gọn câu hỏi hoặc hỏi theo từng ý nhỏ hơn."
            )
        except Exception as exc:
            thinking.delete()
            add_error_message(f"Xử lý thất bại: `{exc}`")
        finally:
            input_field.enabled = True
            send_btn.enabled = True
            input_field.run_method("focus")

    async def on_enter(event) -> None:
        args = event.args if isinstance(event.args, dict) else {}
        if not args.get("shiftKey", False):
            await handle_send()

    input_field.on("keydown.enter", on_enter)
    send_btn.on_click(handle_send)

    add_assistant_message(
        "Tôi sẽ trả lời bằng **tiếng Việt**, chỉ dựa trên tài liệu đã nạp, và cuối mỗi câu sẽ có **Nguồn tham khảo**."
    )
