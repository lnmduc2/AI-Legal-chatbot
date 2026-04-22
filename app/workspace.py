from pathlib import Path

from app.config import DOCS_DIR
from app.prompts import FAQ_PATH, LAW_PATH, POLICY_PATH


def validate_workspace():
    """Ensure the source documents exist in the expected workspace paths."""
    missing = []
    for path in [FAQ_PATH, POLICY_PATH, LAW_PATH]:
        if not Path(path).exists():
            missing.append(str(path))
    if missing:
        raise FileNotFoundError(
            f"Workspace documents missing: {', '.join(missing)}"
        )


def get_workspace_summary() -> str:
    """Return a summary of available documents for the agent workspace."""
    lines = ["Agent Workspace Documents:", ""]
    for path in [FAQ_PATH, POLICY_PATH, LAW_PATH]:
        p = Path(path)
        if p.exists():
            size_kb = p.stat().st_size / 1024
            lines.append(f"- {p.relative_to(DOCS_DIR.parent)} ({size_kb:.1f} KB)")
    return "\n".join(lines)
