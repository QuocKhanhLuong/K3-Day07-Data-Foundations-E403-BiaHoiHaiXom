from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if self.overlap < 0:
            raise ValueError("overlap must be non-negative")

        if self.overlap >= self.chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []

        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)

            if start + self.chunk_size >= len(text):
                break

        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Split after sentence-ending punctuation followed by whitespace.
        # The punctuation itself is retained because lookbehind is used.
        sentence_pattern = r"(?<=[.!?])[ \t]+|(?<=\.)\r?\n+"

        sentences = [
            sentence.strip()
            for sentence in re.split(sentence_pattern, text.strip())
            if sentence.strip()
        ]

        chunks: list[str] = []

        for start in range(
            0,
            len(sentences),
            self.max_sentences_per_chunk,
        ):
            sentence_group = sentences[
                start : start + self.max_sentences_per_chunk
            ]

            chunk = " ".join(sentence_group).strip()

            if chunk:
                chunks.append(chunk)

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\\n\\n", "\\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        separators: list[str] | None = None,
        chunk_size: int = 500,
    ) -> None:
        self.separators = (
            self.DEFAULT_SEPARATORS
            if separators is None
            else list(separators)
        )
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        raw_chunks = self._split(
            current_text=text.strip(),
            remaining_separators=self.separators,
        )

        # Remove chunks containing only whitespace and normalize
        # whitespace around chunk boundaries.
        return [
            current_chunk.strip()
            for current_chunk in raw_chunks
            if current_chunk.strip()
        ]

    def _split(
        self,
        current_text: str,
        remaining_separators: list[str],
    ) -> list[str]:
        """
        Recursively split current_text until every chunk is at most
        self.chunk_size characters long.
        """
        if not current_text:
            return []

        if len(current_text) <= self.chunk_size:
            return [current_text]

        # No separators remain, so perform a hard character split.
        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size]
                for start in range(
                    0,
                    len(current_text),
                    self.chunk_size,
                )
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Empty separator means character-level splitting.
        if separator == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(
                    0,
                    len(current_text),
                    self.chunk_size,
                )
            ]

        # Try the next separator when the current one is not present.
        if separator not in current_text:
            return self._split(
                current_text=current_text,
                remaining_separators=next_separators,
            )

        raw_parts = current_text.split(separator)
        parts: list[str] = []

        # Reattach separators so punctuation and line breaks are not
        # silently discarded during recursive splitting.
        for index, part in enumerate(raw_parts):
            is_last_part = index == len(raw_parts) - 1

            if not is_last_part:
                parts.append(part + separator)
            elif part:
                parts.append(part)

        chunks: list[str] = []
        current_chunk = ""

        for part in parts:
            # The part itself is still too large. Split it again using
            # separators with lower priority.
            if len(part) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""

                chunks.extend(
                    self._split(
                        current_text=part,
                        remaining_separators=next_separators,
                    )
                )
                continue

            candidate = current_chunk + part

            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk)

                current_chunk = part

        if current_chunk:
            chunks.append(current_chunk)

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(
    vec_a: list[float],
    vec_b: list[float],
) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if len(vec_a) != len(vec_b):
        raise ValueError(
            "Vectors must have the same number of dimensions"
        )

    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        # FixedSizeChunker requires overlap < chunk_size.
        overlap = min(50, chunk_size - 1)

        strategy_chunks = {
            "fixed_size": FixedSizeChunker(
                chunk_size=chunk_size,
                overlap=overlap,
            ).chunk(text),
            "by_sentences": SentenceChunker(
                max_sentences_per_chunk=3,
            ).chunk(text),
            "recursive": RecursiveChunker(
                chunk_size=chunk_size,
            ).chunk(text),
        }

        comparison: dict[str, dict] = {}

        for strategy_name, chunks in strategy_chunks.items():
            chunk_lengths = [len(chunk) for chunk in chunks]

            if chunk_lengths:
                average_length = (
                    sum(chunk_lengths) / len(chunk_lengths)
                )
                minimum_length = min(chunk_lengths)
                maximum_length = max(chunk_lengths)
            else:
                average_length = 0.0
                minimum_length = 0
                maximum_length = 0

            comparison[strategy_name] = {
                "chunks": chunks,
                "count": len(chunks),
                "avg_length": average_length,
                "num_chunks": len(chunks),
                "total_characters": sum(chunk_lengths),
                "min_chunk_length": minimum_length,
                "max_chunk_length": maximum_length,
                "avg_chunk_length": average_length,
            }

        return comparison
