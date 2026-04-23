import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
MEMORY_DIR = PROJECT_ROOT / Path(os.getenv("MEMORY_DIR", "demo_memory"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.inter-k.com")
AI_LEGAL_MODEL = os.getenv("AI_LEGAL_MODEL", "kCode")

RESPONSE_TIMEOUT_SECONDS = 60

# Memory / context window settings
MAX_CONTEXT_TOKENS = 100_000
CONTEXT_SUMMARIZE_TRIGGER_TOKENS = 80_000
CONTEXT_KEEP_MESSAGES = 20
