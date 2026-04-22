import uuid

from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

from app.config import DOCS_DIR, MEMORY_DIR
from app.llm import build_llm
from app.prompts import SYSTEM_PROMPT

MEMORY_DIR.mkdir(parents=True, exist_ok=True)

_agent_cache: dict[str, Any] = {}

DOCS_MOUNT = "/docs"


def _build_agent():
    """Create a deep agent with filesystem-backed memory and docs workspace."""
    llm = build_llm()
    return create_deep_agent(
        model=llm,
        system_prompt=SYSTEM_PROMPT,
        backend=CompositeBackend(
            default=StateBackend(),
            routes={
                "/memories/": FilesystemBackend(
                    root_dir=str(MEMORY_DIR), virtual_mode=True
                ),
                DOCS_MOUNT: FilesystemBackend(
                    root_dir=str(DOCS_DIR), virtual_mode=True
                ),
            },
        ),
    )


def get_agent():
    """Get or create a cached deep agent instance."""
    if "default" not in _agent_cache:
        _agent_cache["default"] = _build_agent()
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

    final_message = result.get("messages", [])
    if final_message:
        return final_message[-1].content
    return "Không thể xử lý câu hỏi này."
