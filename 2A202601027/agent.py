from __future__ import annotations

import os
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

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str] | None = None) -> None:
        self.store = store
        if llm_fn is not None:
            self.llm_fn = llm_fn
        else:
            self.llm_fn = create_default_llm_fn()

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        context_parts = []
        for index, r in enumerate(results, 1):
            context_parts.append(f"[{index}] {r.get('content', '')}")
        context = "\n\n".join(context_parts)

        prompt = (
            f"You are a helpful knowledge assistant. Answer the question using only the context provided below.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )

        return self.llm_fn(prompt)


def create_default_llm_fn(model_name: str = "gpt-4o-mini") -> Callable[[str], str]:
    """
    Creates an LLM function that calls OpenAI if OPENAI_API_KEY is present,
    otherwise falls back to a deterministic dummy preview response.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            def _openai_call(prompt: str) -> str:
                response = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", model_name),
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                return response.choices[0].message.content or ""

            return _openai_call
        except Exception:
            pass

    def _fallback_llm(prompt: str) -> str:
        return f"[DEMO LLM] Answer generated from context preview: {prompt[:300]}..."

    return _fallback_llm
