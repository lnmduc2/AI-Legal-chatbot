from pathlib import Path

from app.config import DOCS_DIR
from app.prompts import group_documents_by_section, list_markdown_documents


def validate_workspace():
    """Ensure the docs workspace exists and contains markdown sources."""
    if not DOCS_DIR.exists():
        raise FileNotFoundError(f"Workspace docs directory missing: {DOCS_DIR}")

    documents = list_markdown_documents()
    if not documents:
        raise FileNotFoundError(f"No markdown documents found under: {DOCS_DIR}")


def get_workspace_summary() -> str:
    """Return a summary of available documents for the agent workspace."""
    lines = ["Agent Workspace Documents:", ""]
    grouped = group_documents_by_section()

    if not grouped:
        lines.append("- No markdown documents available.")
        return "\n".join(lines)

    ordered_sections = sorted(
        grouped,
        key=lambda section: (
            0 if section in {"faq", "policy", "law"} else 1,
            section,
        ),
    )

    for section in ordered_sections:
        lines.append(f"[{section}]")
        for path in grouped[section]:
            size_kb = path.stat().st_size / 1024
            lines.append(
                f"- {path.relative_to(DOCS_DIR.parent)} ({size_kb:.1f} KB)"
            )
        lines.append("")

    return "\n".join(lines).rstrip()
