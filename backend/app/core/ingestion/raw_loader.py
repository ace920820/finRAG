from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Iterable


COLLECTION_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


try:
    import fitz
except Exception:  # pragma: no cover - PyMuPDF is expected to exist in the backend env
    fitz = None


@dataclass(frozen=True)
class RawDocument:
    path: Path
    source_name: str
    title: str
    body: str
    frontmatter: dict[str, str] = field(default_factory=dict)
    collection_name: str | None = None


def discover_raw_inputs(raw_root: Path, collection_name: str | None = None, source_dir: Path | None = None) -> list[Path]:
    _validate_collection_name(collection_name)
    roots = _candidate_roots(raw_root, collection_name, source_dir)
    paths: list[Path] = []
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        for path in root.rglob("*"):
            if "_meta" in path.parts:
                continue
            if not path.is_file():
                continue
            if path.name.startswith("._"):
                continue
            if path.suffix.lower() not in {".md", ".txt", ".pdf"}:
                continue
            paths.append(path)
    return sorted(set(paths), key=lambda item: item.as_posix())


def load_raw_documents(raw_root: Path, collection_name: str | None = None, source_dir: Path | None = None) -> list[RawDocument]:
    return [parse_raw_document(path, collection_name=_collection_for_path(path, raw_root, collection_name)) for path in discover_raw_inputs(raw_root, collection_name, source_dir)]


def parse_raw_document(path: Path, collection_name: str | None = None) -> RawDocument:
    if path.suffix.lower() == ".pdf":
        text = _extract_pdf_text(path)
        frontmatter, body = {}, text
    else:
        text = path.read_text(encoding="utf-8")
        frontmatter, body = _split_frontmatter(text) if path.suffix.lower() == ".md" else ({}, text)
    body = _extract_body_text(body)
    title = _title_from_metadata(path, frontmatter, body)
    return RawDocument(
        path=path,
        source_name=str(frontmatter.get("source_pdf_name") or path.name),
        title=title,
        body=body.strip(),
        frontmatter=frontmatter,
        collection_name=str(frontmatter.get("collection") or collection_name or "default"),
    )


def _candidate_roots(raw_root: Path, collection_name: str | None, source_dir: Path | None) -> Iterable[Path]:
    if source_dir is not None:
        yield source_dir
        return
    if collection_name:
        yield raw_root / "extracted" / collection_name
        yield raw_root / "manual" / collection_name
        return
    yield raw_root / "extracted"
    yield raw_root / "manual"


def _validate_collection_name(collection_name: str | None) -> None:
    if collection_name is None:
        return
    if not COLLECTION_NAME_RE.fullmatch(collection_name):
        raise ValueError("collection_name must contain only letters, numbers, hyphen, or underscore")


def _collection_for_path(path: Path, raw_root: Path, collection_name: str | None) -> str | None:
    if collection_name:
        return collection_name
    try:
        relative = path.relative_to(raw_root)
    except ValueError:
        return None
    parts = relative.parts
    if len(parts) >= 3 and parts[0] in {"extracted", "manual"}:
        return parts[1]
    return None


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    values: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return values, "\n".join(lines[index + 1 :])
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = _unquote(value.strip())
    return {}, text


def _extract_body_text(body: str) -> str:
    marker = "## Extracted Text"
    if marker not in body:
        return body.strip()
    return body.split(marker, 1)[1].strip()


def _title_from_metadata(path: Path, frontmatter: dict[str, str], body: str) -> str:
    if frontmatter.get("title"):
        return frontmatter["title"]
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.stem.replace("_", " ").strip() or path.name


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    return value


def _extract_pdf_text(path: Path) -> str:
    if fitz is None:
        raise RuntimeError("PyMuPDF is required to read PDF inputs")
    lines: list[str] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            page_text = (page.get_text("text") or "").strip()
            if not page_text:
                continue
            lines.append(f"<!-- page: {page_index} -->")
            lines.append(page_text)
            lines.append("")
    return "\n".join(lines).strip()
