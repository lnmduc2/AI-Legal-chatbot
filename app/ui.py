import asyncio
import uuid

from nicegui import app, ui

from app.agent import ask_question

HEINEKEN_GREEN_PRIMARY = "#007A33"
HEINEKEN_GREEN_LIGHT = "#0D9B4E"
HEINEKEN_GREEN_BG = "#E8F5E9"
HEINEKEN_GREEN_DARK = "#004D1F"


def get_session_id() -> str:
    session_id = app.storage.client.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
        app.storage.client["session_id"] = session_id
    return session_id


@ui.page("/")
def chat_page():
    session_id = get_session_id()

    ui.add_head_html(f"""
        <style>
            .msg-user {{
                background: {HEINEKEN_GREEN_PRIMARY};
                color: white;
                padding: 10px 18px;
                border-radius: 18px 18px 4px 18px;
                margin: 6px 0;
                max-width: 75%;
                align-self: flex-end;
                word-wrap: break-word;
                line-height: 1.5;
            }}
            .msg-assistant {{
                background: {HEINEKEN_GREEN_BG};
                color: #1B5E20;
                padding: 10px 18px;
                border-radius: 18px 18px 18px 4px;
                margin: 6px 0;
                max-width: 75%;
                align-self: flex-start;
                word-wrap: break-word;
                border: 1px solid #C8E6C9;
                line-height: 1.5;
            }}
            .thinking-dots {{
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 10px 18px;
            }}
            .dot {{
                width: 8px;
                height: 8px;
                background: {HEINEKEN_GREEN_PRIMARY};
                border-radius: 50%;
                animation: pulse 1.4s infinite ease-in-out both;
            }}
            .dot:nth-child(1) {{ animation-delay: -0.32s; }}
            .dot:nth-child(2) {{ animation-delay: -0.16s; }}
            @keyframes pulse {{
                0%, 80%, 100% {{ transform: scale(0.6); opacity: 0.4; }}
                40% {{ transform: scale(1.0); opacity: 1; }}
            }}
            .msg-timeout {{
                color: #C62828;
                font-style: italic;
                padding: 10px 18px;
                background: #FFEBEE;
                border: 1px solid #FFCDD2;
                border-radius: 18px 18px 18px 4px;
                margin: 6px 0;
                max-width: 75%;
                align-self: flex-start;
            }}
            .msg-error {{
                color: #C62828;
                padding: 10px 18px;
                background: #FFEBEE;
                border: 1px solid #FFCDD2;
                border-radius: 18px 18px 18px 4px;
                margin: 6px 0;
                max-width: 75%;
                align-self: flex-start;
            }}
        </style>
    """)

    with ui.column().style("width: 100%; height: calc(100vh - 80px);"):
        # Header
        with ui.row().classes("w-full no-wrap items-center").style("padding: 16px;"):
            ui.label("AI Legal Assistant").style(
                f"color: {HEINEKEN_GREEN_DARK}; font-weight: bold; font-size: 1.3rem;"
            )
            ui.space()
            ui.label(f"Session: {session_id}").style(
                f"color: {HEINEKEN_GREEN_PRIMARY}; font-size: 0.85rem;"
            )
        ui.separator()

        # Chat messages area
        chat_container = ui.scroll_area().style("flex-grow: 1; padding: 0 12px;")
        with chat_container:
            messages_column = ui.column().classes("w-full")

        # Input area
        with ui.row().classes("w-full no-wrap items-center").style("padding: 12px;"):
            input_field = ui.input(placeholder="Nhập câu hỏi của bạn...").props(
                "outlined dense"
            ).style("flex-grow: 1;")
            send_btn = ui.button("Gửi").props("round color=green")

    def add_message(text: str, css_class: str):
        with messages_column:
            ui.html(text).classes(css_class)
        ui.run_javascript(
            "setTimeout(() => { "
            "const el = document.querySelector('.nicegui-scroll-area__content'); "
            "if (el) el.scrollTop = el.scrollHeight; }, 100);"
        )

    async def handle_send():
        question = input_field.value.strip()
        if not question:
            return

        input_field.value = ""
        input_field.enabled = False
        send_btn.enabled = False

        add_message(question, "msg-user")

        with messages_column:
            with ui.element().classes("thinking-dots") as thinking:
                ui.element("div").classes("dot")
                ui.element("div").classes("dot")
                ui.element("div").classes("dot")
                ui.label("Đang xử lý...").style(
                    f"color: {HEINEKEN_GREEN_PRIMARY}; font-size: 0.9rem;"
                )

        try:
            answer = await asyncio.wait_for(
                ask_question(question, session_id),
                timeout=60,
            )
            thinking.delete()
            add_message(answer, "msg-assistant")
        except asyncio.TimeoutError:
            thinking.delete()
            add_message(
                "Câu trả lời vượt quá thời gian chờ (60 giây). Vui lòng thử lại.",
                "msg-timeout",
            )
        except Exception as e:
            thinking.delete()
            add_message(f"Lỗi xử lý: {e}", "msg-error")
        finally:
            input_field.enabled = True
            send_btn.enabled = True
            input_field.run_method("focus")

    input_field.on("keydown.enter", handle_send)
    send_btn.on_click(handle_send)
