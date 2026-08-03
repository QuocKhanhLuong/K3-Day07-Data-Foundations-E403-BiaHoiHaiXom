from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        context_parts = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata") or {}
            source = metadata.get("source_url") or metadata.get("source")
            source_label = f"\nSource: {source}" if source else ""
            context_parts.append(f"[Chunk {index}]{source_label}\n{result.get('content', '')}")

        context = "\n\n".join(context_parts) or "(No relevant context was retrieved.)"
        prompt = (
            "Answer the question using only the retrieved context. "
            "If the context does not contain enough information, say so clearly.\n\n"
            f"Retrieved context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
