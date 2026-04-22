import re
import shutil
from pathlib import Path

from app.config import DOCS_DIR, PROJECT_ROOT

GENERATED_DOCS_DIR = PROJECT_ROOT / ".generated_docs"
DOCS_INDEX_DIR = GENERATED_DOCS_DIR / "docs_index"
DOCS_INDEX_MOUNT = "/docs-index"

ARTICLE_RE = re.compile(r"Điều\s+\d+[\.:]?\s*.*")
CHAPTER_RE = re.compile(r"Chương\s+[IVXLC0-9]+[\.:]?\s*.*", re.IGNORECASE)


def _list_markdown_documents() -> list[Path]:
    if not DOCS_DIR.exists():
        return []
    return sorted(
        (path for path in DOCS_DIR.rglob("*.md") if path.is_file()),
        key=lambda path: str(path.relative_to(DOCS_DIR)),
    )


def _first_nonempty_line(lines: list[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped
    return "Untitled document"


def _clean_inline_whitespace(text: str) -> str:
    return " ".join(text.split())


def _extract_markdown_headings(lines: list[str]) -> list[str]:
    headings: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            headings.append(_clean_inline_whitespace(stripped.lstrip("# ")))
        elif stripped.startswith("**") and stripped.endswith("**"):
            headings.append(_clean_inline_whitespace(stripped.strip("*")))
    return headings[:80]


def _extract_law_headings(lines: list[str]) -> list[str]:
    headings: list[str] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        candidates = [stripped]
        if index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            if next_line:
                candidates.append(f"{stripped}{next_line}")
                candidates.append(f"{stripped} {next_line}")

        for candidate in candidates:
            normalized = _clean_inline_whitespace(candidate.replace("## ", ""))
            if ARTICLE_RE.match(normalized) or CHAPTER_RE.match(normalized):
                if normalized not in headings:
                    headings.append(normalized)
                break
    return headings[:120]


def _extract_law_footer_metadata(lines: list[str]) -> list[str]:
    metadata: list[str] = []
    tail_lines = lines[-60:]

    for index, line in enumerate(tail_lines):
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("Luật này được Quốc hội"):
            metadata.append(_clean_inline_whitespace(stripped))

        if "CHỦ TỊCH QUỐC HỘI" in stripped.upper():
            metadata.append("Chức danh ký: CHỦ TỊCH QUỐC HỘI")
            next_nonempty = ""
            for candidate in tail_lines[index + 1:]:
                candidate = candidate.strip()
                if candidate:
                    next_nonempty = _clean_inline_whitespace(candidate.replace("## ", ""))
                    break
            if next_nonempty:
                metadata.append(f"Người ký: {next_nonempty}")

    return metadata


def _build_index_for_document(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    relative_path = path.relative_to(DOCS_DIR).as_posix()
    title = _first_nonempty_line(lines)
    section = path.relative_to(DOCS_DIR).parts[0] if len(path.relative_to(DOCS_DIR).parts) > 1 else "root"

    headings = (
        _extract_law_headings(lines)
        if section == "law"
        else _extract_markdown_headings(lines)
    )
    footer_metadata = _extract_law_footer_metadata(lines) if section == "law" else []

    output_lines = [
        f"# Document Index: {relative_path}",
        "",
        f"- Original path: /docs/{relative_path}",
        f"- Section: {section}",
        f"- Title/first line: {title}",
        "",
    ]

    if footer_metadata:
        output_lines.append("## Footer metadata")
        output_lines.extend(f"- {item}" for item in footer_metadata)
        output_lines.append("")

    if headings:
        if section == "law":
            output_lines.append("## Article and chapter headings")
        else:
            output_lines.append("## Key headings")
        output_lines.extend(f"- {heading}" for heading in headings)
    else:
        output_lines.extend(
            [
                "## Preview",
                *[f"- {_clean_inline_whitespace(line.strip())}" for line in lines if line.strip()][:12],
            ]
        )

    output_lines.append("")
    output_lines.append(
        "Use this index to locate the right source quickly, then read the original file under /docs for exact wording and citations."
    )
    output_lines.append("")
    return "\n".join(output_lines)


def ensure_doc_indexes() -> None:
    """Rebuild lightweight document indexes for fast agent routing."""
    shutil.rmtree(DOCS_INDEX_DIR, ignore_errors=True)
    DOCS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

    for path in _list_markdown_documents():
        target_path = DOCS_INDEX_DIR / path.relative_to(DOCS_DIR)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(_build_index_for_document(path), encoding="utf-8")
