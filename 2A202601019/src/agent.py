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

    def __init__(
        self,
        store: EmbeddingStore,
        llm_fn: Callable[[str], str],
    ) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        """
        Answer a question using retrieved knowledge-base chunks.

        The LLM is instructed to rely only on the retrieved context and
        explicitly state when the context is insufficient.
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        results = self.store.search(
            query=question.strip(),
            top_k=top_k,
        )

        if not results:
            context = "No relevant context was found in the knowledge base."
        else:
            context_parts: list[str] = []

            for index, result in enumerate(results, start=1):
                content = result.get(
                    "content",
                    result.get("document", ""),
                )
                metadata = result.get("metadata", {})
                score = result.get(
                    "score",
                    result.get("similarity"),
                )

                header = f"[Context {index}]"

                if metadata:
                    header += f"\nMetadata: {metadata}"

                if score is not None:
                    header += f"\nSimilarity score: {float(score):.4f}"

                context_parts.append(
                    f"{header}\n{str(content).strip()}"
                )

            context = "\n\n".join(context_parts)

        prompt = f"""You are a knowledge-base assistant.

Use only the provided context to answer the user's question.
Do not invent facts that are not supported by the context.
If the context does not contain enough information, clearly say that
the knowledge base does not provide sufficient information.

Context:
{context}

Question:
{question.strip()}

Answer:
"""

        return self.llm_fn(prompt)