from langchain.chat_models import init_chat_model

from app.config import AI_LEGAL_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL


def build_llm():
    """Create and return the LLM instance configured for the OpenAI-compatible endpoint."""
    return init_chat_model(
        AI_LEGAL_MODEL,
        model_provider="openai",
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        temperature=0.3,
        max_tokens=4096,
    )
