from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


PAGE_MARKER_RE = re.compile(r"<!--\s*page:\s*(\d+)\s*-->", re.IGNORECASE)
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[。！？.!?；;])\s+")


@dataclass(frozen=True)
class TextChunk:
    section: str
    page_num: int | None
    chunk_index: int
    content: str


def chunk_text(text: str, target_chars: int = 900) -> list[TextChunk]:
    paragraphs = list(_paragraphs_with_pages(text))
    chunks: list[TextChunk] = []
    buffer: list[str] = []
    current_page: int | None = None

    def flush() -> None:
        nonlocal buffer, current_page
        content = "\n\n".join(part for part in buffer if part.strip()).strip()
        if not content:
            buffer = []
            return
        chunks.append(TextChunk(
            section=f"chunk-{len(chunks) + 1}",
            page_num=current_page,
            chunk_index=len(chunks),
            content=content,
        ))
        buffer = []

    for page_num, paragraph in paragraphs:
        for paragraph_part in _split_long_paragraph(paragraph, target_chars):
            if not paragraph_part.strip():
                continue
            if current_page is None:
                current_page = page_num
            prospective = "\n\n".join(buffer + [paragraph_part]).strip()
            if buffer and len(prospective) > target_chars:
                flush()
                current_page = page_num
            elif page_num is not None and current_page is not None and page_num != current_page and buffer:
                flush()
                current_page = page_num
            if current_page is None:
                current_page = page_num
            buffer.append(paragraph_part.strip())
    flush()
    return chunks


def _paragraphs_with_pages(text: str) -> Iterable[tuple[int | None, str]]:
    current_page: int | None = None
    pending: list[str] = []
    for line in text.splitlines():
        marker = PAGE_MARKER_RE.search(line)
        if marker:
            if pending:
                yield current_page, "\n".join(pending).strip()
                pending = []
            current_page = int(marker.group(1))
            continue
        if line.strip():
            pending.append(line.strip())
            continue
        if pending:
            yield current_page, "\n".join(pending).strip()
            pending = []
    if pending:
        yield current_page, "\n".join(pending).strip()


def _split_long_paragraph(paragraph: str, target_chars: int) -> list[str]:
    paragraph = paragraph.strip()
    if len(paragraph) <= target_chars:
        return [paragraph]

    parts: list[str] = []
    buffer = ""
    for sentence in SENTENCE_BOUNDARY_RE.split(paragraph):
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > target_chars:
            if buffer:
                parts.append(buffer.strip())
                buffer = ""
            parts.extend(_hard_wrap(sentence, target_chars))
            continue
        prospective = f"{buffer} {sentence}".strip() if buffer else sentence
        if buffer and len(prospective) > target_chars:
            parts.append(buffer.strip())
            buffer = sentence
        else:
            buffer = prospective
    if buffer:
        parts.append(buffer.strip())
    return parts or _hard_wrap(paragraph, target_chars)


def _hard_wrap(text: str, target_chars: int) -> list[str]:
    return [text[index:index + target_chars].strip() for index in range(0, len(text), target_chars) if text[index:index + target_chars].strip()]
