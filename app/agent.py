import uuid

from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

from app.config import DOCS_DIR, MEMORY_DIR
from app.doc_index import DOCS_INDEX_DIR, DOCS_INDEX_MOUNT, ensure_doc_indexes
from app.llm import build_llm
from app.prompts import build_system_prompt, get_documents_signature

MEMORY_DIR.mkdir(parents=True, exist_ok=True)

_agent_cache: dict[str, Any] = {}

DOCS_MOUNT = "/docs"


def _build_agent():
    """Create a deep agent with filesystem-backed memory and docs workspace."""
    ensure_doc_indexes()
    llm = build_llm()
    return create_deep_agent(
        model=llm,
        system_prompt=build_system_prompt(),
        backend=CompositeBackend(
            default=StateBackend(),
            routes={
                "/memories/": FilesystemBackend(
                    root_dir=str(MEMORY_DIR), virtual_mode=True
                ),
                DOCS_MOUNT: FilesystemBackend(
                    root_dir=str(DOCS_DIR), virtual_mode=True
                ),
                DOCS_INDEX_MOUNT: FilesystemBackend(
                    root_dir=str(DOCS_INDEX_DIR), virtual_mode=True
                ),
            },
        ),
    )


def _message_text(message: Any) -> str:
    """Extract plain text content from an agent message."""
    content = getattr(message, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()

    text_parts: list[str] = []
    for block in getattr(message, "content_blocks", []) or []:
        if isinstance(block, dict) and block.get("type") == "text":
            text = str(block.get("text", "")).strip()
            if text:
                text_parts.append(text)
    return "\n".join(text_parts).strip()


def _is_final_answer(text: str) -> bool:
    """Check whether a message looks like the final answer for the user."""
    normalized = text.strip().lower()
    if not normalized:
        return False

    planning_prefixes = (
        "tôi sẽ",
        "tôi cần",
        "trước tiên",
        "để trả lời",
        "mình sẽ",
    )
    if any(normalized.startswith(prefix) for prefix in planning_prefixes):
        return False

    return "nguồn tham khảo" in normalized


def _extract_best_answer(messages: list[Any]) -> str:
    """Return the latest user-facing answer from the agent conversation."""
    for message in reversed(messages):
        if type(message).__name__ != "AIMessage":
            continue
        text = _message_text(message)
        if _is_final_answer(text):
            return text
    return ""


def get_agent():
    """Get or create a cached deep agent instance."""
    documents_signature = get_documents_signature()
    cached_signature = _agent_cache.get("documents_signature")

    if (
        "default" not in _agent_cache
        or cached_signature != documents_signature
    ):
        _agent_cache["default"] = _build_agent()
        _agent_cache["documents_signature"] = documents_signature
    return _agent_cache["default"]


async def ask_question(question: str, session_id: str | None = None) -> str:
    """Submit a question to the deep agent and return the grounded answer."""
    if not session_id:
        session_id = str(uuid.uuid4())

    agent = get_agent()
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"configurable": {"thread_id": session_id}},
    )

    answer = _extract_best_answer(result.get("messages", []))
    if answer:
        return answer
    return "Cơ sở kiến thức hiện tại không đủ để tạo ra câu trả lời hoàn chỉnh cho câu hỏi này."
