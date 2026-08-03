from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._client = None
        self._next_index = 0

        try:
            import chromadb

            # Ephemeral in-memory ChromaDB client.
            self._client = chromadb.Client()

            # Inner-product search is consistent with the _dot-based
            # similarity used by the fallback implementation.
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "ip"},
            )

            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None
            self._client = None

    @staticmethod
    def _normalize_metadata_for_chroma(
        metadata: dict[str, Any],
    ) -> dict[str, str | int | float | bool]:
        """
        Convert metadata values into types accepted by ChromaDB.

        Nested dictionaries, lists and other unsupported values are
        converted to strings.
        """
        normalized: dict[str, str | int | float | bool] = {}

        for key, value in metadata.items():
            normalized_key = str(key)

            if value is None:
                continue

            if isinstance(value, (str, int, float, bool)):
                normalized[normalized_key] = value
            else:
                normalized[normalized_key] = str(value)

        # Some ChromaDB versions reject empty metadata dictionaries.
        if not normalized:
            normalized["_empty_metadata"] = True

        return normalized

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document."""
        content = getattr(doc, "content", None)

        # Support Document models that use `text` instead of `content`.
        if content is None:
            content = getattr(doc, "text", None)

        if not isinstance(content, str):
            raise TypeError(
                "Document content must be a string stored in "
                "`doc.content` or `doc.text`."
            )

        raw_metadata = getattr(doc, "metadata", None)

        if raw_metadata is None:
            metadata: dict[str, Any] = {}
        elif isinstance(raw_metadata, dict):
            metadata = dict(raw_metadata)
        else:
            try:
                metadata = dict(raw_metadata)
            except (TypeError, ValueError) as exc:
                raise TypeError(
                    "Document metadata must be dictionary-like."
                ) from exc

        # Preserve a document-level ID when the model provides one.
        document_id = getattr(doc, "doc_id", None)

        if document_id is not None:
            metadata.setdefault("doc_id", str(document_id))

        # Preserve a generic source ID, but generate a separate unique
        # chunk ID for storage.
        source_id = getattr(doc, "id", None)

        if source_id is not None:
            metadata.setdefault("source_id", str(source_id))

        record_id = f"{self._collection_name}_{self._next_index}"
        self._next_index += 1

        embedding = [
            float(value)
            for value in self._embedding_fn(content)
        ]

        return {
            "id": record_id,
            "content": content,
            "document": content,
            "metadata": metadata,
            "embedding": embedding,
        }

    @staticmethod
    def _format_search_result(
        record: dict[str, Any],
        score: float,
    ) -> dict[str, Any]:
        """Convert an internal record into a public search result."""
        return {
            "id": record["id"],
            "content": record["content"],
            "document": record["content"],
            "metadata": dict(record.get("metadata", {})),
            "score": float(score),
            "similarity": float(score),
        }

    def _search_records(
        self,
        query: str,
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Run in-memory similarity search over provided records."""
        if top_k <= 0 or not records:
            return []

        query_embedding = [
            float(value)
            for value in self._embedding_fn(query)
        ]

        ranked_results: list[dict[str, Any]] = []

        for record in records:
            stored_embedding = record.get("embedding", [])

            if len(query_embedding) != len(stored_embedding):
                raise ValueError(
                    "Query embedding and stored embedding must have "
                    "the same number of dimensions. "
                    f"Received {len(query_embedding)} and "
                    f"{len(stored_embedding)}."
                )

            similarity = _dot(
                query_embedding,
                stored_embedding,
            )

            ranked_results.append(
                self._format_search_result(
                    record=record,
                    score=similarity,
                )
            )

        ranked_results.sort(
            key=lambda result: result["score"],
            reverse=True,
        )

        return ranked_results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(
            ids=[...],
            documents=[...],
            embeddings=[...],
        ).

        A local mirror is also maintained for deterministic filtering,
        deletion and fallback behavior.
        """
        if not docs:
            return

        records = [
            self._make_record(doc)
            for doc in docs
        ]

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[
                        record["id"]
                        for record in records
                    ],
                    documents=[
                        record["content"]
                        for record in records
                    ],
                    embeddings=[
                        record["embedding"]
                        for record in records
                    ],
                    metadatas=[
                        self._normalize_metadata_for_chroma(
                            record["metadata"]
                        )
                        for record in records
                    ],
                )
            except Exception:
                # Continue using the in-memory mirror if ChromaDB
                # fails at runtime.
                self._use_chroma = False
                self._collection = None
                self._client = None

        self._store.extend(records)

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        Uses ChromaDB when available. Falls back to dot-product search
        over the in-memory records.
        """
        if top_k <= 0 or not self._store:
            return []

        if self._use_chroma and self._collection is not None:
            try:
                query_embedding = [
                    float(value)
                    for value in self._embedding_fn(query)
                ]

                collection_size = self._collection.count()
                result_count = min(top_k, collection_size)

                if result_count <= 0:
                    return []

                chroma_results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=result_count,
                    include=[
                        "documents",
                        "metadatas",
                        "distances",
                    ],
                )

                result_ids = (
                    chroma_results.get("ids", [[]])[0]
                    or []
                )
                distances = (
                    chroma_results.get("distances", [[]])[0]
                    or []
                )

                records_by_id = {
                    record["id"]: record
                    for record in self._store
                }

                results: list[dict[str, Any]] = []

                for index, record_id in enumerate(result_ids):
                    record = records_by_id.get(record_id)

                    if record is None:
                        continue

                    distance = (
                        float(distances[index])
                        if index < len(distances)
                        else 1.0
                    )

                    # With hnsw:space="ip", ChromaDB returns:
                    # distance = 1 - inner_product.
                    similarity = 1.0 - distance

                    results.append(
                        self._format_search_result(
                            record=record,
                            score=similarity,
                        )
                    )

                if results:
                    return results[:top_k]

            except Exception:
                # ChromaDB may be installed but unavailable or
                # incompatible at runtime.
                pass

        return self._search_records(
            query=query,
            records=self._store,
            top_k=top_k,
        )

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run
        similarity search.
        """
        if top_k <= 0:
            return []

        if not metadata_filter:
            return self._search_records(
                query=query,
                records=self._store,
                top_k=top_k,
            )

        filtered_records = [
            record
            for record in self._store
            if all(
                record.get("metadata", {}).get(key) == expected_value
                for key, expected_value in metadata_filter.items()
            )
        ]

        return self._search_records(
            query=query,
            records=filtered_records,
            top_k=top_k,
        )

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        ids_to_delete = [
            record["id"]
            for record in self._store
            if any(
                str(record.get("metadata", {}).get(id_key))
                == str(doc_id)
                for id_key in ("doc_id", "source_id")
            )
        ]

        if not ids_to_delete:
            return False

        ids_to_delete_set = set(ids_to_delete)

        self._store = [
            record
            for record in self._store
            if record["id"] not in ids_to_delete_set
        ]

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=ids_to_delete)
            except Exception:
                # The in-memory source of truth has already been updated.
                pass

        return True
