from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot, compute_similarity
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
        self._next_index = 0

        try:
            import chromadb

            self._chroma_client = chromadb.Client()
            self._collection = self._chroma_client.get_or_create_collection(self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document."""
        embedding = self._embedding_fn(doc.content)
        metadata = dict(doc.metadata) if doc.metadata else {}
        metadata["doc_id"] = doc.id
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Run in-memory similarity search over provided records."""
        if not records:
            return []

        query_emb = self._embedding_fn(query)
        scored_records = []

        for rec in records:
            score = compute_similarity(query_emb, rec["embedding"])
            scored_records.append({
                "id": rec["id"],
                "content": rec["content"],
                "metadata": rec["metadata"],
                "score": score,
            })

        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            rec = self._make_record(doc)
            self._store.append(rec)

        if self._use_chroma and self._collection is not None:
            try:
                ids = [f"{doc.id}_{self._next_index + i}" for i, doc in enumerate(docs)]
                self._next_index += len(docs)
                documents = [doc.content for doc in docs]
                metadatas = [rec["metadata"] for rec in self._store[-len(docs):]]
                embeddings = [rec["embedding"] for rec in self._store[-len(docs):]]
                self._collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                )
            except Exception:
                pass

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        filtered_records = []
        for rec in self._store:
            meta = rec.get("metadata", {})
            match = True
            for k, v in metadata_filter.items():
                if meta.get(k) != v:
                    match = False
                    break
            if match:
                filtered_records.append(rec)

        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        initial_size = len(self._store)
        self._store = [
            rec for rec in self._store
            if rec["id"] != doc_id and rec.get("metadata", {}).get("doc_id") != doc_id
        ]
        removed_count = initial_size - len(self._store)

        if self._use_chroma and self._collection is not None and removed_count > 0:
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                pass

        return removed_count > 0