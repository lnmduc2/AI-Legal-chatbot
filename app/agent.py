import uuid

from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.middleware.summarization import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from app.config import (
    CONTEXT_KEEP_MESSAGES,
    CONTEXT_SUMMARIZE_TRIGGER_TOKENS,
    DOCS_DIR,
    MEMORY_DIR,
)
from app.doc_index import DOCS_INDEX_DIR, DOCS_INDEX_MOUNT, ensure_doc_indexes
from app.llm import build_llm
from app.prompts import build_system_prompt, get_documents_signature

MEMORY_DIR.mkdir(parents=True, exist_ok=True)

_agent_cache: dict[str, Any] = {}

DOCS_MOUNT = "/docs"


class _CustomSummarization(SummarizationMiddleware):
    """Wrapper that changes the middleware name to avoid DeepAgents duplicate check."""

    @property
    def name(self) -> str:
        return "CustomSummarization"


def _build_agent():
    """Create a deep agent with checkpointing, summarization, and filesystem-backed memory."""
    ensure_doc_indexes()
    llm = build_llm()

    backend = CompositeBackend(
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
    )

    summarization = _CustomSummarization(
        model=llm,
        backend=backend,
        trigger=("tokens", CONTEXT_SUMMARIZE_TRIGGER_TOKENS),
        keep=("messages", CONTEXT_KEEP_MESSAGES),
    )

    checkpointer = InMemorySaver()

    return create_deep_agent(
        model=llm,
        system_prompt=build_system_prompt(),
        backend=backend,
        middleware=(summarization,),
        checkpointer=checkpointer,
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

    messages = result.get("messages", [])
    if messages:
        text = _message_text(messages[-1])
        if text:
            return text
    return "Cơ sở kiến thức hiện tại không đủ để tạo ra câu trả lời hoàn chỉnh cho câu hỏi này."
