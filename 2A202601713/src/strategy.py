"""Heading-aware chunking strategy used by Lương Quốc Khánh.

The strategy keeps the Markdown heading hierarchy in every chunk.  A long
section is passed to the existing :class:`RecursiveChunker`, with the heading
context accounted for in the available chunk budget.
"""
from __future__ import annotations

import re

try:
    from .chunking import RecursiveChunker
except ImportError:  # Allow the common root runner to load this file directly.
    from src.chunking import RecursiveChunker


class HeadingAwareChunker:
    """Split Markdown by headings, then recursively split long sections.

    ``chunk_size`` is a character budget for the final chunk, including its
    heading context.  Short sections remain intact; only sections whose body
    does not fit are sent through ``RecursiveChunker``.
    """

    HEADING_PATTERN = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")

    def __init__(
        self,
        chunk_size: int = 800,
        separators: list[str] | None = None,
    ) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size
        self.separators = (
            list(RecursiveChunker.DEFAULT_SEPARATORS)
            if separators is None
            else list(separators)
        )
        self.last_stats: dict[str, int] = {}

    @staticmethod
    def _clean_heading_title(title: str) -> str:
        """Remove optional closing Markdown hashes from a heading title."""
        return re.sub(r"[ \t]+#+[ \t]*$", "", title).strip()

    def _sectionize(self, text: str) -> list[tuple[tuple[tuple[int, str], ...], str]]:
        """Return ``(heading_stack, body)`` sections in document order."""
        sections: list[tuple[tuple[tuple[int, str], ...], str]] = []
        heading_stack: list[tuple[int, str]] = []
        body_lines: list[str] = []

        def flush() -> None:
            body = "\n".join(body_lines).strip()
            if body:
                sections.append((tuple(heading_stack), body))
            body_lines.clear()

        for line in text.splitlines():
            match = self.HEADING_PATTERN.match(line)
            if match:
                flush()
                level = len(match.group(1))
                title = self._clean_heading_title(match.group(2))
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, title))
            else:
                body_lines.append(line)
        flush()
        return sections

    @staticmethod
    def _heading_context(heading_stack: tuple[tuple[int, str], ...]) -> str:
        return "\n".join(f"{'#' * level} {title}" for level, title in heading_stack)

    def chunk(self, text: str) -> list[str]:
        """Chunk Markdown while preserving heading context in each result."""
        self.last_stats = {
            "section_count": 0,
            "fallback_sections": 0,
            "chunk_count": 0,
            "max_chunk_length": 0,
        }
        if not text or not text.strip():
            return []

        sections = self._sectionize(text)
        self.last_stats["section_count"] = len(sections)
        chunks: list[str] = []

        for heading_stack, body in sections:
            context = self._heading_context(heading_stack)
            separator_length = 2 if context else 0
            available = self.chunk_size - len(context) - separator_length

            if len(body) <= available:
                pieces = [body]
            else:
                self.last_stats["fallback_sections"] += 1
                fallback_size = max(1, available)
                fallback = RecursiveChunker(
                    separators=self.separators,
                    chunk_size=fallback_size,
                )
                pieces = fallback.chunk(body)

            for piece in pieces:
                piece = piece.strip()
                if not piece:
                    continue
                chunk = f"{context}\n\n{piece}" if context else piece
                chunks.append(chunk)

        self.last_stats["chunk_count"] = len(chunks)
        self.last_stats["max_chunk_length"] = max((len(chunk) for chunk in chunks), default=0)
        return chunks


# Descriptive alias for callers that want the fallback behavior in the name.
HeadingAwareRecursiveChunker = HeadingAwareChunker


__all__ = ["HeadingAwareChunker", "HeadingAwareRecursiveChunker"]
